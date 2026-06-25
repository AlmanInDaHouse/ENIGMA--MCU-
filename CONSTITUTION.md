# ENIGMA-MCU — Constitution

> **Motor Contextual Unificado** — the unified contextual memory engine.

| | |
|---|---|
| **Project** | ENIGMA-MCU |
| **Repository** | https://github.com/AlmanInDaHouse/ENIGMA--MCU-.git |
| **Version** | 1.0.0 |
| **Status** | Ratified |
| **Date** | 2026-06-26 |
| **Supersedes** | Enigma v3 (deprecated upon delivery of ENIGMA-MCU) |

## Preamble

ENIGMA-MCU is a unified, atomic, shared contextual-memory engine. It ingests
everything that carries context across many projects — decisions, facts, ideas,
open questions, code, and conversations — distills it into self-contained atoms,
and relates those atoms across project boundaries to surface connections and
generate new ideas. It serves this memory on demand to humans and to agents
operating in loops, so that context lives in durable storage rather than in any
single, exhaustible context window. ENIGMA-MCU supersedes and retires the prior
Enigma project.

This Constitution defines the invariants of the system. Implementation decisions
live in ADRs; what to build lives in SPECs; this document defines what must
always be true regardless of either.

---

## Part I — Memory & Architecture

**1. The Markdown vault is the single source of truth.**
Every other store — the graph, the vector index, the visual layer — is a
derived, reconstructible projection of the vault. Tools are replaceable; the
vault is not.

**2. An atom is a self-contained assertion.**
One claim, one topic, one type, with provenance. If a note cannot be understood
outside its own file, it is not yet atomic.

**3. Provenance is mandatory.**
Every atom records its origin: source, author, and timestamp. An atom the system
cannot trace, it does not trust — and neither should its consumers.

**4. Concepts are the join across projects.**
Cross-project intelligence flows exclusively through normalized concept nodes.
The system never relies on brittle, direct item-to-item links to discover
cross-project relationships at scale.

**5. The graph is an index, not a source.**
Neo4j holds the graph and the vectors and must be fully rebuildable from the
vault at any moment. Nothing that cannot be regenerated from the vault is ever
stored only in the graph.

**6. Memory is reached only through the MCP interface.**
Every consumer — the local agent, a future Quetzy, any agentic loop — queries
memory through the MCP server, never the database directly. Storage stays
decoupled from consumers.

**7. Ingestion is idempotent.**
Re-running extraction updates atoms in place; it never duplicates them. Identity
is stable and deterministic per source type.

---

## Part II — Process & Methodology

**8. No code without a spec.**
The order is law: Constitution → SPEC → (ADR for any non-trivial decision) →
harness → implementation. Work that skips a step is rejected, however small.

**9. Harness-first: RED before GREEN.**
Every unit of work opens with a failing test that encodes its contract. The
harness is the project's only non-hallucinable ground truth; code is "done" only
when its harness is GREEN. A test is never edited to make it pass without
explicit instruction.

**10. The documentation is the durable memory.**
Implementation sessions are bounded by finite context windows; the artifacts are
not. The repository — Constitution, SPECs, ADRs, tests — carries project state,
not any single session. If a fresh session cannot reconstitute full context from
the repository alone, that is a defect in the documentation, not merely in the
session. Sessions are disposable; artifacts are permanent.

**11. Automated extraction proposes; a human disposes.**
The pipeline suggests atoms, concepts, and relationships; a human reviews and
prunes them — especially in early phases — and that review feeds back into the
prompts.

**12. Artifacts in English, collaboration in Spanish.**
All repository artifacts — documents, code, comments, commit messages — are
written in English. Working conversation is conducted in Spanish.

---

## Amendment

This Constitution is versioned. A principle changes only through an explicit,
recorded amendment: a superseding ADR that references the principle by number,
mirroring how atoms supersede one another. Principles are stable by design; their
evolution is traceable by design.
