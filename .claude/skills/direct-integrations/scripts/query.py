"""
Unified CLI for Second Brain platform integrations (Phase 4).

Dispatches to .claude/scripts/integrations/*.py modules, each of which
registers its own subcommands via register_cli(). Adding a new integration
means: write the module (following integration_template.py's shape), add it
to registry.py's _REQUIRED_ENV_VARS, and import + register it below.

Usage:
    python query.py notion tasks --database-id <id>
    python query.py notion whoami
    python query.py nimble search "<query>" [--focus news] [--time-range week] [--max-results 10]
    python query.py nimble extract <url> [--render]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add the .claude/scripts directory to Python path for integration imports.
SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from integrations import notion_api, nimble_api, registry  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query Notion and Nimble directly via Python APIs."
    )
    subparsers = parser.add_subparsers(dest="platform", required=True)

    notion_api.register_cli(subparsers)
    nimble_api.register_cli(subparsers)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not registry.is_configured(args.platform):
        missing = registry.missing_env_vars(args.platform)
        if missing:
            missing_str = ", ".join(missing)
            print(
                f"'{args.platform}' is not configured — set {missing_str} in "
                ".claude/scripts/.env"
            )
        else:
            print(f"Unknown platform: {args.platform}")
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
