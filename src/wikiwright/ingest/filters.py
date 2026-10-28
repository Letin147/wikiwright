"""Decide which files enter the index: vendor/tests/binaries out, license precheck in."""

from __future__ import annotations

import re
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules", "vendor",
    "site-packages", "dist", "build", ".mypy_cache", ".pytest_cache", ".tox", ".eggs",
    ".cache", ".github", ".idea", ".vscode",
}

TEXT_EXTS = {
    ".py", ".pyi", ".md", ".rst", ".txt", ".toml", ".cfg", ".ini", ".yml", ".yaml",
    ".json", ".sh", ".bash", ".ps1", ".js", ".ts", ".tsx", ".jsx", ".html", ".css",
    ".c", ".h", ".cpp", ".hpp", ".go", ".rs", ".java", ".rb", ".php", ".sql",
}

SPECIAL_NAMES = {"LICENSE", "LICENSE.txt", "LICENSE.rst", "COPYING", "Makefile",
                 "CHANGELOG", "CONTRIBUTING", "NOTICE", "README"}

_TEST_PATH_RE = re.compile(r"(^|/)(tests?|spec|__tests__)(/|$)", re.IGNORECASE)
_TEST_FILE_RE = re.compile(r"^(test_[^/]*|[^/]*_test|conftest)\.pyi?$", re.IGNORECASE)

_LICENSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # BSD 家族两种形态：显式 "BSD License" 字样，或无字样的标准 BSD 授权文本（pallets 风格）
    ("bsd", re.compile(r"\bBSD\b", re.IGNORECASE)),
    ("bsd", re.compile(r"Redistribution and use in source and binary forms", re.IGNORECASE)),
    ("mit", re.compile(r"\bMIT License\b", re.IGNORECASE)),
    ("apache", re.compile(r"\bApache License\b", re.IGNORECASE)),
    ("mpl", re.compile(r"\bMozilla Public License\b", re.IGNORECASE)),
    ("gpl", re.compile(r"\bGNU (General|Lesser|Affero) Public License\b", re.IGNORECASE)),
]

MAX_FILE_BYTES = 2_000_000


def should_skip(rel_path: str) -> str | None:
    """Return a skip reason for files that must not enter the index, else None."""
    name = rel_path.rsplit("/", 1)[-1]
    if _TEST_PATH_RE.search(rel_path) or _TEST_FILE_RE.match(name):
        return "test"
    ext = Path(name).suffix.lower()
    if ext not in TEXT_EXTS and name not in SPECIAL_NAMES:
        return "nontext"
    return None


def detect_license(repo_dir: Path) -> str | None:
    """Best-effort license family detection from LICENSE*/COPYING* files."""
    for entry in sorted(repo_dir.glob("LICENSE*")) + sorted(repo_dir.glob("COPYING*")):
        if not entry.is_file():
            continue
        try:
            head = entry.read_bytes()[:4096].decode("utf-8", errors="replace")
        except OSError:
            continue
        for family, pattern in _LICENSE_PATTERNS:
            if pattern.search(head):
                return family
    return None
