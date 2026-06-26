"""SPEC-005 unit harness — concept extraction port + normalization + report (T1-T5).

No API, no infrastructure: a `FakeConceptExtractor` and a `ScriptedEmbedder` give
full control over candidates and their pairwise cosine similarity, so the
normalization logic (the risky part — what merges, what stays distinct) is golden.
The pipeline persists NOTHING to the vault; T5 asserts the vault is untouched.
"""

import json

import pytest

from conftest import FIXTURES
from enigma_mcu.embeddings.port import Embedder
from enigma_mcu.extraction.llm_port import ConceptExtractor, FakeConceptExtractor
from enigma_mcu.extraction.normalize import (
    ConceptCandidate,
    ConceptNormalizer,
    NormalizationResult,
)
from enigma_mcu.extraction.pipeline import run_concept_extraction
from enigma_mcu.extraction.report import write_report

SYNC_VAULT = FIXTURES / "sync_vault"


class ScriptedEmbedder(Embedder):
    """Returns a fixed vector per exact text — lets a test engineer similarities."""

    def __init__(self, vectors: dict[str, list[float]]):
        self._vectors = vectors

    def embed(self, text: str) -> list[float]:
        return self._vectors[text]  # KeyError = the test forgot to script a vector


# Vectors engineered so the MCP family is mutually near-1.0 and Neo4j family is
# orthogonal to it; within-family cosines stay >= 0.97.
_VECTORS = {
    "MCP": [1.0, 0.0, 0.0],
    "mcp server": [0.99, 0.14, 0.0],
    "Model Context Protocol": [0.98, 0.20, 0.0],
    "Neo4j": [0.0, 1.0, 0.0],
    "graph database": [0.0, 0.99, 0.14],
}


# --- T1: FakeConceptExtractor is deterministic ------------------------------

def test_t1_fake_extractor_is_deterministic():
    fake = FakeConceptExtractor({"sample atom text": ["MCP", "vector index"]})

    assert fake.extract_concepts("sample atom text") == ["MCP", "vector index"]
    assert fake.extract_concepts("sample atom text") == ["MCP", "vector index"]

    # Unmapped text falls back to a deterministic, non-empty keyword extraction.
    a = fake.extract_concepts("The vault is the single source of truth for memory")
    b = fake.extract_concepts("The vault is the single source of truth for memory")
    assert a == b
    assert isinstance(a, list) and a


# --- T2: normalizer merges near-identical, keeps dissimilar separate --------

def test_t2_normalizer_merges_near_identical_golden():
    candidates = [
        ConceptCandidate("MCP", "a1", "cyberguard"),
        ConceptCandidate("MCP", "a2", "enigma-mcu"),
        ConceptCandidate("mcp server", "a1", "cyberguard"),
        ConceptCandidate("Model Context Protocol", "a3", "quetzy"),
        ConceptCandidate("Neo4j", "a3", "quetzy"),
        ConceptCandidate("graph database", "a2", "enigma-mcu"),
    ]
    result = ConceptNormalizer(ScriptedEmbedder(_VECTORS), threshold=0.9).normalize(candidates)

    assert isinstance(result, NormalizationResult)
    by_canonical = {c.canonical: c for c in result.concepts}
    assert set(by_canonical) == {"MCP", "Neo4j"}

    mcp = by_canonical["MCP"]
    assert mcp.aliases == ["Model Context Protocol", "mcp server"]
    assert set(mcp.members) == {"MCP", "mcp server", "Model Context Protocol"}
    assert mcp.confidence in {"high", "low"}

    neo = by_canonical["Neo4j"]
    assert neo.aliases == ["graph database"]


# --- T3: the threshold dial works -------------------------------------------

