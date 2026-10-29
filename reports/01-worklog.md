# 工作日志 · 第 01 卷

> **卷规则（约束 C-13）**：本卷超过 **1500 行** → 在此标题下方加「已封卷 YYYY-MM-DD」标记 → 新开 `reports/02-worklog.md` 并把「当前状态」块迁移过去。**禁止**为单个实验新建文件；所有实验记录、复盘、badcase、巡逻结论一律追加制写入当前卷。
> **记录模板**：见 `manual/02-operations-manual.md` §13（复制使用，禁止改旧记录，写错补勘误条目）。
> 开卷日期：2026-10-28 · 当前状态：**在卷**

---

## 当前状态（短期工作记忆，每次收工前更新，新会话开场必读）

- **进度**：EXP-01 **完全收官**（2026-10-28）：本地验收四件套全绿 + GitHub CI 10/10 job 全绿；远端 https://github.com/Letin147/wikiwright（gh 账号 Letin147）。
- **卡点**：LLM API key 未落实——旧项目 .env 里的 DeepSeek key 实测无效（authentication_error，已在 .env 中注释并注明）。**EXP-03（W2）前必须办有效 key**（DeepSeek 重办 / 智谱 / 百炼任一）。HF 与 PyPI 账号分别 W4 / W2 前补。
- **下一步一句话**：办有效 LLM key → 执行 EXP-02（Scout 摄取管线，无需 LLM）。
- **本机适配备忘**：中文路径环境必须 `uv sync --no-editable` + `uv run --no-sync`；PyPI 直连不稳时重试 `uv sync`；gh 命令前 `unset GITHUB_TOKEN`（本环境注入的无效 token 会覆盖 keyring 登录）。

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

### 2026-10-28 · 账号密钥核对 + EXP-01 远端收官（阶段：W1 前置）

- **目标**：核对账号与 API key；完成 EXP-01 最后一项验收（推送 + CI 全绿）。
- **过程与结果（逐项）**：
  1. gh CLI 登录 ✔（账号 **Letin147**，keyring，HTTPS，scopes 含 repo+workflow）；
  2. `.env` 密钥核对：旧项目示例文件中的 **DeepSeek key（…86a9）实测无效**（官方 `/models` 端点返回 authentication_error）——如实记录，已在 .env 注释；其余条目（ERNIE 明文 http 中转、Langfuse 云端密钥、百度 OCR 等）属旧项目，已从本仓库 .env 移除；
  3. `.env` 已最小化为 WikiWright 专用（gitignore 验证生效，untracked ✔）；
  4. 误入目录的空文件 `toke百度.txt`（0 字节）已清除（卫生规则）；
  5. 远端创建 + 推送 ✔ → https://github.com/Letin147/wikiwright ；
  6. **CI 10/10 全绿**：ubuntu/macos/windows × py3.10/3.11/3.12 全过 + Directory hygiene job 通过。
- **成本**：LLM 0；全程约 20 分钟。
- **是否正收益**：是——EXP-01 全部验收项（含 CI）达成；密钥无效被及时证实，避免 W2 才发现。
- **问题与坑**：本环境注入的 `GITHUB_TOKEN` 无效且会覆盖 gh keyring——所有 gh/git push 命令前需 `unset GITHUB_TOKEN`（已记入备忘）。
- **下一步（≤2 条）**：① 办有效 LLM key（DeepSeek 重办 / 智谱 / 百炼，EXP-03 前）；② 执行 EXP-02 Scout（无需 LLM）。

### 2026-10-28 · 百度优先供应商核实 + 隐私加固（第二轮，用户指令）

- **目标**：按用户指令将百度飞桨 token 设为 LLM 首选并实测；GitHub 脱敏复查。
- **过程与结果（四条通路，全部实测）**：
  1. 千帆官方 v2（Bearer 40 位 token）→ `invalid_iam_token`（token 类型不符）✗；
  2. BCE OAuth（AppKey+Secret 换 access_token）→ 换 token 成功（30 天有效），但文心工作台对话 `error_code 6 No permission` ✗；
  3. 明文 HTTP 中转 134.199.132.159 → 503 宕机 ✗（且第三方明文传输有隐私风险，**永久弃用**）；
  4. **AI Studio 官方 lmapi v3（openai SDK 直连，用户提供的官方接入方式）→ 鉴权通过、请求格式正确，`errorCode 40408 额度耗尽`**——端点/协议/密钥全就绪，充值即用。
