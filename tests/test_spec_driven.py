"""SPEC-002 harness — SpecDrivenAdapter (T1–T6).

The adapter parses structured repo artifacts (ADR log + Constitution principles)
deterministically into `decision` atoms and feeds them to the SPEC-001
`VaultWriter`. No LLM, no concept extraction (`concepts == []`).
"""

import pytest

from conftest import FIXTURES, StubClock
from enigma_mcu.adapters.spec_driven import (
    ARTIFACT_ADR_LOG,
    ARTIFACT_CONSTITUTION,
    SpecDrivenAdapter,
)
from enigma_mcu.vault import VaultWriter, read_atom

ADR_LOG = FIXTURES / "adr_log_sample.md"
CONSTITUTION = FIXTURES / "constitution_sample.md"
MALFORMED = FIXTURES / "malformed_artifact.md"

REPO_CONSTITUTION = FIXTURES.parent.parent / "CONSTITUTION.md"


# An ADR entry template for the status-mapping cases (T3).
ADR_TEMPLATE = """## ADR-0042 — A representative decision

**Status:** {status}

**Context:** Some context.

**Decision:** The chosen approach is to do the representative thing.

**Consequences:** Some consequences.
"""


def _adapter():
    return SpecDrivenAdapter(
        project="enigma-mcu",
        author="manuel",
        extracted_at="2026-06-26T10:00:00Z",
    )


# --- T1: a single ADR parses to the expected decision atom (golden) ---------

def test_t1_adr_parses_to_expected_decision_atom():
    atoms = _adapter().parse_file(ADR_LOG, ARTIFACT_ADR_LOG, source_ref="docs/ADR-LOG.md")
    by_id = {a.id: a for a in atoms}

    atom = by_id["enigma-mcu-adr-0001"]
    assert atom.type == "decision"
    assert atom.title == "Storage architecture: vault is truth, graph is index"
    assert atom.body == (
        "The markdown vault is the single source of truth; Neo4j is a derived, "
        "fully rebuildable graph and vector index."
    )
    assert atom.status == "accepted"
    assert atom.concepts == []
    assert atom.source.kind == "repo-artifact"
    assert atom.source.ref == "docs/ADR-LOG.md#ADR-0001"
    assert atom.source.author == "manuel"


# --- T2: Constitution principles parse to the expected atoms ----------------

def test_t2_constitution_principles_parse_to_atoms():
    atoms = _adapter().parse_file(
        CONSTITUTION, ARTIFACT_CONSTITUTION, source_ref="CONSTITUTION.md"
    )
    by_id = {a.id: a for a in atoms}

    assert set(by_id) == {
        "enigma-mcu-principle-1",
        "enigma-mcu-principle-2",
        "enigma-mcu-principle-3",
    }
    for atom in atoms:
        assert atom.type == "decision"
        assert atom.status == "accepted"
        assert atom.concepts == []

    p1 = by_id["enigma-mcu-principle-1"]
    assert p1.title == "The vault is the source of truth."
    assert p1.body == (
        "The vault is the source of truth.\n\n"
        "Every other store is a derived projection of the vault."
    )


# --- T3: ADR status mapping (parametrized) + unknown status skipped ---------

@pytest.mark.parametrize(
    "adr_status, atom_status",
    [
        ("Accepted", "accepted"),
        ("Proposed", "proposed"),
        ("Superseded", "superseded"),
        ("Deprecated", "deprecated"),
    ],
)
def test_t3_adr_status_mapping(adr_status, atom_status):
    adapter = _adapter()
    atoms = adapter.parse_adr_text(
        ADR_TEMPLATE.format(status=adr_status), source_ref="x"
    )
    assert len(atoms) == 1
    assert atoms[0].status == atom_status
    assert adapter.warnings == []


def test_t3_unknown_status_is_skipped_with_warning():
    adapter = _adapter()
    atoms = adapter.parse_adr_text(
        ADR_TEMPLATE.format(status="Bogus"), source_ref="docs/ADR-LOG.md"
    )
    assert atoms == []
    assert len(adapter.warnings) == 1
    warning = adapter.warnings[0]
    assert "ADR-0042" in warning.ref
    assert "Bogus" in warning.reason


# --- T4: end-to-end idempotency through VaultWriter -------------------------

def test_t4_end_to_end_idempotent(tmp_path):
    clock = StubClock(["2026-06-26", "2026-06-27"])
    writer = VaultWriter(tmp_path, clock=clock)

    atoms = _adapter().parse_file(ADR_LOG, ARTIFACT_ADR_LOG, source_ref="docs/ADR-LOG.md")
    paths_first = [writer.write(a) for a in atoms]
    bytes_first = {p: p.read_bytes() for p in paths_first}

    # Re-run over unchanged artifacts -> byte-identical, no duplicates.
    atoms_again = _adapter().parse_file(ADR_LOG, ARTIFACT_ADR_LOG, source_ref="docs/ADR-LOG.md")
    paths_again = [writer.write(a) for a in atoms_again]
    assert paths_again == paths_first
    for p in paths_again:
        assert p.read_bytes() == bytes_first[p]
    files = sorted((tmp_path / "enigma-mcu").glob("*.md"))
    assert len(files) == len(paths_first)  # no duplicates

    # Edit the Decision body of ADR-0001 -> in-place update.
    edited_text = ADR_LOG.read_text(encoding="utf-8").replace(
        "The markdown vault is the single source of truth; Neo4j is a derived, "
        "fully rebuildable graph and vector index.",
        "The vault is canonical; the graph is a disposable, rebuildable projection.",
    )
    edited_atoms = _adapter().parse_adr_text(edited_text, source_ref="docs/ADR-LOG.md")
    edited_first = next(a for a in edited_atoms if a.id == "enigma-mcu-adr-0001")
    path = writer.write(edited_first)

    reloaded = read_atom(path)
    assert reloaded.id == "enigma-mcu-adr-0001"
    assert reloaded.created == "2026-06-26"  # preserved
    assert reloaded.updated == "2026-06-27"  # bumped
    assert reloaded.content_hash == edited_first.content_hash


# --- T5: a malformed artifact is skipped; valid ones still written ----------

def test_t5_malformed_artifact_skipped(tmp_path):
    writer = VaultWriter(tmp_path, clock=lambda: "2026-06-26")
    adapter = _adapter()

    atoms = adapter.parse(
        [
            (ADR_LOG, ARTIFACT_ADR_LOG),
            (MALFORMED, ARTIFACT_ADR_LOG),
        ]
    )
    # Valid ADR atoms still produced.
    assert {a.id for a in atoms} == {"enigma-mcu-adr-0001", "enigma-mcu-adr-0002"}
    # Malformed file recorded a structured warning.
    assert any(str(MALFORMED) in w.ref or "malformed" in w.ref for w in adapter.warnings)
    assert len(adapter.warnings) >= 1

    # Valid atoms are writable.
    written = [writer.write(a) for a in atoms]
    assert len(written) == 2


# --- T6: dogfood over the repo's own CONSTITUTION.md ------------------------

def test_t6_dogfood_constitution_yields_12_principles():
    atoms = _adapter().parse_file(
        REPO_CONSTITUTION, ARTIFACT_CONSTITUTION, source_ref="CONSTITUTION.md"
    )
    ids = {a.id for a in atoms}
    expected = {f"enigma-mcu-principle-{n}" for n in range(1, 13)}
    assert ids == expected
    assert len(atoms) == 12
