"""Analyst tests: contract enforcement, repair retries, degradation, budget, cache."""

import json

import pytest

from wikiwright.agents.analyst import analyze_repo
from wikiwright.core.contracts import Conclusion

GOOD_JSON = json.dumps(
    {
        "responsibility": "示例包，提供数值工具",
        "entities": [
            {"name": "util", "kind": "function", "summary": "返回1", "ref": "proj/beta.py:util"}
        ],
        "public_interface": [
            {"symbol": "VALUE", "summary": "常量", "ref": "proj/alpha.py:VALUE"}
        ],
        "relations": [
            {"target": "proj/beta.py", "kind": "imports", "ref": "proj/alpha.py:util"}
        ],
        "conclusions": [
            {"statement": "alpha 依赖 beta", "ref": "proj/alpha.py:util", "unsure": False},
            {"statement": "可能用于演示", "ref": "", "unsure": True},
            {"statement": "坏引用", "ref": "proj/ghost.py:NOPE", "unsure": False},
        ],
    },
    ensure_ascii=False,
)


class FakeLLM:
    """Distinguishes cartographer naming prompts from analyst prompts.

    script: per-mode queues consumed in order; always: sticky per-mode response.
    """

    def __init__(
        self,
        script: dict[str, list[str]] | None = None,
        always: dict[str, str] | None = None,
    ):
        self.script = script or {}
        self.always = always or {}
        self.calls = 0
        self.spent_usd = 0.0
        self.budget_usd = 10.0

    def chat(self, messages, **kwargs):
        self.calls += 1
        user = messages[-1]["content"]
        mode = "naming" if "制图师" in user else "analyst"
        if mode in self.always:
            return self.always[mode], None
        queue = self.script.get(mode)
        if queue:
            return queue.pop(0), None
        return (GOOD_JSON if mode == "analyst" else '{"business_name": "示例|demo"}'), None


def _repo(tmp_path):
    (tmp_path / "proj").mkdir()
    (tmp_path / "proj" / "__init__.py").write_text("from . import alpha\n")
    (tmp_path / "proj" / "alpha.py").write_text("from .beta import util\nVALUE = 1\n")
    (tmp_path / "proj" / "beta.py").write_text("def util():\n    return 1\n")
    (tmp_path / "setup.py").write_text("from proj import alpha\n")
    (tmp_path / "LICENSE").write_text("MIT License\n")
    return tmp_path


def test_conclusion_contract_requires_ref_or_unsure():
    assert Conclusion(statement="x", ref="a.py:f").ref
    assert Conclusion(statement="x", unsure=True).unsure
    with pytest.raises(ValueError, match="unsure"):
        Conclusion(statement="x")


def test_analysis_with_ref_verification(tmp_path):
    report = analyze_repo(str(_repo(tmp_path)), cache_dir=tmp_path / "cache", llm=FakeLLM())
    assert len(report.understandings) == 2
    assert report.total_conclusions >= 5
    # the ghost ref fails verification -> conclusion flips to unsure, ref logged
    assert report.invalid_refs >= 1
    assert report.unsure_conclusions >= 2  # original unsure + flipped one
    proj = next(u for u in report.understandings if u.module == "proj")
    assert proj.entities and proj.entities[0].ref == "proj/beta.py:util"


def test_repair_retry_recovers_from_garbage(tmp_path):
    fake = FakeLLM(script={"analyst": ["not json at all", GOOD_JSON]})
    report = analyze_repo(str(_repo(tmp_path)), cache_dir=tmp_path / "cache", llm=fake)
    assert report.skipped == []
    assert len(report.understandings) == 2


def test_degradation_marks_skipped_without_crashing(tmp_path):
    fake = FakeLLM(always={"analyst": "bad"})
    report = analyze_repo(str(_repo(tmp_path)), cache_dir=tmp_path / "cache", llm=fake)
    assert report.understandings == []
    assert len(report.skipped) == 2
    assert all("contract-failed" in s.reason for s in report.skipped)


def test_budget_fuse_skips_everything_without_calls(tmp_path):
    fake = FakeLLM()
    fake.spent_usd = fake.budget_usd  # fuse already tripped
    report = analyze_repo(str(_repo(tmp_path)), cache_dir=tmp_path / "cache", llm=fake)
    assert report.understandings == []
    assert len(report.skipped) == 2
    assert all(s.reason.startswith("budget") for s in report.skipped)


def test_second_run_is_cached_and_free(tmp_path):
    repo = _repo(tmp_path)
    cache = tmp_path / "cache"
    first = analyze_repo(str(repo), cache_dir=cache, llm=FakeLLM())
    assert first.cache_hit is False
    second = analyze_repo(str(repo), cache_dir=cache, llm=FakeLLM())
    assert second.llm_calls == 0
    assert second.cache_hit is True
    assert (
        [u.model_dump_json() for u in first.understandings]
        == [u.model_dump_json() for u in second.understandings]
    )
