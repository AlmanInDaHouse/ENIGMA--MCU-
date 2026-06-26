"""The Spec-Driven adapter — deterministic, no-LLM extraction (SPEC-002).

Parses two structured repo artifacts into `decision` atoms:

* **ADR entries** in the ADR-log format (`## ADR-NNNN — Title`, `**Status:**`,
  `**Decision:**`, …) → one atom each, body = the Decision text.
* **Constitution principles** (`**N. Title.**` + explanation) → one atom each,
  `status = accepted`, body = title + explanation.

Determinism is the point: predictable artifacts yield predictable, golden-file
testable atoms (SPEC-002 Context). Concept extraction is *not* done here — every
atom is emitted with `concepts == []` (Phase 3 / SPEC-004 owns that). The adapter
is purely additive over SPEC-001's `Atom`/`VaultWriter` and never mutates them.

Robustness contract: a malformed entry is skipped with a structured warning; a
malformed or unreadable file is skipped with a structured warning; the run always
completes (SPEC-002 FR-3, FR-7).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from enigma_mcu.atom import Atom, AtomValidationError, Source

# --- Artifact kinds ---------------------------------------------------------

ARTIFACT_ADR_LOG = "adr-log"
ARTIFACT_CONSTITUTION = "constitution"

# ADR status (as written) -> atom status vocabulary (SPEC-002 FR-3).
ADR_STATUS_MAP = {
    "Accepted": "accepted",
    "Proposed": "proposed",
    "Superseded": "superseded",
    "Deprecated": "deprecated",
}

# `## ADR-0001 — Title`  (em-dash, en-dash, or hyphen separator tolerated).
_ADR_HEADING = re.compile(r"^##\s+ADR-(\d+)\s*[—–-]\s*(.+?)\s*$", re.MULTILINE)

# `**1. Title.**` on its own line.
_PRINCIPLE_HEADING = re.compile(r"^\*\*(\d+)\.\s+(.+?)\*\*\s*$", re.MULTILINE)

# A structural break that ends a principle's explanation.
_STRUCTURAL_BREAK = re.compile(r"^\s*---\s*$|^##\s")


@dataclass(frozen=True)
class ParseWarning:
    """A skipped entry or artifact, with where and why (SPEC-002 FR-7)."""

    ref: str
    reason: str


def _extract_field(block: str, label: str) -> str | None:
    """Return the text of `**Label:**` in `block`, up to the next field/break."""
    pattern = re.compile(
        r"\*\*" + re.escape(label) + r":\*\*\s*"
        r"(.*?)(?=\n\s*\*\*[A-Z][\w ]*:\*\*|\n\s*---\s*\n|\Z)",
        re.DOTALL,
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else None


class SpecDrivenAdapter:
    """Parses structured artifacts into atoms; collects warnings on `self.warnings`."""

    def __init__(
        self,
        project: str = "enigma-mcu",
        author: str = "manuel",
        extracted_at: str = "2026-06-26T00:00:00Z",
    ):
        self.project = project
        self.author = author
        self.extracted_at = extracted_at
        self.warnings: list[ParseWarning] = []

    # --- public entry points ------------------------------------------------

    def parse(self, artifacts: Iterable[tuple]) -> list[Atom]:
        """Parse a set of `(path, kind)` or `(path, kind, source_ref)` artifacts.

        A failing artifact is skipped with a warning; the rest still parse.
        """
        atoms: list[Atom] = []
        for artifact in artifacts:
            path, kind = artifact[0], artifact[1]
            source_ref = artifact[2] if len(artifact) > 2 else str(path)
            try:
                atoms.extend(self.parse_file(path, kind, source_ref=source_ref))
            except Exception as exc:  # never let one artifact crash the run
                self._warn(source_ref, f"failed to parse artifact: {exc}")
        return atoms

    def parse_file(
        self, path: str | Path, kind: str, source_ref: str | None = None
    ) -> list[Atom]:
        """Read `path` and parse it according to `kind`."""
        path = Path(path)
        ref = source_ref if source_ref is not None else str(path)
        text = path.read_text(encoding="utf-8")

        warnings_before = len(self.warnings)
        if kind == ARTIFACT_ADR_LOG:
            atoms = self.parse_adr_text(text, ref)
        elif kind == ARTIFACT_CONSTITUTION:
            atoms = self.parse_constitution_text(text, ref)
        else:
            self._warn(ref, f"unknown artifact kind: {kind!r}")
            return []

        # A file that yields nothing and raised no entry-level warning is itself
        # malformed for its declared kind — record that (SPEC-002 FR-7 / T5).
        if not atoms and len(self.warnings) == warnings_before:
            self._warn(ref, f"no parseable {kind} entries found")
        return atoms

    # --- ADR parsing --------------------------------------------------------

    def parse_adr_text(self, text: str, source_ref: str) -> list[Atom]:
        """Parse all ADR entries in `text` into `decision` atoms."""
        atoms: list[Atom] = []
        headings = list(_ADR_HEADING.finditer(text))
        for index, heading in enumerate(headings):
            number, title = heading.group(1), heading.group(2).strip()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            block = text[heading.end():end]
            entry_ref = f"{source_ref}#ADR-{number}"

            atom = self._adr_atom(number, title, block, entry_ref)
            if atom is not None:
                atoms.append(atom)
        return atoms

    def _adr_atom(
        self, number: str, title: str, block: str, entry_ref: str
    ) -> Atom | None:
        raw_status = _extract_field(block, "Status")
        if raw_status is None:
            self._warn(entry_ref, "ADR entry has no Status field")
            return None
        raw_status = raw_status.splitlines()[0].strip()

        atom_status = ADR_STATUS_MAP.get(raw_status)
        if atom_status is None:
            self._warn(entry_ref, f"unknown ADR status: {raw_status!r}")
            return None

        decision = _extract_field(block, "Decision")
        if not decision:
            self._warn(entry_ref, "ADR entry has no Decision field")
            return None

        return self._build_atom(
            atom_id=f"{self.project}-adr-{number}",
            title=title,
            body=decision,
            status=atom_status,
            entry_ref=entry_ref,
        )

    # --- Constitution parsing ----------------------------------------------

    def parse_constitution_text(self, text: str, source_ref: str) -> list[Atom]:
        """Parse all numbered principles in `text` into `decision` atoms."""
        atoms: list[Atom] = []
        headings = list(_PRINCIPLE_HEADING.finditer(text))
        for index, heading in enumerate(headings):
            number, title = heading.group(1), heading.group(2).strip()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            raw_explanation = text[heading.end():end]
            explanation = self._clean_explanation(raw_explanation)
            entry_ref = f"{source_ref}#principle-{number}"

            body = title if not explanation else f"{title}\n\n{explanation}"
            atom = self._build_atom(
                atom_id=f"{self.project}-principle-{number}",
                title=title,
                body=body,
                status="accepted",
                entry_ref=entry_ref,
            )
            if atom is not None:
                atoms.append(atom)
        return atoms

    @staticmethod
    def _clean_explanation(raw: str) -> str:
        lines: list[str] = []
        for line in raw.splitlines():
            if _STRUCTURAL_BREAK.match(line):
                break
            lines.append(line)
        return "\n".join(lines).strip()

    # --- shared --------------------------------------------------------------

    def _build_atom(
        self, atom_id: str, title: str, body: str, status: str, entry_ref: str
    ) -> Atom | None:
        try:
            return Atom(
                id=atom_id,
                type="decision",
                title=title,
                project=self.project,
                source=Source(
                    kind="repo-artifact",
                    ref=entry_ref,
                    author=self.author,
                    extracted_at=self.extracted_at,
                ),
                status=status,
                confidence="high",
                body=body,
                concepts=[],  # SPEC-002 FR-4 — no concept extraction here
            )
        except AtomValidationError as exc:
            self._warn(entry_ref, f"produced an invalid atom: {exc}")
            return None

    def _warn(self, ref: str, reason: str) -> None:
        self.warnings.append(ParseWarning(ref=ref, reason=reason))
