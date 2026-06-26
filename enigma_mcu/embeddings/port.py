"""The embedder port and a deterministic fake.

`Embedder` is the seam the mapper depends on; the real bge-m3-via-Ollama backend
arrives in SPEC-004. `FakeEmbedder` produces a deterministic 1024-dim vector from
the text alone (no model, no network), so mapping is fully unit-testable and
golden-stable: same text → same vector, different text → different vector.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

# bge-m3 dimensionality, fixed by ADR-0007. The Neo4j vector index commits to it.
EMBEDDING_DIM = 1024

# sha256 yields 32 bytes = 8 four-byte words per call; pull that many floats each round.
_BYTES_PER_FLOAT = 4
_UINT32_MAX = 0xFFFFFFFF


class Embedder(ABC):
    """A source of fixed-dimension embedding vectors for a piece of text."""

    @abstractmethod
    def embed(self, text: str) -> list[float]:
        """Return an `EMBEDDING_DIM`-length vector for `text`."""
        raise NotImplementedError


class FakeEmbedder(Embedder):
    """Deterministic stand-in: a hash-derived vector, stable across calls/runs."""

    def embed(self, text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        while len(values) < EMBEDDING_DIM:
            digest = hashlib.sha256(f"{text}#{counter}".encode("utf-8")).digest()
            for offset in range(0, len(digest), _BYTES_PER_FLOAT):
                if len(values) >= EMBEDDING_DIM:
                    break
                word = int.from_bytes(digest[offset : offset + _BYTES_PER_FLOAT], "big")
                values.append(word / _UINT32_MAX)  # normalized to [0.0, 1.0]
            counter += 1
        return values
