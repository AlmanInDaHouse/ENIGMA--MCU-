# SPEC-002 — Spec-Driven Repo Adapter

| | |
|---|---|
| **ID** | SPEC-002 |
| **Phase** | 1 — Data foundation |
| **Status** | Active |
| **Depends on** | CONSTITUTION, SPEC-atom-schema, SPEC-001 (Atom + VaultWriter) |
| **Session** | SESSION-002 |

## Context

The first source adapter, and the highest-value one: our own Spec-Driven repos
are already half-extracted by hand. This adapter parses **structured artifacts
deterministically — no LLM** — into atoms with structured IDs, then feeds them to
the existing `VaultWriter`. Determinism is the whole advantage: predictable
artifacts give predictable atoms, golden-file testable and fast. LLM-based
extraction is reserved for conversations (a later SPEC).

Scope is deliberately narrow: **ADRs and Constitution principles only.** SPEC
files and code-symbol extraction are out — their structure is more variable and
earns its own SPEC later.

## Scope — in

- `SpecDrivenAdapter`: given a set of artifact files, parse them into `list[Atom]`.
- **ADR entries** (format per the ADR log: `## ADR-NNNN — Title`, `**Status:**`,
  `**Decision:**`, `**Consequences:**`) → one `decision` atom each.
  - `id = {project}-adr-{NNNN}`; `title` = the ADR title; `body` = the Decision
    text (the assertion — not the whole ADR); `status` mapped from ADR status.
- **Constitution principles** (format `**N. Title.**` followed by an explanation
  paragraph) → one `decision` atom each.
  - `id = {project}-principle-{N}`; `title` = the principle title; `body` = title
    + explanation; `status = accepted`.
- **ADR status → atom status** mapping: `Accepted → accepted`, `Proposed →
  proposed`, `Superseded → superseded`, `Deprecated → deprecated`.
- `source.kind = repo-artifact`, `source.ref` = the file path (+ entry locator),
  `source.author = manuel` unless otherwise specified.
- `concepts` is emitted **empty** — concept extraction and linking belong to
  Phase 3 (SPEC-004). The adapter does not invent concepts.
- Integration: write produced atoms through `VaultWriter`; idempotent re-runs are
  inherited from SPEC-001 (structured IDs + `content_hash`).
- Unparseable artifact: skip it and record a warning; never crash the run.

## Scope — out (non-goals)

SPEC-file parsing · code-symbol extraction · any LLM call · Neo4j / embeddings ·
concept extraction or linking · conversation parsing · modifying `enigma_mcu/atom.py`
or `enigma_mcu/vault.py` (the adapter is purely additive; a genuine bug found
there is reported, not silently patched).

## Functional requirements

- **FR-1** Parse an ADR entry into a `decision` atom with `id = {project}-adr-{NNNN}`,
  `title` from the heading, `body` from the Decision section.
- **FR-2** Parse a Constitution principle into a `decision` atom with
  `id = {project}-principle-{N}`, `status = accepted`, `body` = title + explanation.
- **FR-3** Apply the ADR-status → atom-status mapping exactly; an unknown status
  is a parse warning (entry skipped), not a crash.
- **FR-4** Emit `concepts: []` for every atom.
- **FR-5** Produced atoms pass `Atom` validation (SPEC-001 FR-2) — provenance
  present, body non-empty, status in vocab.
- **FR-6** End-to-end through `VaultWriter` is idempotent: a re-run over unchanged
  artifacts writes byte-identical files and creates no duplicates; an edited ADR
  body updates its atom in place (new `content_hash` + `updated`, same `id`, same
  `created`).
- **FR-7** An unparseable or malformed artifact is skipped with a structured
  warning; the rest of the run completes.

## Harness contract (write these RED first — they ARE the definition of done)

- **T1** A single ADR fixture parses to the expected `decision` atom (golden):
  correct structured `id`, `title`, `body` (Decision only), mapped `status`,
  `concepts == []`.
- **T2** A Constitution fixture (several principles) parses to the expected atoms
  with `{project}-principle-{N}` IDs and `status == accepted`.
- **T3** (parametrized) ADR status mapping: each of Accepted / Proposed /
  Superseded / Deprecated maps to the right atom status; an unknown status is
  skipped with a warning.
- **T4** End-to-end idempotency: adapter → `VaultWriter` run twice over the same
  fixtures → byte-identical files, no duplicates; an edited ADR body → updated
  `content_hash` + `updated`, same `id`, same `created`.
- **T5** A malformed artifact in the set is skipped with a structured warning and
  does not prevent the valid artifacts from being written.
- **T6** Dogfood: running the adapter over the repo's own `CONSTITUTION.md`
  produces 12 principle atoms with IDs `enigma-mcu-principle-1` … `-12`.

## Dependencies

Python 3.12+, `pytest`, the SPEC-001 modules (`Atom`, `VaultWriter`), stdlib `re`.
No new heavy dependency. No network, no LLM.

## Definition of Done

T1–T6 GREEN on `main`; `enigma_mcu/adapters/spec_driven.py` implemented; fixtures
under `tests/fixtures/`; `enigma_mcu/atom.py` and `enigma_mcu/vault.py` unchanged.
No RED on `main`.