- **隐私加固（用户指令落实）**：① 全历史密钥扫描（git grep 全部提交）= **零泄露**，`.env` 确认从未入库；② 含明文 token 的 `文心大模型的api.txt` 已从仓库目录删除（内容并入 .env）；③ CI 新增 **gitleaks 全历史密钥扫描 job**（与卫生 job 并列的门禁）；④ manual/02 新增「供应商与隐私铁律」条款。
- **是否正收益**：是——百度接入路径完全打通（唯一缺额度），零泄露，且隐私要求已制度化而非口头。
- **成本**：4 次 API 探测（3 次失败 0 计费 + 1 次额度报错 0 计费）。
- **下一步（≤2 条）**：① 充值 AI Studio（或办智谱备选）；② EXP-02 Scout（无需 LLM，随时可开工）。

### 2026-10-28 · DeepSeek 供应商闭环 + 成本-质量路由定稿（第三轮，用户指令：省钱保性能）

- **目标**：激活新 DeepSeek key；设计并实测「成本-质量平衡」策略。
- **过程与实测结果**：
  1. 用户更新 .env 新 key（sk-c4fd…）→ 激活并实测：`/models` 鉴权 ✔；
  2. 模型线换代确认：当前为 **deepseek-flash**（V4.1-Flash，**1M 上下文 / 393K 最大输出 / 支持图片输入 / effort=low|high|max 推理旋钮**）与 deepseek-v4-pro 两档；旧 deepseek-chat/reasoner 已不在列表；
  3. 对话实测 ×2：默认档 max_tokens=16 被推理内容耗尽（finish=length）→ **effort=low 立杆见影**：finish=stop、content='ok'、reasoning_tokens 12/总 48——旋钮确认可用；
  4. 定价抓取（官方 pricing 页，2026-10-28）：flash 峰时输入命中 $0.006/未命中 $0.30/输出 $1.20 每百万 token，**错峰一律半价**（高峰=UTC 01:00–04:00、06:00–10:00，即北京工作时段）。
- **产出**：manual/02 §15「成本-质量路由表」（8 角色 × 模型 × effort × 温度 × token 预算）+「成本战术六条」（Flash-first 95%、前缀缓存吃命中价 1/50、错峰半价、增量优先、--budget 熔断、effort 旋钮）+ 质量侧保证（温度锁定+契约校验+grounding 闭环 = 模型便宜验证严格）；.env 重构为 DeepSeek 主力双档配置。
- **成本**：2 次调用共 ~98 tokens，≈$0.0001。
- **是否正收益**：是——供应商彻底闭环，成本结构有实测依据，EXP-03 的模型路由有了完整实现规格。
- **下一步（≤2 条）**：① EXP-02 Scout 摄取管线（无 LLM 依赖）；② EXP-03 模型路由按 §15 路由表实现（含 effort/温度/max_tokens 三控）。

### EXP-02：Scout 摄取管线（2026-10-28）

- **目标**：`ingest_repo(source, cache_dir) -> IngestResult`：浅克隆（镜像支持）→ 过滤 → AST 分块 → 内容寻址缓存 → SQLite FTS5。零 LLM。
- **实现**：`ingest/` 7 文件（source/clone/filters/chunker/store/ingest/__init__）+ `IngestResult` 契约入 `core/contracts.py`；Python 文件按顶层 class/def 边界分块（>6000 字符降级滑窗，SyntaxError 显式回退）；行键 `source:chunk_id`。
- **验收结果（金仓库，全过）**：
  - 摄取：click 168 文件/622 chunks、flask 227/496、httpx 117/298（首跑含克隆 17–59s；本地重建索引 0.3–0.7s）；
  - 缓存：三仓二次运行 `cache_hit=True`，0.009–0.015s（提速约 1000×，零重分析成本 ✔）；
  - FTS：`decorator`@click 命中 `src/click/decorators.py:100`、@flask 命中 `docs/patterns/viewdecorators.rst`；httpx 无该词（其文档在独立仓库），换 `transport` 命中 `httpx/_client.py:1397` ✔；
  - 测试：**15 passed**（4 文件全 mock 无网络）+ ruff/import-linter 绿。
