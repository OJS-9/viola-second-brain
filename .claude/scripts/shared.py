"""
Shared utilities for Second Brain hooks and scripts.

State management, daily log helpers, file locking, hook execution logging,
and a generic retry helper. Security pattern matching (bash command
validation) is Phase 8 scope and lives in block_secrets.py instead.
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from config import STATE_DIR, get_today_log_path, now_local

# =============================================================================
# STATE MANAGEMENT
# =============================================================================


def load_state(path: Path) -> dict[str, Any]:
    """Load state from a JSON file with error handling."""
    if path.exists():
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            return data
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict[str, Any], path: Path) -> None:
    """Save state to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


# =============================================================================
# RETRY UTILITY
# =============================================================================


def with_retry(
    func: Any,
    max_retries: int = 3,
    backoff: float = 1.0,
) -> Any:
    """Call func(), retry on transient errors with exponential backoff.

    Retries on: ConnectionError, TimeoutError, HTTP 429/500/502/503.
    Kept generic and simple here — future integration modules (Phase 4) can
    lean on this without needing changes.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            retryable = isinstance(e, (ConnectionError, TimeoutError))
            if hasattr(e, "resp") and hasattr(e.resp, "status"):
                retryable = e.resp.status in (429, 500, 502, 503)
            if hasattr(e, "status_code"):
                retryable = e.status_code in (429, 500, 502, 503)
            if not retryable:
                raise
            time.sleep(backoff * (2**attempt))


# =============================================================================
# FILE LOCKING (cross-platform)
# =============================================================================


@contextlib.contextmanager
def file_lock(lock_path: Path, timeout: float = 30.0) -> Iterator[None]:
    """Cross-platform file lock using a .lock file.

    Uses msvcrt on Windows, fcntl on Unix.
    Raises TimeoutError if the lock cannot be acquired within timeout seconds.
    """
    lock_file = lock_path.with_suffix(lock_path.suffix + ".lock")
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_file, "w", encoding="utf-8")  # noqa: SIM115
    acquired = False
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                if sys.platform == "win32":
                    import msvcrt

                    msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"Could not acquire lock on {lock_file} within {timeout}s"
                    )
                time.sleep(0.1)
        yield
    finally:
        if acquired:
            if sys.platform == "win32":
                import msvcrt

                try:
                    msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()


# =============================================================================
# DAILY LOG HELPERS
# =============================================================================


def _create_daily_log(log_path: Path) -> None:
    """Create a new daily log with standardized sections."""
    from config import DAILY_LOG_SECTIONS

    header = f"# Daily Log: {now_local().strftime('%Y-%m-%d')}\n\n"
    for section in DAILY_LOG_SECTIONS:
        header += f"## {section}\n\n"
    log_path.write_text(header, encoding="utf-8")


def append_to_daily_log(content: str, section_name: str = "Entry") -> None:
    """Append content to today's daily log under a named section."""
    log_path = get_today_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Prevent external data from breaking daily log structure
    safe_content = content.replace("</external_data>", "&lt;/external_data&gt;")

    with file_lock(log_path, timeout=5.0):
        timestamp = now_local().strftime("%H:%M")

        if not log_path.exists():
            _create_daily_log(log_path)

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"### {section_name} ({timestamp})\n\n{safe_content}\n\n")


# =============================================================================
# HOOK EXECUTION LOGGING
# =============================================================================

HOOK_LOG_FILE = STATE_DIR / "hook-execution.log"
HOOK_LOG_MAX_LINES = 1000
HOOK_LOG_KEEP_LINES = 500


def log_hook_execution(
    hook_name: str,
    trigger: str,
    status: str,
    duration_s: float,
    detail: str = "",
) -> None:
    """Append a line to the hook execution log with simple rotation.

    Must never raise — a broken logging call must never break the hook
    that called it.
    """
    try:
        timestamp = now_local().isoformat()
        line = f"{timestamp} | {hook_name} | {trigger} | {status} | {duration_s:.1f}s"
        if detail:
            line += f" | {detail}"

        HOOK_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        if HOOK_LOG_FILE.exists():
            lines = HOOK_LOG_FILE.read_text(encoding="utf-8").splitlines()
            if len(lines) >= HOOK_LOG_MAX_LINES:
                HOOK_LOG_FILE.write_text(
                    "\n".join(lines[-HOOK_LOG_KEEP_LINES:]) + "\n",
                    encoding="utf-8",
                )

        with open(HOOK_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # Hook logging must never crash the hook itself
