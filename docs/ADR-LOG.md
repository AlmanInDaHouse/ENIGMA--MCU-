# ENIGMA-MCU — Architecture Decision Log

Consolidated record of the foundational decisions. Each entry is a small ADR.
While these are stable and rarely change, they live in one log for reviewability;
an entry is split into its own file only when it begins to be superseded (when
lineage earns the separation).

Entry format is fixed and machine-parseable (consumed later by the Spec-Driven
adapter, SPEC-002): `## ADR-NNNN — Title`, then `**Status:**`, `**Context:**`,
`**Decision:**`, `**Consequences:**`.

---

## ADR-0001 — Storage architecture: vault is truth, graph is index

**Status:** Accepted

**Context:** We need durable, portable memory plus fast semantic and relational retrieval and a human-navigable view.

**Decision:** The markdown vault is the single source of truth. Neo4j is a derived, fully rebuildable graph + vector index. Obsidian reads the vault directly as the visual layer.

**Consequences:** Tool changes never threaten the data; the graph can be dropped and rebuilt at will; retiring the old Enigma costs nothing. Implements Constitution §1 and §5.

---

## ADR-0002 — Single store: Neo4j native vector index

**Status:** Accepted

**Context:** Vector search and graph traversal could be served by two systems or one.

**Decision:** Use Neo4j 5.x with its native vector index to hold both the graph and the embeddings, resolving hybrid queries (semantic + traversal) in a single Cypher. Reject a separate vector database (Qdrant).

**Consequences:** At our scale (two people, tens of thousands of atoms) Neo4j's vector index is more than sufficient; one store, one query language, fewer operations; the cross-project idea query becomes a single Cypher statement. Revisit only if scale exceeds the index's envelope.

---

## ADR-0003 — MCP server is the sole memory interface

**Status:** Accepted

**Context:** The local GLM agent today, Quetzy in the future, and agentic loops must all query memory.

**Decision:** Every consumer reaches memory only through an MCP server (`search_memory` / `get_related` / `project_context`). No consumer touches Neo4j directly.

**Consequences:** Storage stays swappable; consumers stay decoupled; the deferred Quetzy integration is simply another client of the same interface. Implements Constitution §6.

---

## ADR-0004 — Two-pass extraction

**Status:** Accepted

**Context:** Atoms cannot be linked across projects until they exist, and extraction and linking have different cost and quality profiles.

**Decision:** Pass 1 extracts atoms per source (parallelizable, cheap, local). Pass 2 runs globally over the whole corpus to normalize concepts and create cross-project links.

**Consequences:** Linking can re-run as the corpus grows without re-extracting; the expensive global step is isolated and run once per batch.

---

## ADR-0005 — Concepts as normalized join nodes

**Status:** Accepted

**Context:** Direct item-to-item linking is O(n²) and noisy; cross-project intelligence needs a stable join.

**Decision:** Cross-project relationships flow through canonical Concept nodes (canonical name + aliases). Items link to Concepts; a shared Concept makes items from different projects candidates for a relation.

**Consequences:** Idea generation becomes a cheap query over shared concepts; concept normalization becomes its own sub-problem (embedding similarity plus a controlled vocabulary). Implements Constitution §4.

---

## ADR-0006 — Identity & idempotency strategy

**Status:** Accepted

**Context:** Re-running extraction must update, never duplicate, and sources differ in stability.

**Decision:** Structured sources use `id = {project}-{kind}-{locator}` (stable across edits); unstructured sources use `id = {type}-{short_hash(normalized_body + source.ref)}`. `content_hash = sha256(normalized body)` drives in-place updates. The body is stored in normalized form.

**Consequences:** Editing a structured artifact updates its atom in place; a real content change to an unstructured atom is a new atom. Implements Constitution §7; refined empirically in SPEC-001 (body normalized at construction).

---

## ADR-0007 — Embedding model & dimension

**Status:** Accepted

**Context:** Content is bilingual (Spanish chat, English repositories), and the Neo4j vector index requires a fixed dimension.

**Decision:** Use bge-m3 (1024 dimensions, cosine) via Ollama; fix the Neo4j vector index at 1024. Multilingual capability is mandatory.

**Consequences:** Spanish and English content share one embedding space; the model can change later only through a reindex; the 1024 dimension is the load-bearing commitment.

---

## ADR-0008 — Pipeline language & runtime

**Status:** Accepted

**Context:** The pipeline needs ML tooling, a Neo4j driver, and local LLM access.

**Decision:** Python 3.12+.

**Consequences:** Natural fit with the ML stack, the official Neo4j driver, Ollama, and reuse of qwen from the prior Enigma.

---

## ADR-0009 — Extraction models, distinct from the query agent

**Status:** Accepted

**Context:** Pass 1 and Pass 2 have different quality needs, and the live query agent is a separate concern.

**Decision:** Pass 1 uses qwen2.5:7b-instruct (local). Pass 2 (global linking, batch, one-off) uses a stronger model. The dedicated live GLM query agent and its hardware are deferred and remain open.

**Consequences:** Cheap parallel extraction; a stronger model only where it pays, on the single global linking pass; agent and hardware sizing decided later. Open item tracked in the roadmap.
