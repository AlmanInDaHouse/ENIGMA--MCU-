# SPEC — Atom Schema (the contract)

| | |
|---|---|
| **ID** | SPEC-atom-schema |
| **Status** | Active |
| **Scope** | Foundational contract. Every SPEC depends on this. |

Defines what an **atom** is on disk and in memory. This is the stable contract
that the vault writer, every source adapter, the Neo4j sync, and the MCP server
all conform to. Changes here are amendments and ripple everywhere — treat as
load-bearing.

## 1. Atom types (`type`)

An atom is a single self-contained assertion (Constitution §2). Exactly one type.

| type | meaning | `status` vocabulary |
|---|---|---|
| `decision` | a closed choice (mostly from ADRs) | `proposed` · `accepted` · `superseded` · `deprecated` |
| `fact` | a stable fact about a project/system | `current` · `outdated` |
| `idea` | an undecided proposal (heart of the ideas chat) | `raw` · `explored` · `promoted` · `discarded` |
| `open_question` | an unresolved question | `open` · `resolved` |

`status` MUST belong to the vocabulary of the atom's `type`.

## 2. Node classes that are NOT atoms

Stored as light stub notes; they exist to wire the graph, not to assert.

| class | role |
|---|---|
| `Concept` | the join across projects (normalized: canonical + aliases) |
| `Project` | the project hub (MOC note) |
| `Conversation` | provenance for conversation-sourced atoms |
| `Person` | provenance (manuel · fran · claude) |

## 3. Frontmatter (the contract)

```yaml
---
# Identity
id: cyberguard-adr-0005          # REQUIRED. = file basename. Globally unique, link-safe.
type: decision                   # REQUIRED. decision | fact | idea | open_question
title: "..."                     # REQUIRED. One-line statement of the assertion.

# Ownership & provenance  (Constitution §3 — all REQUIRED)
project: cyberguard              # BELONGS_TO. Exactly one primary owner.
source:
  kind: repo-artifact            # repo-artifact | conversation | document
  ref: docs/adr/0005-...md       # path | chat-id+range | doc#section
  author: manuel                 # manuel | fran | claude | n/a
  extracted_at: 2026-06-26T10:00:00Z

# Lifecycle
status: accepted                 # REQUIRED. Vocab per type (§1).
confidence: high                 # REQUIRED. high | low. Curation triage; set by the LLM.

# Relationships  (each key = an edge type; values = wikilinks)
concepts: ["[[concept-detection]]"]   # ABOUT — the cross-project join
relates_to: ["[[cyberguard-adr-0007]]"]
supersedes: []                        # decision lineage
superseded_by: []

# Integrity
content_hash: 9f2a7c...          # REQUIRED. sha256(normalized body). Idempotency.
created: 2026-06-26              # REQUIRED.
updated: 2026-06-26              # REQUIRED.
tags: []                         # optional, human use
artifact_ref: null               # optional, facts only: real module/PR/file
---

<body: the self-contained assertion. This text is what gets embedded.>
```

**Relationship keys → graph edges.** The frontmatter key is the edge type; values
are plain `[[wikilinks]]` so Obsidian draws the edges for free and Dataview can
query them. The Neo4j sync maps each key to a typed edge. v2-extensible with the
same pattern: `depends_on`, `contradicts`, `refines`, `blocks`.

**Embedding input.** The vector is computed over `title + "\n\n" + body` and lives
on the `Item` node in Neo4j (Phase 2). The frontmatter feeds the graph.

## 4. Identity & idempotency (Constitution §7)

Per-adapter ID strategy:

- **Structured sources** (repo-artifact): `id = {project}-{kind}-{locator}`,
  e.g. `cyberguard-adr-0005`. Survives edits; `content_hash` detects a change and
  triggers an **update in place**, never a duplicate.
- **Unstructured sources** (conversation, document):
  `id = {type}-{short_hash(normalized_body + source.ref)}`, e.g. `idea-3f9c1a`.
  A real content change is a new atom.

**content_hash** = `sha256` of the normalized body. Normalization: strip leading/
trailing whitespace, collapse trailing spaces per line, LF newlines. Logically
identical bodies hash identically; real changes differ.

## 5. Concept & Project stubs

```yaml
# vault/concepts/concept-mcp.md
---
id: concept-mcp
type: concept
canonical: MCP
aliases: ["Model Context Protocol", "mcp server"]
---
```

```yaml
# vault/projects/project-cyberguard.md  (the MOC)
---
id: project-cyberguard
type: project
name: CyberGuard Enterprise
status: active
stack: [rust, go, typescript, nextjs, python]
---
```

## 6. Vault layout

```
vault/
  cyberguard/        # one folder per project — its atom cluster
  quetzy/
  enigma-mcu/
  ideas/             # conversation-sourced atoms
  concepts/          # Concept stubs — the cross-project connectivity
  projects/          # Project MOC stubs
```

The folder structure IS the representation of the projects in the brain; the
`concepts/` nodes are the connectivity that crosses between them.

## 7. Worked example — unstructured (ideas chat)

```yaml
---
id: idea-3f9c1a
type: idea
title: "Expose ENIGMA-MCU as an MCP server so Quetzy can consume it later"
project: enigma-mcu
source:
  kind: conversation
  ref: ideas-chat/msg-1042..1045
  author: manuel
  extracted_at: 2026-06-26T11:30:00Z
status: explored
confidence: high
concepts: ["[[concept-mcp]]", "[[concept-contextual-memory]]", "[[concept-quetzy]]"]
relates_to: []
supersedes: []
superseded_by: []
content_hash: 3f9c1a...
created: 2026-06-26
updated: 2026-06-26
---

Idea: memory is exposed as an MCP server (search_memory, get_related,
project_context) so the local GLM agent queries it today and Quetzy consumes it
in the future without coupling to Neo4j.
```
