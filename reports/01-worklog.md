# 工作日志 · 第 01 卷

> **卷规则（约束 C-13）**：本卷超过 **1500 行** → 在此标题下方加「已封卷 YYYY-MM-DD」标记 → 新开 `reports/02-worklog.md` 并把「当前状态」块迁移过去。**禁止**为单个实验新建文件；所有实验记录、复盘、badcase、巡逻结论一律追加制写入当前卷。
> **记录模板**：见 `manual/02-operations-manual.md` §13（复制使用，禁止改旧记录，写错补勘误条目）。
> 开卷日期：2026-10-28 · 当前状态：**在卷**

---

## 当前状态（短期工作记忆，每次收工前更新，新会话开场必读）

- **进度**：EXP-01 完成（2026-10-28，早于八周路线的 W1 起点）。骨架+CI+CLI 就位，验收四件套全绿，git 6 个提交在 main。
- **卡点**：无技术卡点。账号缺口未补（LLM API key、gh CLI、HF、PyPI）——EXP-02/03 前必须补 LLM key 与 gh。
- **下一步一句话**：补齐账号清单 → 执行 EXP-02（Scout 摄取管线）。
- **本机适配备忘**：中文路径环境必须 `uv sync --no-editable` + `uv run --no-sync`（原因见 EXP-01 坑 2）；直连 PyPI 不稳时重试 `uv sync`（增量缓存，见坑 1）。

---

## 记录条目（追加制）

### EXP-01：仓库骨架初始化（2026-10-28）

- **目标**：「空但完整」的仓库：src 布局 + pyproject + CLI 入口 + CI 矩阵 + 模板，无业务逻辑。
- **前置条件核对**：git 2.44 ✔（身份已配置）；uv 0.9.7 ✔；conda `lumin` = Python 3.11.14 ✔（作 uv 基础解释器）；无 LLM API key（EXP-01 不需要）；gh CLI 未装（待补）。
- **过程摘要（关键决策）**：
  1. 26 个骨架文件按 manual/02 §4 落位；依赖仅 typer/rich/langchain-core/langgraph/pydantic；
  2. uv 基础解释器选 conda lumin（3.11.14），依赖真源仍是 uv.lock；
  3. CI：三平台 × 三版本矩阵 + 目录卫生 job（C-12）；
  4. 修复过程中暴露的四个坑（见下）。
- **结果（对照验收标准）**：✅ `wikiwright 0.1.0.dev0`（真实 CLI，exit 0）；✅ ruff All checks passed；✅ pytest 2 passed；✅ import-linter 2 contracts kept；✅ git 6 commits（conventional）；✅ 目录卫生扫描通过。CI 矩阵待推送 GitHub 后首次验证。
- **成本（token/¥/耗时）**：LLM 0（无调用）；全程约 2 小时。
- **是否正收益**：是——全部验收项达标，未引入约束违例。
- **问题与坑（4 个，全部已解决并留档）**：
  1. **PyPI 直连不稳**：下载 mypy/grimp 时 TLS 被重置。解法：`UV_HTTP_TIMEOUT=300` + 重试（uv 增量缓存，第 2 次成功）。已沉淀到「当前状态」备忘。
  2. **中文路径 × GBK**：`E:\...\开源项目\...` 使可编辑安装的 `_editable_impl_wikiwright.pth`（UTF-8）被系统 Python 以 GBK 解码，解释器启动即崩，`-X utf8`/`PYTHONUTF8` 均无效（site 模块强制 locale 读 .pth）。解法：`uv sync --no-editable`（包复制进全 ASCII 的 site-packages）+ `uv run --no-sync`。已写入 CONTRIBUTING。根治方案（可选）：仓库迁至纯 ASCII 路径。
  3. **typer 0.27 + click 8.5 的 `--version` 时序**：callback 内 `raise typer.Exit()` 未被捕获（真实 CLI 崩 traceback）；改 `SystemExit(0)` 后 CliRunner 又报「Missing command」。解法：`is_eager=True` 选项回调，解析期即处理，两种模式行为一致。
  4. **骨架笔误**：漏 `cli/__init__.py`（import-linter 报模块不存在）；`[project.scripts]` 误指回调函数 `main`，改为指向可调用对象 `app`；ruff 键名 `extend-immutable-calls`（非 allowed）；4 处 docstring 超 100 字符。
- **下一步（≤2 条）**：① 补账号（LLM key/gh/HF/PyPI，见 plan §9）；② EXP-02 Scout 摄取管线。


### 2026-10-28 · 立项与终选（阶段：策划）

- 完成：多平台调研（GitHub/arXiv/HF/中文社区）→ 五候选加权评分 → 两轮深查终选 **WikiWright**；核验关键事实：deepwiki-open 无增量索引（issue #156）、DeepWiki 官方免费含 MCP 端点、mcp-scan 被 Snyk 吸收（候选 B 出局）、Mintlify B 轮 $45M@$500M 估值背书商业价值。
- 产物：`docs/planning-report.md`（v1 策划）、`docs/deep-dive-verdict.md`（v2 终选 + Kill Criteria）。
- 是否正收益：是——两个高价值问题（选哪个/为什么是它）有了证据链完整的答案。

### 2026-10-28 · 管理体系建立（阶段：策划）

- 完成：四文档管理体系 + 域隔离结构落地：`plan/01`（八周路线+GitHub 管理）、`manual/02`（约束 C-01~C-20+成功指标+日志规范）、`prompts/03`（EXP-01~10 指令）、`manual/04`（Agent 工程 playbook）；本日志卷开卷。
- 是否正收益：是——「小白如何管理生产一个项目」从口头约定变成可执行流程（每日四步仪式 / 每周自审 / 1500 行滚动 / 三次法则沉淀）。
- 下一步：见「当前状态」块。

<!-- 新条目从这里向下追加 -->
