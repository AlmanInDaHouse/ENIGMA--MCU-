# ENIGMA-MCU — Roadmap

Phase map for the build. Each phase is delivered through one or more SPECs, each
SPEC through one or more Claude Code sessions (loops), harness-first.

**Status legend:** ✅ done · ▶ current · ◻ planned

SPEC numbers are assigned when a SPEC is written, not reserved in advance (this
avoids renumbering when a phase is split).

| Phase | Scope | SPECs | Status |
|---|---|---|---|
| 0 — Foundation | Constitution, CLAUDE.md, roadmap, atom-schema contract, ADR log | — | ✅ |
| 1 — Data foundation | Atom model + idempotent vault writer; deterministic Spec-Driven repo adapter | SPEC-001 ✅, SPEC-002 ✅ | ✅ |
| 2 — Graph index | Pure vault→graph mapping + embedder port; live Neo4j sync + vector index + real bge-m3 | SPEC-003 ✅, SPEC-004 ✅ | ✅ |
| 3 — Cross-project | Concept extraction + normalization (005); then materialization to vault+graph; then Pass-2 RELATES_TO linking | SPEC-005 ▶ | ▶ |
| 4 — Interface | MCP server: search_memory / get_related / project_context | — | ◻ |
| 5 — Conversations | Adapter for the dedicated Fran↔Manuel ideas chat (LLM extraction) | — | ◻ |
| 6 — Visual brain | Per-project MOC generation (Obsidian materialization) | — | ◻ |
| 7 — Orchestration | Backfill batch + continuous incremental flow | — | ◻ |

**Current phase: 3.** Active SPEC: **SPEC-005** (concept extraction + normalization).

Phase 3 is the cross-project engine — the reason the whole system exists. SPEC-005
deliberately produces an **inspectable concept set without persisting anything**,
so the make-or-break capability (extraction quality) can be reviewed and curated
before any concept touches the vault or graph.

## Session log

| Session | SPEC | Result | Head |
|---|---|---|---|
| SESSION-001 | SPEC-001 | ✅ T1–T7 GREEN, 22 cases | `15d8c30` |
| SESSION-002 | SPEC-002 | ✅ T1–T6 GREEN, 32 total | `4a11838` |
| SESSION-003 | SPEC-003 | ✅ T1–T7 GREEN, 44 total | `018bf2f` |
| SESSION-004 | SPEC-004 | ✅ T1–T7 GREEN, 54 w/ services (49 CI-safe) | `acea848` |

## Infrastructure notes

- **Neo4j on host ports 7475/7688** (container 7474/7687), isolated from another
  project's Neo4j on the standard ports. All ENIGMA connections use
  `NEO4J_URI=bolt://localhost:7688`. `enigma-neo4j` + `bge-m3` available.
- **Pass-2 LLM via OpenRouter** (OpenAI-compatible) now, local Ollama later — same
  `ConceptExtractor` port, swap by config. Pin an explicit model, disable provider
  retention, cap with `max_price`. `OPENROUTER_API_KEY` via env, never committed.

## Open items

- **Live query agent & hardware** (ADR-0009): deferred.
- **Per-source LLM routing** (orchestration): confidential/client sources (e.g.
  IVECO) route to the local model; own projects route to OpenRouter. Owner decides
  the boundary.
- **Real extraction timestamp** (orchestration): inject real time, not a placeholder.
- **Artifact manifest** (orchestration): map repo files to artifact kind.
- **Lazy skip-probe** (tech-debt, low): integration probe runs at collection (~3s).

Order note: phases 3↔4 are intentionally ordered concepts-before-MCP so the MCP
exposes the full hybrid (vector + traversal) query from its first release.
