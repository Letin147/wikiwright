"""ChunkStore tests: roundtrip, replace/drop, FTS search with snippet."""

from wikiwright.ingest.chunker import Chunk, chunk_id_for
from wikiwright.ingest.store import ChunkStore


def _chunk(path: str, text: str) -> Chunk:
    return Chunk(chunk_id_for(path, 1, 5, text), path, 1, 5, text, "python")


def test_roundtrip_and_search(tmp_path):
    store = ChunkStore(tmp_path / "t.db")
    store.replace_file_chunks(
        "o/n", "src/decorators.py", "sha1",
        [_chunk("src/decorators.py", "def my_decorator(fn):\n    return fn  # decorator helper")],
    )
    store.replace_file_chunks("o/n", "src/other.py", "sha2", [_chunk("src/other.py", "value = 42")])
    assert store.count_chunks("o/n") == 2
    assert store.file_hashes("o/n")["src/other.py"] == "sha2"

    hits = store.search("decorator", source="o/n")
    assert len(hits) == 1
    assert hits[0]["path"] == "src/decorators.py"
    assert "«" in hits[0]["snippet"]
    store.close()


def test_replace_and_drop(tmp_path):
    store = ChunkStore(tmp_path / "t.db")
    store.replace_file_chunks("s", "a.py", "h1", [_chunk("a.py", "old text keyword")])
    store.replace_file_chunks("s", "a.py", "h2", [_chunk("a.py", "new text keyword")])
    assert store.count_chunks("s") == 1  # old chunk fully replaced

    store.drop_file_chunks("s", "a.py")
    assert store.count_chunks("s") == 0
    assert store.search("keyword") == []
    store.close()


def test_identical_content_in_two_sources_does_not_collide(tmp_path):
    """EXP-02 验收发现的回归：同内容同路径的 chunk 曾跨 source 互相覆盖。"""
    store = ChunkStore(tmp_path / "t.db")
    same = [_chunk("setup.cfg", "[metadata]\nname = demo\n")]
    store.replace_file_chunks("a/one", "setup.cfg", "h1", same)
    store.replace_file_chunks("b/two", "setup.cfg", "h1", same)
    assert store.count_chunks("a/one") == 1
    assert store.count_chunks("b/two") == 1
    hits = store.search("demo", source="a/one")
    assert len(hits) == 1
    store.close()
