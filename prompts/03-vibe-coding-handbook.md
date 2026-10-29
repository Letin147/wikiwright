# Vibe Coding / Codex 实验指令手册

> **文档编号**：PROMPTS-03 · **域**：指令资产（`prompts/`） · **用途**：把「与 AI 结对开发」标准化——同一指令 → 同一流程 → 可复现结果
> 使用法：每次会话先粘贴 §2 会话头，再复制对应 EXP 指令全文；完成后按 `manual/02` §13 模板把结果记入 `reports/` 当前卷
> 建立日期：2026-10-28 · 当前版本：v1.0 · EXP 编号连续不复用

---

## 1. 指令书写规范（给 AI 下指令的五条军规）

1. **四段式结构**：每条指令 = 上下文（我是谁/项目是什么）+ 任务（做什么）+ 约束（禁止什么/边界在哪）+ 验收（怎么算完成）。模糊指令是返工之源。
2. **先复述再动手**：任何 EXP 开始前要求 AI 先输出「执行计划」（改哪些文件、顺序、测试怎么写），你确认计划合理后才允许写代码。
3. **一次一个 EXP**：绝不「顺便把 XX 也做了」——scope 膨胀是烂尾第一死因（约束 C-03、C-20）。
4. **小步提交**：每完成一个可验收单元就让 AI 停下，你跑验收命令，绿了才 commit（Conventional Commits）。
5. **解释义务**：进库的每段代码，让 AI 用 ≤5 句话解释「为什么这么写」；解释不通的代码不许进库。

---

## 2. 通用会话头（每次新会话开头粘贴）

```text
【项目上下文】
我在开发 WikiWright（维匠）：LangGraph 多智能体为 Python 代码库生成带证据引用、
随 commit 增量更新、MCP 可查询的活维基。纯 CPU，本地优先，MIT。
- 代码在 src/wikiwright/，包结构与依赖方向规则见 manual/02 §4
- 硬约束：CPU-only；禁引数据库服务/重型前端/厂商私有 SDK；温度 Critic=0 其余≤0.3
- 测试与风格：pytest + ruff，零警告；新公开函数需类型标注
- 文档真源：plan/01（计划）、manual/02（规范）、reports/（日志）
【工作规则】
1. 动手前先给我执行计划，我确认后再写代码；
2. 每个完成的单元附 ≤5 句"为什么"解释；
3. 不扩张 scope：发现相邻问题只报告，不擅自修；
4. 所有新文件落位必须符合 manual/02 §4 目录职责。
现在开始本次任务：
```

---

## 3. 十个实验指令（EXP-01 ~ EXP-10，对应八周路线）

### EXP-01 仓库骨架初始化（W1）

```text
【任务】初始化 WikiWright 仓库骨架，目标是"空但完整"——所有目录/配置/CI 就位，无业务逻辑。
【具体要求】
1. 按 manual/02 §4 生成 src 布局（core/agents/graph/ingest/wiki/mcp/models/eval/cli/web 各含
   __init__.py 与一句话职责 docstring）；
2. pyproject.toml：uv 管理，Python >=3.10,<3.13，deps 仅 typer/rich/langchain-core/langgraph/
   pydantic（其余后补），dev 组含 ruff/pytest/pre-commit/import-linter/mypy；
3. CLI 入口 wikiwright --version（typer），空命令 forge/serve/status 占位；
4. .github/workflows/ci.yml：三平台矩阵(ubuntu/macos/windows)×Python(3.10/3.11/3.12)，
   步骤=ruff check → pytest → import-linter → 目录卫生检查（禁止 wiki/、*.tmp、.env 入库）；
5. CONTRIBUTING.md / LICENSE(MIT) / .gitignore / ISSUE_TEMPLATE（含 manual/02 §6 标签体系）。
【验收】干净机器上：git clone → uv sync → wikiwright --version 输出版本号；CI 全绿。
【禁止】实现任何角色逻辑；引入本清单外依赖。
```

### EXP-02 Scout 摄取管线（W1）

```text
【任务】实现 Scout：给定 repo URL 或本地路径，产出分块库。
流程：浅克隆(支持 ghproxy 镜像前缀) → 过滤(vendor/测试/二进制/许可白名单预检) →
读取文件 → 路径感知分块(按类/函数边界，回退固定行数) → 内容寻址存储(sha256) → SQLite FTS5 索引。
落位：src/wikiwright/ingest/；对外只暴露 ingest_repo(source, cache_dir) -> IngestResult。
【验收】对 pallets/click、pallets/flask、encode/httpx 各跑一次：分块数合理、FTS5 可查
"decorator"命中相关块；重复执行第二次命中缓存零成本；全部测试通过（mock 网络）。
【禁止】调用任何 LLM；GPU 依赖；把克隆内容写进仓库目录（必须进 .cache/）。
```

