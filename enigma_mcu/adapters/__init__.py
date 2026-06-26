"""Source adapters — deterministic and (later) LLM-based parsers that turn
repository artifacts and conversations into atoms for the vault.

Phase 1 ships the Spec-Driven adapter (SPEC-002): ADRs + Constitution principles.
"""

from enigma_mcu.adapters.spec_driven import (
    ARTIFACT_ADR_LOG,
    ARTIFACT_CONSTITUTION,
    ParseWarning,
    SpecDrivenAdapter,
)

__all__ = [
    "ARTIFACT_ADR_LOG",
    "ARTIFACT_CONSTITUTION",
    "ParseWarning",
    "SpecDrivenAdapter",
]
