"""
SQLite database layer for Second Brain memory search.

Local-only (see SecondBrain/Memory/MEMORY.md: "2026-07-03 — Local-only, no
VPS") so this is a plain SQLite module — no Postgres, no backend abstraction.

Storage:
- `chunks_fts` (FTS5) for keyword search.
- `vec_chunks` (sqlite-vec vec0) for vector search — the primary path.
- `chunks.embedding` (plain BLOB column) — a *second* copy of every
  embedding, stored directly on the chunks table. This looks redundant but
  it's the PRD's explicit "insurance policy": if sqlite-vec ever fails to
  load or query on the work PC, `vector_search()` falls back to a numpy
  brute-force KNN over these BLOBs, which has zero dependency on vec0
  working at all.

This module only returns *raw* comparable-within-their-own-method scores
from keyword_search()/vector_search(). Min-max normalization and the
hybrid 70/30 blend happen in memory_search.py, not here — this file stays
focused on retrieval.
"""

from __future__ import annotations

import sqlite3
import sys
from typing import Any

import numpy as np
import sqlite_vec
from numpy.typing import NDArray

from config import DATABASE_PATH, EMBEDDING_DIMENSIONS, EMBEDDING_MODEL

_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    """Lazily open (and cache) the single SQLite connection for this process."""
    global _conn  # noqa: PLW0603
    if _conn is None:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DATABASE_PATH))
        _conn.enable_load_extension(True)
        sqlite_vec.load(_conn)
        _conn.enable_load_extension(False)
        _conn.row_factory = sqlite3.Row
    return _conn


def init_schema() -> None:
    """Create all tables/triggers if they don't already exist."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            content_hash TEXT NOT NULL,
            mtime_ns INTEGER NOT NULL,
            size_bytes INTEGER NOT NULL,
            indexed_at_epoch INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            start_line INTEGER NOT NULL,
            end_line INTEGER NOT NULL,
            section_title TEXT DEFAULT '',
            content TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            created_at_epoch INTEGER NOT NULL,
            embedding BLOB,
            FOREIGN KEY (file_path) REFERENCES files(path)
        );
        CREATE INDEX IF NOT EXISTS idx_chunks_file_path ON chunks(file_path);
    """)
    conn.executescript("""
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            content,
            section_title,
            file_path UNINDEXED,
            content='chunks',
            content_rowid='id'
        );
        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, content, section_title, file_path)
            VALUES (new.id, new.content, new.section_title, new.file_path);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content, section_title, file_path)
            VALUES ('delete', old.id, old.content, old.section_title, old.file_path);
        END;
        CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content, section_title, file_path)
            VALUES ('delete', old.id, old.content, old.section_title, old.file_path);
            INSERT INTO chunks_fts(rowid, content, section_title, file_path)
            VALUES (new.id, new.content, new.section_title, new.file_path);
        END;
    """)
    # distance_metric=cosine must be set explicitly — vec0's default is L2
    # (Euclidean distance), which is the wrong metric for text embeddings.
    conn.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
            embedding float[{EMBEDDING_DIMENSIONS}] distance_metric=cosine
        )
    """)
    upsert_meta("schema_version", "1")
    upsert_meta("embedding_model", EMBEDDING_MODEL)
    upsert_meta("embedding_dimensions", str(EMBEDDING_DIMENSIONS))
    conn.commit()


def close() -> None:
    """Close the connection (safe to call even if never opened)."""
    global _conn  # noqa: PLW0603
    if _conn is not None:
        _conn.close()
        _conn = None


def commit() -> None:
    _get_conn().commit()


# =============================================================================
# META
# =============================================================================


def upsert_meta(key: str, value: str) -> None:
    _get_conn().execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES (?, ?)", (key, value)
    )


def get_meta(key: str) -> str | None:
    row = _get_conn().execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


# =============================================================================
# FILES (incremental re-indexing bookkeeping)
# =============================================================================


def upsert_file(path: str, content_hash: str, mtime_ns: int, size_bytes: int, epoch: int) -> None:
    _get_conn().execute(
        """INSERT OR REPLACE INTO files(path, content_hash, mtime_ns, size_bytes, indexed_at_epoch)
           VALUES (?, ?, ?, ?, ?)""",
        (path, content_hash, mtime_ns, size_bytes, epoch),
    )


def get_file_hash(path: str) -> str | None:
    row = _get_conn().execute("SELECT content_hash FROM files WHERE path = ?", (path,)).fetchone()
    return row[0] if row else None


def get_all_file_paths() -> list[str]:
    rows = _get_conn().execute("SELECT path FROM files").fetchall()
    return [r[0] for r in rows]


def delete_file(path: str) -> None:
    _get_conn().execute("DELETE FROM files WHERE path = ?", (path,))


# =============================================================================
# CHUNKS
# =============================================================================


def get_chunk_ids_for_file(path: str) -> list[int]:
    rows = _get_conn().execute("SELECT id FROM chunks WHERE file_path = ?", (path,)).fetchall()
    return [r[0] for r in rows]


def delete_chunks_for_file(path: str) -> None:
    """Delete a file's chunk rows and their matching vec_chunks rows.

    This prunes *derived search-index data*, not real vault content — the
    markdown files themselves are never touched here. It runs whenever a
    file's content changes (old chunks are stale) or a file disappears from
    the vault (see memory_index.py's remove_stale_files). This does not
    violate the project's "never delete anything" rule, which is about vault
    content the user wrote — this is a cache that regenerates from the vault
    on the next `memory_index.py` run.
    """
    conn = _get_conn()
    chunk_ids = get_chunk_ids_for_file(path)
    for chunk_id in chunk_ids:
        conn.execute("DELETE FROM vec_chunks WHERE rowid = ?", (chunk_id,))
    conn.execute("DELETE FROM chunks WHERE file_path = ?", (path,))


def insert_chunk(
    file_path: str,
    start_line: int,
    end_line: int,
    section_title: str,
    content: str,
    content_hash: str,
    created_at_epoch: int,
    embedding_bytes: bytes | None,
) -> int:
    """Insert one chunk, storing its embedding twice (see module docstring).

    Returns the new chunk id.
    """
    conn = _get_conn()
    cursor = conn.execute(
        """INSERT INTO chunks(file_path, start_line, end_line, section_title,
                              content, content_hash, created_at_epoch, embedding)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (file_path, start_line, end_line, section_title, content, content_hash,
         created_at_epoch, embedding_bytes),
    )
    chunk_id = cursor.lastrowid
    if chunk_id is None:
        raise RuntimeError("Failed to get lastrowid after chunk insert")

    if embedding_bytes is not None:
        conn.execute(
            "INSERT INTO vec_chunks(rowid, embedding) VALUES (?, ?)",
            (chunk_id, embedding_bytes),
        )

    return chunk_id


