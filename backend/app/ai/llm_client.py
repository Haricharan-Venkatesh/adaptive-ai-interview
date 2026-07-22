"""
Unified LLM Client wrapper.

Supports Gemini (via google-generativeai SDK) and provides fallback mock responses
for testing and local development when no API keys are configured.
"""

import json
import time
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from pydantic import BaseModel, ValidationError

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Module-level default client singleton
_client: "LLMClient | None" = None


class LLMClient:
    """
    Class-based LLM client wrapper to support dependency injection
    and multiple isolated client configurations.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key
        self.initialized = False

    def initialize(self) -> None:
        """Configure the Gemini SDK with the key."""
        key = self.api_key or settings.gemini_api_key
        if key:
            try:
                genai.configure(api_key=key)
                self.initialized = True
                logger.info("LLMClient initialized successfully")
            except Exception as exc:
                logger.error("Failed to configure Gemini SDK in LLMClient", error=str(exc))
                self.initialized = False
        else:
            logger.warning("No GEMINI_API_KEY set. LLMClient operating in MOCK MODE.")
            self.initialized = False

    async def generate_json[T: BaseModel](
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.2,
        model_name: str = "gemini-2.5-flash",
        timeout: float = 60.0,
    ) -> T:
        """
        Generate structured JSON output matching a Pydantic model.

        When self.initialized is False, returns a mock instance and logs clearly.
        When self.initialized is True, calls Gemini and RAISES on failure — no
        silent fallback to mock data so that errors are immediately visible.
        """
        if not self.initialized:
            logger.warning(
                "LLMClient is in MOCK MODE — returning mock response (not Gemini)",
                model=response_model.__name__,
            )
            return _generate_mock_instance(response_model)

        start_time = time.monotonic()
        logger.info(
            "Calling Gemini API",
            model=model_name,
            response_model=response_model.__name__,
            prompt_preview=prompt[:300] + "..." if len(prompt) > 300 else prompt,
            prompt_length=len(prompt),
            temperature=temperature,
        )

        schema_dict = _to_gemini_schema(response_model)

        logger.info(
            "Gemini response_schema prepared",
            model_class=response_model.__name__,
            schema=schema_dict,
        )

        generation_config = GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema_dict,
            temperature=temperature,
        )

        candidates = [model_name] + [
            m for m in ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-flash-latest"] if m != model_name
        ]

        last_error: Exception | None = None

        for current_model in candidates:
            try:
                model = genai.GenerativeModel(
                    model_name=current_model,
                    system_instruction=system_instruction,
                )

                response = await model.generate_content_async(
                    prompt,
                    generation_config=generation_config,
                    request_options={"timeout": timeout},
                )

                duration_ms = round((time.monotonic() - start_time) * 1000, 1)

                text = response.text if response.text else None
                if not text:
                    raise ValueError(
                        f"Gemini returned an empty response. "
                        f"Finish reason: {response.candidates[0].finish_reason if response.candidates else 'unknown'}"
                    )

                logger.info(
                    "Gemini API raw response received",
                    model=current_model,
                    duration_ms=duration_ms,
                    response_snippet=text[:500] if len(text) > 500 else text,
                    response_length=len(text),
                )

                try:
                    data = json.loads(text)
                except json.JSONDecodeError as json_err:
                    logger.error(
                        "Gemini returned non-JSON text",
                        error=str(json_err),
                        raw_response=text[:500],
                    )
                    raise ValueError(f"Gemini response is not valid JSON: {json_err}") from json_err

                try:
                    return response_model.model_validate(data)
                except ValidationError as val_err:
                    logger.error(
                        "Gemini response failed Pydantic validation",
                        error=str(val_err),
                        raw_response=text[:500],
                    )
                    raise ValueError(f"Gemini response failed schema validation: {val_err}") from val_err

            except Exception as exc:
                last_error = exc
                is_quota_error = (
                    "ResourceExhausted" in type(exc).__name__
                    or "429" in str(exc)
                    or "Quota exceeded" in str(exc)
                )
                if is_quota_error and current_model != candidates[-1]:
                    logger.warning(
                        "Gemini quota / rate limit exceeded, falling back to next model",
                        failed_model=current_model,
                        error=str(exc)[:150],
                    )
                    continue

                duration_ms = round((time.monotonic() - start_time) * 1000, 1)
                logger.error(
                    "Gemini API request failed",
                    model=current_model,
                    duration_ms=duration_ms,
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                raise

        if last_error:
            raise last_error
        raise RuntimeError("All Gemini model candidates failed")


def _generate_mock_instance[T: BaseModel](model_class: type[T]) -> T:
    """
    Generate a mock instance of a Pydantic model by inspecting its fields.
    Provides realistic placeholders for common field names (e.g. correctness, feedback).
    Only used when LLMClient is explicitly in MOCK MODE (no API key configured).
    """
    mock_data: dict[str, Any] = {}
    
    for field_name, field_info in model_class.model_fields.items():
        # Get field type
        field_type = field_info.annotation
        origin = get_origin(field_type)
        args = get_args(field_type)
        
        # Check standard types and common field names
        if field_name == "correctness":
            mock_data[field_name] = 0.8
        elif field_name in ("reasoning_quality", "explanation_depth", "code_quality", "communication_skills"):
            mock_data[field_name] = 0.75
        elif field_name == "feedback":
            mock_data[field_name] = "[MOCK MODE] The answer demonstrates a solid fundamental understanding, but could expand on edge cases."
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
            mock_data[field_name] = 3 if field_type is int else "intermediate"
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
        elif origin is list:
            # Handle list types (e.g. list[str])
            arg = args[0] if args else str
            if arg is str:
                mock_data[field_name] = [f"Mock {field_name} Item"]
            elif isinstance(arg, type) and issubclass(arg, BaseModel):
                mock_data[field_name] = [_generate_mock_instance(arg)]
            else:
                mock_data[field_name] = []
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Nested model
            mock_data[field_name] = _generate_mock_instance(field_type)
        else:
            # Optional fields (float | None, str | None, etc.) → use None
            mock_data[field_name] = None

    return model_class.model_validate(mock_data)


ALLOWED_GEMINI_SCHEMA_KEYS = {
    "type",
    "format",
    "description",
    "nullable",
    "enum",
    "properties",
    "required",
    "items",
}

TYPE_MAP = {
    "string": "STRING",
    "number": "NUMBER",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
    "array": "ARRAY",
    "object": "OBJECT",
}


def _clean_schema_dict(obj: Any) -> Any:
    """
    Recursively clean a JSON Schema dictionary to remove keywords unsupported by Gemini
    (e.g., minimum, maximum, title, $schema, $defs, default, etc.) and format types
    properly for Gemini's Protobuf Schema parser.
    """
    if isinstance(obj, dict):
        cleaned: dict[str, Any] = {}
        for key, value in obj.items():
            if key == "properties" and isinstance(value, dict):
                cleaned["properties"] = {
                    prop_name: _clean_schema_dict(prop_schema)
                    for prop_name, prop_schema in value.items()
                }
            elif key == "type" and isinstance(value, str):
                cleaned["type"] = TYPE_MAP.get(value.lower(), value.upper())
            elif key in ALLOWED_GEMINI_SCHEMA_KEYS:
                cleaned[key] = _clean_schema_dict(value)
        return cleaned
    elif isinstance(obj, list):
        return [_clean_schema_dict(item) for item in obj]
    return obj


def _to_gemini_schema(model_class: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model class to a clean, Gemini-compatible schema dictionary."""
    raw_schema = model_class.model_json_schema()
    return _clean_schema_dict(raw_schema)


# ─── FastAPI Lifecycle Hooks & Dependencies ───────────────────────────────────

def init_llm_client() -> None:
    """Initialize the default global singleton client during startup."""
    global _client
    _client = LLMClient()
    _client.initialize()


def get_llm_client() -> LLMClient:
    """
    FastAPI dependency injection provider.
    Yields the configured LLMClient instance.
    """
    global _client
    if _client is None:
        # Fallback initialization in case context lifespan hook wasn't run
        init_llm_client()
    return _client  # type: ignore[return-value]


def is_llm_initialized() -> bool:
    """Return True if the default global client has been successfully initialized."""
    if _client is None:
        return False
    return _client.initialized


async def generate_json[T: BaseModel](
    prompt: str,
    response_model: type[T],
    system_instruction: str | None = None,
    temperature: float = 0.2,
    model_name: str = "gemini-2.5-flash",
    timeout: float = 60.0,
) -> T:
    """
    Backward-compatible helper function that delegates content generation
    to the default global LLMClient.
    """
    client = get_llm_client()
    return await client.generate_json(
        prompt=prompt,
        response_model=response_model,
        system_instruction=system_instruction,
        temperature=temperature,
        model_name=model_name,
        timeout=timeout,
    )
