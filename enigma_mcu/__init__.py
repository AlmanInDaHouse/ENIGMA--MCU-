"""ENIGMA-MCU — unified atomic contextual-memory engine.

Phase 1 surface: the in-memory Atom model and the idempotent vault writer.
"""

from enigma_mcu.atom import Atom, AtomValidationError, Source, hashed_id, normalize_body
from enigma_mcu.vault import VaultWriter, read_atom

__all__ = [
    "Atom",
    "AtomValidationError",
    "Source",
    "hashed_id",
    "normalize_body",
    "VaultWriter",
    "read_atom",
]
