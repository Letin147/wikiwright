"""Shallow-clone a repository into the cache (mirror-aware), or reuse an existing clone."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from wikiwright.ingest.source import SourceRef


def ensure_repo(ref: SourceRef, cache_dir: Path, timeout_s: int = 600) -> Path:
    """Return a local directory holding the repository.

    Existing clones are reused as-is (refresh by deleting the cache dir and
    re-ingesting); local sources are indexed in place. Set WIKIWRIGHT_GIT_MIRROR
    (e.g. https://gh-proxy.com) to prefix clone URLs for restricted networks.
    """
    if ref.kind == "local":
        return Path(ref.raw).expanduser()
    repo_dir = cache_dir / "repos" / ref.slug
    if repo_dir.exists() and any(repo_dir.iterdir()):
        return repo_dir
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    url = ref.url or ""
    mirror = os.environ.get("WIKIWRIGHT_GIT_MIRROR", "").rstrip("/")
    if mirror:
        url = f"{mirror}/{url}"
    subprocess.run(
        ["git", "clone", "--depth", "1", "--quiet", url, str(repo_dir)],
        check=True,
        timeout=timeout_s,
        capture_output=True,
        text=True,
    )
    return repo_dir
