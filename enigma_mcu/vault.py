"""The idempotent vault writer and its inverse reader.

Serializes an `Atom` to a Markdown file (deterministic YAML frontmatter + body)
at `vault/{project}/{id}.md`, and parses such a file back into an `Atom`. The
vault is the single source of truth (Constitution §1); this module is the only
sanctioned way to materialize an atom on disk.

Idempotency (SPEC-001 FR-6): re-writing an atom whose body is unchanged leaves
the file byte-identical and creates no duplicate; a changed body updates `body`,
`content_hash`, and `updated` while preserving `created`.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

import yaml

from enigma_mcu.atom import Atom, Source, normalize_body

# Fixed frontmatter key order (SPEC-atom-schema §3 / SPEC-001 FR-5). The order is
# part of the contract: it keeps writes deterministic and diffs reviewable.
_FRONTMATTER_ORDER = (
    "id",
    "type",
    "title",
    "project",
    "source",
    "status",
    "confidence",
    "concepts",
    "relates_to",
    "supersedes",
    "superseded_by",
    "content_hash",
    "created",
    "updated",
    "tags",
    "artifact_ref",
)

_SOURCE_ORDER = ("kind", "ref", "author", "extracted_at")


def _today() -> str:
    return date.today().isoformat()


def _serialize(atom: Atom) -> str:
    """Render an atom to its canonical on-disk string (YAML frontmatter + body)."""
    frontmatter: dict[str, object] = {
        "id": atom.id,
        "type": atom.type,
        "title": atom.title,
        "project": atom.project,
        "source": {key: getattr(atom.source, key) for key in _SOURCE_ORDER},
        "status": atom.status,
        "confidence": atom.confidence,
        "concepts": list(atom.concepts),
        "relates_to": list(atom.relates_to),
        "supersedes": list(atom.supersedes),
        "superseded_by": list(atom.superseded_by),
        "content_hash": atom.content_hash,
        "created": atom.created,
        "updated": atom.updated,
        "tags": list(atom.tags),
        "artifact_ref": atom.artifact_ref,
    }
    # dicts preserve insertion order and we build them in _FRONTMATTER_ORDER, so
    # sort_keys=False yields the contract order without an OrderedDict dance.
    assert tuple(frontmatter) == _FRONTMATTER_ORDER  # guards against drift
    yaml_text = yaml.dump(
        frontmatter,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    return f"---\n{yaml_text}---\n\n{normalize_body(atom.body)}\n"


class VaultWriter:
    """Writes atoms into a vault root, idempotently."""

    def __init__(self, vault_root: str | Path, clock: Callable[[], str] | None = None):
        self.vault_root = Path(vault_root)
        self._clock = clock or _today

    def path_for(self, atom: Atom) -> Path:
        return self.vault_root / atom.project / f"{atom.id}.md"

    def write(self, atom: Atom) -> Path:
        """Materialize `atom`; return its path. See module docstring for idempotency."""
        path = self.path_for(atom)

        if path.exists():
            existing = read_atom(path)
            if existing.content_hash == atom.content_hash:
                # No semantic change: leave the file byte-identical, no rewrite.
                return path
            # Changed body: update in place, preserve the original creation date.
            atom.created = existing.created
            atom.updated = self._clock()
        else:
            now = self._clock()
            atom.created = atom.created or now
            atom.updated = now

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_serialize(atom), encoding="utf-8", newline="\n")
        return path


def read_atom(path: str | Path) -> Atom:
    """Parse a vault Markdown file back into an `Atom` (inverse of the writer)."""
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"not a vault atom file (missing frontmatter): {path}")

    # Split into ["", <frontmatter yaml>, <body>] on the first two `---` fences.
    _, frontmatter_block, body = text.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_block)
    source = Source(**{key: frontmatter["source"][key] for key in _SOURCE_ORDER})

    return Atom(
        id=frontmatter["id"],
        type=frontmatter["type"],
        title=frontmatter["title"],
        project=frontmatter["project"],
        source=source,
        status=frontmatter["status"],
        confidence=frontmatter["confidence"],
        body=body,
        concepts=frontmatter.get("concepts") or [],
        relates_to=frontmatter.get("relates_to") or [],
        supersedes=frontmatter.get("supersedes") or [],
        superseded_by=frontmatter.get("superseded_by") or [],
        created=_as_str(frontmatter.get("created")),
        updated=_as_str(frontmatter.get("updated")),
        tags=frontmatter.get("tags") or [],
        artifact_ref=frontmatter.get("artifact_ref"),
    )


def _as_str(value: object) -> str | None:
    """Coerce a YAML-decoded scalar to a string (PyYAML may decode dates)."""
    if value is None:
        return None
    return str(value)
