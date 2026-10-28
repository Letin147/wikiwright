"""Repository ingestion: clone (mirror-aware), filter, chunk, cache, FTS index (EXP-02)."""

from wikiwright.ingest.ingest import ingest_repo
from wikiwright.ingest.store import ChunkStore

__all__ = ["ChunkStore", "ingest_repo"]
