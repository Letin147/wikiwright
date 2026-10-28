# 贡献指南 · Contributing to WikiWright

感谢你为 ⚒ WikiWright（维匠）做贡献！本项目体积虽小，纪律是产品的一部分——请先花 10 分钟读以下三份文件，它们回答 90% 的「怎么做」：

| 问题 | 文档 |
|---|---|
| 成功指标、20 条硬约束（C-01~C-20）、包结构与命名规范 | [`manual/02-operations-manual.md`](manual/02-operations-manual.md) |
| 当前路线图与本周目标 | [`plan/01-project-plan-and-progress.md`](plan/01-project-plan-and-progress.md) |
| 架构与决策记录 | [`docs/`](docs/) |

## 开发环境（uv，三步）

```bash
git clone https://github.com/<you>/wikiwright && cd wikiwright
uv sync                 # 自动安装 Python 3.10–3.12 与全部依赖
uv run wikiwright --version
```

本地质量门禁（与 CI 完全一致，提交前必须全绿）：

```bash
uv run ruff check .
uv run pytest
uv run lint-imports
```

## 分支与提交

- 分支模型：trunk-based。`feat/ww-<slug>` / `fix/ww-<slug>`，存活 ≤3 天，从 `main` 拉出、合回 `main`。
- Commit：[Conventional Commits](https://www.conventionalcommits.org/)——`feat:` `fix:` `docs:` `test:` `refactor:` `chore:`，一行说清「为什么」。
- PR：≤400 行；描述含自测清单；UI 改动必附截图；**CI 红不合并**（主干常绿，约束 C-16）。

## Issue 与标签

标签体系：`[agent]` `[ingest]` `[wiki]` `[mcp]` `[infra]` `[eval]` `[docs]` × 优先级 `P0-P2` × `good first issue`。
新功能请求先过「三问」（manual/02 §8）：是否让活维基更强？个人是否可维护？CPU+预算内可跑？

## 硬红线（违反即 close）

- ❌ 提交 API key、`.env`、生成产物（`wiki/`）、缓存（C-12）
- ❌ 无测试的纯逻辑改动
- ❌ 引入数据库服务/重型前端框架/厂商私有 SDK（C-11）
- ❌ 破坏依赖方向：`core` 不得 import 上层（manual/02 §4）
