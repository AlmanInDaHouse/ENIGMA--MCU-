"""Graph layer — the pure vault→graph mapping (SPEC-003) and, later, the live
Neo4j sync (SPEC-004).

SPEC-003 ships only infrastructure-free pieces: the operation IR (`ops`) and the
`GraphMapper`. No driver, no Cypher, no vector index here.
"""
