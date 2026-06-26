"""The concept-extraction port and a deterministic fake.

`ConceptExtractor` is the seam behind which the LLM lives (OpenRouter now, local
Ollama later — a config swap). `FakeConceptExtractor` gives unit tests a
deterministic extractor with no API: an explicit text→concepts mapping, with a
deterministic keyword fallback for unmapped text.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

# Words of length >= 5 are kept as fallback candidates (deterministic, first-seen).
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9-]{4,}")


class ConceptExtractor(ABC):
    """Extracts candidate concept strings from a piece of atom text."""

    @abstractmethod
    def extract_concepts(self, text: str) -> list[str]:
        raise NotImplementedError


class FakeConceptExtractor(ConceptExtractor):
    """Deterministic extractor: explicit mapping first, keyword fallback otherwise."""

    def __init__(self, mapping: dict[str, list[str]] | None = None):
        self._mapping = dict(mapping or {})

    def extract_concepts(self, text: str) -> list[str]:
        if text in self._mapping:
            return list(self._mapping[text])
        # Deterministic fallback: unique words (len >= 5) in first-seen order.
        seen: list[str] = []
        for word in _WORD.findall(text):
            lowered = word.lower()
            if lowered not in seen:
                seen.append(lowered)
        return seen
