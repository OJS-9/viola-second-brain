"""
Reference template for a Second Brain integration module.

This file is documentation-as-code — it is NOT imported by registry.py,
query.py, or anything else. Copy this shape when adding a new integration
(e.g. a future Phase 4.3+ module) so every integration looks the same to
the CLI and to whoever reads the code next.

The pattern, in order:
    1. A dataclass holding whatever config the integration needs (base URL,
       timeouts, cached IDs) — NOT the secret itself. Secrets are read once
       from config.py (which loads them from .env) and passed to auth calls;
       they should never be stored on the dataclass or logged.
    2. is_configured() — a cheap check (usually just registry.is_configured())
       so callers can fail with a clear message instead of a stack trace.
    3. Auth setup — build whatever client object the SDK/API needs.
    4. Query functions — one function per operation, returning plain
       Python objects (dataclasses/dicts), never raw SDK response blobs,
       so callers don't need to know the wire format.
    5. format_for_context() — turns query results into readable plain text
       for feeding into an LLM prompt. Keep it terse; this is what an agent
       reads, not a human staring at a terminal.
    6. register_cli(subparsers) — wires up an argparse subcommand so
       query.py can dispatch to this module without every module needing
       its own __main__ block.

Retries: wrap outbound calls with shared.with_retry() rather than writing
bespoke retry logic per integration.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any

import config
from integrations import registry
from shared import with_retry

INTEGRATION_NAME = "example"


# === 1. Config dataclass ===
@dataclass
class ExampleConfig:
    """Whatever an integration needs to remember between calls.

    Cache expensive-to-resolve IDs here (e.g. Notion's database_id ->
    data_source_id resolution) so repeated calls in one process don't
    redo the lookup.
    """

    base_url: str = "https://api.example.com"
    # Example of a cache populated lazily by a query function:
    resolved_ids: dict[str, str] = field(default_factory=dict)


# === 2. Configuration check ===
def is_configured() -> bool:
    """Cheap check so the CLI can print 'set EXAMPLE_API_KEY' instead of a traceback."""
    return registry.is_configured(INTEGRATION_NAME)


# === 3. Auth setup ===
def _get_client() -> Any:
    """Build (or return a cached) authenticated client.

    Read the secret from config.py, never from os.environ directly in this
    module — config.py is the one place that touches .env, so a grep for
    "os.getenv" outside config.py should turn up nothing.
    """
    api_key = getattr(config, "EXAMPLE_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "EXAMPLE_API_KEY not set — add it to .claude/scripts/.env"
        )
    # return SomeSDKClient(api_key=api_key)
    raise NotImplementedError("template only — not a real integration")


# === 4. Query functions ===
def list_things(max_results: int = 10) -> list[dict[str, Any]]:
    """Example query function. Wrap the actual API call in with_retry()."""

    def _call() -> list[dict[str, Any]]:
        client = _get_client()
        return client.things.list(max_results=max_results)

    return with_retry(_call)


# === 5. Context formatter ===
def format_for_context(things: list[dict[str, Any]]) -> str:
    """Render query results as plain text suitable for an LLM prompt."""
    if not things:
        return "No items found."
    lines = [f"Found {len(things)} item(s):", ""]
    for thing in things:
        lines.append(f"- {thing.get('name', '(unnamed)')}")
    return "\n".join(lines)


# === 6. CLI wiring ===
def register_cli(subparsers: argparse._SubParsersAction) -> None:
    """Register this integration's subcommands on the shared query.py CLI.

    query.py calls this for every known integration at startup; each
    integration only needs to know about its own subcommands.
    """
    parser = subparsers.add_parser(INTEGRATION_NAME, help="Example integration (template)")
    action_subparsers = parser.add_subparsers(dest="action", required=True)

    list_parser = action_subparsers.add_parser("list", help="List things")
    list_parser.add_argument("--max-results", type=int, default=10)

    def _dispatch(args: argparse.Namespace) -> None:
        if args.action == "list":
            print(format_for_context(list_things(max_results=args.max_results)))

    parser.set_defaults(func=_dispatch)