def bulk_clear() -> None:
    """Wipe all indexed data (used by --rebuild)."""
    conn = _get_conn()
    conn.execute("DELETE FROM vec_chunks")
    conn.execute("DELETE FROM chunks")
    conn.execute("DELETE FROM files")
    conn.commit()


# =============================================================================
# KEYWORD SEARCH (FTS5)
# =============================================================================


def _quote_fts_query(query: str) -> str:
    """Quote each term for FTS5 AND search — dodges FTS5 syntax errors from
    punctuation/operators in a raw user query."""
    terms = query.strip().split()
    if not terms:
        return query
    quoted = [f'"{term}"' for term in terms]
    return " AND ".join(quoted)


def keyword_search(query: str, limit: int, path_prefix: str = "") -> list[dict[str, Any]]:
    """FTS5 keyword search. Returns raw_score = -rank (higher = better).

    FTS5's `rank` column is negative BM25 (more negative = more relevant),
    so we negate it here to get a normal "higher is better" score. The
    caller (memory_search.py) min-max normalizes this alongside the vector
    scores before combining.
    """
    conn = _get_conn()
    fts_query = _quote_fts_query(query)

    if path_prefix:
        sql = """
            SELECT c.file_path, c.start_line, c.end_line, c.content,
                   c.section_title, rank
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ? AND c.file_path LIKE ?
            ORDER BY rank
            LIMIT ?
        """
        params: tuple = (fts_query, path_prefix + "%", limit)
    else:
        sql = """
            SELECT c.file_path, c.start_line, c.end_line, c.content,
                   c.section_title, rank
            FROM chunks_fts
            JOIN chunks c ON c.id = chunks_fts.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        params = (fts_query, limit)

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # Quoting still produced something FTS5 couldn't parse — give up
        # quietly rather than raising all the way up to the CLI.
        return []

    results: list[dict[str, Any]] = []
    for row in rows:
        raw_score = -float(row["rank"])
        results.append({
            "file_path": row["file_path"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "content": row["content"],
            "section_title": row["section_title"] or "",
            "raw_score": raw_score,
        })
    return results


# =============================================================================
# VECTOR SEARCH (sqlite-vec, with numpy KNN fallback)
# =============================================================================


def knn(
    query_embedding: NDArray[np.float32],
    candidates: list[tuple[int, bytes]],
    k: int,
) -> list[tuple[int, float]]:
    """Brute-force cosine-similarity KNN in numpy — the fallback path.

    `candidates` is a list of (chunk_id, embedding_bytes) pairs. Independent
    of sqlite/sqlite-vec: given the raw bytes, this is pure numpy math, which
    is why it works as an "insurance policy" if sqlite-vec misbehaves.

    Returns up to k (chunk_id, score) pairs sorted descending by cosine
    similarity (higher = more similar, same convention as vector_search).
    """
    if not candidates:
        return []

    ids = [c[0] for c in candidates]
    matrix = np.stack(
        [np.frombuffer(c[1], dtype=np.float32) for c in candidates]
    ).astype(np.float32)

    query = np.asarray(query_embedding, dtype=np.float32)

    # Vectorized cosine similarity: dot(query, row) / (|query| * |row|)
    query_norm = np.linalg.norm(query)
    row_norms = np.linalg.norm(matrix, axis=1)
    denom = query_norm * row_norms
    # Avoid divide-by-zero for any degenerate (all-zero) embedding.
    denom[denom == 0] = 1e-12
    similarities = (matrix @ query) / denom

    order = np.argsort(-similarities)[:k]
    return [(ids[i], float(similarities[i])) for i in order]


def vector_search(
    embedding: NDArray[np.float32], limit: int, path_prefix: str = ""
) -> list[dict[str, Any]]:
    """Vector similarity search. Returns raw_score = 1 - distance (higher = better).

    Tries the sqlite-vec vec0 MATCH query first (fast, indexed). If that
    raises ANY exception — extension load failure, missing table, bad
    query — falls back to the numpy knn() brute-force path over the plain
    BLOB embeddings stored on the chunks table. Both paths return the same
    shape of results so callers don't need to know which one ran.
    """
    conn = _get_conn()
    query_bytes = np.asarray(embedding, dtype=np.float32).tobytes()

    try:
        # sqlite-vec doesn't support WHERE filters inside a MATCH query, so
        # when path_prefix is set we over-fetch and filter in Python.
        fetch_limit = limit * 5 if path_prefix else limit
        rows = conn.execute(
            """
            SELECT v.rowid, v.distance,
                   c.file_path, c.start_line, c.end_line, c.content, c.section_title
            FROM vec_chunks v
            JOIN chunks c ON c.id = v.rowid
            WHERE v.embedding MATCH ?
                AND k = ?
            ORDER BY v.distance
            """,
            (query_bytes, fetch_limit),
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            if path_prefix and not row["file_path"].startswith(path_prefix):
                continue
            distance = float(row["distance"])
            # Cosine distance ranges 0 (identical) to 2 (opposite); 1 - distance
            # converts it back to cosine similarity (-1 to 1, higher = better),
            # which is a more meaningful "raw_score" than a bare negation would
            # be — it keeps 0.0 as a genuinely neutral/orthogonal midpoint
            # instead of every non-perfect match reading as a large negative.
            results.append({
                "file_path": row["file_path"],
                "start_line": row["start_line"],
                "end_line": row["end_line"],
                "content": row["content"],
                "section_title": row["section_title"] or "",
                "raw_score": 1.0 - distance,
            })
            if len(results) >= limit:
                break
        return results

    except Exception as e:
        print(f"[db] sqlite-vec query failed, falling back to numpy KNN: {e}", file=sys.stderr)
        return _vector_search_fallback(conn, embedding, limit, path_prefix)


def _vector_search_fallback(
    conn: sqlite3.Connection,
    embedding: NDArray[np.float32],
    limit: int,
    path_prefix: str,
) -> list[dict[str, Any]]:
    """numpy brute-force KNN fallback, reading embeddings from chunks.embedding."""
    if path_prefix:
        rows = conn.execute(
            "SELECT id, embedding FROM chunks WHERE file_path LIKE ? AND embedding IS NOT NULL",
            (path_prefix + "%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, embedding FROM chunks WHERE embedding IS NOT NULL"
        ).fetchall()

    candidates = [(row["id"], row["embedding"]) for row in rows]
    top_k = knn(embedding, candidates, limit)
    if not top_k:
        return []

    id_to_score = dict(top_k)
    placeholders = ",".join("?" for _ in id_to_score)
    chunk_rows = conn.execute(
        f"""SELECT id, file_path, start_line, end_line, content, section_title
            FROM chunks WHERE id IN ({placeholders})""",
        tuple(id_to_score.keys()),
    ).fetchall()

    results: list[dict[str, Any]] = []
    for row in chunk_rows:
        results.append({
            "file_path": row["file_path"],
            "start_line": row["start_line"],
            "end_line": row["end_line"],
            "content": row["content"],
            "section_title": row["section_title"] or "",
            "raw_score": id_to_score[row["id"]],
        })
    results.sort(key=lambda r: r["raw_score"], reverse=True)
    return results


# =============================================================================
# STATS
# =============================================================================


def get_stats() -> dict[str, Any]:
    conn = _get_conn()
    file_count: int = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
    chunk_count: int = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    vec_count: int = conn.execute("SELECT COUNT(*) FROM vec_chunks").fetchone()[0]
    model_row = conn.execute("SELECT value FROM meta WHERE key = 'embedding_model'").fetchone()
    model_name = model_row[0] if model_row else "unknown"
    stats: dict[str, Any] = {
        "files": file_count,
        "chunks": chunk_count,
        "vectors": vec_count,
        "model": model_name,
    }
    if DATABASE_PATH.exists():
        stats["db_size_kb"] = DATABASE_PATH.stat().st_size / 1024
    return stats
