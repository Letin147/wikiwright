"""Path-aware chunking: Python AST boundaries first, fixed-line windows as fallback."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass

MAX_CHARS = 6000
WINDOW_LINES = 100
OVERLAP_LINES = 10


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    text: str
    lang: str


def chunk_id_for(path: str, start: int, end: int, text: str) -> str:
    """Content-addressed id: same path+span+text always yields the same id."""
    digest = hashlib.sha256(f"{path}:{start}:{end}\n{text}".encode()).hexdigest()
    return digest[:16]


def chunk_text(rel_path: str, text: str, lang: str) -> list[Chunk]:
    """Split one file into chunks; Python files use AST top-level boundaries."""
    if lang == "python":
        try:
            return _chunk_python(rel_path, text)
        except SyntaxError:
            pass  # explicit fallback, not a silent skip
    return _chunk_windows(rel_path, text, lang)


def _chunk_python(path: str, text: str) -> list[Chunk]:
    lines = text.splitlines()
    tree = ast.parse(text)
    spans: list[tuple[int, int]] = []
    cursor = 1
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            end = node.end_lineno or node.lineno
            if node.lineno > cursor:
                spans.append((cursor, node.lineno - 1))
            spans.append((node.lineno, end))
            cursor = end + 1
    if cursor <= len(lines):
        spans.append((cursor, len(lines)))
    chunks: list[Chunk] = []
    for start, end in spans:
        segment = "\n".join(lines[start - 1 : end])
        if not segment.strip():
            continue
        if len(segment) > MAX_CHARS:
            chunks.extend(_chunk_windows(path, segment, "python", line_offset=start))
        else:
            chunks.append(
                Chunk(chunk_id_for(path, start, end, segment), path, start, end, segment, "python")
            )
    return chunks


def _chunk_windows(
    path: str, segment: str, lang: str, line_offset: int = 1
) -> list[Chunk]:
    lines = segment.splitlines()
    chunks: list[Chunk] = []
    step = max(1, WINDOW_LINES - OVERLAP_LINES)
    i = 0
    while i < len(lines):
        window = lines[i : i + WINDOW_LINES]
        start = line_offset + i
        end = start + len(window) - 1
        text = "\n".join(window)
        if text.strip():
            chunks.append(Chunk(chunk_id_for(path, start, end, text), path, start, end, text, lang))
        if i + WINDOW_LINES >= len(lines):
            break
        i += step
    return chunks
