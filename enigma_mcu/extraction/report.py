"""The dry-run report — the curation surface (SPEC-005 FR-6).

Renders the proposed concept set (canonical + aliases + members), the atom→concept
assignments, and confidences as both Markdown (for human review) and JSON (for
tooling), written to a directory the caller chooses — which must be OUTSIDE the
vault. This module only writes where told; the pipeline picks a non-vault path.
Nothing here touches the vault or graph.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from enigma_mcu.extraction.normalize import NormalizationResult

MARKDOWN_NAME = "concepts-report.md"
JSON_NAME = "concepts-report.json"


@dataclass(frozen=True)
class ReportPaths:
    markdown: Path
    json: Path


def _to_dict(result: NormalizationResult) -> dict:
    return {
        "concepts": [
            {
                "canonical": c.canonical,
                "aliases": c.aliases,
                "members": c.members,
                "confidence": c.confidence,
            }
            for c in result.concepts
        ],
        "assignments": [
            {
                "atom_id": a.atom_id,
                "project": a.project,
                "candidate": a.candidate,
                "concept": a.concept,
                "confidence": a.confidence,
            }
            for a in result.assignments
        ],
    }


def _to_markdown(result: NormalizationResult) -> str:
    lines = ["# Concept extraction — dry-run report", ""]
    lines.append(f"_Proposed concepts: {len(result.concepts)} · "
                 f"assignments: {len(result.assignments)}. Nothing is persisted._")
    lines.append("")

    lines.append("## Proposed concepts")
    lines.append("")
    for concept in sorted(result.concepts, key=lambda c: c.canonical):
        aliases = ", ".join(concept.aliases) if concept.aliases else "—"
        lines.append(f"### {concept.canonical}  ({concept.confidence})")
        lines.append(f"- aliases: {aliases}")
        lines.append(f"- members: {', '.join(concept.members)}")
        lines.append("")

    lines.append("## Atom → concept assignments")
    lines.append("")
    lines.append("| atom | project | candidate | concept | confidence |")
    lines.append("|---|---|---|---|---|")
    for a in result.assignments:
        lines.append(
            f"| {a.atom_id} | {a.project} | {a.candidate} | {a.concept} | {a.confidence} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_report(result: NormalizationResult, out_dir: str | Path) -> ReportPaths:
    """Write the Markdown + JSON dry-run report into `out_dir`. Returns the paths."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    markdown_path = out / MARKDOWN_NAME
    json_path = out / JSON_NAME
    markdown_path.write_text(_to_markdown(result), encoding="utf-8", newline="\n")
    json_path.write_text(
        json.dumps(_to_dict(result), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return ReportPaths(markdown=markdown_path, json=json_path)
