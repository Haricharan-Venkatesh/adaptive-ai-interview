"""
Unit tests for the unified LLM client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from app.ai.llm_client import (
    generate_json,
    init_llm_client,
    is_llm_initialized,
)
from app.core.config import settings


class DummyResponseModel(BaseModel):
    correctness: float
    feedback: str
    concepts_mastered: list[str]


class TestLLMClient:
    """Test suite for LLM Client initialization and Generation."""

    def test_init_without_api_key(self) -> None:
        """If gemini_api_key is empty, it should initialize as False."""
        with patch.object(settings, "gemini_api_key", ""):
            init_llm_client()
            assert is_llm_initialized() is False

    @patch("google.generativeai.configure")
    def test_init_with_api_key(self, mock_configure: MagicMock) -> None:
        """If gemini_api_key is present, configure should be called and set to True."""
        with patch.object(settings, "gemini_api_key", "test_secret_key"):
            init_llm_client()
            assert is_llm_initialized() is True
            mock_configure.assert_called_once_with(api_key="test_secret_key")

    @pytest.mark.asyncio
    async def test_mock_generation_when_uninitialized(self) -> None:
        """If uninitialized, generating json should fallback to mock generation."""
        with patch("app.ai.llm_client._initialized", False):
            result = await generate_json("Hello", DummyResponseModel)
            assert isinstance(result, DummyResponseModel)
            assert result.correctness == 0.8
            assert "solid fundamental understanding" in result.feedback
            assert result.concepts_mastered == ["Variables", "Control Flow"]

    @pytest.mark.asyncio
    @patch("google.generativeai.GenerativeModel")
    async def test_real_generation_success(self, mock_gen_model_class: MagicMock) -> None:
        """If initialized, generate_json should request Gemini and parse the response."""
        mock_response = MagicMock()
        mock_response.text = '{"correctness": 0.95, "feedback": "Great job!", "concepts_mastered": ["Loops"]}'
        
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_gen_model_class.return_value = mock_model

        with patch("app.ai.llm_client._initialized", True):
            result = await generate_json(
                prompt="Evaluate this code",
                response_model=DummyResponseModel,
                system_instruction="Test system prompt",
            )
            assert isinstance(result, DummyResponseModel)
            assert result.correctness == 0.95
            assert result.feedback == "Great job!"
            assert result.concepts_mastered == ["Loops"]
            mock_model.generate_content_async.assert_called_once()

    @pytest.mark.asyncio
    @patch("google.generativeai.GenerativeModel")
    async def test_real_generation_invalid_json_fallback(self, mock_gen_model_class: MagicMock) -> None:
        """If Gemini returns invalid JSON, it should fallback to mock model gracefully."""
        mock_response = MagicMock()
        mock_response.text = "invalid-non-json-output"
        
        mock_model = MagicMock()
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        mock_gen_model_class.return_value = mock_model

        with patch("app.ai.llm_client._initialized", True):
            result = await generate_json(
                prompt="Evaluate this code",
                response_model=DummyResponseModel,
            )
            # Should fallback to mock data
            assert isinstance(result, DummyResponseModel)
            assert result.correctness == 0.8
