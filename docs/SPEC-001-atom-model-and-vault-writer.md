# SPEC-001 — Atom Model & Vault Writer

| | |
|---|---|
| **ID** | SPEC-001 |
| **Phase** | 1 — Data foundation |
| **Status** | Active |
| **Depends on** | CONSTITUTION, SPEC-atom-schema |
| **Session** | SESSION-001 |

## Context

The first executable unit. It builds the in-memory **Atom** representation and
the **idempotent vault writer** that serializes atoms to markdown — the target
that every later source adapter will feed. No source parsing yet (SPEC-002), no
Neo4j (SPEC-003). This validates the atom schema (Constitution §2) and idempotent
ingestion (§7) before any adapter exists, using hand-built atoms in fixtures.

## Scope — in

- `Atom` model mirroring SPEC-atom-schema (frontmatter fields + body).
- Schema validation: type enum, per-type `status` vocabulary, mandatory
  provenance, non-empty title/body.
- Deterministic identity: accept structured IDs as-is; helper for hashed IDs.
- `content_hash` over the normalized body.
- `VaultWriter`: Atom → markdown file (YAML frontmatter + body) at
  `vault/{project}/{id}.md`, with stable key order. Idempotent.
- Reader: parse a vault markdown file back into an `Atom` (round-trip).

## Scope — out (non-goals)

Source adapters / parsing (SPEC-002) · Neo4j, embeddings, concepts, MCP · any
network or LLM call · inventing atom fields beyond SPEC-atom-schema.

## Functional requirements

- **FR-1** `Atom` carries every field of SPEC-atom-schema §3 plus `body`.
- **FR-2** Validation rejects: unknown `type`; `status` outside the type's
  vocabulary; missing `source.kind|ref|author`; empty `title` or `body`.
- **FR-3** `content_hash = sha256(normalize(body))`. `normalize` = strip outer
  whitespace, collapse trailing spaces per line, LF newlines.
- **FR-4** Structured IDs are used verbatim. Helper computes
  `{type}-{short_hash(normalize(body) + source.ref)}` for unstructured atoms.
- **FR-5** `VaultWriter` writes deterministic YAML frontmatter (fixed key order)
  + body to `vault/{project}/{id}.md`.
- **FR-6** Idempotency: re-writing an atom whose `id` exists with unchanged
  `content_hash` leaves the file byte-identical and creates no duplicate. A
  changed body updates `body`, `content_hash`, and `updated`; preserves `created`.
- **FR-7** Round-trip: write → read yields an `Atom` equal by `id`,
  `content_hash`, and all fields.

## Harness contract (write these RED first — they ARE the definition of done)

- **T1** A valid atom of each of the four types constructs and validates.
- **T2** (parametrized) Invalid atoms are rejected: bad type; status-not-in-vocab;
  missing provenance; empty body; empty title.
- **T3** `content_hash` is identical for whitespace-variant bodies and differs on
  a real content change.
- **T4** Hashed-ID helper is deterministic and yields distinct IDs for distinct
  bodies/refs.
- **T5** `VaultWriter` produces the expected file at the expected path with
  expected frontmatter + body (golden-file comparison).
- **T6** Idempotent re-write: identical content → byte-identical file, no
  duplicate; changed body → updated `content_hash` + `updated`, same `created`,
  same path.
- **T7** Round-trip write → read → equal.

## Dependencies

Python 3.12+, `pytest`, a YAML library (`pyyaml` or `ruamel.yaml`), stdlib
`hashlib`. Nothing else.

## Definition of Done

T1–T7 GREEN on `main`; `enigma_mcu/atom.py` and `enigma_mcu/vault.py` implemented;
fixtures under `tests/fixtures/`; running instructions in `README.md`. No RED on
`main`.
