# ENIGMA-MCU — Roadmap

Phase map for the build. Each phase is delivered through one or more SPECs, each
SPEC through one or more Claude Code sessions (loops), harness-first.

**Status legend:** ✅ done · ▶ current · ◻ planned

| Phase | SPEC(s) | Scope | Status |
|---|---|---|---|
| 0 — Foundation | — | Constitution, CLAUDE.md, roadmap, atom-schema contract, ADR log | ✅ |
| 1 — Data foundation | SPEC-001 ✅, SPEC-002 ✅ | Atom model + idempotent vault writer; deterministic Spec-Driven repo adapter | ✅ |
| 2 — Graph index | SPEC-003 ✅, SPEC-004 ▶ | Pure vault→graph mapping + embedder port (done); live Neo4j sync + vector index + real bge-m3 | ▶ |
| 3 — Cross-project | SPEC-005 | Concept extraction + normalization + Pass-2 linking (RELATES_TO) | ◻ |
| 4 — Interface | SPEC-006 | MCP server: search_memory / get_related / project_context | ◻ |
| 5 — Conversations | SPEC-007 | Adapter for the dedicated Fran↔Manuel ideas chat (LLM extraction) | ◻ |
| 6 — Visual brain | SPEC-008 | Per-project MOC generation (Obsidian materialization) | ◻ |
| 7 — Orchestration | SPEC-009 | Backfill batch + continuous incremental flow | ◻ |

**Current phase: 2.** Active SPEC: **SPEC-004**. Active session: **SESSION-004**.

Phase 2 split: SPEC-003 (infra-free mapping + fake embedder) is done; SPEC-004 is
the live I/O — real Neo4j via Docker, native vector index, real bge-m3.

## Session log

| Session | SPEC | Result | Head |
|---|---|---|---|
| SESSION-001 | SPEC-001 | ✅ T1–T7 GREEN, 22 cases | `15d8c30` |
| SESSION-002 | SPEC-002 | ✅ T1–T6 GREEN, 32 total | `4a11838` |
| SESSION-003 | SPEC-003 | ✅ T1–T7 GREEN, 44 total | `018bf2f` |

## Open items

- **Live query agent & hardware (ADR-0009):** the dedicated GLM agent and its
  machine are deferred. To be specified before Phase 4 ships, or later.
- **Real extraction timestamp → SPEC-009:** the adapter's `source.extracted_at`
  is a fixed placeholder; orchestration must inject the real time.
- **Artifact manifest → SPEC-009:** the adapter takes explicit `(path, kind)`;
  orchestration needs a manifest mapping repo files to their artifact kind.

**Order note:** phases 3↔4 are intentionally ordered concepts-before-MCP so the MCP
exposes the full hybrid (vector + traversal) query from its first release.
