# ENIGMA-MCU — Roadmap

Phase map for the build. Each phase is delivered through one or more SPECs, each
SPEC through one or more Claude Code sessions (loops), harness-first.

**Status legend:** ✅ done · ▶ current · ◻ planned

| Phase | SPEC(s) | Scope | Status |
|---|---|---|---|
| 0 — Foundation | — | Constitution, CLAUDE.md, roadmap, atom-schema contract | ✅ |
| 1 — Data foundation | SPEC-001, SPEC-002 | Atom model + idempotent vault writer (001); Spec-Driven repo adapter → atoms (002) | ▶ |
| 2 — Graph index | SPEC-003 | Sync vault → Neo4j: nodes, edges, native vector index (bge-m3, 1024d) | ◻ |
| 3 — Cross-project | SPEC-004 | Concept extraction + normalization + Pass-2 linking (RELATES_TO) | ◻ |
| 4 — Interface | SPEC-005 | MCP server: search_memory / get_related / project_context | ◻ |
| 5 — Conversations | SPEC-006 | Adapter for the dedicated Fran↔Manuel ideas chat | ◻ |
| 6 — Visual brain | SPEC-007 | Per-project MOC generation (Obsidian materialization) | ◻ |
| 7 — Orchestration | SPEC-008 | Backfill batch + continuous incremental flow | ◻ |

**Current phase: 1.** Active SPEC: **SPEC-001**. Active session: **SESSION-001**.

Order note: phases 3↔4 are intentionally ordered concepts-before-MCP so the MCP
exposes the full hybrid (vector + traversal) query from its first release.
