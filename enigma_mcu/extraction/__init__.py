"""Concept extraction & normalization (SPEC-005) — the curation surface.

Extracts candidate concepts from atoms (LLM behind a port), normalizes them into
a canonical concept set with aliases (conservative embedding clustering), and
renders an inspectable dry-run report. Persists NOTHING to the vault or graph —
materialization of a curated set is a later SPEC (Constitution §11).
"""
