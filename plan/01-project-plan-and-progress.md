# WikiWright 项目规划与进展记录

> **文档编号**：PLAN-01 · **域**：计划管理（`plan/`） · **维护规则**：每周日更新进展记录 §8；路线图变更须在 §8 留痕并注明理由
> **配套阅读**：`manual/02-operations-manual.md`（怎么做）、`prompts/03-vibe-coding-handbook.md`（指令）、`reports/`（做了什么）
> 建立日期：2026-10-28 · 当前版本：v1.0

---

## 1. 项目一页纸

| 项 | 内容 |
|---|---|
| 项目名 | WikiWright（维匠） · `wikiwright` |
| 定位 | 一群 LangGraph 多智能体「匠人」，为任意代码库锻造**带证据引用、随 commit 增量更新、可通过 MCP 被任何 Agent 查询**的活维基 |
| 定位语 | *DeepWiki generates a wiki. WikiWright keeps it alive — incremental, evidence-grounded, and yours.* |
| 目标用户 | 开源维护者、接手陌生仓库的工程师、编码 Agent 用户、求职学生、研究者 |
| 北极星目标 | **2026-12-13 前发布 v0.3.0 并完成首发（Show HN 等五渠道同日），30 天内 500★** |
| 三条价值曲线 | 开源 star 曲线 · ICSE/FSE 论文曲线（v0.4 后启动 WikiBench）· 托管订阅收入曲线（v1.0 后） |
| 许可 | MIT |
| 立项依据 | `docs/planning-report.md`（v1 策划）+ `docs/deep-dive-verdict.md`（v2 终选，含 Kill Criteria） |

---

## 2. 资源与平台清单（启动前逐项核对）

### 2.1 硬件（现有设备即满足）

| 项 | 要求 | 实际 |
|---|---|---|
| CPU | 任意近 5 年处理器，**无 GPU 需求** | 现有 Windows 电脑 ✔ |
| 内存 | 8GB 起步 / 16GB 舒适 | — |
| 磁盘 | 预留 10–20GB（仓库克隆+缓存） | — |
| 网络 | 可访问 GitHub 与 LLM API；克隆慢时走镜像（ghproxy 等） | — |

### 2.2 软件环境

| 项 | 选型 | 说明 |
|---|---|---|
| Python | 3.10–3.12（锁定，v0.4 前不加新版本） | uv 管理虚拟环境与依赖 |
| 包管理 | uv | `uv sync` 一键复现环境 |
| Git | ≥2.40 | trunk-based 短分支模型 |
| IDE | VS Code / Trae / Cursor 任一 | AI 结对主战场 |
| 质量链 | ruff + pytest + pre-commit + mypy(宽松) | CI 门禁，零警告 |
| 可选 | Ollama（本地 1.5B 小模型分流） | v0.3 后再引入，v0.1 全走 API |

### 2.3 账号与 API（唯一花钱项）

| 项 | 用途 | 费用/预算 |
|---|---|---|
| LLM API key（GLM / DeepSeek / Qwen 任一，OpenAI 兼容） | 8 个智能体的大脑 | 开发期 **≤¥150/月**（硬约束 C-05） |
| GitHub 账号 + PAT（最小权限） | 克隆 / Action / Pages | 免费 |
| Hugging Face 账号 | 免费 CPU Space 在线 demo、嵌入模型下载 | 免费 |
| PyPI 账号 | 发布 `pipx install wikiwright` | 免费 |
| 域名（后期可选） | 文档站 | ≈¥50/年 |

**成本量级参考**：中型仓库（约 500 文件）全量锻造一次——便宜档 ¥0.5–2，主力档 ¥2–10；增量更新一次 ¥0.1–1。首月总成本控制在 ¥100–200 内。

### 2.4 平台矩阵（开发平台 + 分发渠道）

