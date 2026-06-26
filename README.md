# ENIGMA-MCU

Unified, atomic, shared contextual-memory engine. See `CONSTITUTION.md` for the
invariants and `docs/ROADMAP.md` for the phase map.

Phase 1 delivers the in-memory **Atom** model and the **idempotent vault writer**
(`enigma_mcu/atom.py`, `enigma_mcu/vault.py`) per
`docs/specs/SPEC-001-atom-model-and-vault-writer.md`.

## Requirements

- Python 3.12+
- `pyyaml`

## Install (dev)

```bash
python -m pip install -e ".[dev]"
```

`pyyaml` and `pytest` are the only runtime/test dependencies.

## Run the tests

```bash
python -m pytest
```

The test suite (`tests/`) is the contract: it encodes SPEC-001's harness
(T1–T7). Code is "done" only when the harness is GREEN.
