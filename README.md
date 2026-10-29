# ⚒ WikiWright · 维匠

> An agent crew that forges — and keeps alive — the wiki your codebase deserves.
>
> 一群 LangGraph 多智能体「匠人」，为任意代码库锻造**带证据引用、随 commit 增量更新、可通过 MCP 被任何 Agent 查询**的活维基。

**项目状态：v0.1 功能闭环（2026-10-28）· EXP-01~05 完成 · 38 tests · 待 v0.1.0 发版（PyPI） · 纯 CPU · MIT**

```bash
$ uv sync && uv run wikiwright forge pallets/click   # 一条命令锻造完整 wiki vault
✔ vault forged → wiki/pallets__click
#   index.md / architecture.md(mermaid) / modules/*.md(证据引用) / index.html(离线单文件)
#   82 refs 全部独立核验有效 · 重跑字节级一致（C-09） · click 全程成本 < ¥0.5
```

```text
$ wikiwright forge owner/repo
  ├─ Scout        摄取仓库……
  ├─ Cartographer 绘制模块地图……
  ├─ Analyst × N  并行深读模块……
  ├─ Scribe       撰写 wiki 页面……
  ├─ Critic       核验每条论断的证据……
  └─ Curator      增量合并 → wiki/ + MCP server
```

## 📚 文档导航（按身份进入）

| 你想做什么 | 读这份 |
|---|---|
| **了解项目是什么、为什么值得做**（调研、五候选、竞品、商业模式、论文路线） | [docs/planning-report.md](docs/planning-report.md)（v1 策划）· [docs/deep-dive-verdict.md](docs/deep-dive-verdict.md)（v2 终选 + Kill Criteria） |
| **今天该做什么、这周交付什么、GitHub 怎么管** | [plan/01-project-plan-and-progress.md](plan/01-project-plan-and-progress.md)（八周路线 + 进展记录） |
| **怎么做：成功指标、20 条约束、包结构、日志与可复现规范** | [manual/02-operations-manual.md](manual/02-operations-manual.md)（操作手册） |
| **给 AI 下什么指令**（vibe coding / codex 实验手册） | [prompts/03-vibe-coding-handbook.md](prompts/03-vibe-coding-handbook.md)（EXP-01~10） |
| **如何做 Agent 工程**（可观测/可评测/可控/可兜底/可迭代） | [manual/04-agent-engineering-playbook.md](manual/04-agent-engineering-playbook.md) |
| **做过什么、卡在哪** | [reports/01-worklog.md](reports/01-worklog.md)（滚动日志，先读顶部「当前状态」块） |

**小白三步上手**：① 周日 30 分钟读 `plan/01` §4 本周目标 → ② 每天按 `prompts/03` 指令做一个 EXP → ③ 收工按 `manual/02` §13 模板记日志。

## 🗂 目录结构（六域隔离，互不污染）

```text
WikiWright/
├── README.md          # 本文件：总导航
├── docs/              # 报告域：研究决策史（策划/终选/ADR），只增不改
├── plan/              # 计划域：八周路线、进展记录、资源清单
├── manual/            # 方法域：操作手册(02)、Agent 工程 playbook(04)
├── prompts/           # 指令域：EXP 实验指令、AI 结对资产
├── reports/           # 日志域：滚动工作卷（>1500 行开新卷）
├── src/wikiwright/    # 代码域：core/agents/graph/ingest/wiki/mcp/models/eval/cli/web
└── tests/             # 测试域：38 项（含 fixtures 离线确定性回归）
```

隔离规则与卫生铁律见 `manual/02` §12：禁止中间产物入库、缓存进 `.cache/`、输出进用户目录——**目录干净是产品品质的一部分**。

## 🧱 技术底座

LangGraph 1.x（8 角色编排 + checkpoint 回放）· MCP v2（四工具：search/ask/get_diagram/changes）· 可插拔 LLM（GLM / DeepSeek / Qwen / Ollama，OpenAI 兼容）· bge ONNX INT8 嵌入（CPU 毫秒级）· tree-sitter（可选）· typer/rich/textual CLI · FastAPI · GitHub Action —— **全程纯 CPU，本地优先**。

差异化四把凿子（对 DeepWiki/deepwiki-open）：**增量活文档 · 证据 grounding（`[commit:path:symbol]` 锚定 + Grounding Score）· wiki 归你所有（落盘进你的仓库）· 本地私有仓库可用**。详见 [docs/deep-dive-verdict.md](docs/deep-dive-verdict.md) §2。
