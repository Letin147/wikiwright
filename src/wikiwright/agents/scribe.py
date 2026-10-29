"""Scribe: the ONLY writer. LLM turns verified material into prose — never new facts.

Overview/quickstart paragraphs must restate the given ModuleUnderstanding; any
code fact appearing in prose is expected to come from its refs. Results are
cached by understanding content hash (unchanged input -> free rerun, C-09).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from wikiwright.core.contracts import AnalysisReport, ModuleUnderstanding, ScribePage
from wikiwright.models.router import LLMClient, LLMError

COMPLETION_BUDGETS = (8192, 16384)  # writing needs the widest budgets (EXP-04 SOP)


def _page_key(understanding: ModuleUnderstanding) -> str:
    return hashlib.sha256(understanding.model_dump_json().encode()).hexdigest()[:16]


def _extract_md(content: str) -> str:
    """Strip code fences / preambles; keep the markdown body."""
    text = re.sub(r"^```(markdown)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
    return text


def scribe_module(llm: LLMClient, understanding: ModuleUnderstanding) -> ScribePage:
    """Write overview + quickstart prose for one module from verified material only."""
    material = json.dumps(
        {
            "module": understanding.module,
            "business_name": understanding.business_name,
            "responsibility": understanding.responsibility,
            "entities": [e.model_dump() for e in understanding.entities],
            "public_interface": [i.model_dump() for i in understanding.public_interface],
            "relations": [r.model_dump() for r in understanding.relations],
            "conclusions": [c.model_dump() for c in understanding.conclusions],
        },
        ensure_ascii=False,
    )
    prompt = (
        "你是书记官（Scribe）。只根据下方已核验的结构化材料，撰写该模块 wiki 页的两段散文：\n"
        "1. overview：3-6 句中文概述（模块职责与设计要点）；\n"
        "2. quickstart：2-4 句「如何使用/从哪里读起」。\n"
        "铁律：只准复述材料中已有的事实，禁止引入任何新代码事实、文件名或符号名；"
        "不确定的不写。输出格式：\nOVERVIEW:\n<markdown>\nQUICKSTART:\n<markdown>"
        f"\n\n材料（JSON）：\n{material}"
    )
    errors: list[str] = []
    for budget in COMPLETION_BUDGETS:
        try:
            content, _usage = llm.chat(
                [
                    {"role": "system", "content": "你是严谨的技术文档作者，绝不编造事实。"},
                    {
                        "role": "user",
                        "content": prompt
                        + ("\n\n上次错误（修复后重试）:\n" + "\n".join(errors) if errors else ""),
                    },
                ],
                effort="high",
                temperature=0.3,
                max_tokens=budget,
            )
        except LLMError:
            break
        overview, quickstart = _split_sections(content)
        if overview:
            return ScribePage(
                module=understanding.module,
                overview_md=overview,
                quickstart_md=quickstart,
            )
        errors.append("输出缺少 OVERVIEW: 段或为空")
    return ScribePage(module=understanding.module)  # explicit empty-page degradation


def _split_sections(content: str) -> tuple[str, str]:
    match = re.search(
        r"OVERVIEW:\s*(.*?)\s*QUICKSTART:\s*(.*)", _extract_md(content), re.DOTALL
    )
    if not match:
        return "", ""
    return match.group(1).strip(), match.group(2).strip()


def scribe_all(
    llm: LLMClient | None,
    report: AnalysisReport,
    cache_dir: str | Path | None = None,
) -> dict[str, ScribePage]:
    """Write pages for every understanding; cached by content hash per module."""
    cache = Path(cache_dir).expanduser() if cache_dir else Path(".cache/wikiwright")
    pages_dir = cache / "scribe"
    pages_dir.mkdir(parents=True, exist_ok=True)

    pages: dict[str, ScribePage] = {}
    for understanding in report.understandings:
        key = pages_dir / f"{_page_key(understanding)}.json"
        if key.exists():
            try:
                page = ScribePage.model_validate_json(key.read_text(encoding="utf-8"))
                pages[understanding.module] = page
                continue
            except (OSError, ValueError):
                pass
        if llm is None:
            pages[understanding.module] = ScribePage(module=understanding.module)
            continue
        page = scribe_module(llm, understanding)
        key.write_text(page.model_dump_json(), encoding="utf-8")
        pages[understanding.module] = page
    return pages
