"""SyncService — the end-to-end vault → Neo4j sync (SPEC-004).

Wires the pieces: `VaultReader` routes the vault, `GraphMapper` (with an injected
`Embedder`) turns its contents into the op IR, and `Neo4jExecutor` MERGEs that IR
into the graph. Idempotent by construction (FR-6): the mapping is deterministic
and the executor MERGEs, so a re-sync over an unchanged vault changes no counts.

Defaults wire the real backends (bge-m3 + Neo4j on ENIGMA's dedicated port); tests
inject a `FakeEmbedder` and a pointed executor.
"""

from __future__ import annotations

from pathlib import Path

from enigma_mcu.embeddings.bge_m3 import BgeM3Embedder
from enigma_mcu.embeddings.port import Embedder
from enigma_mcu.graph.mapper import GraphMapper
from enigma_mcu.graph.neo4j_executor import Neo4jExecutor
from enigma_mcu.graph.reader import VaultContents, VaultReader


class SyncService:
    """Sync a vault directory into Neo4j through the mapper and executor."""

    def __init__(
        self,
        reader: VaultReader | None = None,
        embedder: Embedder | None = None,
        executor: Neo4jExecutor | None = None,
    ):
        self._reader = reader or VaultReader()
        self._embedder = embedder or BgeM3Embedder()
        self._executor = executor or Neo4jExecutor()

    def sync(self, vault_root: str | Path) -> VaultContents:
        """Read the vault, map it, ensure schema, and execute. Returns what was read."""
        contents = self._reader.read(vault_root)
        ops = GraphMapper(self._embedder).map_vault(
            contents.atoms, concepts=contents.concepts, projects=contents.projects
        )
        self._executor.ensure_schema()
        self._executor.execute(ops)
        return contents
