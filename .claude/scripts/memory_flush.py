"""
Memory Flush — Background Agent SDK Script

Spawned by pre_compact_flush.py / session_end_flush.py (not run directly by
Claude Code). Reads conversation context from a temp file and uses Claude to
decide what decisions, lessons, and facts are worth saving to the daily log.

Usage:
    uv run --project . python memory_flush.py --context-file <path>         # Run flush
    uv run --project . python memory_flush.py --context-file <path> --test  # Dry run
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime
from pathlib import Path

from config import LOCAL_TZ, PROJECT_ROOT, STATE_DIR, ensure_directories, now_local
from shared import append_to_daily_log, file_lock, load_state, save_state

FLUSH_STATE_FILE = STATE_DIR / "flush-state.json"


def _extract_session_id(context_file: Path) -> str:
    """Extract session_id from a context filename.

    Filename patterns (set by the hooks, kept consistent with them):
        flush-context-{session_id}-{YYYYMMDD}-{HHMMSS}.md
        session-flush-{session_id}-{YYYYMMDD}-{HHMMSS}.md
    """
    stem = context_file.stem
    parts = stem.split("-")
    # Last 2 parts are the date/time stamp; first 2 are the prefix words.
    if len(parts) >= 5:
        return "-".join(parts[2:-2])
    return "unknown"


# =============================================================================
# MAIN FLUSH FUNCTION
# =============================================================================


async def run_flush(context_file: Path, test_mode: bool = False) -> str | None:
    """Run the memory flush with a concurrency guard.

    Wraps the inner flush with a file lock so a PreCompact and a SessionEnd
    flush firing close together don't race each other.
    """
    try:
        with file_lock(FLUSH_STATE_FILE, timeout=5.0):
            return await _run_flush_inner(context_file, test_mode)
    except TimeoutError:
        print(f"[{now_local()}] Another flush is already running, skipping")
        return None


async def _run_flush_inner(context_file: Path, test_mode: bool = False) -> str | None:
    """Run the memory flush using the Agent SDK.

    Args:
        context_file: Path to the context file written by the hook.
        test_mode: If True, run in dry-run mode (no file edits).

    Returns:
        Response summary, or None if FLUSH_OK / nothing to do.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    if not context_file.exists():
        print(f"[memory-flush] Context file not found: {context_file}")
        return None

    # Dedup: skip if the same session was flushed < 60s ago
    state = load_state(FLUSH_STATE_FILE)
    session_id = _extract_session_id(context_file)
    last_session = state.get("last_flushed_session_id", "")
    last_flush_str = state.get("last_flush", "")
    if session_id != "unknown" and session_id == last_session and last_flush_str:
        try:
            last_flush_time = datetime.fromisoformat(last_flush_str)
            if last_flush_time.tzinfo is None:
                last_flush_time = last_flush_time.replace(tzinfo=LOCAL_TZ)
            if (now_local() - last_flush_time).total_seconds() < 60:
                print(f"[{now_local()}] Skipping duplicate flush for session {session_id}")
                return None
        except ValueError:
            pass  # Malformed timestamp, proceed with flush

    context_content = context_file.read_text(encoding="utf-8").strip()
    if not context_content:
        print("[memory-flush] Context file is empty, nothing to flush")
        return None

    if len(context_content) > 15_000:
        context_content = context_content[-15_000:]

    dry_run_note = (
        "\n\nDRY RUN: Do NOT edit any files. Just describe what you would save.\n"
        if test_mode
        else ""
    )

    flush_prompt = f"""Memory flush. This is a conversation excerpt from Or's second brain session.
{dry_run_note}
Review the conversation context below and respond with a concise summary of important items.
Do NOT use any tools — just return plain text.

Format your response as bullet points covering:
- Decisions made and their rationale
- Lessons learned or mistakes to avoid
- Important facts, configurations, or patterns discovered
- Action items or follow-ups mentioned
- Key context that would be lost after compaction or session end

Skip anything that is:
- Routine tool calls or file reads
- Content that's already in memory files
- Trivial back-and-forth or clarification exchanges

If nothing is worth saving, respond with exactly: FLUSH_OK

## Conversation Context

{context_content}
"""

    print(f"[{now_local()}] Running memory flush (test={test_mode})...")

    response_text = ""

    try:
        # Recursion guard (other half): the query() call below spawns Claude
        # Code's own headless subprocess, which would otherwise trigger its
        # own PreCompact/SessionEnd hooks and spawn another flush, forever.
        os.environ["CLAUDE_INVOKED_BY"] = "memory_flush"

        async for message in query(
            prompt=flush_prompt,
            options=ClaudeAgentOptions(
                cwd=str(PROJECT_ROOT),
                allowed_tools=[],
                max_turns=2,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
            elif isinstance(message, ResultMessage):
                print(f"[{now_local()}] Flush completed: {message.subtype}")
                if message.total_cost_usd:
                    print(f"[{now_local()}] Cost: ${message.total_cost_usd:.4f}")

    except Exception as e:
        print(f"[{now_local()}] Flush error: {e}")
        if not test_mode:
            append_to_daily_log(f"**ERROR**: Memory flush failed - {e}", "Session Notes")
        return None

    response_text = response_text.strip()

    if test_mode:
        print(f"[{now_local()}] DRY RUN - would have saved:\n{response_text[:500]}")
        return None if "FLUSH_OK" in response_text else response_text

    # Update state (real run only)
    state["last_flush"] = now_local().isoformat()
    state["context_file"] = str(context_file)
    state["last_flushed_session_id"] = session_id
    state["result"] = "FLUSH_OK" if "FLUSH_OK" in response_text else "flushed"
    save_state(state, FLUSH_STATE_FILE)

    # Clean up context file
    try:
        context_file.unlink()
        print(f"[{now_local()}] Cleaned up context file: {context_file}")
    except OSError as e:
        print(f"[{now_local()}] Warning: Could not delete context file: {e}")

    if "FLUSH_OK" in response_text:
        print(f"[{now_local()}] Flush OK - nothing worth saving")
        return None

    append_to_daily_log(response_text, "Session Notes")
    print(f"[{now_local()}] Flush saved items to daily log")
    return response_text


# =============================================================================
# ENTRY POINT
# =============================================================================


def main() -> None:
    """Main entry point."""
    ensure_directories()

    parser = argparse.ArgumentParser(description="Memory flush background agent")
    parser.add_argument("--context-file", required=True, help="Path to context file")
    parser.add_argument("--test", action="store_true", help="Dry run mode")
    args = parser.parse_args()

    context_file = Path(args.context_file)

    if args.test:
        print("Running in TEST MODE (dry run, no file edits)")

    try:
        result = asyncio.run(run_flush(context_file=context_file, test_mode=args.test))
    except Exception as e:
        # Never exit non-gracefully — log and move on.
        print(f"[memory-flush] Unhandled error: {e}")
        try:
            if not args.test:
                append_to_daily_log(f"**ERROR**: Memory flush failed - {e}", "Session Notes")
        except Exception:
            pass
        return

    if result:
        try:
            print(f"\nFlush result:\n{result[:500]}")
        except UnicodeEncodeError:
            print(f"\nFlush result:\n{result[:500].encode('ascii', 'replace').decode()}")
    else:
        print("\nFlush complete: OK or skipped")


if __name__ == "__main__":
    main()
