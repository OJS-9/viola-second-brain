"""
Session Start Context Injection Hook

Called by Claude Code when a session starts. Reads key memory files and
outputs a context summary as JSON on stdout, which Claude Code injects
into the assistant's context.

This hook does NO API calls — pure local file reads for speed.
"""

from __future__ import annotations

import json
import re
import sys
import time as _time
from pathlib import Path

# Add scripts directory to path for config imports
_scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_scripts_dir))

from config import DAILY_DIR, MEMORY_DIR, now_local  # noqa: E402
from shared import log_hook_execution  # noqa: E402

# === Constants ===
MAX_DAILY_LOG_LINES = 30
MAX_CONTEXT_CHARS = 20_000
NUM_DAILY_LOGS = 2


def read_file_safe(path: Path) -> str:
    """Read a file, returning empty string if it doesn't exist."""
    try:
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


def get_recent_daily_logs(max_lines: int = MAX_DAILY_LOG_LINES) -> str:
    """Read the tail of the last NUM_DAILY_LOGS daily logs that exist on disk.

    Picks the most recent files by filename (YYYY-MM-DD.md sorts correctly),
    not just today/yesterday — a log might be missing for a day Or didn't use
    the system.
    """
    if not DAILY_DIR.exists():
        return ""

    log_files = sorted(DAILY_DIR.glob("????-??-??.md"), reverse=True)[:NUM_DAILY_LOGS]
    if not log_files:
        return ""

    # Oldest first, so context reads chronologically
    log_files.reverse()

    parts: list[str] = []
    for log_file in log_files:
        content = read_file_safe(log_file)
        if not content:
            continue
        lines = content.strip().splitlines()
        if len(lines) > max_lines:
            lines = lines[-max_lines:]
        parts.append(f"### {log_file.stem}\n" + "\n".join(lines))

    return "\n\n".join(parts)


def build_context(source: str) -> str:
    """Build the context string to inject into Claude's session.

    Args:
        source: The session start source (startup, resume, clear, compact)
    """
    parts: list[str] = []

    # Inject day of week + date so Claude always knows what day it is
    today = now_local()
    parts.append(f"## Today\n{today.strftime('%A, %B')} {today.day}, {today.strftime('%Y')}")

    # First-run onboarding — if BOOTSTRAP.md exists, inject it as the first section.
    # Phase 1 already ran onboarding and archived BOOTSTRAP.md, so normally this
    # is a graceful no-op — but if it ever reappears (re-onboarding), pick it up.
    bootstrap = read_file_safe(MEMORY_DIR / "BOOTSTRAP.md")
    if bootstrap:
        parts.append("## BOOTSTRAP (First-Run Onboarding)\n" + bootstrap.strip())

    # Core personality and behavioral guidelines
    soul = read_file_safe(MEMORY_DIR / "SOUL.md")
    if soul:
        parts.append("## Soul\n" + soul.strip())

    # Who Or is — preferences, schedule, team, integrations
    user = read_file_safe(MEMORY_DIR / "USER.md")
    if user:
        parts.append("## User\n" + user.strip())

    # Long-term facts, decisions, lessons
    memory = read_file_safe(MEMORY_DIR / "MEMORY.md")
    if memory:
        parts.append("## Long-Term Memory\n" + memory.strip())

    # Last 2 daily logs that exist on disk
    daily = get_recent_daily_logs()
    if daily:
        parts.append("## Recent Daily Logs\n" + daily.strip())

    context = "\n\n---\n\n".join(parts)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]
        # Truncate at last complete line
        last_newline = context.rfind("\n")
        if last_newline > 0:
            context = context[:last_newline]

    return context


def main() -> None:
    """Main hook entry point. Reads stdin, builds context, outputs JSON on stdout."""
    _start = _time.time()

    try:
        # Read hook input from stdin.
        # Claude Code on Windows may pass paths with unescaped backslashes (e.g.
        # C:\Users\...), which are invalid JSON. Try normal parse first; on
        # failure, escape lone backslashes and retry.
        raw_input = sys.stdin.read()
        try:
            hook_input: dict[str, object] = json.loads(raw_input)
        except json.JSONDecodeError:
            fixed_input = re.sub(r'(?<!\\)\\(?!["\\])', r"\\\\", raw_input)
            hook_input = json.loads(fixed_input)

        source = hook_input.get("source", "startup")
        if not isinstance(source, str):
            source = "startup"

        context = build_context(source)

        if not context.strip():
            log_hook_execution(
                "session-start-context", source, "SKIP", _time.time() - _start, "empty context"
            )
            sys.exit(0)

        output = {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context,
            }
        }

        # CRITICAL: Only valid JSON on stdout. No other output.
        json.dump(output, sys.stdout)
        log_hook_execution(
            "session-start-context", source, "OK", _time.time() - _start, f"{len(context)} chars"
        )
    except Exception as e:
        # A broken SessionStart hook must never block a session from starting.
        try:
            log_hook_execution(
                "session-start-context", "unknown", "ERROR", _time.time() - _start, str(e)
            )
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
