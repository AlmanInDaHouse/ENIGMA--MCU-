"""The extraction entry point: vault atoms → extraction → normalization → report.

Reads atoms from a vault via the existing `VaultReader` (read-only; does not
modify `vault.py`), runs the injected `ConceptExtractor` over each atom's
title+body, normalizes the candidates with the injected `Embedder`, and writes a
dry-run report OUTSIDE the vault. It persists nothing to the vault or graph — the
report is the only output (SPEC-005, Constitution §11).
"""

from __future__ import annotations

from pathlib import Path

from enigma_mcu.embeddings.port import Embedder
from enigma_mcu.extraction.llm_port import ConceptExtractor
from enigma_mcu.extraction.normalize import (
    DEFAULT_THRESHOLD,
    ConceptCandidate,
    ConceptNormalizer,
    NormalizationResult,
)
from enigma_mcu.extraction.report import ReportPaths, write_report
from enigma_mcu.graph.reader import VaultReader


def run_concept_extraction(
    vault_root: str | Path,
    extractor: ConceptExtractor,
    embedder: Embedder,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    report_dir: str | Path,
) -> tuple[NormalizationResult, ReportPaths]:
    """Extract → normalize → report. Returns the result and the written report paths."""
    atoms = VaultReader().read(vault_root).atoms

    candidates: list[ConceptCandidate] = []
    for atom in atoms:
        text = f"{atom.title}\n\n{atom.body}"
        for concept_text in extractor.extract_concepts(text):
            candidates.append(
                ConceptCandidate(text=concept_text, atom_id=atom.id, project=atom.project)
            )

    result = ConceptNormalizer(embedder, threshold=threshold).normalize(candidates)
    paths = write_report(result, report_dir)
    return result, paths
