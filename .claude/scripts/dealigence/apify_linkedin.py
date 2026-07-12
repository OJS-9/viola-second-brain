"""
Call Apify actor harvestapi/linkedin-profile-scraper on a batch of LinkedIn
profile URLs / public identifiers / profile IDs. Profile-details-only mode
($4 / 1,000 profiles). Outputs newline-delimited JSON to stdout or a file.

Usage
-----
    # from a text file (one URL/handle/ID per line, blanks and #-comments ignored)
    python apify_linkedin.py --input profiles.txt --out output/profiles.jsonl

    # from CLI args
    python apify_linkedin.py williamhgates https://www.linkedin.com/in/satyanadella

    # piped from stdin
    Get-Content profiles.txt | python apify_linkedin.py --input -

Token resolution order: --token > $APIFY_TOKEN env var > .env at repo root.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib import error, request

ACTOR_ID = "harvestapi~linkedin-profile-scraper"  # `~` form is what the REST API expects
BASE = "https://api.apify.com/v2"
POLL_SECS = 5
RUN_TIMEOUT_SECS = 60 * 20  # 20 min hard cap on a single run


def load_token(cli_token: str | None) -> str:
    if cli_token:
        return cli_token
    tok = os.environ.get("APIFY_TOKEN")
    if tok:
        return tok
    # fall back to .env at .claude/scripts/ (script's parent's parent)
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "APIFY_TOKEN":
                return v.strip().strip('"').strip("'")
    sys.exit("ERROR: APIFY_TOKEN not found. Set env var, pass --token, or add to .env")


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
    seen, out = set(), []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def classify(item: str) -> tuple[str, str]:
    """Bucket each input into the field the actor expects.

    Returns (field_name, value). Fields: urls, publicIdentifiers, profileIds.
    """
    s = item.strip()
    if s.startswith("http://") or s.startswith("https://") or "linkedin.com/" in s:
        return "urls", s
    if s.startswith("ACoA"):  # LinkedIn opaque profile IDs start with ACoA
        return "profileIds", s
    return "publicIdentifiers", s


MODE_DEFAULT = "Profile details no email ($4 per 1k)"
MODE_EMAIL = "Profile details + email search ($10 per 1k)"


def build_actor_input(items: list[str], with_email: bool = False) -> dict:
    payload: dict[str, object] = {
        "profileScraperMode": MODE_EMAIL if with_email else MODE_DEFAULT,
        "urls": [],
        "publicIdentifiers": [],
        "profileIds": [],
    }
    for it in items:
        field, val = classify(it)
        payload[field].append(val)  # type: ignore[union-attr]
    # drop empty lists so the actor schema stays clean
    return {k: v for k, v in payload.items() if v or k == "profileScraperMode"}


def http_json(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {method} {url}: {e.read().decode('utf-8', 'replace')}")


def stream_dataset_items(dataset_id: str, token: str) -> Iterable[dict]:
    """Stream items from a dataset as JSON lines."""
    url = f"{BASE}/datasets/{dataset_id}/items?format=json&clean=true&token={token}"
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=120) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            for item in payload:
                yield item
    except error.HTTPError as e:
        sys.exit(f"HTTP {e.code} fetching dataset: {e.read().decode('utf-8', 'replace')}")


def run_actor(token: str, actor_input: dict) -> str:
    """Start a run, poll until terminal, return dataset id."""
    start = http_json("POST", f"{BASE}/acts/{ACTOR_ID}/runs", token, actor_input)
    run_id = start["data"]["id"]
    print(f"[apify] run started: {run_id}", file=sys.stderr)

    t0 = time.time()
    while True:
        if time.time() - t0 > RUN_TIMEOUT_SECS:
            sys.exit(f"timeout after {RUN_TIMEOUT_SECS}s on run {run_id}")
        info = http_json("GET", f"{BASE}/actor-runs/{run_id}", token)["data"]
        status = info["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            print(f"[apify] run {run_id} -> {status}", file=sys.stderr)
            if status != "SUCCEEDED":
                sys.exit(f"run did not succeed: {status}")
            return info["defaultDatasetId"]
        time.sleep(POLL_SECS)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", nargs="*", help="LinkedIn URLs, public IDs, or profile IDs (ACoA...)")
    p.add_argument("--input", help="Path to text file (one entry per line) or '-' for stdin")
    p.add_argument("--out", help="Write JSONL here instead of stdout")
    p.add_argument("--token", help="Apify API token (overrides env / .env)")
    p.add_argument("--dry-run", action="store_true", help="Print payload + exit, don't call API")
    p.add_argument("--with-email", action="store_true", help="Use $10/1k mode with email-finder")
    args = p.parse_args()

    items = read_inputs(args.input, args.inputs)
    if not items:
        sys.exit("no inputs provided")
    actor_input = build_actor_input(items, with_email=args.with_email)
    lists = {k: v for k, v in actor_input.items() if isinstance(v, list)}
    total = sum(len(v) for v in lists.values())
    print(f"[apify] mode={actor_input['profileScraperMode']!r} | {total} inputs ({', '.join(f'{k}={len(v)}' for k, v in lists.items())})", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(actor_input, indent=2))
        return

    token = load_token(args.token)
    dataset_id = run_actor(token, actor_input)
    out_fh = open(args.out, "w", encoding="utf-8") if args.out else sys.stdout
    n = 0
    try:
        for item in stream_dataset_items(dataset_id, token):
            out_fh.write(json.dumps(item, ensure_ascii=False) + "\n")
            n += 1
    finally:
        if args.out:
            out_fh.close()
    print(f"[apify] wrote {n} profiles" + (f" -> {args.out}" if args.out else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
