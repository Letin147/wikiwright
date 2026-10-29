# ADR-0002：引入 langgraph-checkpoint-sqlite 与 markdown 两个依赖（EXP-05）

- 状态：已接受（2026-10-28，EXP-05）
- 背景：EXP-05 全管线装配需要 checkpoint/replay（「可审阅」承诺的实现载体），LangGraph 内置仅
  InMemorySaver，持久化需独立包 `langgraph-checkpoint-sqlite`；wiki 单文件离线 HTML 需要把
  Markdown（含表格）渲染为 HTML，手写解析器不可靠。
- 决策：新增 `langgraph-checkpoint-sqlite>=2.0`（checkpoint 存 `.cache/checkpoints.db`，
  thread_id=source slug 支持断点续跑）与 `markdown>=3.6`（仅渲染层使用，带 tables 扩展）。
- 后果：安装体积小幅增加；换取管线可回放（`wikiwright replay` 于后续版本暴露 CLI）与离线
  HTML 能力。依赖变更均记录于 pyproject 与本 ADR，符合 C-11。
