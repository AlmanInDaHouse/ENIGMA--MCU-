"""The graph operation IR — a pure description of upserts, executed by nobody here.

`NodeOp` and `EdgeOp` are value types with MERGE-by-key semantics: a later
executor (SPEC-004) turns each into an idempotent Cypher MERGE. Keeping them as
plain, comparable dataclasses makes the mapping logic golden-file testable
without a database in the loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NodeOp:
    """Upsert a node `(label {key})` with `properties` (MERGE-by-key)."""

    label: str
    key: str
    properties: dict = field(default_factory=dict)


@dataclass
class EdgeOp:
    """Upsert a directed edge `(from_key)-[type]->(to_key)` (MERGE-by-endpoints)."""

    type: str
    from_key: str
    to_key: str
    properties: dict = field(default_factory=dict)
