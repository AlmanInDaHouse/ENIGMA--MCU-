"""OpenRouterConceptExtractor — the real concept extractor via OpenRouter.

Implements the `ConceptExtractor` port against OpenRouter's OpenAI-compatible
chat-completions endpoint (FR-2). Config from env: `OPENROUTER_API_KEY` (required;
a clear error if missing), `OPENROUTER_MODEL`, `OPENROUTER_BASE_URL`. Each request
disables provider data retention and may cap price via `max_price`. The model is
asked for a JSON array of concept strings, parsed defensively. The HTTP client is
imported lazily so importing this module never touches the network.
"""

from __future__ import annotations

import json
import os
import re

from enigma_mcu.extraction.llm_port import ConceptExtractor

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.5-haiku"

_SYSTEM_PROMPT = (
    "You extract the key concepts from a note. Return ONLY a JSON array of short "
    "concept strings (canonical nouns/noun-phrases), no prose, no markdown. "
    'Example: ["MCP", "vector index", "idempotent ingestion"].'
)


class ConfigurationError(RuntimeError):
    """Raised when required OpenRouter configuration is missing (FR-2)."""


class OpenRouterConceptExtractor(ConceptExtractor):
    """Calls OpenRouter's chat-completions endpoint and parses a concept list."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_price: dict | None = None,
        timeout: float = 60.0,
    ):
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self._api_key:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is not set; cannot call the OpenRouter extractor"
            )
        self._model = model or os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL)
        self._base_url = (
            base_url or os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self._max_price = max_price
        self._timeout = timeout

    def extract_concepts(self, text: str) -> list[str]:
        import requests

        # Retention off: deny provider data collection/logging for this request.
        provider: dict = {"data_collection": "deny"}
        if self._max_price is not None:
            provider["max_price"] = self._max_price

        body = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "provider": provider,
            "temperature": 0,
        }
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=self._timeout,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return _parse_concepts(content)


def _parse_concepts(content: str) -> list[str]:
    """Parse a model response into a clean list of concept strings, defensively."""
    text = content.strip()
    # Strip a ```json ... ``` fence if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    concepts: list[str] = []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            parsed = parsed.get("concepts", [])
        if isinstance(parsed, list):
            concepts = [str(item).strip() for item in parsed]
    except (json.JSONDecodeError, TypeError):
        # Fallback: one concept per non-empty line, stripped of list bullets.
        for line in text.splitlines():
            cleaned = line.strip().lstrip("-*0123456789. ").strip().strip('",')
            if cleaned:
                concepts.append(cleaned)

    # Dedupe, drop empties, preserve order.
    seen: list[str] = []
    for concept in concepts:
        if concept and concept not in seen:
            seen.append(concept)
    return seen
