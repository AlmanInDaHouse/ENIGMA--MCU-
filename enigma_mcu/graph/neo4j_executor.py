"""Neo4jExecutor — turn the SPEC-003 op IR into idempotent Cypher and run it.

Two layers, deliberately separated:

* **Pure builders** (`build_node_cypher`, `build_edge_cypher`, the schema Cypher
  constants) generate parameterized Cypher without a database — unit-testable and
  golden-comparable (T2).
* **The executor** runs those statements against a live Neo4j 5.x (T3–T5).

MERGE semantics give idempotency (FR-2/FR-3): a node MERGEs on a base `:Node`
label keyed by `key`, then adds its specific label and `SET n += $props`
(additive — a minimal edge-target stub never clobbers a full stub). Edges resolve
endpoints label-agnostically via `(:Node {key})`. Labels and relationship types
are interpolated (Cypher cannot parameterize them), so both are whitelisted
against an identifier pattern to prevent injection.

Connection config comes from the environment; NEO4J_URI defaults to ENIGMA's
dedicated bolt://localhost:7688 — never the machine-wide 7687.
"""

from __future__ import annotations

import os
import re

from enigma_mcu.graph.ops import EdgeOp, NodeOp

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

VECTOR_INDEX_NAME = "item_embedding"

# Native vector index on Item embeddings: 1024-dim, cosine (ADR-0007). Idempotent.
VECTOR_INDEX_CYPHER = (
    "CREATE VECTOR INDEX item_embedding IF NOT EXISTS "
    "FOR (n:Item) ON (n.embedding) "
    "OPTIONS {indexConfig: {`vector.dimensions`: 1024, "
    "`vector.similarity_function`: 'cosine'}}"
)

# One node per key: the base :Node label carries the uniqueness constraint.
NODE_KEY_CONSTRAINT_CYPHER = (
    "CREATE CONSTRAINT node_key_unique IF NOT EXISTS "
    "FOR (n:Node) REQUIRE n.key IS UNIQUE"
)


def _safe_identifier(value: str, kind: str) -> str:
    if not _IDENTIFIER.match(value):
        raise ValueError(f"unsafe {kind} for Cypher interpolation: {value!r}")
    return value


def build_node_cypher(op: NodeOp) -> tuple[str, dict]:
    """`NodeOp` → idempotent MERGE that adds the label and additively sets props."""
    label = _safe_identifier(op.label, "node label")
    cypher = f"MERGE (n:Node {{key: $key}}) SET n:{label}, n += $props"
    return cypher, {"key": op.key, "props": dict(op.properties)}


def build_edge_cypher(op: EdgeOp) -> tuple[str, dict]:
    """`EdgeOp` → MATCH endpoints by key, then idempotent MERGE of the typed rel."""
    rel_type = _safe_identifier(op.type, "relationship type")
    cypher = (
        "MATCH (a:Node {key: $from_key}), (b:Node {key: $to_key}) "
        f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props"
    )
    return cypher, {
        "from_key": op.from_key,
        "to_key": op.to_key,
        "props": dict(op.properties),
    }


class Neo4jExecutor:
    """Executes node/edge ops against a live Neo4j; lazy driver, env config."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ):
        self._uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7688")
        self._user = user or os.environ.get("NEO4J_USER", "neo4j")
        self._password = password or os.environ.get("NEO4J_PASSWORD", "enigmatest")
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
        return self._driver

    def run(self, cypher: str, params: dict | None = None) -> list[dict]:
        """Run one statement and return its records as dicts."""
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def ensure_schema(self) -> None:
        """Create the :Node key constraint and the Item vector index (idempotent)."""
        self.run(NODE_KEY_CONSTRAINT_CYPHER)
        self.run(VECTOR_INDEX_CYPHER)

    def execute(self, ops) -> None:
        """Execute all NodeOps first, then all EdgeOps (so endpoints exist)."""
        nodes = [op for op in ops if isinstance(op, NodeOp)]
        edges = [op for op in ops if isinstance(op, EdgeOp)]
        with self.driver.session() as session:
            for node in nodes:
                cypher, params = build_node_cypher(node)
                session.run(cypher, params)
            for edge in edges:
                cypher, params = build_edge_cypher(edge)
                session.run(cypher, params)

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
