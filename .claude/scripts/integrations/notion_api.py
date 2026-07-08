"""
Notion integration (Phase 4.1).

SDK: notion-client (ramnes/notion-sdk-py) v3.x, import name `notion_client`.
Auth: NOTION_API_KEY from .env (via config.py).

Critical post-2025 API model: databases are containers; rows + schema live
in "data sources". To query a database given its ID (32-hex extracted from
a Notion URL):
    1. databases.retrieve(database_id)  -> response has a "data_sources"
       list; each entry has an "id" (the data_source_id) and "name".
    2. Cache the resolved data_source_id (don't re-resolve on every call).
    3. data_sources.query(data_source_id, filter=..., sorts=...) to read rows.
Creating pages uses parent={"type": "data_source_id", "data_source_id": ...}.

notion-client 3.1.0 already defaults notion_version to "2025-09-03" and has
its own built-in retry (429 always retried honoring Retry-After; 5xx retried
for idempotent methods) — we still wrap calls in shared.with_retry() as a
second layer per the plan, since with_retry is generic and cheap insurance
if the SDK's own retry option is ever disabled.

Notion has no markdown input — blocks must be constructed as typed objects.
markdown_to_blocks() below handles headings, bullet/numbered lists, and
plain paragraphs. Limits respected: 100 blocks per single append call
(chunked), ~2000 chars per rich_text segment (split).
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from typing import Any

import config
from integrations import registry
from shared import with_retry

INTEGRATION_NAME = "notion"

NOTION_VERSION = "2025-09-03"

# Notion API limits (see module docstring).
MAX_BLOCKS_PER_APPEND = 100
MAX_RICH_TEXT_CHARS = 2000


# === 1. Config ===
@dataclass
class NotionConfig:
    """Holds the client and a cache of resolved database_id -> data_source_id."""

    data_source_cache: dict[str, str] = field(default_factory=dict)


_config = NotionConfig()
_client: Any = None


# === 2. Configuration check ===
def is_configured() -> bool:
    return registry.is_configured(INTEGRATION_NAME)


# === 3. Auth setup ===
def _get_client() -> Any:
    """Return a cached notion_client.Client, creating it on first use."""
    global _client
    if _client is not None:
        return _client

    if not config.NOTION_API_KEY:
        raise RuntimeError(
            "NOTION_API_KEY not set — add it to .claude/scripts/.env"
        )

    from notion_client import Client

    _client = Client(auth=config.NOTION_API_KEY, notion_version=NOTION_VERSION)
    return _client


def _resolve_data_source_id(database_id: str) -> str:
    """Resolve a database ID to its (first/primary) data_source_id, caching the result.

    A database can technically have multiple data sources, but the common
    case (and the only one this project needs) is a single data source per
    database — use the first one returned.
    """
    if database_id in _config.data_source_cache:
        return _config.data_source_cache[database_id]

    client = _get_client()

    def _call() -> Any:
        return client.databases.retrieve(database_id=database_id)

    database = with_retry(_call)
    data_sources = database.get("data_sources") or []
    if not data_sources:
        raise RuntimeError(
            f"Database {database_id} has no data sources — check the ID and "
            "that the integration has been shared with this database."
        )
    data_source_id = data_sources[0]["id"]
    _config.data_source_cache[database_id] = data_source_id
    return data_source_id


def extract_database_id(url_or_id: str) -> str:
    """Extract the 32-hex database ID from a Notion URL, or pass through a bare ID."""
    # Bare 32-hex ID (with or without dashes already stripped).
    hex_match = re.search(r"([a-f0-9]{32})", url_or_id.replace("-", ""))
    if hex_match:
        return hex_match.group(1)
    raise ValueError(f"Could not extract a 32-hex database ID from: {url_or_id!r}")


# === 4. Query functions ===
@dataclass
class NotionTask:
    """A single row from a Notion task database, flattened for readability."""

    page_id: str
    title: str
    status: str | None
    due_date: str | None
    url: str


def _plain_text_from_title_property(prop: dict[str, Any]) -> str:
    """Extract plain text from a Notion 'title' property value."""
    rich_text = prop.get("title", [])
    return "".join(segment.get("plain_text", "") for segment in rich_text)


def _extract_status(properties: dict[str, Any]) -> str | None:
    """Find the first status/select-type property and return its label, if any."""
    for prop in properties.values():
        prop_type = prop.get("type")
        if prop_type == "status" and prop.get("status"):
            return prop["status"].get("name")
        if prop_type == "select" and prop.get("select"):
            return prop["select"].get("name")
    return None


def _extract_due_date(properties: dict[str, Any]) -> str | None:
    """Find the first date-type property and return its start date, if any."""
    for prop in properties.values():
        if prop.get("type") == "date" and prop.get("date"):
            return prop["date"].get("start")
    return None


def query_open_tasks(database_id: str, max_results: int = 50) -> list[NotionTask]:
    """Query a task database for open (not-Done) tasks, sorted by due date.

    "Open" is inferred generically (any status property whose value isn't
    Done/Complete/Closed) since this project doesn't yet have a confirmed
    task database schema — see USER.md's Task DB ID placeholder.
    """
    database_id = extract_database_id(database_id)
    data_source_id = _resolve_data_source_id(database_id)
    client = _get_client()

    done_labels = {"done", "complete", "completed", "closed"}
    tasks: list[NotionTask] = []
    start_cursor: str | None = None

    while len(tasks) < max_results:
        def _call() -> Any:
            kwargs: dict[str, Any] = {"page_size": min(100, max_results)}
            if start_cursor:
                kwargs["start_cursor"] = start_cursor
            return client.data_sources.query(data_source_id, **kwargs)

        response = with_retry(_call)

        for page in response.get("results", []):
            properties = page.get("properties", {})
            title = ""
            for prop in properties.values():
                if prop.get("type") == "title":
                    title = _plain_text_from_title_property(prop)
                    break
            status = _extract_status(properties)
            if status and status.strip().lower() in done_labels:
                continue
            tasks.append(
                NotionTask(
                    page_id=page["id"],
                    title=title or "(untitled)",
                    status=status,
                    due_date=_extract_due_date(properties),
                    url=page.get("url", ""),
                )
            )
            if len(tasks) >= max_results:
                break

        if not response.get("has_more") or not response.get("next_cursor"):
            break
        start_cursor = response["next_cursor"]

    return tasks


def create_page(
    parent_id: str,
    title: str,
    parent_type: str = "page_id",
    markdown_body: str = "",
) -> dict[str, Any]:
    """Create a page under a parent page or data source.

    parent_type: "page_id" (create as a child page — the digest/DD staging
    area convention) or "data_source_id" (create as a row in a database).
    For "data_source_id", properties must include the title property named
    to match the target schema — callers pass a fully-formed properties
    dict via create_database_row() instead for that case.
    """
    client = _get_client()
    children = markdown_to_blocks(markdown_body) if markdown_body else []
    # Notion allows at most 100 children on page creation; extra blocks are
    # appended afterward via append_markdown_to_page().
    first_batch, remainder = children[:MAX_BLOCKS_PER_APPEND], children[MAX_BLOCKS_PER_APPEND:]

    def _call() -> Any:
        return client.pages.create(
            parent={"type": parent_type, parent_type: parent_id},
            properties={"title": {"title": [{"text": {"content": title}}]}},
            children=first_batch,
        )

    page = with_retry(_call)

    if remainder:
        _append_blocks(page["id"], remainder)

    return page


def create_database_row(
    data_source_id_or_database_id: str,
    properties: dict[str, Any],
) -> dict[str, Any]:
    """Create a new row (page) in a database's data source with explicit properties.

    Accepts either a database_id (resolved automatically) or an
    already-known data_source_id.
    """
    client = _get_client()
    data_source_id = data_source_id_or_database_id
    try:
        data_source_id = _resolve_data_source_id(
            extract_database_id(data_source_id_or_database_id)
        )
    except ValueError:
        # Not a URL/database-id shape — assume it's already a data_source_id.
        pass

    def _call() -> Any:
        return client.pages.create(
            parent={"type": "data_source_id", "data_source_id": data_source_id},
            properties=properties,
        )

    return with_retry(_call)


def _append_blocks(page_id: str, blocks: list[dict[str, Any]]) -> None:
    """Append blocks to a page, chunking to respect the 100-blocks-per-call limit."""
    client = _get_client()
    for i in range(0, len(blocks), MAX_BLOCKS_PER_APPEND):
        chunk = blocks[i : i + MAX_BLOCKS_PER_APPEND]

        def _call(chunk: list[dict[str, Any]] = chunk) -> Any:
            return client.blocks.children.append(block_id=page_id, children=chunk)

        with_retry(_call)


def append_markdown_to_page(page_id: str, markdown_body: str) -> None:
    """Convert markdown to blocks and append them to an existing page."""
    blocks = markdown_to_blocks(markdown_body)
    _append_blocks(page_id, blocks)


# === Markdown -> Notion blocks converter ===


def _split_rich_text(text: str) -> list[dict[str, Any]]:
    """Split text into rich_text segments respecting the ~2000 char limit."""
    if not text:
        return []
    segments = []
    for i in range(0, len(text), MAX_RICH_TEXT_CHARS):
        chunk = text[i : i + MAX_RICH_TEXT_CHARS]
        segments.append({"type": "text", "text": {"content": chunk}})
    return segments


def markdown_to_blocks(markdown_text: str) -> list[dict[str, Any]]:
    """Convert a markdown string into a list of Notion block objects.

    Handles: headings (#/##/###), bullet lists (-/*), numbered lists (1.),
    and plain paragraphs. Anything else (tables, code fences, etc.) is
    passed through as a paragraph — good enough for digest/DD notes, which
    is the only writer of markdown in this project so far.
    """
    blocks: list[dict[str, Any]] = []
    lines = markdown_text.splitlines()

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.*)$", line)
        bullet_match = re.match(r"^[-*]\s+(.*)$", line)
        numbered_match = re.match(r"^\d+\.\s+(.*)$", line)

        if heading_match:
            level = len(heading_match.group(1))
            text = heading_match.group(2)
            block_type = f"heading_{level}"
            blocks.append(
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {"rich_text": _split_rich_text(text)},
                }
            )
        elif bullet_match:
            text = bullet_match.group(1)
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": _split_rich_text(text)},
                }
            )
        elif numbered_match:
            text = numbered_match.group(1)
            blocks.append(
                {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": _split_rich_text(text)},
                }
            )
        else:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": _split_rich_text(line)},
                }
            )

    return blocks


# === 5. Context formatter ===
def format_for_context(tasks: list[NotionTask]) -> str:
    """Render task query results as plain text for an LLM prompt."""
    if not tasks:
        return "No open tasks found."
    lines = [f"{len(tasks)} open task(s):", ""]
    for task in tasks:
        due = f" (due {task.due_date})" if task.due_date else ""
        status = f" [{task.status}]" if task.status else ""
        lines.append(f"- {task.title}{status}{due}")
        lines.append(f"  {task.url}")
    return "\n".join(lines)


def check_auth() -> dict[str, Any]:
    """Lightweight live check that the token + API version work: GET /users/me.

    Returns the bot user object on success; raises on failure. Useful as a
    connectivity smoke test that doesn't require a database ID.
    """
    client = _get_client()

    def _call() -> Any:
        return client.users.me()

    return with_retry(_call)


# === 6. CLI wiring ===
def register_cli(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("notion", help="Query/update Notion")
    action_subparsers = parser.add_subparsers(dest="action", required=True)

    tasks_parser = action_subparsers.add_parser("tasks", help="List open tasks from a database")
    tasks_parser.add_argument("--database-id", required=True, help="Notion database ID or URL")
    tasks_parser.add_argument("--max-results", type=int, default=50)

    whoami_parser = action_subparsers.add_parser("whoami", help="Check auth (GET /users/me)")

    def _dispatch(args: argparse.Namespace) -> None:
        if args.action == "tasks":
            tasks = query_open_tasks(args.database_id, max_results=args.max_results)
            print(format_for_context(tasks))
        elif args.action == "whoami":
            user = check_auth()
            name = user.get("name") or user.get("bot", {}).get("owner", {}).get("type", "unknown")
            print(f"Authenticated as: {name} (id={user.get('id')}, type={user.get('type')})")

    parser.set_defaults(func=_dispatch)
    tasks_parser.set_defaults(func=_dispatch)
    whoami_parser.set_defaults(func=_dispatch)