| 平台 | 用途 | 启用时间 |
|---|---|---|
| GitHub | 代码托管 / CI / Action / Pages / 社区 | W1 |
| PyPI | 发包 | W2（v0.1.0 内测版即发包，练管线） |
| Hugging Face Space（CPU 免费） | 在线 demo「60 秒体验」 | W4 |
| Gitee 镜像 | 中文渠道可见性 | W6（首发时同步） |
| Hacker News / Reddit(r/LocalLLaMA, r/opensource) | 英文首发 | W6 |
| V2EX / 掘金 / 知乎 / CSDN | 中文首发 | W6 |
| 魔搭创空间 / 华为云社区 / Trae 社区 | 中文生态二次分发 | W7–W8 |
| X(Twitter) / 少数派 | 发布节奏广播 | 每次发版 |

---

## 3. 前后端与全栈架构管理

**原则：CLI 优先，接口契约先行，前端最后。** 本项目核心是引擎，不是网站——前端是展示层，永远不得反向侵入核心逻辑。

| 层 | 选型 | 版本策略 | 管理规则 |
|---|---|---|---|
| CLI | typer + rich（W1 起） | 跟随主版本 | 命令即产品：`forge / serve / replay / status` 四命令覆盖 90% 场景 |
| TUI | textual（W3 起） | 同上 | 只读展示进度与结果，禁止在 TUI 里写业务逻辑 |
| 后端 API | FastAPI（W4 起，同时服务 Web 与 MCP） | 同上 | **OpenAPI schema 先行**：先在 `docs/api-contract.md` 定契约再写实现；MCP 四工具与 REST 共用 service 层 |
| 前端 | 阶段一：单文件 `index.html`（模板渲染，W2）；阶段二：GitHub Pages 站点（W5）；阶段三：Vite+轻量框架（**v1.0 前不启动**） | — | 前端只消费契约，不定义契约；任何「前端需要后端改接口」的需求必须走 ADR |

**全栈分工铁律**：`src/wikiwright/core`（引擎，不依赖任何 IO 框架）→ `cli` / `web` / `mcp` 都是 core 的薄壳。依赖方向单向，CI 用 import-linter 强制。

---

## 4. 八周路线图（2026-11-02 → 2026-12-27）

> 每周含：目标 / 任务 / 交付物（Definition of Done）/ 验收标准。周节奏：周一至周五执行（每天 2h），周日 30 分钟自审+更新本文件 §8。
> 对应实验：W1–W6 的开发任务即 `prompts/03` 中的 EXP-01 ~ EXP-09，逐个执行，逐个记日志。

### Week 1（11.02–11.08）：骨架与 Scout —— 地基周

- **目标**：仓库初始化，摄取管线跑通。
- **任务**：EXP-01（骨架+CI）、EXP-02（Scout：克隆/打包/分块/内容寻址缓存）。
- **DoD**：① `uv sync && wikiwright --version` 在干净机器成功；② 对 3 个金仓库完成摄取，分块落盘+FTS5 可查；③ CI（lint+test+矩阵 3.10/3.11/3.12）全绿；④ 目录卫生检查通过。
- **验收**：`pytest tests/ingest/` 通过；分块边界抽样 20 个人工检查合理。
- **风险**：Windows 下 ONNX/tree-sitter 轮子问题 → 备援 WSL2。

### Week 2（11.09–11.15）：四角色最小闭环 —— v0.1.0

- **目标**：`wikiwright forge <repo>` 产出第一本 wiki。
- **任务**：EXP-03（Cartographer 模块地图）、EXP-04（Analyst map-reduce）、EXP-05（Scribe 撰写+引用格式）。
- **DoD**：① 一条命令产出 `wiki/index.md` + 1 张 AST 级 mermaid 架构图 + 各模块页（带 `path:line` 引用）；② PyPI 发 v0.1.0（内部版）；③ 金仓库回归测试建立（快照对比）。
- **验收**：引用锚定抽样 50 条，正确率 ≥90%（人工判定）。

### Week 3（11.16–11.22）：信任与颜值 —— Critic + TUI

- **任务**：EXP-06（Critic 证据核验 + Grounding Score）、TUI 进度界面。
- **DoD**：① 每页挂 Grounding Score 徽章，未锚定论断显式 ⚠；② `_evidence.jsonl` 可导出；③ TUI 演示录屏（首张 GIF 素材）。
- **验收**：金仓库 Grounding Score ≥90%；**自用周**——用 wikiwright 吃透 2 个陌生真实仓库并记录体验（dogfooding 是最好的测试）。

