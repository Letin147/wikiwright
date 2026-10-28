"""End-to-end local ingestion (no network): filter + chunk + cache-hit + search."""

from wikiwright.ingest import ChunkStore, ingest_repo


def _make_repo(root) -> None:
    (root / "src").mkdir(parents=True)
    (root / "src" / "app.py").write_text(
        "import functools\n\n\ndef decorator(fn):\n"
        "    return functools.wraps(fn)(lambda: fn())\n\n\nclass App:\n    pass\n",
        encoding="utf-8",
    )
    (root / "tests").mkdir()
    (root / "tests" / "test_app.py").write_text("def test_decorator():\n    assert True\n")
    (root / "img.bin").write_bytes(b"\x00\x01\x02png-ish")
    (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")


def test_local_ingest_cache_and_search(tmp_path):
    repo = tmp_path / "proj"
    _make_repo(repo)
    cache = tmp_path / "cache"

    first = ingest_repo(str(repo), cache_dir=cache)
    assert first.license_family == "mit"
    assert first.chunks >= 3  # app header/decorator/App + LICENSE
    assert first.cache_hit is False
    assert first.files_filtered >= 2  # tests/ + binary
    assert first.files_indexed == 2

    store = ChunkStore(cache / "ingest.db")
    hits = store.search("decorator", source=first.source)
    assert hits and any(h["path"] == "src/app.py" for h in hits)
    assert all("/tests/" not in h["path"] for h in hits)
    store.close()

    second = ingest_repo(str(repo), cache_dir=cache)
    assert second.cache_hit is True
    assert second.chunks == first.chunks

    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    third = ingest_repo(str(repo), cache_dir=cache)
    assert third.cache_hit is False
    assert third.chunks < first.chunks
