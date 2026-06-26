# SESSION-004 — Brief

| | |
|---|---|
| **Session** | 004 |
| **Phase** | 2 — Graph index |
| **Active SPEC** | SPEC-004 — Live Neo4j Sync |
| **Type** | Inner loop (Claude Code) |

## Entry state

SPEC-003 is delivered: `enigma_mcu/graph/ops.py`, `enigma_mcu/graph/mapper.py`,
`enigma_mcu/embeddings/port.py` exist; 44 tests GREEN on `main` (head `018bf2f`).
SPEC-004 exists at `docs/specs/SPEC-004-live-neo4j-sync.md`.

**Infrastructure required for the integration milestones:** Docker Neo4j 5.x
running, and Ollama with `bge-m3` pulled. The unit milestones (T1–T2) need
neither. If the services are not up, the integration tests must skip, not fail.

## Bootstrap (per CLAUDE.md)

Read, in order: `CONSTITUTION.md` → `docs/ROADMAP.md` →
`docs/specs/SPEC-004-live-neo4j-sync.md` → `docs/SPEC-atom-schema.md`. Then read
`enigma_mcu/graph/ops.py`, `mapper.py`, and `embeddings/port.py` — this loop
consumes the op IR and implements the embedder port; do not reinvent them.

## Scope

Implement the live Neo4j sync exactly per SPEC-004, harness-first: VaultReader,
Neo4jExecutor (idempotent MERGE), native vector index, real BgeM3Embedder,
SyncService, and `docker-compose.yml`.

## Tasks (in order — milestone-gated)

1. **Scaffold + deps.** Add `neo4j` and an HTTP client to `pyproject.toml`. Add
   `docker-compose.yml` (Neo4j 5.x). Add a service-availability probe + the
   `integration` pytest marker.
2. **Harness RED.** Write the unit tests (T1–T2) and the integration tests
   (T3–T7, marked + skip-gated), with a synthetic fixture vault (atoms with a
   shared concept + concept/project stubs). Confirm RED for the right reason.
   Commit locally.
3. **GREEN — unit.** Implement `graph/reader.py` (routing) and the Cypher-building
   logic in `graph/neo4j_executor.py` until T1–T2 pass everywhere.
4. **GREEN — graph integration.** Implement the executor's live run + the vector
   index against Docker Neo4j until T3–T5 pass locally.
5. **GREEN — embedder + e2e.** Implement `embeddings/bge_m3.py` and
   `enigma_mcu/sync.py` until T6–T7 pass locally with Ollama up.
6. **Verify.** `pytest -m "not integration"` GREEN (CI-safe); full run GREEN with
   services up; prior suites still GREEN. Commit per milestone, push only on GREEN.

## Done

T1–T2 GREEN everywhere; T3–T7 GREEN locally with services up (skipped, not red,
where absent); prior suites GREEN; pushed.

## Do NOT touch

Do not modify `atom.py`, `vault.py`, `mapper.py`, `ops.py`, `port.py`, or the
adapter — this loop is additive. No concept extraction, no MOC generation, no MCP,
no conversation parsing. Do not edit a test to make it pass. If you find a genuine
bug in a prior module, stop and report it.

## On finish or degradation

This loop is larger than the prior ones. Stop at the last GREEN milestone if
context degrades — do not push through it. Emit the **Session Report** (format in
`CLAUDE.md`); note which milestones landed and which remain. The architect will
dispatch a continuation if needed. End the chat — a fresh session resumes via
Bootstrap.
