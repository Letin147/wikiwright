"""Scribe tests: section parsing, degradation, content-hash caching."""

from wikiwright.agents.scribe import scribe_all, scribe_module
from wikiwright.core.contracts import AnalysisReport, Conclusion, ModuleUnderstanding


def _understanding() -> ModuleUnderstanding:
    return ModuleUnderstanding(
        module="proj",
        business_name="示例|demo",
        files=["proj/alpha.py"],
        responsibility="示例模块",
        conclusions=[Conclusion(statement="alpha 依赖 beta", ref="proj/alpha.py:util")],
    )


class FakeLLM:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls = 0
        self.spent_usd = 0.0
        self.budget_usd = 10.0

    def chat(self, messages, **kwargs):
        self.calls += 1
        return self.reply, None


GOOD = "OVERVIEW:\n这是示例模块的概述，职责为示例。\nQUICKSTART:\n从 alpha.run 开始阅读。"


def test_scribe_module_parses_sections():
    page = scribe_module(FakeLLM(GOOD), _understanding())
    assert page.overview_md.startswith("这是示例模块")
    assert "alpha.run" in page.quickstart_md


def test_scribe_module_degrades_to_empty_page_on_garbage():
    fake = FakeLLM("no sections here")
    page = scribe_module(fake, _understanding())
    assert page.overview_md == "" and page.quickstart_md == ""
    assert fake.calls == 2  # both budget tiers attempted


def test_scribe_all_caches_by_content(tmp_path):
    report = AnalysisReport(source="x", understandings=[_understanding()])
    first = FakeLLM(GOOD)
    scribe_all(first, report, cache_dir=tmp_path)
    assert first.calls == 1
    second = FakeLLM(GOOD)
    pages = scribe_all(second, report, cache_dir=tmp_path)
    assert second.calls == 0  # cached: zero LLM cost
    assert pages["proj"].overview_md.startswith("这是示例模块")


def test_scribe_all_without_llm_yields_empty_pages(tmp_path):
    report = AnalysisReport(source="x", understandings=[_understanding()])
    pages = scribe_all(None, report, cache_dir=tmp_path)
    assert pages["proj"].overview_md == ""
