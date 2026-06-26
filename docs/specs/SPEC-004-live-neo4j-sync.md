# SPEC-004 — Live Neo4j Sync

| | |
|---|---|
| **ID** | SPEC-004 |
| **Phase** | 2 — Graph index |
| **Status** | Active |
| **Depends on** | CONSTITUTION, SPEC-atom-schema, SPEC-001, SPEC-003 |
| **Session** | SESSION-004 |

## Context

The live I/O half of Phase 2. It executes the SPEC-003 op IR against a real
Neo4j 5.x via idempotent `MERGE`, creates the native vector index, provides the
real bge-m3 embedder via Ollama, and wires the end-to-end sync. The risky *logic*
(Cypher generation, routing) is unit-tested infra-free; the wiring is verified by
**integration tests gated to never red `main` when services are absent**.

This loop **needs infrastructure**: Docker Neo4j 5.x and Ollama with `bge-m3`.

## Scope — in

- **VaultReader** (`enigma_mcu/graph/reader.py`, additive — imports `read_atom`,
  does not modify `vault.py`): enumerate vault `.md` files and route by frontmatter
  `type` → `Atom` (atom types) / `ConceptStub` / `ProjectStub`; warn on unknown.
- **Neo4jExecutor** (`enigma_mcu/graph/neo4j_executor.py`): execute `NodeOp`s and
  `EdgeOp`s idempotently via the official `neo4j` driver. Config from env
  (`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`).
  - Nodes execute **before** edges.
  - Node: `MERGE (n:Label {key:$key}) SET n += $props`. **Additive `+=`, never
    `=`** — so minimal edge-target stubs never clobber full-stub properties.
  - Every node also carries a base `:Node` label with a uniqueness constraint on
    `:Node(key)`; edges resolve endpoints label-agnostically via `(:Node {key})`.
  - Edge: `MATCH (a:Node {key:$from}), (b:Node {key:$to}) MERGE (a)-[r:TYPE]->(b)
    SET r += $props`.
- **Vector index**: `CREATE VECTOR INDEX ... IF NOT EXISTS` on `:Item(embedding)`,
  1024 dimensions, cosine. Idempotent.
- **BgeM3Embedder** (`enigma_mcu/embeddings/bge_m3.py`): implements the `Embedder`
  port by calling Ollama's embeddings endpoint with model `bge-m3`; returns a
  1024-float vector. Config from env (`OLLAMA_URL`, default `http://localhost:11434`).
- **SyncService** (`enigma_mcu/sync.py`): VaultReader → `GraphMapper(embedder)` →
  Neo4jExecutor. One entry point to sync a vault into Neo4j. Idempotent re-sync.
- **`docker-compose.yml`**: a Neo4j 5.x service (auth via env, ports 7474/7687, a
  named volume) sufficient to run the integration tests locally.

## Scope — out (non-goals)

Concept extraction/normalization (SPEC-005) · MOC generation (SPEC-008) · MCP
server (SPEC-006) · conversation adapter (SPEC-007) · backfill/continuous
orchestration and real-timestamp injection (SPEC-009) · modifying `atom.py`,
`vault.py`, `mapper.py`, `ops.py`, `port.py`, or the adapter.

## Functional requirements

- **FR-1** VaultReader routes by `type`: atom types → `Atom`; `concept` →
  `ConceptStub`; `project` → `ProjectStub`; unknown → skipped with a warning.
- **FR-2** Node execution uses `MERGE (n:Label {key}) SET n += props` (additive),
  plus the `:Node` base label and its uniqueness constraint.
- **FR-3** Edge execution runs after all nodes, resolving endpoints via
  `(:Node {key})`, `MERGE`-ing the typed relationship with additive property set.
- **FR-4** The vector index on `:Item(embedding)` is created idempotently with
  1024 dims and cosine similarity.
- **FR-5** BgeM3Embedder returns exactly 1024 floats from the real model.
- **FR-6** SyncService is idempotent: a second sync over an unchanged vault leaves
  node and relationship counts unchanged (no duplicates); a changed property is
  updated in place.
- **FR-7** Integration tests skip (do not fail) when Neo4j or Ollama is unreachable.

## Harness contract (write these RED first — they ARE the definition of done)

**Unit (no infrastructure — must pass everywhere, including CI):**

- **T1** VaultReader routing: a fixture vault with atom notes + a concept stub + a
  project stub + an unknown-type note → the expected routed objects; unknown warned.
- **T2** Cypher generation: `NodeOp`/`EdgeOp` → the expected parameterized Cypher
  strings and params (build, do not execute). Asserts additive `SET +=`, the
  `:Node` base label, and the endpoint-by-key edge pattern. Golden.

**Integration (`@pytest.mark.integration`, skip-if-unavailable):**

- **T3** Sync a synthetic fixture vault (two Items in different projects sharing a
  concept, plus the concept + project stubs) → read back via Cypher: both Items
  exist, both have an `ABOUT` edge to the **same** `Concept` node (the cross-project
  join), `BELONGS_TO` and `AUTHORED_BY` present.
- **T4** Idempotency: sync the fixture twice → identical node and relationship
  counts; change one atom's body/property and re-sync → node updated, no duplicate.
- **T5** Vector index exists with 1024 dims + cosine; a `db.index.vector.queryNodes`
  call returns the expected nearest `Item`.
- **T6** BgeM3Embedder returns 1024 floats for a sample text (real bge-m3).
- **T7** End-to-end: SyncService with the real embedder + real Neo4j syncs the
  fixture; a vector search returns a sensible `Item`.

## Dependencies

Python 3.12+, `pytest`, the `neo4j` driver, an HTTP client (`httpx` or `requests`)
for Ollama, the SPEC-001/003 modules. Integration requires Docker Neo4j 5.x and
Ollama with `bge-m3` pulled.

## Definition of Done

T1–T2 GREEN everywhere; T3–T7 GREEN locally with services up (skipped, not red,
where absent); `docker-compose.yml` present; prior suites still GREEN; `main` not
red under `pytest -m "not integration"`.

## Note on session size

This loop is larger than its predecessors. If context degradation appears before
all milestones land, stop at the last GREEN milestone, emit the Session Report,
and the architect will dispatch a continuation. Suggested milestone order: unit
(T1–T2) → executor + index against Neo4j (T3–T5) → real embedder + end-to-end
(T6–T7). Do not push through degradation.