### EXP-03 Cartographer 模块地图（W2）

```text
【任务】实现 Cartographer：基于 ingest 结果构建模块依赖图。
规则：解析 import（ast 模块，tree-sitter 可选加速）→ 归并为模块级有向图 → 识别入口/核心/边缘
模块（入度/出度+路径启发）→ 输出 ModuleMap（pydantic 模型，含每模块：路径集、依赖、角色标签）。
LLM 仅用于给模块起"业务名"（便宜档，温度 0）。
【验收】flask 的 ModuleMap：wsgi/app/routing 等核心模块被正确识别；图无环检测通过；
对金仓库人工抽查 3 个模块标签合理；代码未变时两次运行 ModuleMap diff 为空（C-09）。
【禁止】LLM 参与图结构判定；分析非 Python 文件。
```

### EXP-04 Analyst 深读（W2）

> **2026-10-28 执行修正**：LangGraph map-reduce 编排移至 EXP-05 全管线装配时引入（单阶段加图层无 checkpoint 价值，且 SqliteSaver 需新增依赖须走 ADR）；本 EXP 以 ThreadPool 实现同等并行语义。max_tokens 预算按 EXP-03 教训上调至 2048。

```text
【任务】实现 Analyst 的 map-reduce：对 ModuleMap 每个模块并行深读，产出结构化理解 JSON。
每模块输出契约（pydantic 严格校验）：职责一段话；关键实体列表(名称/类型/一句话)；
对外接口；与其他模块关系；每条结论必须带 [path:symbol] 引用；无证据结论必须标 unsure:true。
实现 LangGraph map-reduce 并行节点 + 失败重试(2 次)与降级(标记模块为 skipped，不中断全局)。
【验收】flask 全仓跑通；抽 10 条结论人工核验引用真实存在；skipped 模块 ≤1；
pydantic 校验失败率 0（结构化输出重试兜底生效）；--budget 生效（超限即停并报告）。
【禁止】在结论里出现无引用的断言；温度 >0.3。
```

### EXP-05 Scribe 撰写（W2，v0.1 收口）

```text
【任务】实现 Scribe：把 Analyst/Historian 的结构化理解渲染为 wiki。
产出 wiki/ vault：index.md（总览+快速上手）、modules/<slug>.md（每模块一页：职责/入口/
依赖/关键代码段/引用列表）、architecture.md（由 ModuleMap 生成 mermaid 图，模板渲染非 LLM 画图）。
引用渲染规范：展示为 [path:line]，底层锚 = commit:path:symbol（C-08）。
【验收】wikiwright forge pallets/click 一条命令产出完整 vault；mermaid 在 GitHub 渲染无语法错；
每页底部"引用"节与正文一一对应；单文件 index.html 可离线打开。
【验收附加】引用锚定抽检 50 条正确率 ≥90%（v0.1 门禁）。
```

### EXP-06 Critic 证据核验（W3）

```text
【任务】实现 Critic：对 Scribe 产出的每条论断做证据核验。
双通道：① 检索通道——论断 → 取其引用锚 ± 邻域 → 相似度判定支持/不支持；
② AST 通道——涉及符号存在性/签名一致性检查。两通道至少一通道明确支持才通过；
未通过 → 该论断加 ⚠ 前缀并写入 GroundingReport。汇总输出每页 Grounding Score
= 通过论断/总论断，渲染为徽章；全量导出 _evidence.jsonl。
【验收】金仓库 Grounding Score ≥90%（v0.2 门禁预演）；人为注入 5 条幻觉论断全部被抓出；
Critic 温度 =0；核验日志可追溯（每条论断的通道结果落盘）。
【禁止】Critic 静默跳过（超时必须显式降级标记）。
```

### EXP-07a Historian + Sentinel 补齐（W4）

```text
【任务】Historian：GitHub API 拉取 commit/issue/release 统计与高光事件，LLM 提炼演进叙事
（生成 history.md，每事件附 commit/issue 链接）。Sentinel：依赖清单提取 + osv.dev 漏洞查询 +
LLM 风险解读（生成 security.md，风险必须附 advisory 链接）。
【验收】flask 的 history.md 时间线与真实 release 对齐；security.md 无 advisory 链接的断言为零；
两角色输出均走 pydantic 契约；API 限流处理（429 退避重试）。
```

### EXP-07b Curator 文件级增量（W4，v0.2 收口）

