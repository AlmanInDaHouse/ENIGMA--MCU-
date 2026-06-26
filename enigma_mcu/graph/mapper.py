"""The vault→graph mapper — pure, deterministic translation to the op IR.

Turns an `Atom` (an Item) and the Concept/Project stub notes into a list of
`NodeOp`/`EdgeOp` upserts, and attaches a 1024-dim embedding of `title + body`
from an injected `Embedder`. No database, no model, no network: the logic that is
easy to get wrong — which edge type, which direction, which target — is isolated
here and fully unit-testable (SPEC-003 Context).

Determinism is a contract (FR-6): the same input always yields the same op list,
in the same order, so MERGE-by-key execution is idempotent downstream.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from enigma_mcu.atom import Atom
from enigma_mcu.embeddings.port import Embedder
from enigma_mcu.graph.ops import EdgeOp, NodeOp

_WIKILINK = re.compile(r"^\s*\[\[(?P<target>.+?)\]\]\s*$")


def parse_wikilink(value: str) -> str:
    """`[[id]]` → `id`; `[[id|alias]]` → `id`; a bare value is returned trimmed."""
    match = _WIKILINK.match(value)
    target = match.group("target") if match else value
    return target.split("|", 1)[0].strip()


def parse_wikilinks(values: Iterable[str] | None) -> list[str]:
    """Parse a list of wikilink values, skipping empty/None entries."""
    return [parse_wikilink(v) for v in (values or []) if v]


@dataclass
class ConceptStub:
    """A Concept note (the cross-project join): canonical name + aliases."""

    id: str
    canonical: str
    aliases: list[str] = field(default_factory=list)


@dataclass
class ProjectStub:
    """A Project MOC note: display name, lifecycle status, tech stack."""

    id: str
    name: str
    status: str
    stack: list[str] = field(default_factory=list)


class GraphMapper:
    """Maps atoms and stubs to graph ops, embedding via the injected `Embedder`."""

    def __init__(self, embedder: Embedder):
        self._embedder = embedder

    # --- atoms (Items) ------------------------------------------------------

    def map_atom(self, atom: Atom) -> list:
        """Map one Item atom to its Item node, relationship edges, and edge stubs."""
        item = atom.id
        ops: list = [self._item_node(atom)]

        # BELONGS_TO its primary project (+ a MERGE-stub for the Project node).
        project_key = f"project-{atom.project}"
        ops.append(NodeOp("Project", project_key))
        ops.append(EdgeOp("BELONGS_TO", item, project_key))

        # ABOUT each concept (the cross-project join) (+ Concept MERGE-stubs).
        for concept_id in parse_wikilinks(atom.concepts):
            ops.append(NodeOp("Concept", concept_id))
            ops.append(EdgeOp("ABOUT", item, concept_id))

        # Item-to-Item edges — targets are other Items, so no stub is created.
        for target in parse_wikilinks(atom.relates_to):
            ops.append(EdgeOp("RELATES_TO", item, target))
        for target in parse_wikilinks(atom.supersedes):
            ops.append(EdgeOp("SUPERSEDES", item, target))
        # superseded_by is the reverse of SUPERSEDES: the other Item supersedes this.
        for target in parse_wikilinks(atom.superseded_by):
            ops.append(EdgeOp("SUPERSEDES", target, item))

        # AUTHORED_BY its provenance author (+ a Person MERGE-stub).
        person_key = f"person-{atom.source.author}"
        ops.append(NodeOp("Person", person_key))
        ops.append(EdgeOp("AUTHORED_BY", item, person_key))

        return ops

    def _item_node(self, atom: Atom) -> NodeOp:
        embedding = self._embedder.embed(f"{atom.title}\n\n{atom.body}")
        return NodeOp(
            "Item",
            atom.id,
            {
                "id": atom.id,
                "type": atom.type,
                "title": atom.title,
                "body": atom.body,
                "status": atom.status,
                "confidence": atom.confidence,
                "project": atom.project,
                "source_kind": atom.source.kind,
                "source_ref": atom.source.ref,
                "source_author": atom.source.author,
                "content_hash": atom.content_hash,
                "created": atom.created,
                "updated": atom.updated,
                "embedding": embedding,
            },
        )

    # --- stubs --------------------------------------------------------------

    def map_concept(self, stub: ConceptStub) -> NodeOp:
        return NodeOp(
            "Concept",
            stub.id,
            {"canonical": stub.canonical, "aliases": list(stub.aliases)},
        )

    def map_project(self, stub: ProjectStub) -> NodeOp:
        return NodeOp(
            "Project",
            stub.id,
            {"name": stub.name, "status": stub.status, "stack": list(stub.stack)},
        )

    # --- collections --------------------------------------------------------

    def map_vault(
        self,
        atoms: Sequence[Atom],
        concepts: Sequence[ConceptStub] = (),
        projects: Sequence[ProjectStub] = (),
    ) -> list:
        """Map a set of atoms plus Concept/Project stubs into one op list.

        Order is deterministic: all atoms (in order), then concepts, then projects.
        """
        ops: list = []
        for atom in atoms:
            ops.extend(self.map_atom(atom))
        for concept in concepts:
            ops.append(self.map_concept(concept))
        for project in projects:
            ops.append(self.map_project(project))
        return ops
