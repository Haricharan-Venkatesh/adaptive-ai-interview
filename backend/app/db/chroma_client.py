"""
ChromaDB Client — M4.1 Vector Embeddings.

Manages initialization and access to the ChromaDB 'questions' collection.

Architecture:
  - Module-level singleton matching redis_client.py pattern
  - init_chroma() called in app lifespan AFTER embed service and DB are ready
  - get_chroma_collection() used for FastAPI dependency injection
  - Tests can pass testing=True to use EphemeralClient (no disk I/O)
"""

from __future__ import annotations

from typing import Any

import chromadb  # type: ignore[import]
from chromadb.api import ClientAPI  # type: ignore[import]

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

COLLECTION_NAME = "questions"

_client: ClientAPI | None = None
_collection: chromadb.Collection | None = None  # type: ignore[name-defined]


def _make_client(testing: bool = False) -> ClientAPI:
    """Create a ChromaDB client — persistent for prod, ephemeral for tests."""
    if testing:
        return chromadb.EphemeralClient()
    return chromadb.PersistentClient(path=settings.chroma_persist_path)


async def init_chroma(testing: bool = False) -> None:
    """
    Initialize ChromaDB and upsert all question embeddings.

    Called once during app lifespan startup.
    This function is idempotent — safe to call multiple times.
    """
    global _client, _collection

    try:
        _client = _make_client(testing=testing)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "ChromaDB initialized",
            collection=COLLECTION_NAME,
            existing_items=_collection.count(),
        )
    except Exception as exc:
        logger.error("ChromaDB initialization failed", error=str(exc))
        _client = None
        _collection = None


async def close_chroma() -> None:
    """Graceful shutdown — ChromaDB PersistentClient auto-flushes, but we reset refs."""
    global _client, _collection
    _client = None
    _collection = None
    logger.info("ChromaDB connection closed")


def get_chroma_collection() -> chromadb.Collection:  # type: ignore[name-defined]
    """
    FastAPI dependency: return the active ChromaDB collection.
    Raises RuntimeError if not initialized.
    """
    if _collection is None:
        raise RuntimeError("ChromaDB not initialized — call init_chroma() first")
    return _collection


def is_chroma_ready() -> bool:
    """Return True if ChromaDB is initialized and the collection is available."""
    return _collection is not None


async def upsert_question_embeddings(
    question_ids: list[str],
    question_texts: list[str],
    metadatas: list[dict[str, Any]],
    embeddings: list[list[float]],
) -> None:
    """
    Upsert a batch of question embeddings into the ChromaDB collection.

    Args:
        question_ids: Unique string IDs (PostgreSQL UUIDs).
        question_texts: Raw question text (stored as document).
        metadatas: Dict per question with topic, difficulty, concepts.
        embeddings: Pre-computed float vectors from EmbeddingService.
    """
    if _collection is None:
        logger.warning("ChromaDB not ready — skipping upsert")
        return

    try:
        _collection.upsert(
            ids=question_ids,
            documents=question_texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.info("Upserted question embeddings", count=len(question_ids))
    except Exception as exc:
        logger.error("ChromaDB upsert failed", error=str(exc))


def query_similar(
    query_embedding: list[float],
    n_results: int = 5,
    where_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Query the questions collection for semantically similar items.

    Args:
        query_embedding: The query vector.
        n_results: Number of results to return.
        where_filter: Optional ChromaDB metadata filter (e.g., {"topic": "DSA"}).

    Returns:
        List of dicts with keys: id, document, metadata, distance.
    """
    if _collection is None:
        logger.warning("ChromaDB not ready — returning empty results")
        return []

    try:
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        raw = _collection.query(**kwargs)

        results: list[dict[str, Any]] = []
        ids = raw.get("ids", [[]])[0]
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        dists = raw.get("distances", [[]])[0]

        for qid, doc, meta, dist in zip(ids, docs, metas, dists, strict=False):
            results.append(
                {
                    "id": qid,
                    "document": doc,
                    "metadata": meta,
                    "distance": dist,
                }
            )
        return results

    except Exception as exc:
        logger.error("ChromaDB query failed", error=str(exc))
        return []