### Week 4（11.23–11.29）：八角色补齐 + 文件级增量 —— v0.2.0 静默发布

- **任务**：EXP-07a（Historian/Sentinel 补齐）、EXP-07b（Curator 文件级增量）、HF Space demo 上线。
- **DoD**：① 8 角色全图跑通；② 增量更新：改动 5% 文件时成本 ≤ 全量的 30%；③ v0.2.0 发布（不宣传，收集首批 issue）。
- **验收**：增量成本比达标；Space demo 60 秒内出结果。

### Week 5（11.30–12.06）：MCP + Action —— 差异化齐活

- **任务**：EXP-08（MCP server 四工具：search/ask/get_diagram/changes）、EXP-09（GitHub Action + PR 漂移评论）。
- **DoD**：① Cursor/Claude 实际调通四工具并录屏；② 示例仓库装上 Action 后，制造一个 API 变更 commit，PR 里出现正确漂移评论。
- **验收**：MCP 调用成功率 100%（20 次连测）；漂移评论误报率 ≤1/10。

### Week 6（12.07–12.13）：首发冲刺 —— v0.3.0 🚀

- **任务**：EXP-10 前的打磨：README 双语+对比表+GIF、错误信息友好化、`--budget` 硬上限、发版。
- **首发日（建议 12.09 周三，美东周二晚发 HN）**：Show HN + Reddit + V2EX + 掘金 + 知乎同日；Gitee 镜像同步。
- **DoD**：v0.3.0 发布；五渠道帖发出；issue 模板与 good-first-issue 就位。
- **验收**：首发帖 24h 内回复所有评论（硬性）。

### Week 7（12.14–12.20）：响应与复盘

- **任务**：issue 分流与 hotfix（每天 ≤30 分钟封顶）；增长数据复盘（star/clone/访问来源）写入 `reports/`。
- **DoD**：issue 24h 响应率 100%；P0 bug 48h 内修复发版；复盘报告一卷。

### Week 8（12.21–12.27）：评测起步 —— v0.4 规划

- **任务**：EXP-10（WikiBench v0：30 仓库 + QA 标注 schema）、消融脚本骨架、论文选题细化（对照 `docs/planning-report.md` §10）。
- **DoD**：WikiBench v0 可跑出首组数字；v0.4 季度计划写入本文件。

---

## 5. 工作循环与节奏

**每日循环（约 2 小时，四步仪式）**：

1. **读**（5min）：`plan/01` §9 下一步行动 + `reports/` 当前卷顶部「当前状态」块；
2. **做**（80min）：只做一个 EXP 或一个 issue，指令从 `prompts/03` 复制；
3. **验**（15min）：跑验收标准里的命令，绿了才算完；
4. **记**（10min）：按 `manual/02` §13 模板把结果追加进 `reports/` 当前卷。

**每周自审（周日 30min）**：对照本周 DoD 打勾/打叉 → 更新本文件 §8 → 把未完成项移入下周或砍掉（优先砍）→ 检查目录卫生（`manual/02` §12 三条命令）。

---

## 6. GitHub 日常管理规范（高标准）

| 项 | 规范 |
|---|---|
| 分支模型 | trunk-based：`main` 常绿，短分支 `feat/ww-<slug>` / `fix/ww-<slug>`，存活 ≤3 天 |
| Commit | Conventional Commits：`feat:` `fix:` `docs:` `test:` `refactor:` `chore:`；一行说清「为什么」 |
| PR | ≤400 行；模板含：改动摘要/自测清单/截图（UI 类必附）；自己先 review 一遍再提 |
| Issue 标签 | `[agent]` `[ingest]` `[wiki]` `[mcp]` `[infra]` `[eval]` `[docs]` + `good first issue` / `P0-P2` |
| Milestone | 与版本号一一对应（v0.1.0 …）；issue 不入里程碑不开发 |
| Project Board | 六列：Backlog → This Week → In Progress → Review → Done → Icebox（拒绝的 idea 进 Icebox 留档） |
| CI 门禁 | ruff 零警告 · pytest 全绿+覆盖 ≥70%（核心模块）· import-linter 依赖方向 · 目录卫生检查 · 三平台矩阵 |
| Release | python-semantic-release 自动出版本+CHANGELOG；每发版=一条渠道广播 |
| 依赖 | dependabot 周检；新增**任何**第三方依赖须在 `docs/adr/` 留 ADR（半页即可） |
| 安全 | PAT 最小权限；API key 只进环境变量/CI Secrets，**严禁**入库；公开仓库无此例外 |

