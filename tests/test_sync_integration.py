"""SPEC-004 integration harness — live Neo4j + real bge-m3 (T3–T7).

Every test here is marked `integration` and skip-gated: when ENIGMA's Neo4j
(NEO4J_URI, default bolt://localhost:7688) or Ollama's bge-m3 is unreachable, the
test SKIPS — it never fails, and it never touches any other Neo4j on this machine.
Module-level imports of the live modules are deferred into the test bodies so the
file collects cleanly even before the implementation exists.
"""

import pytest

from conftest import (
    FIXTURES,
    neo4j_available,
    ollama_model_available,
)

pytestmark = pytest.mark.integration

requires_neo4j = pytest.mark.skipif(
    not neo4j_available(), reason="ENIGMA Neo4j (NEO4J_URI, default :7688) not reachable"
)
requires_bge_m3 = pytest.mark.skipif(
    not ollama_model_available(), reason="Ollama bge-m3 model not available"
)

SYNC_VAULT = FIXTURES / "sync_vault"


def _fresh_executor():
    """A Neo4jExecutor pointed at ENIGMA's dedicated DB, wiped clean.

    Wiping is safe ONLY because NEO4J_URI is the dedicated test instance (:7688);
    the probe guarantees we are not connected to any other project's Neo4j.
    """
    from enigma_mcu.graph.neo4j_executor import Neo4jExecutor

    executor = Neo4jExecutor()
    executor.run("MATCH (n) DETACH DELETE n")
    return executor


def _map_fixture(embedder):
    from enigma_mcu.graph.mapper import GraphMapper
    from enigma_mcu.graph.reader import VaultReader

    contents = VaultReader().read(SYNC_VAULT)
    return GraphMapper(embedder).map_vault(
        contents.atoms, concepts=contents.concepts, projects=contents.projects
    )


# --- T3: sync builds the cross-project join ---------------------------------

@requires_neo4j
def test_t3_sync_creates_cross_project_join():
    from enigma_mcu.embeddings.port import FakeEmbedder

    executor = _fresh_executor()
    try:
        executor.ensure_schema()
        executor.execute(_map_fixture(FakeEmbedder()))

        item_keys = {r["key"] for r in executor.run("MATCH (i:Item) RETURN i.key AS key")}
        assert {"cyberguard-fact-0001", "enigma-mcu-idea-0001"} <= item_keys

        about = {
            r["key"]
            for r in executor.run(
                "MATCH (i:Item)-[:ABOUT]->(c:Concept {key: 'concept-mcp'}) RETURN i.key AS key"
            )
        }
        assert about == {"cyberguard-fact-0001", "enigma-mcu-idea-0001"}

        belongs = executor.run("MATCH (:Item)-[:BELONGS_TO]->(:Project) RETURN count(*) AS c")
        authored = executor.run("MATCH (:Item)-[:AUTHORED_BY]->(:Person) RETURN count(*) AS c")
        assert belongs[0]["c"] >= 2
        assert authored[0]["c"] >= 2
    finally:
        executor.close()


# --- T4: idempotent re-sync, in-place update --------------------------------

@requires_neo4j
def test_t4_idempotent_resync_and_update():
    from enigma_mcu.embeddings.port import FakeEmbedder

    executor = _fresh_executor()
    try:
        executor.ensure_schema()
        ops = _map_fixture(FakeEmbedder())
        executor.execute(ops)

        def counts():
            n = executor.run("MATCH (n) RETURN count(n) AS c")[0]["c"]
            r = executor.run("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
            return n, r

        first = counts()
        executor.execute(ops)  # re-run identical ops
        assert counts() == first  # no duplicates

        # Change one Item's title property and re-sync that node.
        from enigma_mcu.graph.ops import NodeOp

        executor.execute([NodeOp("Item", "cyberguard-fact-0001", {"title": "Edited title"})])
        assert counts() == first  # still no new nodes/rels
        title = executor.run(
            "MATCH (i:Item {key: 'cyberguard-fact-0001'}) RETURN i.title AS t"
        )[0]["t"]
        assert title == "Edited title"
    finally:
        executor.close()


# --- T5: vector index exists and answers a nearest-neighbour query ----------

@requires_neo4j
def test_t5_vector_index_query_returns_expected_item():
    from enigma_mcu.embeddings.port import FakeEmbedder

    embedder = FakeEmbedder()
    executor = _fresh_executor()
    try:
        executor.ensure_schema()
        executor.execute(_map_fixture(embedder))

        # Query with the exact embedding of one Item's title+body -> itself is nearest.
        query_vec = embedder.embed(
            "Expose ENIGMA-MCU as an MCP server\n\n"
            "Memory is exposed as an MCP server so the local agent and Quetzy can query it."
        )
        rows = executor.run(
            "CALL db.index.vector.queryNodes('item_embedding', 1, $vec) "
            "YIELD node RETURN node.key AS key",
            {"vec": query_vec},
        )
        assert rows[0]["key"] == "enigma-mcu-idea-0001"
    finally:
        executor.close()


# --- T6: the real bge-m3 embedder returns 1024 floats -----------------------

@requires_bge_m3
def test_t6_bge_m3_returns_1024_floats():
    from enigma_mcu.embeddings.bge_m3 import BgeM3Embedder

    vector = BgeM3Embedder().embed("the Markdown vault is the single source of truth")
    assert len(vector) == 1024
    assert all(isinstance(x, float) for x in vector)


# --- T7: end-to-end SyncService with real embedder + real Neo4j -------------

@requires_neo4j
@requires_bge_m3
def test_t7_end_to_end_sync_and_vector_search():
    from enigma_mcu.embeddings.bge_m3 import BgeM3Embedder
    from enigma_mcu.sync import SyncService

    executor = _fresh_executor()
    try:
        embedder = BgeM3Embedder()
        SyncService(embedder=embedder, executor=executor).sync(SYNC_VAULT)

        query_vec = embedder.embed("how does the system expose its memory to agents")
        rows = executor.run(
            "CALL db.index.vector.queryNodes('item_embedding', 2, $vec) "
            "YIELD node RETURN node.key AS key",
            {"vec": query_vec},
        )
        assert len(rows) >= 1
        assert all(r["key"] for r in rows)
    finally:
        executor.close()