- **成本**：LLM 0 调用；网络 3 次浅克隆。
- **是否正收益**：是——全部验收达标，且发现并修复两个真实缺陷。
- **问题与坑（2 个，均已修复+回归测试）**：
  1. **BSD 无字样文本**：pallets/httpx 的 LICENSE 均为无 "BSD" 字样的标准授权文本（"Redistribution and use in source and binary forms"），首轮三仓全部识别为 None → 补充惯用句式模式，复测全部 `bsd` ✔；
  2. **跨 source 块碰撞**：`chunk_id` 原为路径+内容哈希，不含 source——两个仓库含相同内容文件时后写者覆盖前者的行（实测 click 622→621 静默丢块）→ 行键改 `source:chunk_id` 复合键 + 回归测试，三仓块数跨轮稳定 ✔。此坑对未来「多仓库知识网格」是地基级修复。
- **下一步（≤2 条）**：① EXP-03 Cartographer 模块地图（LLM 仅命名，便宜档 effort=low）；② 顺带把 `forge` 命令接到 `ingest_repo`（EXP-05 前的过渡）。

### EXP-03：Cartographer 模块地图 + 模型路由层（2026-10-28，首次真实计费调用）

- **目标**：AST import 图 + 角色标注 + 环检测 + 目录聚类，LLM 仅做聚类业务命名；`forge` 接通 `ingest_repo`。
- **实现**：`models/router.py`（标准库 http，ADR-0001，零新依赖；成本按峰时价折算 + `WIKIWRIGHT_BUDGET_CNY=10` 熔断，`.env` 自动加载）；`agents/cartographer.py`（文件级 import 图：AST 解析、最长前缀解析、入/出度角色、DFS 环检测、目录聚类；命名缓存于 `.cache/maps/<slug>.json` 保证 C-09）；CLI `forge <src> --map [--offline]`。
- **验收结果（金仓库，全过）**：
  - flask：24 文件/102 边/15 core/2 entry/40 cycles，聚类命名 `Web应用框架|web-application-framework`、`JSON 序列化`、`无I/O应用核心`；click：`命令行界面框架|cli-framework`；httpx：`HTTP客户端核心` + `传输层|transports`；
  - **C-09 确定性**：二次运行 map JSON 字节级一致，**零 LLM 调用**（名字按聚类文件集缓存）；
  - 环检测如实报告（flask 40 个真实环，`__init__ ↔ app` 等，非缺陷）；
  - 测试 **26 passed** + ruff/import-linter 绿；CLI 演示：`forge --map` 缓存命中 0.062s 全业务名落地。
- **成本（真实计费）**：全程约 12 次调用 ≈ **¥0.02**（budget ¥10 内的 0.2%）——成本-质量路由表（manual/02 §15）首次实战验证。
- **是否正收益**：是。验收暴露三个真问题并全部修复（见下）。
- **问题与坑（3 个，均已修复）**：
  1. **RemoteDisconnected 击穿重试**：该异常属 `http.client.HTTPException` 而非 `URLError`，DeepSeek 连接瞬断直接裸抛 → 重试捕获族扩为 `(OSError, HTTPException)`；
  2. **thinking 模型 max_tokens 截断**（最重要）：推理内容先烧 completion 预算，256 上限时验收中 3 个聚类返回空 content（debug 实测一次刚好 250/256 贴线）→ 命名改 256/1024 双档自愈重试。**EXP-04 Analyst 的 max_tokens 必须给推理留足余量，router 后续应透出 finish_reason**；
  3. **图混入 docs/examples 噪声**：flask 曾出现 8 个聚类（6 个是 docs/examples）→ Cartographer 排除集增加 `docs/examples/benchmarks`（摄取层保留它们供 wiki 引用，地图层只描述产品代码）；
  4. 阈值实证调整：core 判定 in_degree≥3（曾 2 时 flask 63% 文件都算 core）；`__init__.py` 聚合器直接判 core；EXP 指令中 routing.py/wsgi.py 在 flask 3.x 已并入 app.py/不存在，验收按现代布局解释（app.py 为 core ✔ `__main__.py` 为 entry ✔）。