---

## 7. 六性验收清单（「高标准」的定义，每版发布前逐条过）

| 性质 | 验收证据 |
|---|---|
| 可持续 | 双周发版达成率 ≥80%；ROADMAP 公开；good-first-issue ≥3 个常备 |
| 可迭代 | 依赖锁定+ADR；换模型不改核心（model router 单测覆盖）；插件式角色注册 |
| 可靠 | 金仓库回归全绿；`--budget` 生效；错误信息含可操作建议 |
| 可审阅 | 每论断有 `[commit:path:line]` 锚点；`wikiwright replay` 可回放任意一次运行；`_evidence.jsonl` 完整 |
| 可管理 | 单一配置源 `wikiwright.toml`；`wikiwright status` 一屏看清缓存/成本/状态 |
| 美观 | 首屏 GIF ≤60s；统一色板与吉祥物；CLI 输出对齐无乱码（Windows 终端实测） |

---

## 8. 进展记录（只增不改；每周日更新）

| 日期 | 阶段 | 完成事项 | 证据/产物 | 下一步 |
|---|---|---|---|---|
| 2026-10-28 | 立项 | 多平台调研、五候选评分、两轮深查终选 WikiWright；四文档管理体系建立 | `docs/` 两报告；`plan/` `manual/` `prompts/` `reports/` 域就位 | W1 前置：注册核对 §2.3 账号；通读 `manual/02` 约束清单 |
| 2026-10-28 | W1 前置（提前） | **EXP-01 完成**：26 文件骨架 + CI 矩阵 + CLI；验收四件套全绿；git main 分支 6 个 conventional commits；环境适配完成（conda lumin=Py3.11.14 作 uv 解释器、中文路径 `--no-editable` 方案） | `reports/01-worklog.md` EXP-01 条目（含 4 坑记录）；`git log` | 补账号缺口 → EXP-02 Scout |
| 2026-10-28 | W1 前置（提前） | **EXP-01 完全收官**：gh 登录（Letin147）✔；远端 https://github.com/Letin147/wikiwright 建立并推送 ✔；**CI 10/10 全绿**；DeepSeek key 实测无效已标注（待办有效 key） | `reports/01-worklog.md` 当日第二条；GitHub Actions run 40695897565 | 办有效 LLM key → EXP-02 |
| | | | | |

---

## 9. 下一步行动（Next Actions，≤3 条，随时覆盖）

1. ~~LLM 供应商~~ **已闭环（2026-10-28）**：DeepSeek 新 key 实测通过（鉴权/对话/effort 旋钮），`deepseek-flash` 主力 + `v4-pro` 重案档，成本-质量路由表落进 manual/02 §15；百度 AI Studio 留作备选（额度耗尽，充值即用）。HF 账号 W4 前、PyPI 账号 W2 发版前补齐即可。
2. **[W1]** 执行 **EXP-02**（Scout 摄取管线，无需 LLM；指令在 `prompts/03` §3）：对 `pallets/click`、`pallets/flask`、`encode/httpx` 跑通克隆→过滤→分块→FTS5；完成后按模板记录进 `reports/01`。
3. **[W1 周日]** 首次周自审：对照 W1 DoD 打勾 → 更新本文件 §8 → 目录卫生三命令（`manual/02` §12）→ `git push`。

---

## 10. 资料来源与复核

- 立项与终选的全部在线来源（含日期）见 `docs/planning-report.md` §15 与 `docs/deep-dive-verdict.md` §7。
- **月度竞品巡逻**（每月最后一个周日，30 分钟）：检查 deepwiki-open release notes、Cognition 官方博客（Kill Criteria 触发源）、mcp 生态数据；结论追加进 `reports/` 当前卷，格式见 `manual/02` §13。
