"""SPEC-005 integration harness — real OpenRouter extractor (T6-T7).

Marked `integration` and skip-gated on OPENROUTER_API_KEY (and bge-m3 for the
end-to-end). Kept deliberately MINIMAL — these cost API tokens. Live-module imports
are deferred into the test bodies so the file collects cleanly before the
implementation exists and skips when the key is absent.
"""

import pytest

from conftest import FIXTURES, ollama_model_available, openrouter_available

pytestmark = pytest.mark.integration

requires_openrouter = pytest.mark.skipif(
    not openrouter_available(), reason="OPENROUTER_API_KEY not set"
)
requires_bge_m3 = pytest.mark.skipif(
    not ollama_model_available(), reason="Ollama bge-m3 model not available"
)

SYNC_VAULT = FIXTURES / "sync_vault"


# --- T6: the real OpenRouter extractor returns a sane concept list ----------

@requires_openrouter
def test_t6_openrouter_returns_nonempty_concepts():
    from enigma_mcu.extraction.openrouter import OpenRouterConceptExtractor

    concepts = OpenRouterConceptExtractor().extract_concepts(
        "ENIGMA-MCU exposes its contextual memory as an MCP server backed by a "
        "Neo4j graph and bge-m3 embeddings."
    )
    assert isinstance(concepts, list)
    assert concepts  # non-empty
    assert all(isinstance(c, str) and c.strip() for c in concepts)


# --- T7: end-to-end over the (tiny) fixture vault, real model + real bge-m3 --

@requires_openrouter
@requires_bge_m3
def test_t7_end_to_end_real_models(tmp_path):
    from enigma_mcu.embeddings.bge_m3 import BgeM3Embedder
    from enigma_mcu.extraction.openrouter import OpenRouterConceptExtractor
    from enigma_mcu.extraction.pipeline import run_concept_extraction

    result, paths = run_concept_extraction(
        SYNC_VAULT,
        OpenRouterConceptExtractor(),
        BgeM3Embedder(),
        report_dir=tmp_path / "reports",
    )
    assert paths.markdown.exists() and paths.json.exists()
    assert len(result.concepts) >= 1
