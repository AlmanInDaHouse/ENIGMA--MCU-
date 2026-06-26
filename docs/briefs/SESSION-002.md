# SESSION-002 — Brief

| | |
|---|---|
| **Session** | 002 |
| **Phase** | 1 — Data foundation |
| **Active SPEC** | SPEC-002 — Spec-Driven Repo Adapter |
| **Type** | Inner loop (Claude Code) |

## Entry state

SPEC-001 is delivered: `enigma_mcu/atom.py` and `enigma_mcu/vault.py` exist with
T1–T7 GREEN on `main` (head `15d8c30`). The ADR log exists at
`docs/adr/ADR-LOG.md`. SPEC-002 exists at
`docs/specs/SPEC-002-spec-driven-adapter.md`.

## Bootstrap (per CLAUDE.md)

Read, in order: `CONSTITUTION.md` → `docs/ROADMAP.md` →
`docs/specs/SPEC-002-spec-driven-adapter.md` → `docs/SPEC-atom-schema.md`. Then
read the existing `enigma_mcu/atom.py`, `enigma_mcu/vault.py`, and their tests —
this adapter **uses** `Atom` and `VaultWriter`; do not reinvent them.

## Scope

Implement the deterministic Spec-Driven adapter (ADRs + Constitution principles →
atoms, fed to `VaultWriter`) exactly per SPEC-002, harness-first. No LLM.

## Tasks (in order)

1. **Fixtures.** Add a minimal ADR fixture (one entry in the ADR-log format) and
   a minimal Constitution fixture (a few principles) under `tests/fixtures/`.
2. **Harness RED.** Write tests T1–T6 from SPEC-002 §Harness contract. Run, confirm
   RED for the right reason. Commit locally.
3. **GREEN — parsing.** Implement `enigma_mcu/adapters/spec_driven.py`
   (`SpecDrivenAdapter`: ADR + principle parsers, status mapping, `concepts: []`)
   until T1–T3 pass.
4. **GREEN — integration & robustness.** Wire the adapter to `VaultWriter`; cover
   idempotency (T4), malformed-skip (T5), and the dogfood run over the repo's own
   `CONSTITUTION.md` (T6).
5. **Verify.** Full suite GREEN (SPEC-001 tests must still pass). Commit per
   milestone, conventional messages. Push only on GREEN.

## Done

T1–T6 GREEN on `main` (and SPEC-001's T1–T7 still GREEN), pushed.

## Do NOT touch

No LLM, Neo4j, embeddings, concepts (emit `[]`), conversation parsing, or
SPEC-file parsing. Do not modify `enigma_mcu/atom.py` or `enigma_mcu/vault.py` —
the adapter is additive. If you find a genuine bug in them, stop and report it as
a deviation rather than patching silently. Do not edit a test to make it pass.

## On finish or degradation

Stop and emit the **Session Report** (format in `CLAUDE.md`). Paste it back to the
architect. End the chat — a fresh session resumes via Bootstrap.
