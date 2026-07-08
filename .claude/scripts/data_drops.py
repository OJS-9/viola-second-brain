"""
Data-drop detector for Second Brain (Phase 4.6: Snowflake, no direct connection).

Or has no direct Snowflake/BI API access (IT won't approve it), so the
pattern is manual: he exports query results himself (Snowsight -> Download
CSV/XLSX, or from the BI tool) into SecondBrain/data-drops/. This script
detects new files there, summarizes them with pandas so an agent session can
decide what to do with the data, then moves each file into
data-drops/processed/ with a timestamp prefix (moved, never deleted --
project convention).

Zero credentials, zero IT surface -- the read-only boundary is physical.

Usage:
    uv run python data_drops.py --scan     # Report new files, don't move them
    uv run python data_drops.py --process  # Summarize AND move new files
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from config import DATA_DROPS_DIR, DATA_DROPS_PROCESSED_DIR, ensure_directories, now_local

DATA_DROP_EXTENSIONS = (".csv", ".xlsx")


@dataclass
class DataDropSummary:
    """Basic summary of one detected data-drop file."""

    filename: str
    row_count: int
    columns: list[str]


def find_new_files(data_drops_dir: Path = DATA_DROPS_DIR) -> list[Path]:
    """Scan data-drops/ for new .csv/.xlsx files, skipping processed/."""
    if not data_drops_dir.exists():
        return []
    files = [
        f
        for f in data_drops_dir.iterdir()
        if f.is_file() and f.suffix.lower() in DATA_DROP_EXTENSIONS
    ]
    return sorted(files)


def summarize_file(path: Path) -> DataDropSummary:
    """Read a data-drop file with pandas and return a basic summary."""
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        df = pd.read_excel(path)
    return DataDropSummary(
        filename=path.name,
        row_count=len(df),
        columns=list(df.columns),
    )


def move_to_processed(
    path: Path, processed_dir: Path = DATA_DROPS_PROCESSED_DIR
) -> Path:
    """Move a data-drop file into processed/ with a timestamp prefix.

    Never deletes -- moves only, per project convention. The timestamp
    prefix avoids collisions if the same filename shows up again later.
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    timestamp = now_local().strftime("%Y%m%d-%H%M%S")
    dest = processed_dir / f"{timestamp}_{path.name}"
    path.rename(dest)
    return dest


def format_summary(summary: DataDropSummary) -> str:
    """Render a summary as plain text."""
    columns_str = ", ".join(summary.columns)
    return f"{summary.filename}: {summary.row_count} rows, columns: [{columns_str}]"


# =============================================================================
# CLI
# =============================================================================


def main() -> None:
    ensure_directories()

    parser = argparse.ArgumentParser(description="Detect and process Snowflake data drops")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scan", action="store_true", help="Report new files without moving them (dry run)"
    )
    group.add_argument(
        "--process", action="store_true", help="Summarize new files AND move them to processed/"
    )
    args = parser.parse_args()

    new_files = find_new_files()

    if not new_files:
        print("No new data-drop files found.")
        return

    if args.scan:
        print(f"{len(new_files)} new file(s) found:")
        for path in new_files:
            try:
                summary = summarize_file(path)
                print(f"  - {format_summary(summary)}")
            except Exception as e:
                print(f"  - {path.name}: could not read ({e})")
        return

    # --process
    print(f"{len(new_files)} new file(s) to process:")
    for path in new_files:
        try:
            summary = summarize_file(path)
        except Exception as e:
            print(f"  - {path.name}: could not read ({e}) -- skipping, not moved")
            continue
        dest = move_to_processed(path)
        print(f"  - {format_summary(summary)}")
        print(f"    moved to {dest}")


if __name__ == "__main__":
    main()
