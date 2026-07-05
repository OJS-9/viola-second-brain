"""
Configuration for the Second Brain hooks and scripts.

Path constants and timezone helper, all derived from this file's location
so nothing is hardcoded to a specific machine.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# === Paths ===
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent.parent  # repo root (0. Second Brain)
CLAUDE_DIR = PROJECT_ROOT / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"

MEMORY_DIR = PROJECT_ROOT / "SecondBrain" / "Memory"
DAILY_DIR = MEMORY_DIR / "daily"

# .claude/data/ is already gitignored — per-machine, regenerable state
DATA_DIR = CLAUDE_DIR / "data"
STATE_DIR = DATA_DIR / "state"

# Load environment variables from .env in scripts directory (no-op until Phase 4 adds one)
load_dotenv(SCRIPTS_DIR / ".env")

# === Timezone (PRD global convention: Asia/Jerusalem everywhere) ===
LOCAL_TZ = ZoneInfo("Asia/Jerusalem")


def now_local() -> datetime:
    """Return the current time in the configured timezone (Asia/Jerusalem)."""
    return datetime.now(LOCAL_TZ)


# === Daily Log Template ===
DAILY_LOG_SECTIONS = ["Session Notes", "Decisions", "Heartbeat"]


def get_today_log_path() -> Path:
    """Get path to today's daily log (based on local date)."""
    return DAILY_DIR / f"{now_local():%Y-%m-%d}.md"


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for directory in (DATA_DIR, STATE_DIR, DAILY_DIR):
        directory.mkdir(parents=True, exist_ok=True)
