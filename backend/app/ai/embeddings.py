"""
Embedding Service — M4.1 Vector Embeddings.

Wraps sentence-transformers to produce dense text embeddings.
Uses 'all-MiniLM-L6-v2' by default (384-dim, fast, good quality).

Architecture:
  - Module-level singleton (matches LLMClient pattern)
  - init_embedding_service() called in app lifespan startup
  - get_embedding_service() used for FastAPI dependency injection
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Module-level singleton
_service: "EmbeddingService | None" = None


class EmbeddingService:
    """
    Wraps a SentenceTransformer model for synchronous embedding calls.

    SentenceTransformer.encode() is CPU/GPU bound and not natively async;
    we keep it synchronous. For high-throughput, callers can wrap in
    asyncio.run_in_executor if needed.
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self.embedding_dim: int = 0

    def initialize(self) -> None:
        """Load the model into memory. Called once at startup."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]

            self._model = SentenceTransformer(self.model_name)
            # Probe the embedding dimension
            sample = self._model.encode(["probe"], convert_to_numpy=True)
            self.embedding_dim = int(sample.shape[1])
            logger.info(
                "EmbeddingService initialized",
                model=self.model_name,
                dim=self.embedding_dim,
            )
        except Exception as exc:
            logger.error("EmbeddingService initialization failed", error=str(exc))
            self._model = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def embed_text(self, text: str) -> list[float]:
        """
        Embed a single text string.

        Returns a float list of length `embedding_dim`.
        Falls back to a zero-vector if the model is not loaded.
        """
        if not self.is_ready:
            logger.warning("EmbeddingService not ready — returning zero vector")
            return [0.0] * 384  # fallback dim for all-MiniLM-L6-v2

        import numpy as np  # type: ignore[import]

        vec: np.ndarray = self._model.encode([text], convert_to_numpy=True)[0]  # type: ignore[index]
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts in a single forward pass (efficient batching).

        Returns a list of float lists, one per input text.
        """
        if not self.is_ready:
            logger.warning("EmbeddingService not ready — returning zero vectors")
            return [[0.0] * 384 for _ in texts]

        import numpy as np  # type: ignore[import]

        vecs: np.ndarray = self._model.encode(texts, convert_to_numpy=True)  # type: ignore
        return [row.tolist() for row in vecs]


# ─── FastAPI Lifecycle & Dependencies ─────────────────────────────────────────


def init_embedding_service() -> None:
    """
    Create and initialize the global EmbeddingService singleton.
    Call this once during app startup lifespan.
    """
    global _service
    _service = EmbeddingService(model_name=settings.embedding_model_name)
    _service.initialize()


def get_embedding_service() -> EmbeddingService:
    """
    FastAPI dependency: return the initialized EmbeddingService.
    If lifespan hook was skipped (e.g. test), initializes lazily.
    """
    global _service
    if _service is None:
        init_embedding_service()
    return _service  # type: ignore[return-value]