- **下一步（≤2 条）**：① EXP-04 Analyst map-reduce 深读（结构化抽取契约 + 重试降级 + --budget 实战）；② 把「completion 预算-推理余量」教训写进 prompts/03 的 EXP-04 指令。

### EXP-04：Analyst map-reduce 深读（2026-10-28，含一次返工）

- **目标**：按 Cartographer 聚类并行深读，产出 `ModuleUnderstanding` 契约（每条结论带 `[path:symbol]` 引用，无证据必须 `unsure:true`），失败重试+降级 skipped，--budget 熔断。
- **实现**：契约族入 `core/contracts.py`（`Conclusion` 带 ref-or-unsure 校验器，pydantic 强制）；`agents/analyst.py`（ThreadPool 并行、契约修复式重试 3 次、引用自动核验：路径在清单+符号真实出现于文件文本、失效引用进 `invalid_refs` 不静默丢弃、按聚类文件集哈希缓存）；CLI `analyze` 命令；`ChunkStore.chunks_for_path`。**指令修正已记 prompts/03**：LangGraph 编排移至 EXP-05（单阶段无 checkpoint 价值，SqliteSaver 需新依赖走 ADR）。
- **验收结果（flask，全过）**：3 模块理解/0 skipped（≤1 ✔）；**19 条结论、0 unsure、0 失效引用**（自动核验全过）；抽 10 条人工可验：`__init__.py:Flask` 重导出、`globals.py:_cv_app` ContextVar 代理、`app.py:SecureCookieSessionInterface` 默认会话、`__main__.py:main` 入口等——语义准确；**C-09：重跑 0 调用、字节级一致**；测试 **33 passed** 全绿。
- **成本（真实计费，含返工）**：成功轮 6 调用 $0.037；**返工浪费 $0.024**（首轮 9 调用全空 content）。合计 ≈ ¥0.44。
- **是否正收益**：是（第二轮达标），但返工暴露了本 EXP 最有价值的教训。
- **问题与坑（3 个，均已修复）**：
  1. **扁平 2048 completion 预算全被推理吃光**（返工根因）：分析任务比命名任务推理量大得多，`finish_reason=length`、content 全空、9 调用白烧 $0.024 → 改为**按尝试阶梯放大 (4096, 8192, 16384)**，与修复重试对齐。命名 256/1024 双档、分析 4K/8K/16K 三档——「thinking 模型预算必须给推理留足」已成 SOP；
  2. **SQLite 跨线程**：worker 里查 `chunks_for_path` 触发 `ProgrammingError` → 改为**主线程预取上下文**，worker 只调 LLM（设计上更干净：连接不跨线程）；
  3. **LLMClient 计数器竞态**：并行 chat 下 `calls/spent` 累加加锁；测试夹具补根目录 setup.py（地图聚类需 ≥2）；测试替身加 `always` 粘性模式（队列共享被并行聚类竞争消费）。
- **下一步（≤2 条）**：① EXP-05 Scribe 撰写 + 全管线装配（LangGraph 此时引入 + ADR SqliteSaver）→ v0.1.0（PyPI 账号需就位）；② 金仓库回归测试基线建立（C-09 固化进 CI）。

### EXP-05：Scribe + LangGraph 全管线 + vault 渲染（2026-10-28，v0.1 功能闭环）

