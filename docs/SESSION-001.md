# SESSION-001 — Brief

| | |
|---|---|
| **Session** | 001 |
| **Phase** | 1 — Data foundation |
| **Active SPEC** | SPEC-001 — Atom Model & Vault Writer |
| **Type** | Inner loop (Claude Code) |

## Entry state

Repository contains: `CONSTITUTION.md`, `CLAUDE.md`, `docs/ROADMAP.md`,
`docs/SPEC-atom-schema.md`, `docs/specs/SPEC-001-atom-model-and-vault-writer.md`.
No application code yet. `enigma_mcu/` and `tests/` do not exist.

## Bootstrap (per CLAUDE.md)

Read, in order: `CONSTITUTION.md` → `docs/ROADMAP.md` →
`docs/specs/SPEC-001-atom-model-and-vault-writer.md` → `docs/SPEC-atom-schema.md`.
The test suite is empty; you are creating it.

## Scope

Implement the Atom model + idempotent VaultWriter exactly per SPEC-001,
harness-first.

## Tasks (in order)

1. **Scaffold.** `pyproject.toml` (Python 3.12, pytest, a YAML lib), package
   `enigma_mcu/`, `tests/` with `tests/fixtures/`. Minimal `README.md` with the
   test command.
2. **Harness RED.** Write tests T1–T7 from SPEC-001 §Harness contract. Run the
   suite and confirm they fail for the right reason (RED). Commit.
3. **GREEN — model.** Implement `enigma_mcu/atom.py` (Atom + validation + hashing
   + ID helper) until T1–T4 pass.
4. **GREEN — writer.** Implement `enigma_mcu/vault.py` (VaultWriter + reader)
   until T5–T7 pass.
5. **Verify.** Full suite GREEN. Commit per milestone, conventional messages.

## Done

T1–T7 GREEN on `main`, pushed.

## Do NOT touch

No Neo4j, embeddings, adapters, MCP, network, or LLM. Do not add atom fields
beyond SPEC-atom-schema. Do not edit a test to make it pass. Stay inside SPEC-001.

## On finish or degradation

Stop and emit the **Session Report** (format in `CLAUDE.md`). Paste it back to the
architect. End the chat — a fresh session resumes via Bootstrap.
