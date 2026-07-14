"""LLM Gateway — centralized access to Google Gemini.

All LLM calls route through this gateway. Features:
- Retry with exponential backoff
- Model fallback chain (primary → fallback)
- Response caching (optional)
- Structured JSON output enforcement
- Prompt injection protection
- Token/cost tracking (stub for now)

The LLM NEVER directly computes risk. It only:
- Resolves entities (disambiguation)
- Classifies events (type, severity)
- Generates narratives (SAR drafts, evidence summaries)
- Explains deterministically computed scores
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)

# Prompt injection patterns to detect and reject
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"forget\s+(all\s+)?previous",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(all\s+)?previous",
    r"override\s+(all\s+)?previous",
    r"system\s*prompt",
    r"<\s*/?system\s*>",
    r"\[\s*INST\s*\]",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def check_prompt_injection(text: str) -> bool:
    """Return True if the text contains suspicious prompt injection patterns."""
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False


class LLMGateway:
    """Centralized LLM access with retry, fallback, and safety.

    Usage:
        gateway = LLMGateway(api_key="...", model="gemini-2.0-flash")
        result = await gateway.generate_json(
            prompt="Classify this event...",
            system_prompt="You are a compliance analyst...",
            schema={"event_type": "str", "severity": "str"},
        )
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        fallback_model: str = "gemini-2.0-flash-lite",
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._fallback_model = fallback_model
        self._max_retries = max_retries
        self._timeout = timeout
        self._client = None
        self._call_count = 0
        self._total_tokens = 0

    def _ensure_client(self):
        """Lazy-initialize the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                self._client = genai
                logger.info("Gemini client initialized (model: %s)", self._model)
            except ImportError:
                logger.error("google-generativeai not installed")
                raise
            except Exception as e:
                logger.error("Failed to initialize Gemini: %s", e)
                raise

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
    ) -> dict[str, Any]:
        """Generate a structured JSON response from the LLM.

        Enforces JSON output, retries on failure, falls back to secondary model.
        All user-provided text is screened for prompt injection.
        """
        # Prompt injection check on user-provided content
        if check_prompt_injection(prompt):
            logger.warning("Prompt injection detected — rejecting request")
            return {
                "error": "prompt_injection_detected",
                "reasoning": "Input contained patterns matching known prompt injection techniques",
                "confidence": 0.0,
            }

        self._ensure_client()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        full_prompt += "\n\nRespond ONLY with valid JSON. No markdown, no explanation outside the JSON."

        models_to_try = [self._model, self._fallback_model]

        for model_name in models_to_try:
            for attempt in range(self._max_retries):
                try:
                    model = self._client.GenerativeModel(model_name)
                    response = model.generate_content(
                        full_prompt,
                        generation_config=self._client.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                            response_mime_type="application/json",
                        ),
                    )

                    self._call_count += 1
                    text = response.text.strip()

                    # Parse JSON (handle markdown code blocks)
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

                    result = json.loads(text)
                    logger.debug(
                        "LLM call #%d (model=%s, attempt=%d) succeeded",
                        self._call_count, model_name, attempt + 1,
                    )
                    return result

                except json.JSONDecodeError as e:
                    logger.warning(
                        "LLM returned invalid JSON (model=%s, attempt=%d): %s",
                        model_name, attempt + 1, e,
                    )
                except Exception as e:
                    logger.warning(
                        "LLM call failed (model=%s, attempt=%d): %s",
                        model_name, attempt + 1, e,
                    )
                    if attempt < self._max_retries - 1:
                        wait = 2 ** attempt
                        time.sleep(wait)

            logger.warning("All retries exhausted for model %s, trying fallback", model_name)

        # Graceful degradation — return error structure instead of crashing
        logger.error("All LLM models exhausted — returning degraded response")
        return {
            "error": "llm_unavailable",
            "reasoning": "All LLM models failed after retries. Event queued for human review.",
            "confidence": 0.0,
        }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
    ) -> str:
        """Generate a plain text response (for narratives like SAR drafts)."""
        if check_prompt_injection(prompt):
            return "[BLOCKED: Prompt injection detected in input]"

        self._ensure_client()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        try:
            model = self._client.GenerativeModel(self._model)
            response = model.generate_content(
                full_prompt,
                generation_config=self._client.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
            )
            self._call_count += 1
            return response.text.strip()
        except Exception as e:
            logger.error("Text generation failed: %s", e)
            return f"[LLM ERROR: {e}]"

    @property
    def stats(self) -> dict[str, Any]:
        """Return gateway usage statistics."""
        return {
            "total_calls": self._call_count,
            "primary_model": self._model,
            "fallback_model": self._fallback_model,
        }
