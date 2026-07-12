"""
Scrape LinkedIn profiles via the Nimble Web Search Agent (linkedin_person_8d8884b2).
Drop-in replacement for apify_linkedin.py — same CLI surface, no token handling needed
(Nimble CLI is pre-authenticated).

Usage
-----
    # from a text file (one URL/slug per line, blanks and #-comments ignored)
    python scripts\\nimble_linkedin.py --input state\\batch-6-profiles.txt --out output\\batch-6.jsonl

    # from CLI args (URL or bare slug both accepted)
    python scripts\\nimble_linkedin.py satyanadella https://www.linkedin.com/in/billgates

    # piped from stdin
    Get-Content profiles.txt | python scripts\\nimble_linkedin.py --input -

    # preview resolved slugs without calling nimble
    python scripts\\nimble_linkedin.py --input state\\batch-6-profiles.txt --dry-run
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

AGENT_ID = "linkedin_person_8d8884b2"

# Resolve the nimble executable once at import time (.cmd shim on Windows).
_NIMBLE = shutil.which("nimble")
if _NIMBLE is None:
    sys.exit("ERROR: 'nimble' not found on PATH. Install the Nimble CLI and ensure it is accessible.")


def resolve_slug(raw: str) -> str:
    """Extract the LinkedIn public identifier from a full URL or return the bare slug as-is."""
    s = raw.strip().rstrip("/")
    # treat anything containing 'linkedin.com' as a URL
    if "linkedin.com/" in s:
        parsed = urlparse(s if s.startswith("http") else "https://" + s)
        parts = [p for p in parsed.path.split("/") if p]
        # path is like ['in', '<slug>'] or ['pub', '<slug>', ...]
        if "in" in parts:
            idx = parts.index("in")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        # fall back to last non-empty segment
        return parts[-1] if parts else s
    return s


def read_inputs(path: str | None, cli_args: list[str]) -> list[str]:
    items: list[str] = []
    if path:
        if path == "-":
            text = sys.stdin.read()
        else:
            text = Path(path).read_text(encoding="utf-8")
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                items.append(line)
    items.extend(cli_args)
    # de-dup while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def scrape_one(slug: str) -> dict | None:
    """Run the Nimble agent for a single slug. Returns the parsed profile dict or None on failure."""
    params = f"identifier: {slug}"
    cmd = [_NIMBLE, "agent", "run", "--agent", AGENT_ID, "--params", params]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(
            f"[nimble] WARN non-zero exit ({result.returncode}) for {slug!r}: "
            f"{result.stderr.strip()[:200]}",
            file=sys.stderr,
        )
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"[nimble] WARN JSON parse error for {slug!r}: {exc}", file=sys.stderr)
        return None
    if payload.get("status") != "success":
        print(
            f"[nimble] WARN status={payload.get('status')!r} for {slug!r}",
            file=sys.stderr,
        )
        return None
    profile: dict = payload.get("data", {}).get("parsing", {})
    return profile


def main() -> None:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("inputs", nargs="*", help="LinkedIn URLs or public slugs")
    p.add_argument("--input", help="Path to text file (one entry per line) or '-' for stdin")
    p.add_argument("--out", help="Write JSONL here instead of stdout")
    p.add_argument("--dry-run", action="store_true", help="Print resolved slugs and exit, don't call nimble")
    args = p.parse_args()

    raw_items = read_inputs(args.input, args.inputs)
    if not raw_items:
        sys.exit("no inputs provided")

    # build (raw_input, slug) pairs
    pairs = [(raw, resolve_slug(raw)) for raw in raw_items]
    total = len(pairs)

    if args.dry_run:
        print(f"[nimble] agent={AGENT_ID} | {total} slug(s) resolved:")
        for raw, slug in pairs:
            print(f"  {slug}  (from {raw!r})")
        return

    out_fh = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    n = 0
    try:
        for i, (raw, slug) in enumerate(pairs, 1):
            print(f"[nimble] ({i}/{total}) {slug}", file=sys.stderr)
            profile = scrape_one(slug)
            if profile is None:
                continue
            # inject provenance fields
            profile["linkedinUrl"] = raw if "linkedin.com/" in raw else f"https://www.linkedin.com/in/{slug}"
            profile["publicIdentifier"] = slug
            profile["originalQuery"] = raw
            out_fh.write(json.dumps(profile, ensure_ascii=False) + "\n")
            n += 1
    finally:
        if args.out:
            out_fh.close()

    out_label = f" -> {args.out}" if args.out else ""
    print(f"[nimble] wrote {n}/{total} profiles{out_label}", file=sys.stderr)


if __name__ == "__main__":
    main()