- **目标**：`wikiwright forge <repo>` 一条命令产出完整 wiki/ vault（index / modules / mermaid 架构 / 引用 / 离线 HTML）；LangGraph 装配 + SqliteSaver（ADR-0002）；回归基线入 CI。
- **实现**：`agents/scribe.py`（散文仅复述材料、8K/16K 阶梯预算、按理解内容哈希缓存）；`wiki/render.py`（确定性渲染、cluster 级 mermaid、引用最佳努力行号解析、`markdown` 单文件 HTML）；`graph/build.py`（StateGraph 五节点 + SqliteSaver checkpoint，thread_id=slug 支持断点续跑）；CLI forge 终版（--offline/--out/--cache）；`tests/fixtures/mini_repo` + 离线确定性回归入 CI。
- **验收结果（click，真实计费，全过）**：
  - 一条命令产出 vault（commit 锚定 `2247b35`）；**82 引用独立复检 100% 有效**（≥90% 门禁）；行号抽查 5/5 精确落在定义行（`core.py:989 → class Command:`）；mermaid 结构合法；index.html 离线单文件含表格与图；**重跑全部 5 个文件字节级一致（C-09）**；
  - 测试 **38 passed**（scribe/render/离线管线确定性/CLI）+ ruff/import-linter 绿。
- **成本**：click 全管线（分析+撰写+渲染）+ 误触发见坑 2，合计 < ¥0.5。
- **问题与坑（2 个，均已修复，均为测试当场抓获）**：
  1. **`.gitignore` 未锚定模式致包被静默排除**：`wiki/` 规则被 hatchling 遵循，`src/wikiwright/wiki/` 整包未进 wheel（ModuleNotFoundError）→ 运行时产物模式全部锚定根目录（`/wiki/` `/.cache/` 等），已留档 .gitignore 注释；
  2. **离线管线漏调真实 API**：cartographer 节点未透传 `offline`，`llm=None` 触发内部自建客户端，「离线」测试两次运行各产生真实命名调用（也正是 index.md 不确定的根因）→ 节点显式透传 `offline`；教训入册：**"offline" 语义必须是显式参数，禁止依赖 llm=None 隐式表达**。
- **已知偏差（记录非缺陷）**：EXP-05 指令提及 Historian 输入（W4 才实现），v0.1 Scribe 仅消费 Analyst；引用行号为最佳努力（symbol 定位），Critic（EXP-06）将补全证据闭环。
- **下一步（≤2 条）**：① v0.1.0 发版（版本号 + PyPI 发布 + CHANGELOG）——**阻塞项：PyPI 账号**；② EXP-06 Critic（W3）：证据核验闭环 + Grounding Score 徽章。

### 2026-10-28 · 全项目深度审计（EXP-05 收口后，用户指令）

- **范围**：代码、文档、一致性、卫生、安全、真实性（幻觉）六维。
- **核查结果**：
  1. **安全**：全历史密钥模式扫描（git grep 全部提交）= 零泄露；`.env`/wiki 输出确认未跟踪（check-ignore 验证）；gitleaks CI 门禁持续生效；
  2. **真实性**：click 结论 8/8 语义抽样与真实架构吻合（termui 惰性导入、ParamType 体系、CliRunner 隔离、_utils 哨兵等均为事实）；82 引用对仓库克隆原文独立复检 100% 有效；行号抽查 5/5 精确；**未发现幻觉迹象**；
  3. **一致性**：目录结构与 manual/02 §4 一致（src 十包全部就位）；git 全部 conventional commits；工作日志 140 行（<1500 卷限）；plan §8 六行进展与提交历史一一对应；两份 ADR 与实际依赖一致；
  4. **卫生**：仓库工作树仅含本次待提交变更；缓存/输出全部 gitignored 且锚定修复；fixture 为有意提交的测试数据；
  5. **文档陈旧项（本次修复）**：CLI status 占位文案过时（EXP-05 已完成）→ 更新为 v0.2；README 状态/目录树刷新为实况；
  6. **待办偏差（如实）**：W2 DoD 第②项「PyPI 发 v0.1.0」未达成——阻塞于 PyPI 账号（唯一账号缺口）；EXP-05 的 Historian 输入与 agents/prompts/ 目录外置为计划内后续项。
- **审计结论**：项目当前状态真实、一致、干净、可审计；无已知未修复缺陷。

<!-- 新条目从这里向下追加 -->
