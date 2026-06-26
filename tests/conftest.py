"""Shared test helpers for the SPEC-001 harness.

`conftest.py` is auto-discovered by pytest; importing the factories from here
keeps every test building atoms the same way, so a test that mutates one field
isolates exactly that field as the cause of a failure.
"""

from pathlib import Path

from enigma_mcu.atom import Atom, Source

FIXTURES = Path(__file__).parent / "fixtures"


def make_source(**overrides):
    """A complete, valid provenance block; override any field to invalidate it."""
    base = dict(
        kind="repo-artifact",
        ref="CONSTITUTION.md#part-i",
        author="manuel",
        extracted_at="2026-06-26T10:00:00Z",
    )
    base.update(overrides)
    return Source(**base)


def make_atom(**overrides):
    """A valid `fact` atom; override any field (incl. `source`) to vary the case.

    `created`/`updated` default to None so the VaultWriter governs the dates.
    """
    base = dict(
        id="enigma-mcu-fact-0001",
        type="fact",
        title="The Markdown vault is the single source of truth",
        project="enigma-mcu",
        source=make_source(),
        status="current",
        confidence="high",
        body="The Markdown vault is the single source of truth.",
        concepts=["[[concept-contextual-memory]]"],
        relates_to=[],
        supersedes=[],
        superseded_by=[],
        created=None,
        updated=None,
        tags=[],
        artifact_ref=None,
    )
    base.update(overrides)
    return Atom(**base)


class StubClock:
    """Returns the next canned date string per call; raises if drained.

    Lets a test assert exactly when the writer stamps `created`/`updated`.
    """

    def __init__(self, values):
        self._values = list(values)

    def __call__(self):
        return self._values.pop(0)
