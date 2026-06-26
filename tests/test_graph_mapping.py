"""SPEC-003 harness — graph mapping IR, GraphMapper, and the Embedder port (T1–T7).

Pure and infrastructure-free: no Neo4j, no Ollama, no network. The mapper turns
atoms and stub notes into a deterministic list of NodeOp/EdgeOp upserts and
attaches a 1024-dim embedding from an injected `Embedder`.
"""

import pytest

from conftest import FIXTURES, make_atom, make_source
from enigma_mcu.embeddings.port import EMBEDDING_DIM, Embedder, FakeEmbedder
from enigma_mcu.graph.mapper import (
    ConceptStub,
    GraphMapper,
    ProjectStub,
    parse_wikilink,
    parse_wikilinks,
)
from enigma_mcu.graph.ops import EdgeOp, NodeOp
from enigma_mcu.vault import read_atom

VAULT = FIXTURES / "vault"


def _mapper():
    return GraphMapper(FakeEmbedder())


def _item_node(ops):
    return next(o for o in ops if isinstance(o, NodeOp) and o.label == "Item")


def _props_without_embedding(node):
    props = dict(node.properties)
    props.pop("embedding", None)
    return props


# --- T1: an Item atom maps to the expected Item NodeOp (golden) -------------

def test_t1_item_atom_maps_to_item_node():
    atom = make_atom(
        id="enigma-mcu-fact-0001",
        type="fact",
        title="The vault is the source of truth",
        project="enigma-mcu",
        status="current",
        confidence="high",
        body="The Markdown vault is canonical; everything else is derived.",
        concepts=[],
        created="2026-06-26",
        updated="2026-06-26",
        source=make_source(kind="repo-artifact", ref="docs/x.md", author="manuel"),
    )
    ops = _mapper().map_atom(atom)
    item = _item_node(ops)

    assert item.key == "enigma-mcu-fact-0001"
    assert _props_without_embedding(item) == {
        "id": "enigma-mcu-fact-0001",
        "type": "fact",
        "title": "The vault is the source of truth",
        "body": "The Markdown vault is canonical; everything else is derived.",
        "status": "current",
        "confidence": "high",
        "project": "enigma-mcu",
        "source_kind": "repo-artifact",
        "source_ref": "docs/x.md",
        "source_author": "manuel",
        "content_hash": atom.content_hash,
        "created": "2026-06-26",
        "updated": "2026-06-26",
    }
    assert len(item.properties["embedding"]) == EMBEDDING_DIM


# --- T2: each relationship key maps to the right EdgeOp(s) + stub NodeOps ---

ITEM = "enigma-mcu-fact-0001"
PROJECT = "enigma-mcu"


@pytest.mark.parametrize(
    "overrides, expected_edges, expected_nodes",
    [
        pytest.param(
            {},
            [EdgeOp("BELONGS_TO", ITEM, "project-enigma-mcu")],
            [NodeOp("Project", "project-enigma-mcu")],
            id="project",
        ),
        pytest.param(
            {"concepts": ["[[concept-mcp]]"]},
            [EdgeOp("ABOUT", ITEM, "concept-mcp")],
            [NodeOp("Concept", "concept-mcp")],
            id="concepts",
        ),
        pytest.param(
            {"relates_to": ["[[enigma-mcu-fact-0002]]"]},
            [EdgeOp("RELATES_TO", ITEM, "enigma-mcu-fact-0002")],
            [],
            id="relates_to",
        ),
        pytest.param(
            {"supersedes": ["[[enigma-mcu-fact-0000]]"]},
            [EdgeOp("SUPERSEDES", ITEM, "enigma-mcu-fact-0000")],
            [],
            id="supersedes",
        ),
        pytest.param(
            {"superseded_by": ["[[enigma-mcu-fact-0009]]"]},
            [EdgeOp("SUPERSEDES", "enigma-mcu-fact-0009", ITEM)],
            [],
            id="superseded_by-reverse",
        ),
        pytest.param(
            {},
            [EdgeOp("AUTHORED_BY", ITEM, "person-manuel")],
            [NodeOp("Person", "person-manuel")],
            id="source_author",
        ),
    ],
)
def test_t2_relationship_edges(overrides, expected_edges, expected_nodes):
    atom = make_atom(
        id=ITEM, project=PROJECT, source=make_source(author="manuel"), **overrides
    )
    ops = _mapper().map_atom(atom)
    for edge in expected_edges:
        assert edge in ops
    for node in expected_nodes:
        assert node in ops


# --- T3: wikilink parsing ---------------------------------------------------

