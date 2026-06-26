"""SPEC-001 harness — Atom model (T1–T4)."""

import pytest

from conftest import make_atom, make_source
from enigma_mcu.atom import AtomValidationError, hashed_id


# --- T1: a valid atom of each of the four types constructs and validates ----

@pytest.mark.parametrize(
    "atom_type, status",
    [
        ("decision", "accepted"),
        ("fact", "current"),
        ("idea", "raw"),
        ("open_question", "open"),
    ],
)
def test_t1_valid_atom_of_each_type_constructs(atom_type, status):
    atom = make_atom(type=atom_type, status=status)
    assert atom.type == atom_type
    assert atom.status == status
    # validation is part of construction and must not have raised
    atom.validate()
    # content_hash is derived on construction
    assert atom.content_hash
    assert len(atom.content_hash) == 64  # sha256 hex digest


# --- T2: invalid atoms are rejected ----------------------------------------

@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"type": "rumor"}, id="unknown-type"),
        pytest.param({"type": "fact", "status": "accepted"}, id="status-not-in-vocab"),
        pytest.param({"type": "idea", "status": "current"}, id="status-cross-vocab"),
        pytest.param({"source": make_source(kind="")}, id="missing-source-kind"),
        pytest.param({"source": make_source(ref="")}, id="missing-source-ref"),
        pytest.param({"source": make_source(author="")}, id="missing-source-author"),
        pytest.param({"body": "   \n  "}, id="empty-body"),
        pytest.param({"title": ""}, id="empty-title"),
        pytest.param({"confidence": "medium"}, id="bad-confidence"),
    ],
)
def test_t2_invalid_atoms_are_rejected(overrides):
    with pytest.raises(AtomValidationError):
        make_atom(**overrides)


# --- T3: content_hash is stable under whitespace, sensitive to content ------

def test_t3_content_hash_ignores_whitespace_variants():
    canonical = make_atom(body="Memory lives in the vault.")
    outer_ws = make_atom(body="\n   Memory lives in the vault.   \n\n")
    assert canonical.content_hash == outer_ws.content_hash

    trailing = make_atom(body="line one   \nline two")
    clean = make_atom(body="line one\nline two")
    assert trailing.content_hash == clean.content_hash

    crlf = make_atom(body="line one\r\nline two")
    assert crlf.content_hash == clean.content_hash


def test_t3_content_hash_changes_on_real_edit():
    a = make_atom(body="Memory lives in the vault.")
    b = make_atom(body="Memory lives in Neo4j.")
    assert a.content_hash != b.content_hash


# --- T4: hashed-ID helper is deterministic and collision-distinct -----------

def test_t4_hashed_id_is_deterministic():
    id1 = hashed_id("idea", "Expose memory as MCP.", "ideas-chat/msg-1042")
    id2 = hashed_id("idea", "Expose memory as MCP.", "ideas-chat/msg-1042")
    assert id1 == id2
    assert id1.startswith("idea-")


def test_t4_hashed_id_normalizes_body():
    base = hashed_id("idea", "Expose memory as MCP.", "ideas-chat/msg-1042")
    ws_variant = hashed_id("idea", "  Expose memory as MCP.  ", "ideas-chat/msg-1042")
    assert base == ws_variant


def test_t4_hashed_id_distinct_for_distinct_body_or_ref():
    base = hashed_id("idea", "Expose memory as MCP.", "ideas-chat/msg-1042")
    other_body = hashed_id("idea", "Expose memory as a graph.", "ideas-chat/msg-1042")
    other_ref = hashed_id("idea", "Expose memory as MCP.", "ideas-chat/msg-9999")
    assert len({base, other_body, other_ref}) == 3
