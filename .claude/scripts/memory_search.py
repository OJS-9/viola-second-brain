"""
Memory Search for Second Brain.

Three search modes: keyword (FTS5/BM25), semantic (FastEmbed + vector), and
hybrid (weighted combination, default).

Hybrid scoring follows the PRD's literal min-max normalization algorithm:
fetch the top SEARCH_HYBRID_FETCH_K candidates from each side, min-max
normalize each side's scores to 0-1 independently, then combine
0.7*vector + 0.3*keyword. This is more literal-to-spec than a reciprocal
(1/(1+x)) scoring scheme, and keeps every score comparable on a 0-1 scale.

Usage:
    uv run python memory_search.py "query"                    # Hybrid (default)
    uv run python memory_search.py "query" --mode keyword
    uv run python memory_search.py "query" --mode semantic
    uv run python memory_search.py "query" --mode hybrid --path-prefix research/
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

import db
from config import (
    SEARCH_DEFAULT_LIMIT,
    SEARCH_HYBRID_FETCH_K,
    SEARCH_KEYWORD_WEIGHT,
    SEARCH_MIN_SCORE,
    SEARCH_VECTOR_WEIGHT,
)


@dataclass
class SearchResult:
    """A single search result with metadata."""

    path: str
    start_line: int
    end_line: int
    text: str
    score: float
    match_type: str  # "keyword" | "semantic" | "hybrid"
    section_title: str = ""


def _neutralize(text: str) -> str:
    """Same lightweight defensive escaping shared.py's append_to_daily_log
    already applies — neutralize a literal closing external-data tag so
    vault/search output can't masquerade as a trust-boundary close."""
    return text.replace("</external_data>", "&lt;/external_data&gt;")


def _min_max_normalize(values: list[float]) -> list[float]:
    """Normalize a list of scores to 0-1 range.

    Edge case: if there's only one value, or all values are equal (so
    max == min), normalizing would divide by zero — default to 1.0 for
    every entry in that case instead of crashing.
    """
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0 for _ in values]
    return [(v - lo) / (hi - lo) for v in values]


def search_keyword(
    query: str,
    limit: int = SEARCH_DEFAULT_LIMIT,
    min_score: float = SEARCH_MIN_SCORE,
    path_prefix: str = "",
) -> list[SearchResult]:
    """Keyword search (FTS5/BM25 only).

    raw_score from db.keyword_search() is -rank (BM25, unbounded, higher is
    better but not on a fixed scale) — min-max normalize to 0-1 over this
    query's own result set so scores are comparable and SEARCH_MIN_SCORE
    means something consistent across modes.
    """
    if not query.strip():
        return []

    db.init_schema()
    rows = db.keyword_search(query, limit, path_prefix=path_prefix)
    db.close()

    normalized = _min_max_normalize([r["raw_score"] for r in rows])

    return [
        SearchResult(
            path=r["file_path"],
            start_line=r["start_line"],
            end_line=r["end_line"],
            text=r["content"],
            score=score,
            match_type="keyword",
            section_title=r.get("section_title", ""),
        )
        for r, score in zip(rows, normalized)
        if score >= min_score
    ]


def search_semantic(
    query: str,
    limit: int = SEARCH_DEFAULT_LIMIT,
    min_score: float = SEARCH_MIN_SCORE,
    path_prefix: str = "",
) -> list[SearchResult]:
    """Semantic search using vector similarity only.

    raw_score from db.vector_search() is 1 - distance (cosine distance
    ranges 0-2, so raw_score is cosine similarity, ranging -1 to 1) —
    min-max normalize to 0-1 over this query's own result set, same
    reasoning as search_keyword() above.
    """
    if not query.strip():
        return []

    from embeddings import embed_text

    query_embedding = embed_text(query)

    db.init_schema()
    rows = db.vector_search(query_embedding, limit, path_prefix=path_prefix)
    db.close()

    normalized = _min_max_normalize([r["raw_score"] for r in rows])

    return [
        SearchResult(
            path=r["file_path"],
            start_line=r["start_line"],
            end_line=r["end_line"],
            text=r["content"],
            score=score,
            match_type="semantic",
            section_title=r.get("section_title", ""),
        )
        for r, score in zip(rows, normalized)
        if score >= min_score
    ]


