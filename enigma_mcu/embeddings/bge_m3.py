"""BgeM3Embedder — the real `Embedder`, backed by bge-m3 via Ollama.

Implements the SPEC-003 port (FR-5): `embed(text)` returns a 1024-float vector
from the bge-m3 model served by a local Ollama. Config from the environment
(`OLLAMA_URL`, default `http://localhost:11434`). The HTTP client is imported
lazily so importing this module never touches the network.
"""

from __future__ import annotations

import os

from enigma_mcu.embeddings.port import Embedder


class BgeM3Embedder(Embedder):
    """Calls Ollama's embeddings endpoint with model `bge-m3`."""

    MODEL = "bge-m3"

    def __init__(self, url: str | None = None, model: str | None = None, timeout: float = 60.0):
        self._url = (url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self._model = model or self.MODEL
        self._timeout = timeout

    def embed(self, text: str) -> list[float]:
        import requests

        response = requests.post(
            f"{self._url}/api/embeddings",
            json={"model": self._model, "prompt": text},
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        vector = payload.get("embedding")
        if not vector:
            raise RuntimeError(f"Ollama returned no embedding for model {self._model!r}: {payload}")
        return [float(value) for value in vector]
