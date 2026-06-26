# SPEC-003 — Graph Mapping & Embedder Port

| | |
|---|---|
| **ID** | SPEC-003 |
| **Phase** | 2 — Graph index |
| **Status** | Active |
| **Depends on** | CONSTITUTION, SPEC-atom-schema, SPEC-001 |
| **Session** | SESSION-003 |

## Context

The translation layer from vault to graph — **pure and infrastructure-free**. It
turns atoms and stub notes into a deterministic intermediate representation (IR)
of graph operations (nodes + typed edges), and defines the **embedder port** that
later supplies vectors. No Neo4j and no Ollama here: the actual execution against
the database and the real bge-m3 model are SPEC-004. This split keeps the
error-prone *logic* (which edge type, which properties, which target) fully
unit-testable and golden-comparable, and lets the database and model be stood up
in parallel rather than blocking this loop.

This loop requires **no new infrastructure** — it runs immediately.

## Scope — in

- **IR** (`enigma_mcu/graph/ops.py`): `NodeOp(label, key, properties)` and
  `EdgeOp(type, from_key, to_key, properties)` value types. They describe upserts
  (MERGE-by-key semantics) without executing anything.
- **`GraphMapper`** (`enigma_mcu/graph/mapper.py`): atom + stubs → list of ops.
  - An **`Item`** atom → one `NodeOp(label="Item", key=id, ...)` carrying:
    `id, type, title, body, status, confidence, project, source_kind, source_ref,
    source_author, content_hash, created, updated, embedding`.
  - Relationship edges from the frontmatter keys:
    - `project` → `EdgeOp("BELONGS_TO", item, "project-{project}")` + a MERGE-stub
      `NodeOp(label="Project", key="project-{project}")`.
    - `concepts: [[concept-x]]` → `EdgeOp("ABOUT", item, "concept-x")` + stub
      `NodeOp(label="Concept", key="concept-x")` (wikilink parsed to its id).
    - `relates_to: [[id]]` → `EdgeOp("RELATES_TO", item, id)`.
    - `supersedes: [[id]]` → `EdgeOp("SUPERSEDES", item, id)`;
      `superseded_by: [[id]]` → `EdgeOp("SUPERSEDES", id, item)` (reverse).
    - `source_author` → `EdgeOp("AUTHORED_BY", item, "person-{author}")` + stub
      `NodeOp(label="Person", key="person-{author}")`.
  - A **`Concept`** stub → `NodeOp(label="Concept", key=id, {canonical, aliases})`.
  - A **`Project`** stub → `NodeOp(label="Project", key=id, {name, status, stack})`.
- **Embedder port** (`enigma_mcu/embeddings/port.py`): an `Embedder` interface
  with `embed(text: str) -> list[float]` returning a 1024-dim vector, and a
  `FakeEmbedder` that returns a **deterministic** 1024-dim vector derived from the
  text (same text → same vector; different text → different vector).
- The mapper embeds `title + "\n\n" + body` via the injected `Embedder` and
  attaches the result to `Item.embedding`.
- **Wikilink helper**: `[[x]]` → `x`; handles lists and empties.

## Scope — out (non-goals)

The Neo4j driver, any Cypher execution, the vector index, the real bge-m3 model,
Ollama, any network call (all SPEC-004) · `Conversation`/`EXTRACTED_FROM` edges
(SPEC-007, no such atoms exist yet) · concept extraction/normalization (SPEC-005)
· modifying `enigma_mcu/atom.py`, `vault.py`, or the adapter.

## Functional requirements

- **FR-1** An `Item` atom maps to the specified `Item` `NodeOp` with all listed
  properties, including a 1024-dim `embedding` from the injected embedder.
- **FR-2** Each frontmatter relationship key maps to the correct `EdgeOp` type and
  direction, with MERGE-stub `NodeOp`s for edge targets (Project, Concept, Person).
- **FR-3** Wikilink values are parsed to bare ids before use as edge targets.
- **FR-4** `Concept` and `Project` stubs map to their respective `NodeOp`s.
- **FR-5** `Embedder.embed` returns exactly 1024 floats; `FakeEmbedder` is
  deterministic.
- **FR-6** Mapping is pure and deterministic: mapping the same input twice yields
  identical ops (MERGE semantics make execution idempotent later).

## Harness contract (write these RED first — they ARE the definition of done)

- **T1** An `Item` atom → expected `Item` `NodeOp` (golden), embedding length 1024.
- **T2** (parametrized) Each relationship key → expected `EdgeOp`(s) with correct
  type/direction and the expected stub `NodeOp`s. Covers `project`, `concepts`,
  `relates_to`, `supersedes`, `superseded_by`, `source_author`.
- **T3** Wikilink parsing: `[[concept-mcp]]` → `concept-mcp`; list and empty cases.
- **T4** `Concept` stub → `Concept` `NodeOp` (canonical + aliases); `Project` stub
  → `Project` `NodeOp` (name + status + stack).
- **T5** `FakeEmbedder` returns 1024 floats and is deterministic across calls;
  distinct texts yield distinct vectors.
- **T6** A small multi-project vault fixture (two `Item`s in different projects
  sharing one concept, plus the Concept and Project stubs) → the expected complete
  op set (golden), showing both Items with `ABOUT` edges to the same Concept node
  (the cross-project join).
- **T7** Determinism: mapping the same fixture twice yields identical op lists.

## Dependencies

Python 3.12+, `pytest`, the SPEC-001 modules. **No** `neo4j` driver, **no**
Ollama client. Stdlib only beyond pytest.

## Definition of Done

T1–T7 GREEN on `main` (SPEC-001/002 suites still GREEN); `enigma_mcu/graph/ops.py`,
`enigma_mcu/graph/mapper.py`, and `enigma_mcu/embeddings/port.py` implemented;
`atom.py`, `vault.py`, and the adapter unchanged. No RED on `main`.
