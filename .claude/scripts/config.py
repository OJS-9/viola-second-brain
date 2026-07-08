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

# === Memory Search (Phase 3: Hybrid RAG) ===
DATABASE_PATH = DATA_DIR / "memory.db"

# FastEmbed model — 384-dim, ONNX/CPU, no PyTorch. ~90MB one-time download.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
# Must be set explicitly — FastEmbed's default cache_dir is a temp dir, which
# would re-download the model every time the OS clears temp files.
EMBEDDING_CACHE_DIR = DATA_DIR / "models"

# Chunking: ~400 tokens per chunk (~4 chars/token heuristic), 50-token overlap
# so a fact split across a chunk boundary is still findable in the neighbor chunk.
SEARCH_CHUNK_MAX_TOKENS = 400
SEARCH_CHUNK_OVERLAP_TOKENS = 50

SEARCH_DEFAULT_LIMIT = 10
SEARCH_MIN_SCORE = 0.0

# Hybrid scoring weights (PRD: 70% semantic, 30% keyword)
SEARCH_VECTOR_WEIGHT = 0.7
SEARCH_KEYWORD_WEIGHT = 0.3

# Hybrid search always pulls this many candidates from EACH side (keyword and
# vector) before merging/ranking — independent of the final --limit requested.
SEARCH_HYBRID_FETCH_K = 20


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
    for directory in (DATA_DIR, STATE_DIR, DAILY_DIR, EMBEDDING_CACHE_DIR):
        directory.mkdir(parents=True, exist_ok=True)
