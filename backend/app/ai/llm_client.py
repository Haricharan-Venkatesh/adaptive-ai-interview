"""
Unified LLM Client wrapper.

Supports Gemini (via google-generativeai SDK) and provides fallback mock responses
for testing and local development when no API keys are configured.
"""

import json
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level variable to store initialized state
_initialized = False


def init_llm_client() -> None:
    """Initialize the Google Generative AI SDK with the configured API key."""
    global _initialized
    api_key = settings.gemini_api_key
    if api_key:
        try:
            genai.configure(api_key=api_key)
            _initialized = True
            logger.info("Gemini client successfully initialized")
        except Exception as exc:
            logger.error("Failed to configure Gemini SDK", error=str(exc))
            _initialized = False
    else:
        logger.warning("GEMINI_API_KEY is not set. LLM Client will operate in MOCK MODE.")
        _initialized = False


def is_llm_initialized() -> bool:
    """Return True if Gemini SDK has been configured with an API key."""
    return _initialized


def _generate_mock_instance[T: BaseModel](model_class: type[T]) -> T:
    """
    Generate a mock instance of a Pydantic model by inspecting its fields.
    Provides realistic placeholders for common field names (e.g. correctness, feedback).
    """
    mock_data: dict[str, Any] = {}
    
    for field_name, field_info in model_class.model_fields.items():
        # Get field type
        field_type = field_info.annotation
        
        # Check standard types and common field names
        if field_name == "correctness":
            mock_data[field_name] = 0.8
        elif field_name in ("reasoning_quality", "explanation_depth", "code_quality", "communication_skills"):
            mock_data[field_name] = 0.75
        elif field_name == "feedback":
            mock_data[field_name] = "The answer demonstrates a solid fundamental understanding, but could expand on edge cases."
        elif field_name in ("concepts_mastered", "mastered_concepts"):
            mock_data[field_name] = ["Variables", "Control Flow"]
        elif field_name in ("concepts_failed", "failed_concepts"):
            mock_data[field_name] = ["Error Handling"]
        elif field_name == "question_text":
            mock_data[field_name] = "Explain the difference between process and thread."
        elif field_name == "reference_answer":
            mock_data[field_name] = "A process has its own memory space, whereas a thread shares memory with other threads."
        elif field_name == "topic":
            mock_data[field_name] = "OS"
        elif field_name == "difficulty":
            mock_data[field_name] = "intermediate"
        elif field_name == "concepts":
            mock_data[field_name] = ["Processes", "Threads"]
        elif field_type is float:
            mock_data[field_name] = 0.7
        elif field_type is int:
            mock_data[field_name] = 1
        elif field_type is bool:
            mock_data[field_name] = True
        elif field_type is str:
            mock_data[field_name] = f"Mock {field_name}"
        elif getattr(field_type, "__origin__", None) is list:
            # Handle list types (e.g. list[str])
            arg = field_type.__args__[0] if field_type.__args__ else str
            if arg is str:
                mock_data[field_name] = [f"Mock {field_name} Item"]
            elif issubclass(arg, BaseModel):
                mock_data[field_name] = [_generate_mock_instance(arg)]
            else:
                mock_data[field_name] = []
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Nested model
            mock_data[field_name] = _generate_mock_instance(field_type)
        else:
            mock_data[field_name] = None

    return model_class.model_validate(mock_data)


async def generate_json[T: BaseModel](
    prompt: str,
    response_model: type[T],
    system_instruction: str | None = None,
    temperature: float = 0.2,
    model_name: str = "gemini-1.5-flash",
) -> T:
    """
    Generate structured JSON output matching a Pydantic model.
    Falls back to mock generation if GEMINI_API_KEY is not configured or fails.
    """
    if not _initialized:
        logger.debug("Operating in mock mode — generating mock model response", model=response_model.__name__)
        return _generate_mock_instance(response_model)

    try:
        # Configuration for structured JSON output
        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=response_model,
            temperature=temperature,
        )

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
        )

        # generate_content_async is the async SDK call
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config,
        )
        
        text = response.text
        if not text:
            raise ValueError("Empty response received from Gemini API")
            
        data = json.loads(text)
        return response_model.model_validate(data)

    except ValidationError as val_err:
        logger.error(
            "Gemini response validation failed, falling back to mock response",
            error=str(val_err),
            response_text=response.text if 'response' in locals() else None,
        )
        return _generate_mock_instance(response_model)
    except Exception as exc:
        logger.error(
            "Gemini API request failed, falling back to mock response",
            error=str(exc),
        )
        return _generate_mock_instance(response_model)
