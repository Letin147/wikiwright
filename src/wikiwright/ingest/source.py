"""Resolve a source string (GitHub URL / owner-name / local path) into a SourceRef."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_GITHUB_RE = re.compile(
    r"^(?:https?://)?(?:www\.)?github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.IGNORECASE
)
_SHORT_RE = re.compile(r"^([\w.-]+)/([\w.-]+?)(?:\.git)?$")


@dataclass(frozen=True)
class SourceRef:
    """Normalized description of the thing to ingest."""

    raw: str
    kind: str  # "url" | "local"
    url: str | None
    slug: str  # cache dir name: owner__name or local dir name
    display: str  # canonical id used in the store: owner/name or abs path


def _from_github(raw: str, owner: str, name: str) -> SourceRef:
    url = f"https://github.com/{owner}/{name}.git"
    return SourceRef(raw, "url", url, f"{owner}__{name}", f"{owner}/{name}")


def resolve_source(raw: str) -> SourceRef:
    """Accept 'https://github.com/o/n(.git)', 'o/n', or an existing local directory."""
    raw = raw.strip()
    gh = _GITHUB_RE.match(raw)
    if gh:
        return _from_github(raw, gh.group(1), gh.group(2))
    candidate = Path(raw).expanduser()
    if candidate.is_dir():
        return SourceRef(raw, "local", None, candidate.name, str(candidate.resolve()))
    short = _SHORT_RE.match(raw)
    if short and "/" in raw:
        return _from_github(raw, short.group(1), short.group(2))
    raise ValueError(f"unrecognized source: {raw!r} (GitHub URL, owner/name, or local dir)")
