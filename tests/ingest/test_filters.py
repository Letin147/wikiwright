"""Filter rule tests: test files, non-text files, license detection."""

from wikiwright.ingest.filters import detect_license, should_skip


def test_test_paths_and_files_are_skipped():
    assert should_skip("tests/test_app.py") == "test"
    assert should_skip("src/test_app.py") == "test"
    assert should_skip("src/conftest.py") == "test"
    assert should_skip("src/app_test.py") == "test"


def test_nontext_skipped_but_sources_allowed():
    assert should_skip("assets/logo.png") == "nontext"
    assert should_skip("src/app.py") is None
    assert should_skip("README.md") is None
    assert should_skip("LICENSE") is None


def test_license_detection(tmp_path):
    (tmp_path / "LICENSE").write_text("MIT License\nCopyright (c) 2026", encoding="utf-8")
    assert detect_license(tmp_path) == "mit"
    (tmp_path / "LICENSE").write_text("GNU General Public License v3", encoding="utf-8")
    assert detect_license(tmp_path) == "gpl"


def test_license_detection_bsd_boilerplate(tmp_path):
    # pallets 风格：无 "BSD" 字样、以标准授权文本开头（EXP-02 验收实测发现的原盲区）
    (tmp_path / "LICENSE.txt").write_text(
        "Copyright 2014 Pallets\n\nRedistribution and use in source and binary forms,",
        encoding="utf-8",
    )
    assert detect_license(tmp_path) == "bsd"


def test_license_detection_unknown(tmp_path):
    assert detect_license(tmp_path) is None