def test_t3_wikilink_parsing():
    assert parse_wikilink("[[concept-mcp]]") == "concept-mcp"
    assert parse_wikilink("concept-mcp") == "concept-mcp"  # already bare
    assert parse_wikilink("[[id|Display Name]]") == "id"  # alias form
    assert parse_wikilinks(["[[a]]", "[[b]]"]) == ["a", "b"]
    assert parse_wikilinks([]) == []
    assert parse_wikilinks(["[[a]]", "", None]) == ["a"]  # skips empties


# --- T4: Concept and Project stubs map to their NodeOps ---------------------

def test_t4_concept_and_project_stubs():
    mapper = _mapper()

    concept = mapper.map_concept(
        ConceptStub(id="concept-mcp", canonical="MCP", aliases=["Model Context Protocol", "mcp server"])
    )
    assert concept == NodeOp(
        "Concept",
        "concept-mcp",
        {"canonical": "MCP", "aliases": ["Model Context Protocol", "mcp server"]},
    )

    project = mapper.map_project(
        ProjectStub(id="project-enigma-mcu", name="ENIGMA-MCU", status="active", stack=["python"])
    )
    assert project == NodeOp(
        "Project",
        "project-enigma-mcu",
        {"name": "ENIGMA-MCU", "status": "active", "stack": ["python"]},
    )


# --- T5: FakeEmbedder is 1024-dim and deterministic -------------------------

def test_t5_fake_embedder_dim_and_determinism():
    embedder = FakeEmbedder()
    assert isinstance(embedder, Embedder)

    v1 = embedder.embed("the vault is the source of truth")
    v2 = embedder.embed("the vault is the source of truth")
    v3 = embedder.embed("a different assertion entirely")

    assert len(v1) == EMBEDDING_DIM
    assert all(isinstance(x, float) for x in v1)
    assert v1 == v2  # deterministic
    assert v1 != v3  # distinct text -> distinct vector


# --- T6: multi-project vault fixture -> expected op set (cross-project join) -

def _load_fixture_vault():
    a = read_atom(VAULT / "cyberguard" / "cyberguard-fact-0001.md")
    b = read_atom(VAULT / "enigma-mcu" / "enigma-mcu-idea-0001.md")
    concepts = [ConceptStub("concept-mcp", "MCP", ["Model Context Protocol"])]
    projects = [
        ProjectStub("project-cyberguard", "CyberGuard", "active", ["rust"]),
        ProjectStub("project-enigma-mcu", "ENIGMA-MCU", "active", ["python"]),
    ]
    return a, b, concepts, projects


def test_t6_multi_project_vault_golden():
    a, b, concepts, projects = _load_fixture_vault()
    ops = _mapper().map_vault([a, b], concepts=concepts, projects=projects)

    node_keys = {(o.label, o.key) for o in ops if isinstance(o, NodeOp)}
    assert node_keys == {
        ("Item", "cyberguard-fact-0001"),
        ("Item", "enigma-mcu-idea-0001"),
        ("Concept", "concept-mcp"),
        ("Project", "project-cyberguard"),
        ("Project", "project-enigma-mcu"),
        ("Person", "person-manuel"),
    }

    edges = {(o.type, o.from_key, o.to_key) for o in ops if isinstance(o, EdgeOp)}
    assert edges == {
        ("BELONGS_TO", "cyberguard-fact-0001", "project-cyberguard"),
        ("BELONGS_TO", "enigma-mcu-idea-0001", "project-enigma-mcu"),
        ("ABOUT", "cyberguard-fact-0001", "concept-mcp"),
        ("ABOUT", "enigma-mcu-idea-0001", "concept-mcp"),
        ("AUTHORED_BY", "cyberguard-fact-0001", "person-manuel"),
        ("AUTHORED_BY", "enigma-mcu-idea-0001", "person-manuel"),
    }

    # The cross-project join: both Items point ABOUT the same Concept node.
    about = {(o.from_key, o.to_key) for o in ops if isinstance(o, EdgeOp) and o.type == "ABOUT"}
    assert about == {
        ("cyberguard-fact-0001", "concept-mcp"),
        ("enigma-mcu-idea-0001", "concept-mcp"),
    }

    items = [o for o in ops if isinstance(o, NodeOp) and o.label == "Item"]
    assert len(items) == 2
    for item in items:
        assert len(item.properties["embedding"]) == EMBEDDING_DIM


# --- T7: mapping is pure and deterministic ----------------------------------

def test_t7_mapping_is_deterministic():
    a, b, concepts, projects = _load_fixture_vault()
    ops1 = _mapper().map_vault([a, b], concepts=concepts, projects=projects)
    ops2 = _mapper().map_vault([a, b], concepts=concepts, projects=projects)
    assert ops1 == ops2
