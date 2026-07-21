"""
Tests for M4.1 — EmbeddingService and ChromaDB client.

All tests use in-memory ChromaDB (EphemeralClient) — no disk I/O.
SentenceTransformer is mocked to return fixed-size float vectors.
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

# ─── EmbeddingService tests ───────────────────────────────────────────────────


class TestEmbeddingService:
    """Tests for app.ai.embeddings.EmbeddingService."""

    def _make_service(self, dim: int = 384):
        """Build a fully initialised EmbeddingService with a mocked model."""
        from app.ai.embeddings import EmbeddingService

        svc = EmbeddingService(model_name="all-MiniLM-L6-v2")

        # Create a mock model that returns a numpy array
        mock_model = MagicMock()
        mock_model.encode.return_value = np.zeros((1, dim), dtype=np.float32)
        svc._model = mock_model
        svc.embedding_dim = dim
        return svc

    def test_embed_text_returns_float_list(self):
        svc = self._make_service(dim=384)
        result = svc.embed_text("What is a binary search tree?")
        assert isinstance(result, list)
        assert all(isinstance(v, float) for v in result)
        assert len(result) == 384

    def test_embed_text_not_ready_returns_fallback(self):
        from app.ai.embeddings import EmbeddingService

        svc = EmbeddingService(model_name="all-MiniLM-L6-v2")
        svc._model = None
        result = svc.embed_text("some text")
        assert isinstance(result, list)
        assert len(result) == 384
        assert all(v == 0.0 for v in result)

    def test_embed_batch_returns_list_of_lists(self):
        svc = self._make_service(dim=384)
        # Setup mock to return (N, dim) array for N texts
        svc._model.encode.return_value = np.zeros((3, 384), dtype=np.float32)
        texts = ["q1", "q2", "q3"]
        result = svc.embed_batch(texts)
        assert len(result) == 3
        for vec in result:
            assert isinstance(vec, list)
            assert len(vec) == 384

    def test_is_ready_false_when_not_initialized(self):
        from app.ai.embeddings import EmbeddingService

        svc = EmbeddingService(model_name="test-model")
        assert not svc.is_ready


# ─── ChromaDB client tests ────────────────────────────────────────────────────


class TestChromaClient:
    """Tests for app.db.chroma_client using in-memory EphemeralClient."""

    @pytest.fixture(autouse=True)
    async def setup_chroma(self):
        """Init ChromaDB in-memory before each test and close after."""
        from app.db import chroma_client as cc

        # Reset any previous state
        cc._client = None
        cc._collection = None

        await cc.init_chroma(testing=True)
        yield
        await cc.close_chroma()

    def test_is_chroma_ready(self):
        from app.db.chroma_client import is_chroma_ready

        assert is_chroma_ready() is True

    async def test_upsert_and_query(self):
        from app.db.chroma_client import query_similar, upsert_question_embeddings

        ids = ["q1", "q2"]
        texts = ["What is a linked list?", "Explain binary search."]
        metas = [
            {"topic": "data_structures", "difficulty": "3"},
            {"topic": "algorithms", "difficulty": "4"},
        ]
        embeddings = [[0.1] * 384, [0.2] * 384]

        await upsert_question_embeddings(ids, texts, metas, embeddings)

        results = query_similar(query_embedding=[0.1] * 384, n_results=2)
        assert len(results) > 0
        result_ids = [r["id"] for r in results]
        assert "q1" in result_ids

    async def test_query_returns_empty_when_not_ready(self):
        from app.db import chroma_client as cc
        from app.db.chroma_client import query_similar

        # Temporarily disable
        cc._collection = None
        results = query_similar(query_embedding=[0.0] * 384)
        assert results == []

    def test_get_collection_raises_when_not_initialized(self):
        from app.db import chroma_client as cc
        from app.db.chroma_client import get_chroma_collection

        cc._collection = None
        with pytest.raises(RuntimeError, match="ChromaDB not initialized"):
            get_chroma_collection()
