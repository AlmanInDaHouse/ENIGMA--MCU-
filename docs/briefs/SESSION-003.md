# SESSION-003 — Brief

| | |
|---|---|
| **Session** | 003 |
| **Phase** | 2 — Graph index |
| **Active SPEC** | SPEC-003 — Graph Mapping & Embedder Port |
| **Type** | Inner loop (Claude Code) |

## Entry state

Phase 1 is delivered: `enigma_mcu/atom.py`, `enigma_mcu/vault.py`, and
`enigma_mcu/adapters/spec_driven.py` exist; 32 tests GREEN on `main` (head
`4a11838`). SPEC-003 exists at
`docs/specs/SPEC-003-graph-mapping-and-embedder-port.md`.

## Bootstrap (per CLAUDE.md)

Read, in order: `CONSTITUTION.md` → `docs/ROADMAP.md` →
`docs/specs/SPEC-003-graph-mapping-and-embedder-port.md` → `docs/SPEC-atom-schema.md`.
Then read the existing `enigma_mcu/atom.py` — the mapper consumes `Atom`
instances; do not reinvent the model.

## Scope

Implement the pure vault→graph mapping IR, the `GraphMapper`, and the `Embedder`
port + `FakeEmbedder`, exactly per SPEC-003, harness-first. **No Neo4j, no Ollama,
no network** — this loop requires no new infrastructure.

## Tasks (in order)

1. **Scaffold.** Add packages `enigma_mcu/graph/` and `enigma_mcu/embeddings/`.
2. **Harness RED.** Write tests T1–T7 from SPEC-003 §Harness contract, with a small
   multi-project vault fixture under `tests/fixtures/`. Run, confirm RED for the
   right reason. Commit locally.
3. **GREEN — IR & embedder port.** Implement `graph/ops.py` (`NodeOp`, `EdgeOp`)
   and `embeddings/port.py` (`Embedder`, `FakeEmbedder`) until T1, T5 pass.
4. **GREEN — mapper.** Implement `graph/mapper.py` (`GraphMapper`: Item node,
   relationship edges + stub targets, Concept/Project stubs, wikilink parsing,
   embedding attachment) until T2–T4, T6–T7 pass.
5. **Verify.** Full suite GREEN (SPEC-001/002 still GREEN). Commit per milestone,
   conventional messages. Push only on GREEN.

## Done

T1–T7 GREEN on `main` (and prior suites still GREEN), pushed.

## Do NOT touch

No `neo4j` driver, no Cypher, no vector index, no real embeddings, no Ollama, no
network — all of that is SPEC-004. No `Conversation`/`EXTRACTED_FROM` edges. No
concept extraction. Do not modify `enigma_mcu/atom.py`, `vault.py`, or the adapter
— this loop is additive. If you find a genuine bug in them, stop and report it.
Do not edit a test to make it pass.

## On finish or degradation

Stop and emit the **Session Report** (format in `CLAUDE.md`). Paste it back to the
architect. End the chat — a fresh session resumes via Bootstrap.
