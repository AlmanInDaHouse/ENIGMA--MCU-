"""SPEC-004 unit harness — VaultReader routing (T1) and Cypher generation (T2).

No infrastructure: these must pass everywhere, including CI. They cover the
error-prone logic — which note routes where, and exactly what Cypher is built —
so the live wiring (integration tests) only has to confirm the plumbing.
"""

import pytest

from conftest import FIXTURES
from enigma_mcu.atom import Atom
from enigma_mcu.graph.mapper import ConceptStub, ProjectStub
from enigma_mcu.graph.neo4j_executor import (
    NODE_KEY_CONSTRAINT_CYPHER,
    VECTOR_INDEX_CYPHER,
    build_edge_cypher,
    build_node_cypher,
)
from enigma_mcu.graph.ops import EdgeOp, NodeOp
from enigma_mcu.graph.reader import VaultReader

SYNC_VAULT = FIXTURES / "sync_vault"


# --- T1: VaultReader routes by frontmatter type -----------------------------

def test_t1_vault_reader_routes_by_type():
    reader = VaultReader()
    contents = reader.read(SYNC_VAULT)

    assert {a.id for a in contents.atoms} == {"cyberguard-fact-0001", "enigma-mcu-idea-0001"}
    assert all(isinstance(a, Atom) for a in contents.atoms)

    assert [c.id for c in contents.concepts] == ["concept-mcp"]
    concept = contents.concepts[0]
    assert isinstance(concept, ConceptStub)
    assert concept.canonical == "MCP"
    assert concept.aliases == ["Model Context Protocol", "mcp server"]

    assert {p.id for p in contents.projects} == {"project-cyberguard", "project-enigma-mcu"}
    assert all(isinstance(p, ProjectStub) for p in contents.projects)

    # The unknown-type note is skipped with a warning, not routed and not crashed.
    assert len(reader.warnings) == 1
    assert "glossary" in reader.warnings[0].reason


# --- T2: Cypher generation (build, do not execute) --------------------------

def test_t2_node_cypher_is_additive_with_node_base_label():
    cypher, params = build_node_cypher(
        NodeOp("Item", "enigma-mcu-fact-0001", {"title": "T", "status": "current"})
    )
    assert cypher == "MERGE (n:Node {key: $key}) SET n:Item, n += $props"
    assert params == {
        "key": "enigma-mcu-fact-0001",
        "props": {"title": "T", "status": "current"},
    }


def test_t2_edge_cypher_resolves_endpoints_by_key():
    cypher, params = build_edge_cypher(EdgeOp("ABOUT", "enigma-mcu-fact-0001", "concept-mcp"))
    assert cypher == (
        "MATCH (a:Node {key: $from_key}), (b:Node {key: $to_key}) "
        "MERGE (a)-[r:ABOUT]->(b) SET r += $props"
    )
    assert params == {
        "from_key": "enigma-mcu-fact-0001",
        "to_key": "concept-mcp",
        "props": {},
    }


def test_t2_node_and_edge_reject_unsafe_label_or_type():
    # Labels and relationship types are interpolated, so they MUST be whitelisted.
    with pytest.raises(ValueError):
        build_node_cypher(NodeOp("Bad Label; DROP", "k", {}))
    with pytest.raises(ValueError):
        build_edge_cypher(EdgeOp("BAD-TYPE", "a", "b"))


def test_t2_vector_index_and_constraint_cypher():
    assert "VECTOR INDEX" in VECTOR_INDEX_CYPHER
    assert "IF NOT EXISTS" in VECTOR_INDEX_CYPHER
    assert ":Item" in VECTOR_INDEX_CYPHER
    assert "embedding" in VECTOR_INDEX_CYPHER
    assert "1024" in VECTOR_INDEX_CYPHER
    assert "cosine" in VECTOR_INDEX_CYPHER

    assert "CONSTRAINT" in NODE_KEY_CONSTRAINT_CYPHER
    assert "IF NOT EXISTS" in NODE_KEY_CONSTRAINT_CYPHER
    assert ":Node" in NODE_KEY_CONSTRAINT_CYPHER
    assert "key IS UNIQUE" in NODE_KEY_CONSTRAINT_CYPHER
