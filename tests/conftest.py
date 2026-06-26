"""Shared test helpers for the SPEC-001 harness.

`conftest.py` is auto-discovered by pytest; importing the factories from here
keeps every test building atoms the same way, so a test that mutates one field
isolates exactly that field as the cause of a failure.
"""

import os
from pathlib import Path

from enigma_mcu.atom import Atom, Source

FIXTURES = Path(__file__).parent / "fixtures"

# --- SPEC-004 integration: service-availability probes ----------------------
#
# SAFETY: ENIGMA's Neo4j defaults to bolt://localhost:7688 (its dedicated
# docker-compose port), NOT the standard 7687. Another project's Neo4j may bind
# 7687 on this machine; the integration tests must never read or write it. When
# ENIGMA's own Neo4j is down, the probe finds nothing on 7688 and the tests skip.

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "enigmatest")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
EMBED_MODEL = "bge-m3"


def neo4j_available() -> bool:
    """True only if ENIGMA's Neo4j (NEO4J_URI) accepts a connection. Never raises."""
    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), connection_timeout=3
        )
        try:
            driver.verify_connectivity()
            return True
        finally:
            driver.close()
    except Exception:
        return False


def ollama_model_available(model: str = EMBED_MODEL) -> bool:
    """True only if Ollama is reachable AND `model` is pulled. Never raises."""
    try:
        import requests

        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        resp.raise_for_status()
        names = [m.get("name", "") for m in resp.json().get("models", [])]
        return any(name == model or name.startswith(f"{model}:") for name in names)
    except Exception:
        return False


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
    Use when each write should see a distinct date (one value consumed per call).
    """

    def __init__(self, values):
        self._values = list(values)

    def __call__(self):
        return self._values.pop(0)


class MutableClock:
    """Returns a fixed "today" until reassigned — models a real wall clock.

    Multiple writes in the same run all see the same date; advance `now` to
    simulate a later run. Use when a run writes several files on the "same day".
    """

    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now
