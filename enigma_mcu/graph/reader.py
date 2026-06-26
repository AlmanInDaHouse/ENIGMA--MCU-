"""VaultReader — enumerate a vault and route each note to its in-memory type.

Additive over SPEC-001: it reuses `read_atom` for atom notes and parses the
lightweight Concept/Project stub frontmatter itself. Routing is by frontmatter
`type`: atom types → `Atom`, `concept` → `ConceptStub`, `project` → `ProjectStub`,
anything else → skipped with a structured warning (FR-1). It never modifies
`vault.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from enigma_mcu.atom import ATOM_TYPES
from enigma_mcu.graph.mapper import ConceptStub, ProjectStub
from enigma_mcu.vault import read_atom


@dataclass(frozen=True)
class ReadWarning:
    """A vault note that could not be routed, with where and why."""

    path: str
    reason: str


@dataclass
class VaultContents:
    """The routed contents of a vault: atoms and the two stub classes."""

    atoms: list = field(default_factory=list)
    concepts: list = field(default_factory=list)
    projects: list = field(default_factory=list)


class VaultReader:
    """Reads a vault directory into routed objects; collects warnings."""

    def __init__(self):
        self.warnings: list[ReadWarning] = []

    def read(self, vault_root: str | Path) -> VaultContents:
        contents = VaultContents()
        for path in sorted(Path(vault_root).rglob("*.md")):
            frontmatter = self._frontmatter(path)
            note_type = frontmatter.get("type") if frontmatter else None

            if note_type in ATOM_TYPES:
                contents.atoms.append(read_atom(path))
            elif note_type == "concept":
                contents.concepts.append(
                    ConceptStub(
                        frontmatter["id"],
                        frontmatter.get("canonical", ""),
                        list(frontmatter.get("aliases") or []),
                    )
                )
            elif note_type == "project":
                contents.projects.append(
                    ProjectStub(
                        frontmatter["id"],
                        frontmatter.get("name", ""),
                        frontmatter.get("status", ""),
                        list(frontmatter.get("stack") or []),
                    )
                )
            else:
                self.warnings.append(
                    ReadWarning(str(path), f"unknown note type: {note_type!r}")
                )
        return contents

    @staticmethod
    def _frontmatter(path: Path) -> dict | None:
        text = Path(path).read_text(encoding="utf-8")
        if not text.startswith("---"):
            return None
        parts = text.split("---", 2)
        if len(parts) < 3:
            return None
        return yaml.safe_load(parts[1]) or {}
