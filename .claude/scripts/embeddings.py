"""
FastEmbed wrapper for memory search embeddings.

Lazy-loaded embedding model (loaded once per process, on first use) plus
serialization helpers for storing embeddings in SQLite (both the vec0
table and the plain BLOB fallback column — see db.py).
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from config import EMBEDDING_CACHE_DIR, EMBEDDING_MODEL

if TYPE_CHECKING:
    from fastembed import TextEmbedding

# Lazy singleton — model loaded on first use (~90MB download, one time only).
_model: TextEmbedding | None = None


def _get_model() -> TextEmbedding:
    """Get or create the embedding model singleton."""
    global _model  # noqa: PLW0603
    if _model is None:
        from fastembed import TextEmbedding

        # cache_dir must be passed explicitly — FastEmbed's default is a temp
        # dir, which means the ~90MB model would re-download after every
        # temp-file cleanup instead of being cached in the project.
        EMBEDDING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _model = TextEmbedding(
            model_name=EMBEDDING_MODEL,
            cache_dir=str(EMBEDDING_CACHE_DIR),
        )
    return _model


def embed_text(text: str) -> NDArray[np.float32]:
    """Embed a single text string into a 384-dim float32 vector."""
    model = _get_model()
    results = list(model.embed([text]))
    embedding: NDArray[np.float32] = np.array(results[0], dtype=np.float32)
    return embedding


def embed_batch(texts: list[str], batch_size: int = 32) -> list[NDArray[np.float32]]:
    """Embed a batch of texts. Returns a list of 384-dim float32 vectors."""
    if not texts:
        return []
    model = _get_model()
    results = list(model.embed(texts, batch_size=batch_size))
    return [np.array(r, dtype=np.float32) for r in results]


def embedding_to_bytes(embedding: NDArray[np.float32]) -> bytes:
    """Serialize an embedding to raw bytes for SQLite BLOB storage."""
    return np.asarray(embedding, dtype=np.float32).tobytes()


def bytes_to_embedding(data: bytes) -> NDArray[np.float32]:
    """Deserialize bytes back into an embedding array."""
    arr: NDArray[np.float32] = np.frombuffer(data, dtype=np.float32).copy()
    return arr


def text_hash(text: str) -> str:
    """SHA-256 prefix (16 hex chars) for content dedup/change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