def search_hybrid(
    query: str,
    limit: int = SEARCH_DEFAULT_LIMIT,
    min_score: float = SEARCH_MIN_SCORE,
    vector_weight: float = SEARCH_VECTOR_WEIGHT,
    keyword_weight: float = SEARCH_KEYWORD_WEIGHT,
    path_prefix: str = "",
) -> list[SearchResult]:
    """Hybrid search: top-K candidates from each side, min-max normalize
    each side independently, combine with weighted sum, sort, truncate."""
    if not query.strip():
        return []

    from embeddings import embed_text

    query_embedding = embed_text(query)

    db.init_schema()
    keyword_rows = db.keyword_search(query, SEARCH_HYBRID_FETCH_K, path_prefix=path_prefix)
    vector_rows = db.vector_search(query_embedding, SEARCH_HYBRID_FETCH_K, path_prefix=path_prefix)
    db.close()

    def chunk_key(r: dict) -> str:
        return f"{r['file_path']}:{r['start_line']}-{r['end_line']}"

    # Min-max normalize each side's raw scores independently, over that
    # side's own candidate set (not the union) — this is the PRD's literal
    # spec, not the reference implementation's 1/(1+x) reciprocal scoring.
    keyword_keys = [chunk_key(r) for r in keyword_rows]
    keyword_normalized = _min_max_normalize([r["raw_score"] for r in keyword_rows])
    keyword_norm_by_key = dict(zip(keyword_keys, keyword_normalized))

    vector_keys = [chunk_key(r) for r in vector_rows]
    vector_normalized = _min_max_normalize([r["raw_score"] for r in vector_rows])
    vector_norm_by_key = dict(zip(vector_keys, vector_normalized))

    # Merge by chunk key so a candidate appearing on only one side still
    # shows up, scored 0.0 on the side it's missing from.
    merged: dict[str, dict] = {}
    for r in keyword_rows:
        merged[chunk_key(r)] = r
    for r in vector_rows:
        merged.setdefault(chunk_key(r), r)

    results: list[SearchResult] = []
    for key, data in merged.items():
        vector_score = vector_norm_by_key.get(key, 0.0)
        keyword_score = keyword_norm_by_key.get(key, 0.0)
        combined_score = vector_weight * vector_score + keyword_weight * keyword_score
        if combined_score < min_score:
            continue
        results.append(
            SearchResult(
                path=data["file_path"],
                start_line=data["start_line"],
                end_line=data["end_line"],
                text=data["content"],
                score=combined_score,
                match_type="hybrid",
                section_title=data.get("section_title", ""),
            )
        )

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]


def search(
    query: str,
    mode: str = "hybrid",
    limit: int = SEARCH_DEFAULT_LIMIT,
    min_score: float = SEARCH_MIN_SCORE,
    path_prefix: str = "",
) -> list[SearchResult]:
    """Main search entry point. Dispatches to the requested mode."""
    if mode == "keyword":
        return search_keyword(query, limit, path_prefix=path_prefix)
    elif mode == "semantic":
        return search_semantic(query, limit, min_score, path_prefix=path_prefix)
    elif mode == "hybrid":
        return search_hybrid(query, limit, min_score, path_prefix=path_prefix)
    else:
        print(f"Unknown search mode: {mode}")
        return []


def format_results(results: list[SearchResult]) -> str:
    """Pretty-print search results with file paths, scores, and snippets."""
    if not results:
        return "No results found."

    lines: list[str] = []
    lines.append(f"Found {len(results)} result(s):\n")

    for i, r in enumerate(results, 1):
        snippet = r.text.replace("\n", " ").strip()
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        snippet = _neutralize(snippet)

        section_title = _neutralize(r.section_title) if r.section_title else ""
        section = f" [{section_title}]" if section_title else ""
        lines.append(f"{i}. {r.path}:{r.start_line}-{r.end_line}{section}")
        lines.append(f"   Score: {r.score:.3f} ({r.match_type})")
        lines.append(f"   {snippet}")
        lines.append("")

    return "\n".join(lines)


def _print(output: str) -> None:
    """Print, falling back to ascii-safe output on Windows console encoding errors."""
    try:
        print(output)
    except UnicodeEncodeError:
        print(output.encode("ascii", errors="replace").decode("ascii"))


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Search memory files")
    parser.add_argument("query", nargs="?", default="", help="Search query")
    parser.add_argument(
        "--mode",
        choices=["keyword", "semantic", "hybrid"],
        default="hybrid",
        help="Search mode (default: hybrid)",
    )
    parser.add_argument("--limit", type=int, default=SEARCH_DEFAULT_LIMIT, help="Max results")
    parser.add_argument("--min-score", type=float, default=SEARCH_MIN_SCORE, help="Min score")
    parser.add_argument(
        "--path-prefix", default="",
        help="Filter results to files under this path prefix (e.g. 'drafts/sent')",
    )
    args = parser.parse_args()

    if not args.query:
        parser.error("query is required")

    results = search(
        args.query,
        mode=args.mode,
        limit=args.limit,
        min_score=args.min_score,
        path_prefix=args.path_prefix,
    )
    _print(format_results(results))


if __name__ == "__main__":
    main()
