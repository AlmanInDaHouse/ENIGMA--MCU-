"""The Atom model — the in-memory form of a self-contained assertion.

Mirrors `docs/SPEC-atom-schema.md` §3 (the on-disk contract) and implements the
functional requirements of SPEC-001: schema validation, deterministic identity,
and a `content_hash` over the normalized body.

An atom is a single claim with mandatory provenance (Constitution §2, §3). This
module holds no I/O; serialization to the vault lives in `enigma_mcu.vault`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

# --- Schema vocabularies (SPEC-atom-schema §1, §3) --------------------------

# type -> the closed set of statuses that type may carry.
STATUS_VOCABULARY: dict[str, frozenset[str]] = {
    "decision": frozenset({"proposed", "accepted", "superseded", "deprecated"}),
    "fact": frozenset({"current", "outdated"}),
    "idea": frozenset({"raw", "explored", "promoted", "discarded"}),
    "open_question": frozenset({"open", "resolved"}),
}

ATOM_TYPES: frozenset[str] = frozenset(STATUS_VOCABULARY)

CONFIDENCE_VALUES: frozenset[str] = frozenset({"high", "low"})

# Length of the short hash in a generated (unstructured) id, e.g. `idea-3f9c1a`.
SHORT_HASH_LEN = 6


class AtomValidationError(ValueError):
    """Raised when an atom violates the schema contract (SPEC-001 FR-2)."""


def normalize_body(body: str) -> str:
    """Canonical body form for hashing and storage (SPEC-001 FR-3).

    LF newlines, trailing spaces collapsed per line, outer whitespace stripped.
    Logically identical bodies normalize identically; real edits differ.
    """
    text = body.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def _content_hash(body: str) -> str:
    return hashlib.sha256(normalize_body(body).encode("utf-8")).hexdigest()


def hashed_id(atom_type: str, body: str, source_ref: str) -> str:
    """Deterministic id for unstructured atoms (SPEC-atom-schema §4, FR-4).

    `{type}-{short_hash(normalize(body) + source_ref)}`. A real content change or
    a different source ref yields a different id; whitespace variants do not.
    """
    digest = hashlib.sha256(
        (normalize_body(body) + source_ref).encode("utf-8")
    ).hexdigest()
    return f"{atom_type}-{digest[:SHORT_HASH_LEN]}"


@dataclass
class Source:
    """Provenance block (Constitution §3 — all fields mandatory)."""

    kind: str  # repo-artifact | conversation | document
    ref: str  # path | chat-id+range | doc#section
    author: str  # manuel | fran | claude | n/a
    extracted_at: str  # ISO-8601 timestamp


@dataclass
class Atom:
    """A single self-contained assertion plus its frontmatter and body.

    Construction validates the atom and derives `content_hash`; an invalid atom
    cannot be constructed. `created`/`updated` are governed by the VaultWriter
    and default to None on a bare in-memory atom.
    """

    id: str
    type: str
    title: str
    project: str
    source: Source
    status: str
    confidence: str
    body: str
    concepts: list[str] = field(default_factory=list)
    relates_to: list[str] = field(default_factory=list)
    supersedes: list[str] = field(default_factory=list)
    superseded_by: list[str] = field(default_factory=list)
    content_hash: str | None = None
    created: str | None = None
    updated: str | None = None
    tags: list[str] = field(default_factory=list)
    artifact_ref: str | None = None

    def __post_init__(self) -> None:
        # Canonicalize the body first so validation and hashing see one form.
        self.body = normalize_body(self.body)
        self.validate()
        self.content_hash = _content_hash(self.body)

    def validate(self) -> None:
        """Enforce the schema contract; raise AtomValidationError on violation."""
        if self.type not in ATOM_TYPES:
            raise AtomValidationError(f"unknown atom type: {self.type!r}")

        if not self.title or not self.title.strip():
            raise AtomValidationError("title must be non-empty")

        if not self.body or not self.body.strip():
            raise AtomValidationError("body must be non-empty")

        if not self.project or not self.project.strip():
            raise AtomValidationError("project must be non-empty")

        allowed = STATUS_VOCABULARY[self.type]
        if self.status not in allowed:
            raise AtomValidationError(
                f"status {self.status!r} is not valid for type {self.type!r}; "
                f"allowed: {sorted(allowed)}"
            )

        if self.confidence not in CONFIDENCE_VALUES:
            raise AtomValidationError(
                f"confidence {self.confidence!r} must be one of {sorted(CONFIDENCE_VALUES)}"
            )

        self._validate_provenance()

    def _validate_provenance(self) -> None:
        src = self.source
        if src is None:
            raise AtomValidationError("source (provenance) is mandatory")
        for attr in ("kind", "ref", "author"):
            value = getattr(src, attr, None)
            if not value or not str(value).strip():
                raise AtomValidationError(f"source.{attr} is mandatory")