def test_t3_threshold_dial_changes_merging():
    candidates = [
        ConceptCandidate("MCP", "a1", "p"),
        ConceptCandidate("Model Context Protocol", "a2", "p"),
    ]
    # cosine(MCP, Model Context Protocol) ~ 0.98
    lenient = ConceptNormalizer(ScriptedEmbedder(_VECTORS), threshold=0.9).normalize(candidates)
    assert len(lenient.concepts) == 1  # merged

    strict = ConceptNormalizer(ScriptedEmbedder(_VECTORS), threshold=0.99).normalize(candidates)
    assert len(strict.concepts) == 2  # kept distinct


# --- T4: cross-project candidates normalize to the same concept -------------

def test_t4_cross_project_assignment_to_same_concept():
    candidates = [
        ConceptCandidate("MCP", "cg-1", "cyberguard"),
        ConceptCandidate("mcp server", "en-1", "enigma-mcu"),
    ]
    result = ConceptNormalizer(ScriptedEmbedder(_VECTORS), threshold=0.9).normalize(candidates)
    assert len(result.concepts) == 1
    canonical = result.concepts[0].canonical

    assigned = {(a.atom_id, a.project): a.concept for a in result.assignments}
    assert assigned[("cg-1", "cyberguard")] == canonical
    assert assigned[("en-1", "enigma-mcu")] == canonical
    assert all(a.confidence in {"high", "low"} for a in result.assignments)


# --- T5: dry-run report written outside the vault; vault untouched ----------

class _KeywordExtractor(ConceptExtractor):
    """Deterministic extractor keyed on substrings present in the fixture atoms."""

    def extract_concepts(self, text: str) -> list[str]:
        found = []
        if "MCP" in text:
            found.append("MCP")
        if "memory" in text.lower():
            found.append("contextual memory")
        return found


def test_t5_report_written_outside_vault_and_vault_untouched(tmp_path):
    vault_files_before = {p for p in SYNC_VAULT.rglob("*") if p.is_file()}

    embedder = ScriptedEmbedder(
        {"MCP": [1.0, 0.0], "contextual memory": [0.0, 1.0]}
    )
    report_dir = tmp_path / "reports"

    result, paths = run_concept_extraction(
        SYNC_VAULT,
        _KeywordExtractor(),
        embedder,
        threshold=0.9,
        report_dir=report_dir,
    )

    # Report exists, lives under report_dir (outside the vault).
    assert paths.markdown.exists() and paths.json.exists()
    assert report_dir in paths.markdown.parents
    assert str(SYNC_VAULT) not in str(paths.markdown.resolve())

    markdown = paths.markdown.read_text(encoding="utf-8")
    assert "MCP" in markdown
    assert "contextual memory" in markdown

    data = json.loads(paths.json.read_text(encoding="utf-8"))
    assert {c["canonical"] for c in data["concepts"]} == {"MCP", "contextual memory"}
    assert data["assignments"]
    assert all("confidence" in a for a in data["assignments"])
    # Both fixture atoms (different projects) appear in the assignments.
    assert {a["project"] for a in data["assignments"]} == {"cyberguard", "enigma-mcu"}

    # The vault is byte-for-byte untouched: no files added or removed.
    vault_files_after = {p for p in SYNC_VAULT.rglob("*") if p.is_file()}
    assert vault_files_after == vault_files_before


# --- write_report is callable directly with a result (unit-level) -----------

def test_t5_write_report_directly(tmp_path):
    result = ConceptNormalizer(ScriptedEmbedder(_VECTORS), threshold=0.9).normalize(
        [ConceptCandidate("MCP", "a1", "p"), ConceptCandidate("Neo4j", "a2", "p")]
    )
    paths = write_report(result, tmp_path / "out")
    assert paths.markdown.exists() and paths.json.exists()
    assert "MCP" in paths.markdown.read_text(encoding="utf-8")


# --- FR-2: missing OPENROUTER_API_KEY raises a clear configuration error -----
# (Unit-level: constructing the extractor without a key must fail fast, no API.)

def test_openrouter_missing_key_raises_configuration_error(monkeypatch):
    from enigma_mcu.extraction.openrouter import (
        ConfigurationError,
        OpenRouterConceptExtractor,
    )

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        OpenRouterConceptExtractor()
