"""
Nimble web research integration (Phase 4.2).

Auth: Authorization: Bearer <NIMBLE_API_KEY>. Base URL: https://sdk.nimbleway.com.
(Ignore any legacy api.webit.live / Basic-auth docs found online — outdated.)

Endpoints:
    POST /v1/search  -- the digest workhorse. Returns results with
        title/description/url. search_depth "lite" (default) is
        token-efficient metadata-only; "deep" also fetches page content
        (+1 credit/page).
    POST /v1/extract -- DD reading. Returns clean markdown at data.markdown.
        If the returned markdown comes back suspiciously thin, automatically
        retries once with render=True (heavier headless-browser mode) — the
        caller doesn't have to remember to do this. Client timeout for
        extract calls specifically is 120s (they can be slow).

Retries via shared.with_retry(): retry on 429 (honor a retry_after field if
present), 5xx, and 555 (render timeout). Never retry 400/402 (bad request /
out of credits) — permanent failures, retrying wastes credits.

Rate limit (~83 req/s) is a non-issue at this project's scale — no
throttling built.

Credit usage logging: this key is on a shared Viola account, so every call
appends one line (endpoint, query/url, timestamp) to
.claude/data/state/nimble-usage.log for auditability.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

import httpx

import config
from integrations import registry
from shared import with_retry

INTEGRATION_NAME = "nimble"

# Extract responses shorter than this (chars) are considered "suspiciously
# thin" and trigger one automatic retry with render=True.
THIN_MARKDOWN_THRESHOLD = 200

DEFAULT_SEARCH_TIMEOUT_S = 30.0
EXTRACT_TIMEOUT_S = 120.0

# Status codes that must NEVER be retried — permanent failures that would
# waste credits on retry.
NON_RETRYABLE_STATUS = {400, 402}
RETRYABLE_STATUS = {429, 500, 502, 503, 504, 555}


class NimbleAPIError(Exception):
    """Raised for non-retryable Nimble API errors (400/402/other 4xx)."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"Nimble API error {status_code}: {message}")
        self.status_code = status_code


# === 1. Config ===
@dataclass
class NimbleResult:
    title: str
    description: str
    url: str


# === 2. Configuration check ===
def is_configured() -> bool:
    return registry.is_configured(INTEGRATION_NAME)


# === 3. Auth setup ===
def _headers() -> dict[str, str]:
    if not config.NIMBLE_API_KEY:
        raise RuntimeError(
            "NIMBLE_API_KEY not set — add it to .claude/scripts/.env"
        )
    return {
        "Authorization": f"Bearer {config.NIMBLE_API_KEY}",
        "Content-Type": "application/json",
    }


def _log_usage(endpoint: str, detail: str) -> None:
    """Append a one-line credit-usage log entry. Must never raise."""
    try:
        config.STATE_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = config.now_local().isoformat()
        # Keep detail short and single-line so the log stays greppable.
        safe_detail = " ".join(detail.split())[:200]
        line = f"{timestamp} | {endpoint} | {safe_detail}\n"
        with open(config.NIMBLE_USAGE_LOG, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass  # Usage logging must never break the actual API call.


def _raise_for_status(response: httpx.Response) -> None:
    """Raise NimbleAPIError for non-retryable errors, or a generic exception
    (carrying a .status_code) for retryable ones so with_retry() can act on it.
    """
    if response.status_code < 400:
        return

    if response.status_code in NON_RETRYABLE_STATUS:
        raise NimbleAPIError(response.status_code, response.text)

    # Retryable (or unknown) status — raise something with .status_code so
    # shared.with_retry()'s status_code check picks it up.
    error = httpx.HTTPStatusError(
        f"HTTP {response.status_code}", request=response.request, response=response
    )
    error.status_code = response.status_code  # type: ignore[attr-defined]
    raise error


# === 4. Query functions ===
def search(
    query: str,
    focus: str = "news",
    time_range: str = "week",
    max_results: int = 10,
    search_depth: str = "lite",
) -> list[NimbleResult]:
    """POST /v1/search — returns results with title/description/url."""

    def _call() -> httpx.Response:
        return httpx.post(
            f"{config.NIMBLE_BASE_URL}/v1/search",
            headers=_headers(),
            json={
                "query": query,
                "focus": focus,
                "time_range": time_range,
                "max_results": max_results,
                "search_depth": search_depth,
            },
            timeout=DEFAULT_SEARCH_TIMEOUT_S,
        )

    response = with_retry(_call)
    _raise_for_status(response)
    _log_usage("/v1/search", query)

    data = response.json()
    results = data.get("results", [])
    return [
        NimbleResult(
            title=r.get("title", ""),
            description=r.get("description", ""),
            url=r.get("url", ""),
        )
        for r in results
    ]


def extract(url: str, formats: list[str] | None = None, render: bool = False) -> str:
    """POST /v1/extract — returns clean markdown at data.markdown.

    If the returned markdown comes back suspiciously thin and render was not
    already True, automatically retries once with render=True.
    """
    formats = formats or ["markdown"]

    def _call(render_flag: bool) -> httpx.Response:
        return httpx.post(
            f"{config.NIMBLE_BASE_URL}/v1/extract",
            headers=_headers(),
            json={"url": url, "formats": formats, "render": render_flag},
            timeout=EXTRACT_TIMEOUT_S,
        )

    response = with_retry(lambda: _call(render))
    _raise_for_status(response)
    _log_usage("/v1/extract", f"{url} render={render}")

    markdown = response.json().get("data", {}).get("markdown", "") or ""

    if not render and len(markdown.strip()) < THIN_MARKDOWN_THRESHOLD:
        # Automatic fallback: retry once with a heavier headless-browser render.
        retry_response = with_retry(lambda: _call(True))
        _raise_for_status(retry_response)
        _log_usage("/v1/extract", f"{url} render=True (thin-markdown retry)")
        markdown = retry_response.json().get("data", {}).get("markdown", "") or markdown

    return markdown


# === 5. Context formatter ===
def format_for_context(results: list[NimbleResult]) -> str:
    """Render search results as plain text for an LLM prompt."""
    if not results:
        return "No results found."
    lines = [f"{len(results)} result(s):", ""]
    for r in results:
        lines.append(f"- {r.title}")
        if r.description:
            lines.append(f"  {r.description}")
        lines.append(f"  {r.url}")
    return "\n".join(lines)


# === 6. CLI wiring ===
def register_cli(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("nimble", help="Web research via Nimble")
    action_subparsers = parser.add_subparsers(dest="action", required=True)

    search_parser = action_subparsers.add_parser("search", help="Search the web")
    search_parser.add_argument("query")
    search_parser.add_argument("--focus", default="news")
    search_parser.add_argument("--time-range", default="week")
    search_parser.add_argument("--max-results", type=int, default=10)
    search_parser.add_argument("--search-depth", default="lite", choices=["lite", "deep"])

    extract_parser = action_subparsers.add_parser("extract", help="Extract page content as markdown")
    extract_parser.add_argument("url")
    extract_parser.add_argument("--render", action="store_true", help="Force headless-browser render")

    def _dispatch(args: argparse.Namespace) -> None:
        if args.action == "search":
            results = search(
                args.query,
                focus=args.focus,
                time_range=args.time_range,
                max_results=args.max_results,
                search_depth=args.search_depth,
            )
            print(format_for_context(results))
        elif args.action == "extract":
            markdown = extract(args.url, render=args.render)
            print(markdown)

    parser.set_defaults(func=_dispatch)
    search_parser.set_defaults(func=_dispatch)
    extract_parser.set_defaults(func=_dispatch)
