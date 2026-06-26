"""ConceptNormalizer — conservative embedding clustering of candidate concepts.

Candidate strings (each tied to its source atom) are clustered by cosine
similarity above a **conservative threshold** (default high — only near-identical
merge, FR-4). Per cluster: a deterministic canonical name (the most frequent
candidate, ties broken by shortest-then-lexicographic), the rest as aliases. The
result is the canonical concept set plus per-atom assignments, each carrying a
confidence (FR-5). Pure and deterministic given the embeddings — it persists
nothing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from enigma_mcu.embeddings.port import Embedder

# Conservative by design: only near-identical candidates merge (FR-4).
DEFAULT_THRESHOLD = 0.92
# A merge is "high" confidence only if every member clears threshold + this margin.
DEFAULT_CONFIDENCE_MARGIN = 0.05


@dataclass(frozen=True)
class ConceptCandidate:
    """A raw candidate concept string and the atom it was extracted from."""

    text: str
    atom_id: str
    project: str


@dataclass
class NormalizedConcept:
    """A canonical concept with its aliases and member candidate texts."""

    canonical: str
    aliases: list[str] = field(default_factory=list)
    members: list[str] = field(default_factory=list)
    confidence: str = "high"


@dataclass
class ConceptAssignment:
    """A candidate's mapping to the canonical concept it normalized into."""

    atom_id: str
    project: str
    candidate: str
    concept: str
    confidence: str


@dataclass
class NormalizationResult:
    concepts: list[NormalizedConcept] = field(default_factory=list)
    assignments: list[ConceptAssignment] = field(default_factory=list)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class ConceptNormalizer:
    """Clusters candidate concepts by embedding cosine similarity."""

    def __init__(
        self,
        embedder: Embedder,
        threshold: float = DEFAULT_THRESHOLD,
        confidence_margin: float = DEFAULT_CONFIDENCE_MARGIN,
    ):
        self._embedder = embedder
        self._threshold = threshold
        self._confidence_margin = confidence_margin

    def normalize(self, candidates: list[ConceptCandidate]) -> NormalizationResult:
        texts = [c.text for c in candidates]
        counts = {text: texts.count(text) for text in texts}
        embeddings = {text: self._embedder.embed(text) for text in counts}

        # Process unique texts most-frequent-first (ties: shortest, then lexical),
        # so each cluster's seed — its canonical — is its most frequent member.
        ordered = sorted(counts, key=lambda t: (-counts[t], len(t), t))

        clusters: list[dict] = []  # {canonical, members: set[str]}
        for text in ordered:
            best, best_sim = None, self._threshold
            for cluster in clusters:
                sim = _cosine(embeddings[text], embeddings[cluster["canonical"]])
                if sim >= best_sim:
                    best, best_sim = cluster, sim
            if best is None:
                clusters.append({"canonical": text, "members": {text}})
            else:
                best["members"].add(text)

        concepts = [self._build_concept(c, embeddings) for c in clusters]
        member_to_canonical = {
            member: cluster["canonical"]
            for cluster in clusters
            for member in cluster["members"]
        }
        assignments = [
            self._build_assignment(candidate, member_to_canonical, embeddings)
            for candidate in candidates
        ]
        return NormalizationResult(concepts=concepts, assignments=assignments)

    def _build_concept(self, cluster: dict, embeddings: dict) -> NormalizedConcept:
        canonical = cluster["canonical"]
        members = sorted(cluster["members"])
        aliases = [m for m in members if m != canonical]
        confidence = self._cluster_confidence(canonical, cluster["members"], embeddings)
        return NormalizedConcept(
            canonical=canonical, aliases=aliases, members=members, confidence=confidence
        )

    def _cluster_confidence(self, canonical: str, members: set, embeddings: dict) -> str:
        others = [m for m in members if m != canonical]
        if not others:
            return "high"  # singleton: exactly what the extractor proposed
        worst = min(_cosine(embeddings[m], embeddings[canonical]) for m in others)
        return "high" if worst >= self._threshold + self._confidence_margin else "low"

    def _build_assignment(
        self, candidate: ConceptCandidate, member_to_canonical: dict, embeddings: dict
    ) -> ConceptAssignment:
        canonical = member_to_canonical[candidate.text]
        if candidate.text == canonical:
            confidence = "high"
        else:
            sim = _cosine(embeddings[candidate.text], embeddings[canonical])
            confidence = "high" if sim >= self._threshold + self._confidence_margin else "low"
        return ConceptAssignment(
            atom_id=candidate.atom_id,
            project=candidate.project,
            candidate=candidate.text,
            concept=canonical,
            confidence=confidence,
        )
