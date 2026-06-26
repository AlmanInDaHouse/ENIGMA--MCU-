# Sample ADR Log

Minimal fixture mirroring the ADR-LOG entry format consumed by SPEC-002.

---

## ADR-0001 — Storage architecture: vault is truth, graph is index

**Status:** Accepted

**Context:** We need durable, portable memory plus fast retrieval.

**Decision:** The markdown vault is the single source of truth; Neo4j is a derived, fully rebuildable graph and vector index.

**Consequences:** Tool changes never threaten the data; the graph can be dropped and rebuilt at will.

---

## ADR-0002 — MCP server is the sole memory interface

**Status:** Accepted

**Context:** Many consumers must query memory.

**Decision:** Every consumer reaches memory only through an MCP server; no consumer touches Neo4j directly.

**Consequences:** Storage stays swappable; consumers stay decoupled.
