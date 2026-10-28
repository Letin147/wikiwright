"""Chunker unit tests: AST boundaries, fallback windows, stable content-addressed ids."""

from wikiwright.ingest.chunker import chunk_id_for, chunk_text

PY_SOURCE = '''"""Module docstring."""
import os


def helper(x):
    return x + 1


class Service:
    def run(self):
        return helper(1)
'''


def test_python_chunks_align_to_ast_boundaries():
    chunks = chunk_text("src/app.py", PY_SOURCE, "python")
    spans = [(c.start_line, c.end_line) for c in chunks]
    # header (docstring + import) / helper / Service each get their own chunk
    assert (1, 4) in spans
    assert (5, 6) in spans
    assert (9, 11) in spans
    assert all(c.lang == "python" for c in chunks)


def test_fallback_windows_for_plain_text():
    text = "\n".join(f"line {i}" for i in range(1, 251))
    chunks = chunk_text("README.md", text, "text")
    assert len(chunks) == 3
    assert (chunks[0].start_line, chunks[0].end_line) == (1, 100)
    assert chunks[-1].end_line == 250


def test_ids_are_stable_and_content_addressed():
    first = chunk_text("src/app.py", PY_SOURCE, "python")
    second = chunk_text("src/app.py", PY_SOURCE, "python")
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert chunk_id_for("p", 1, 2, "x") == chunk_id_for("p", 1, 2, "x")
    assert chunk_id_for("p", 1, 2, "x") != chunk_id_for("p", 1, 3, "x")


def test_syntax_error_falls_back_to_windows():
    chunks = chunk_text("bad.py", "def broken(:\n    pass\n", "python")
    assert chunks and chunks[0].lang == "python"
