# SPEC-005 — Concept Extraction & Normalization

| | |
|---|---|
| **ID** | SPEC-005 |
| **Phase** | 3 — Cross-project |
| **Status** | Active |
| **Depends on** | CONSTITUTION, SPEC-atom-schema, SPEC-001, SPEC-003 (Embedder port) |
| **Session** | SESSION-005 |

## Context

The first step of the make-or-break phase. It extracts candidate concepts from
atoms (LLM, behind a port) and normalizes them into a canonical concept set with
aliases (embedding clustering, conservative). It deliberately **produces an
inspectable concept set and does not persist anything** — no vault writes, no
graph edges. The reason is curation (Constitution §11): the quality of concept
extraction determines whether the cross-project graph is useful, so it must be
**reviewed and tuned before any concept is committed**. Materialization to the
vault and graph is a separate SPEC that runs only on a curated set.

The LLM lives behind a port so the provider is a swappable adapter — OpenRouter
now, local Ollama later, by config.

## Scope — in

- **`ConceptExtractor` port** (`enigma_mcu/extraction/llm_port.py`):
  `extract_concepts(text: str) -> list[str]` returning candidate concept strings.
  Plus a deterministic `FakeConceptExtractor` for unit tests.
- **`OpenRouterConceptExtractor`** (`enigma_mcu/extraction/openrouter.py`):
  implements the port via OpenRouter's OpenAI-compatible endpoint. Model slug,
  base URL, and key from env (`OPENROUTER_API_KEY`, `OPENROUTER_MODEL`,
  `OPENROUTER_BASE_URL`). Disables provider retention on the request; supports a
  `max_price` cap. Parses a structured concept list from the response.
- **`ConceptNormalizer`** (`enigma_mcu/extraction/normalize.py`): given candidate
  concepts (each tied to its source atom) and an injected `Embedder`, cluster by
  cosine similarity above a **conservative threshold** (config, default high — only
  near-identical merge), pick a canonical name per cluster, collect the rest as
  aliases. Produces the canonical `Concept` set + per-atom concept assignments,
  each with a `confidence`.
- **Dry-run report** (`enigma_mcu/extraction/report.py`): render the proposed
  concept set (canonical, aliases, member candidates), the atom→concept
  assignments, and confidences as an **inspectable artifact** (markdown + JSON)
  written to a report path **outside the vault**. This is the curation surface.
- An entry point that runs extraction over a vault's atoms → normalization →
  report. (Reads atoms via the existing `read_atom`; does not modify `vault.py`.)

## Scope — out (non-goals)

Writing Concept stubs to the vault · updating atom frontmatter `concepts` · graph
`ABOUT` edges · RELATES_TO linking · per-source routing (orchestration) · the
local Ollama extractor (a later config swap) · modifying `atom.py`, `vault.py`,
`mapper.py`, `ops.py`, `port.py`, the adapter, or the sync.

## Functional requirements

- **FR-1** `ConceptExtractor.extract_concepts` returns a list of candidate concept
  strings; `FakeConceptExtractor` is deterministic.
- **FR-2** `OpenRouterConceptExtractor` calls the OpenAI-compatible endpoint with
  the configured model, sends the retention-off flag, and parses a structured
  concept list; missing `OPENROUTER_API_KEY` raises a clear configuration error.
- **FR-3** `ConceptNormalizer` clusters candidates by cosine similarity above the
  configured threshold; below it, candidates stay distinct. Canonical selection
  and alias collection are deterministic given the embeddings.
- **FR-4** The default threshold is conservative (near-identical only); it is a
  single config value (the normalization-aggressiveness dial).
- **FR-5** Each proposed concept and assignment carries a `confidence`.
- **FR-6** The dry-run report lists proposed concepts (canonical + aliases +
  members), atom→concept assignments, and confidences, and is written outside the
  vault. Nothing is written into the vault or graph.

## Harness contract (write these RED first — they ARE the definition of done)

**Unit (no infrastructure, no API — must pass everywhere):**

- **T1** `FakeConceptExtractor` is deterministic and returns candidates for sample
  atom text.
- **T2** `ConceptNormalizer` with controlled fake embeddings: near-identical
  candidates (similarity ≥ threshold) merge into one canonical concept with the
  others as aliases; dissimilar candidates stay separate. Canonical + aliases are
  the expected values (golden).
- **T3** Threshold behavior: lowering/raising the configured threshold changes
  merging as expected (the dial works).
- **T4** Cross-project assignment: two atoms from different projects whose
  candidates normalize to the same concept both map to that one concept (the join,
  at the assignment level).
- **T5** Report generation: the dry-run report contains the expected concepts,
  aliases, assignments, and confidences, and writes outside the vault; the vault
  is untouched (assert no new vault files).

**Integration (`@pytest.mark.integration`, skip when `OPENROUTER_API_KEY` absent;
keep minimal — it costs tokens):**

- **T6** `OpenRouterConceptExtractor` returns a sane, non-empty concept list for a
  sample atom against the real configured model.
- **T7** End-to-end on a few real atoms: extraction (real model) → normalization
  (real bge-m3) → a report whose concepts are inspectably reasonable.

## Dependencies

Python 3.12+, `pytest`, an HTTP client (`httpx`/`requests`), the SPEC-001/003
modules (`read_atom`, `Embedder`). Integration requires an OpenRouter key (and the
local Ollama bge-m3 already used in Phase 2).

## Definition of Done

T1–T5 GREEN everywhere; T6–T7 GREEN locally with a key present (skipped, not red,
where absent); the vault and graph are untouched by this SPEC; prior suites still
GREEN; `main` not red under `pytest -m "not integration"`.

## Curation gate (why this SPEC stops at a report)

When this loop lands, the owner runs the extractor over real repos and **reviews
the report** — tuning the threshold and the extraction prompt until the concept
set is good. Only then does the next SPEC materialize a curated set into the vault
and graph. Do not skip the human review; it is the point of stopping here.
