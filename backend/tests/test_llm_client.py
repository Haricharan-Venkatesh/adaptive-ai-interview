"""
Unit tests for the class-based unified LLM client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from app.ai.llm_client import (
    LLMClient,
    generate_json,
    get_llm_client,
    init_llm_client,
    is_llm_initialized,
)
from app.core.config import settings


class DummyResponseModel(BaseModel):
    correctness: float
    feedback: str
    concepts_mastered: list[str]


class TestLLMClientClass:
    """Test suite for the class-based LLMClient."""

    def test_client_init_without_key(self) -> None:
        """Client should default to mock mode if initialized without key."""
        with patch.object(settings, "gemini_api_key", ""):
            client = LLMClient()
            client.initialize()
            assert client.initialized is False

    @patch("google.generativeai.configure")
    def test_client_init_with_key(self, mock_configure: MagicMock) -> None:
        """Client should configure the SDK if key is provided."""
        client = LLMClient(api_key="explicit_key")
        client.initialize()
        assert client.initialized is True
        mock_configure.assert_called_once_with(api_key="explicit_key")

    @pytest.mark.asyncio
    async def test_client_mock_generation(self) -> None:
        """Uninitialized client generates mock responses."""
        # Patch the env key to ensure the client stays in mock mode
        # even if a real GEMINI_API_KEY is present in the environment.
        with patch.object(settings, "gemini_api_key", ""):
            client = LLMClient()
            client.initialize()  # should be False with no key
            assert client.initialized is False
            result = await client.generate_json("Hello", DummyResponseModel)
            assert isinstance(result, DummyResponseModel)
            assert result.correctness == 0.8
            assert "MOCK MODE" in result.feedback

    @pytest.mark.asyncio
    @patch("google.generativeai.GenerativeModel")
    async def test_client_real_generation_success(self, mock_gen_model_class: MagicMock) -> None:
        """Initialized client requests Gemini."""
        mock_response = MagicMock()
        mock_response.text = '{"correctness": 0.9, "feedback": "Nice", "concepts_mastered": ["Loops"]}'
        
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_gen_model_class.return_value = mock_model

        client = LLMClient(api_key="fake_key")
        client.initialize()
        
        result = await client.generate_json("test prompt", DummyResponseModel)
        assert isinstance(result, DummyResponseModel)
        assert result.correctness == 0.9
        assert result.feedback == "Nice"
        mock_model.generate_content_async.assert_called_once()


class TestLLMClientGlobalWrapper:
    """Test suite for backward-compatible global hooks and wrappers."""

    def test_init_and_initialized(self) -> None:
        """is_llm_initialized reflects default client initialized status."""
        with patch.object(settings, "gemini_api_key", ""):
            init_llm_client()
            assert is_llm_initialized() is False
            assert get_llm_client().initialized is False

    @pytest.mark.asyncio
    async def test_global_generate_json(self) -> None:
        """Global generate_json function uses default client."""
        with patch.object(settings, "gemini_api_key", ""):
            init_llm_client()
            result = await generate_json("Hello", DummyResponseModel)
            assert isinstance(result, DummyResponseModel)
            assert result.correctness == 0.8
