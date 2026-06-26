"""SPEC-001 harness — VaultWriter + reader (T5–T7)."""

from conftest import FIXTURES, StubClock, make_atom
from enigma_mcu.vault import VaultWriter, read_atom


# The body of the golden fixture (tests/fixtures/expected_fact.md).
GOLDEN_BODY = (
    "The Markdown vault is the single source of truth. Every other store — "
    "graph, vector index, visual layer — is a derived, reconstructible "
    "projection of the vault."
)


def _golden_atom():
    return make_atom(
        id="enigma-mcu-fact-0001",
        type="fact",
        title="The Markdown vault is the single source of truth",
        project="enigma-mcu",
        status="current",
        confidence="high",
        concepts=["[[concept-contextual-memory]]"],
        body=GOLDEN_BODY,
    )


# --- T5: writer produces the expected file at the expected path -------------

def test_t5_writer_golden_file(tmp_path):
    writer = VaultWriter(tmp_path, clock=lambda: "2026-06-26")
    path = writer.write(_golden_atom())

    assert path == tmp_path / "enigma-mcu" / "enigma-mcu-fact-0001.md"

    expected = (FIXTURES / "expected_fact.md").read_text(encoding="utf-8")
    assert path.read_text(encoding="utf-8") == expected


# --- T6: idempotency --------------------------------------------------------

def test_t6_identical_rewrite_is_byte_identical_no_duplicate(tmp_path):
    clock = StubClock(["2026-06-26", "2026-06-27"])
    writer = VaultWriter(tmp_path, clock=clock)

    path = writer.write(make_atom(body="Original assertion."))
    first_bytes = path.read_bytes()

    again = writer.write(make_atom(body="Original assertion."))
    assert again == path
    assert again.read_bytes() == first_bytes  # unchanged, updated NOT bumped

    files = list((tmp_path / "enigma-mcu").glob("*.md"))
    assert files == [path]  # no duplicate


def test_t6_changed_body_updates_hash_and_updated_preserves_created(tmp_path):
    clock = StubClock(["2026-06-26", "2026-06-27"])
    writer = VaultWriter(tmp_path, clock=clock)

    original = make_atom(body="Original assertion.")
    path = writer.write(original)

    changed = make_atom(body="A materially different assertion.")
    path2 = writer.write(changed)

    assert path2 == path  # same id -> same path, update in place
    reloaded = read_atom(path2)
    assert reloaded.content_hash == changed.content_hash
    assert reloaded.content_hash != original.content_hash
    assert reloaded.created == "2026-06-26"  # preserved
    assert reloaded.updated == "2026-06-27"  # bumped


# --- T7: round-trip write -> read -> equal ----------------------------------

def test_t7_round_trip_preserves_all_fields(tmp_path):
    writer = VaultWriter(tmp_path, clock=lambda: "2026-06-26")
    atom = _golden_atom()
    path = writer.write(atom)

    loaded = read_atom(path)

    assert loaded.id == atom.id
    assert loaded.content_hash == atom.content_hash
    assert loaded.type == atom.type
    assert loaded.title == atom.title
    assert loaded.project == atom.project
    assert loaded.status == atom.status
    assert loaded.confidence == atom.confidence
    assert loaded.body == atom.body
    assert loaded.concepts == atom.concepts
    assert loaded.relates_to == atom.relates_to
    assert loaded.supersedes == atom.supersedes
    assert loaded.superseded_by == atom.superseded_by
    assert loaded.source == atom.source
    assert loaded.created == "2026-06-26"
    assert loaded.updated == "2026-06-26"
    assert loaded.tags == atom.tags
    assert loaded.artifact_ref == atom.artifact_ref