```text
【任务】实现 Curator 文件级增量：输入上次运行的 checkpoint 与本次 git diff →
变更文件集 → 受影响模块集（文件→模块映射反查 + 依赖图一跳邻域保守扩展）→ 仅重跑
受影响模块的 Analyst/Scribe/Critic → 合并 wiki diff → 输出"文档漂移"摘要。
【验收】flask 改 5% 文件场景：成本 ≤ 全量 30%（门禁）；未受影响页面零 diff（C-09）；
构造一个"接口变更但 wiki 未更新"用例，漂移摘要正确点名该模块。
【禁止】v0.2 就做子图级精细级联（留给 v0.4 研究点）。
```

### EXP-08 MCP Server（W5）

```text
【任务】基于 FastAPI + 官方 MCP SDK(v2) 实现 wikiwright serve：暴露四工具
wiki.search(关键词→块列表)、wiki.ask(问题→基于 wiki 的带引用回答)、
wiki.get_diagram(图名→mermaid 源)、wiki.changes(since→漂移摘要)。
与 REST 共用 service 层；工具入参出参全部 pydantic 契约。
【验收】Cursor 与 Claude 各实测 20 次调用 100% 成功（v0.3 门禁）；
ask 的回答必附引用；录屏留存；unauthorized 情况（未初始化 wiki 时）返回结构化错误而非崩溃。
```

### EXP-09 GitHub Action（W5）

```text
【任务】提供 .github/action.yml 与示例 workflow：PR 触发 → 检出 → wikiwright forge --incremental
→ 检测漂移 → 在 PR 评论（首次创建，后续编辑同一条）→ 失败不阻塞 PR（只标注）。
密钥走 secrets；提供 actionlint 通过的样例。
【验收】在示例仓库实测：改函数签名后 PR 出现正确漂移评论；误报 ≤1/10（门禁）；
无 API key 时优雅跳过并说明。
```

### EXP-10 WikiBench v0 评测（W8）

```text
【任务】搭建 eval 管线：30 个分层抽样仓库（许可白名单）→ 跑 forge → 用标注 QA 对
（manual/02 §3.2 schema）评分：QA Accuracy、Grounding Precision、Update Cost；
输出 results/ 下的 markdown 结果表与原始 JSONL。消融开关：--no-critic --no-cartographer。
【验收】两次运行指标一致（可复现门禁）；结果表可直接贴论文/报告；
基线对照（直接把 repomix 输出喂 LLM 问答）至少跑通一组。
【禁止】用同一模型既生成 wiki 又当评判而不声明（循环验证须显式标注）。
```

---

## 4. Badcase 分析指令模板（ anytime 发现问题）

```text
【上下文】+ 会话头
【任务】分析以下 badcase，禁止直接改代码：
现象：<观察到的错误行为>
期望：<正确行为>
复现：<命令/输入 + 运行 ID>
Trace/日志：<wikiwright replay <run-id> 的相关片段，或报错原文>
请输出：1) 根因假设（按可能性排序，≤3 个）；2) 每个假设的验证方法（最小实验）；
3) 推荐修复方案与影响面；4) 该 badcase 应归入哪一类（选错工具/参数错/幻觉/兜底失效/其他）。
我确认方案后再开 fix/ww-<slug> 分支修复。
```

---

## 5. 上线前 AI Code Review 指令模板（每版发布前）

```text
【任务】以严格审阅者身份 review 本分支全部 diff，输出问题清单，不做修改。
审查维度（逐项给 通过/警告/失败+证据行号）：
1) 正确性：边界条件、错误路径、非确定性来源；
2) 契约：pydantic 模型与实际数据一致；对外接口有向后兼容评估；
3) 安全：密钥泄漏、注入面（wiki 内容会被下游 Agent 消费——间接注入风险）、危险默认值；
4) 性能与成本：无失控循环、token 预算受控、缓存生效；
5) 可测性：新逻辑有对应测试；测试不是恒真断言；
6) 结构：依赖方向、文件落位、命名（manual/02 §4/§6）；
7) 文档：公开 API 有 docstring；行为变更同步到 README/manual。
```

---

## 6. 反模式清单（禁止的 vibe coding 行为）

1. ❌ 一条指令让 AI 生成整个项目/多个角色（必然失控）；
2. ❌ 接受「看起来能跑」但没有测试的代码；
3. ❌ 让 AI 直接改 main 分支；
4. ❌ 报错直接贴给 AI 说「修一下」而不问根因（用 §4 模板）；
5. ❌ 接受幻觉的行号/库名/参数——证据锚点是产品命根（C-08）；
6. ❌ 用 AI 生成测试只为凑覆盖率（恒真断言是负资产）;
7. ❌ 沉迷重构漂亮的抽象——YAGNI，v0.x 只做路线图内的事（C-20）；
8. ❌ 把 key、中间产物、大输出提交进仓库（C-12）。
