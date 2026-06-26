# SESSION-005 — Brief

| | |
|---|---|
| **Session** | 005 |
| **Phase** | 3 — Cross-project |
| **Active SPEC** | SPEC-005 — Concept Extraction & Normalization |
| **Type** | Inner loop (Claude Code) |

## Entry state

Phase 2 is delivered: the vault→graph mapping, live Neo4j sync, and real bge-m3
embedder exist; 54/49 tests GREEN on `main` (head `acea848`). SPEC-005 exists at
`docs/specs/SPEC-005-concept-extraction-and-normalization.md`.

**Infrastructure for integration milestones:** an `OPENROUTER_API_KEY` in env (and
the Phase-2 Ollama bge-m3). The unit milestones need neither. Integration tests
skip — never fail — when the key is absent, and must be kept minimal (they cost
tokens).

## Bootstrap (per CLAUDE.md)

Read, in order: `CONSTITUTION.md` → `docs/ROADMAP.md` →
`docs/specs/SPEC-005-concept-extraction-and-normalization.md` →
`docs/SPEC-atom-schema.md`. Then read `enigma_mcu/embeddings/port.py` (the
`Embedder` you will inject) and `enigma_mcu/vault.py` (`read_atom`).

## Scope

Implement concept extraction (LLM behind a port) + normalization (embedding
clustering, conservative) producing an **inspectable dry-run report**, exactly per
SPEC-005, harness-first. **Persist nothing** — no vault writes, no graph edges.

## Tasks (in order)

1. **Scaffold + deps.** Add package `enigma_mcu/extraction/`; add an HTTP client to
   `pyproject.toml`. Add the `OPENROUTER_*` env config + a key-presence probe for
   skip-gating.
2. **Harness RED.** Write the unit tests (T1–T5) with controlled fake embeddings
   and a `FakeConceptExtractor`, and the integration tests (T6–T7, marked +
   skip-gated, minimal). Confirm RED for the right reason. Commit locally.
3. **GREEN — port + normalization.** Implement `extraction/llm_port.py`
   (`ConceptExtractor` + `FakeConceptExtractor`) and `extraction/normalize.py`
   (`ConceptNormalizer`, conservative threshold) until T1–T4 pass.
4. **GREEN — report + OpenRouter.** Implement `extraction/report.py` (dry-run
   report, written outside the vault) and `extraction/openrouter.py`
   (`OpenRouterConceptExtractor`, retention-off, `max_price`) until T5 passes and
   T6–T7 pass locally with a key.
5. **Verify.** `pytest -m "not integration"` GREEN; full run GREEN with a key;
   prior suites still GREEN; **assert the vault and graph are untouched**. Commit
   per milestone, push only on GREEN.

## Done

T1–T5 GREEN everywhere; T6–T7 GREEN locally with a key (skipped, not red, where
absent); vault and graph untouched; prior suites GREEN; pushed.

## Do NOT touch

Do not write to the vault or graph — this SPEC only produces a report. Do not
modify `atom.py`, `vault.py`, `mapper.py`, `ops.py`, `port.py`, the adapter, or the
sync. No materialization, no RELATES_TO, no per-source routing, no local Ollama
extractor. Never commit the API key. Do not edit a test to make it pass. If you
find a genuine bug in a prior module, stop and report it.

## On finish or degradation

Stop at the last GREEN milestone if context degrades — do not push through it.
Emit the **Session Report** (format in `CLAUDE.md`). End the chat — a fresh session
resumes via Bootstrap.

## After this loop (owner action, not Claude Code)

Run the extractor over real repos and **review the dry-run report** — tune the
threshold and prompt until the concept set is good. The next SPEC materializes a
curated set; this gate is deliberate.
