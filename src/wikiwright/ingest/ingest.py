"""ingest_repo — the Scout entry point: resolve, clone, filter, chunk, store."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

from wikiwright.core.contracts import IngestResult
from wikiwright.ingest.chunker import chunk_text
from wikiwright.ingest.clone import ensure_repo
from wikiwright.ingest.filters import (
    EXCLUDED_DIRS,
    MAX_FILE_BYTES,
    detect_license,
    should_skip,
)
from wikiwright.ingest.source import resolve_source
from wikiwright.ingest.store import ChunkStore


def _lang_for(rel_path: str) -> str:
    if rel_path.endswith((".py", ".pyi")):
        return "python"
    if rel_path.endswith((".md", ".rst", ".txt")):
        return "text"
    return "code"


def ingest_repo(source: str, cache_dir: str | Path | None = None) -> IngestResult:
    """Ingest one repository into the chunk store; second run with no changes is free."""
    started = time.perf_counter()
    ref = resolve_source(source)
    cache = Path(cache_dir).expanduser() if cache_dir else Path(".cache/wikiwright")
    cache.mkdir(parents=True, exist_ok=True)
    repo_dir = ensure_repo(ref, cache)
    store = ChunkStore(cache / "ingest.db")

    license_family = detect_license(repo_dir)
    previous = store.file_hashes(ref.display)
    current: dict[str, str] = {}
    files_total = files_indexed = files_filtered = rechunked = 0

    for dirpath, dirnames, filenames in os.walk(repo_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            files_total += 1
            full = Path(dirpath) / filename
            rel = full.relative_to(repo_dir).as_posix()
            if should_skip(rel) is not None:
                files_filtered += 1
                continue
            try:
                data = full.read_bytes()
            except OSError:
                files_filtered += 1
                continue
            if b"\x00" in data[:8192] or len(data) > MAX_FILE_BYTES:
                files_filtered += 1
                continue
            digest = hashlib.sha256(data).hexdigest()
            current[rel] = digest
            files_indexed += 1
            if previous.get(rel) == digest:
                continue  # unchanged file: cache hit, zero re-chunk cost
            text = data.decode("utf-8", errors="replace")
            store.replace_file_chunks(
                ref.display, rel, digest, chunk_text(rel, text, _lang_for(rel))
            )
            rechunked += 1

    removed = set(previous) - set(current)
    for rel in removed:
        store.drop_file_chunks(ref.display, rel)

    store.save_source_meta(ref.display, str(repo_dir), license_family)
    chunks_total = store.count_chunks(ref.display)
    store.close()

    return IngestResult(
        source=ref.display,
        run_id=ref.slug,
        repo_dir=str(repo_dir),
        license_family=license_family,
        files_total=files_total,
        files_indexed=files_indexed,
        files_filtered=files_filtered,
        chunks=chunks_total,
        cache_hit=bool(previous) and rechunked == 0 and not removed,
        duration_s=round(time.perf_counter() - started, 3),
    )
