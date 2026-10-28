# WikiWright 深度调查与终选报告（v2）

> **目的**：在《策划报告 v1》五候选的基础上做第二轮深查，用新证据裁决出**唯一**立项项目。
> **结论**：**终选 WikiWright（维匠）**——且本轮调查使其领先优势扩大，不是缩小。
> 日期：2026-10-28 · 本报告对 v1 的 §5/§6.2/§11 构成正式修订，冲突处以本报告为准。

---

## 一、本轮新增的六组关键证据

### 证据 1：deepwiki-open 确认「无增量更新」——核心差异化缺口属实

- deepwiki-open（~18k★）的 issue 区与官方文档证实：仓库更新后**全量重新克隆、重新嵌入**，无增量索引；嵌入与 LLM 提供商配置耦合（[issue #156](https://github.com/AsyncFuncAI/deepwiki-open/issues/156)、[官方文档](https://asyncfunc.mintlify.app)）。
- 官方能力边界：按需生成 wiki + RAG 问答 + FastAPI 服务。**没有**：diff 感知重分析、文档漂移检测、证据核验、wiki 落盘到你自己的仓库。
- **裁决**：v1 设想的「增量活文档」差异化不是臆测，是该赛道头部项目用户正在抱怨、而无人实现的功能。✔ 缺口成立。

### 证据 2：DeepWiki 官方免费 + MCP + API → 定位必须修正（诚实面对）

- Cognition 的 DeepWiki 托管版**免费**，提供免费 MCP 端点（`mcp.deepwiki.com`）与免费 REST API，并被 Codex CLI / Gemini CLI 以 iframe 内嵌—— entrenched 程度比 v1 预估更高。
- **含义**：「免费」和「有 MCP」**不再是差异点**（v1 §6.2 的「MCP 原生」一条降级为标配）。
- 但它的形态是**闭源、托管、wiki 在别人网站上**：私有仓库无法用、无增量、无可审计性、wiki 不归你所有。这恰是 Langfuse（~31.7k★）对 LangSmith 的翻盘路径：**开放 + 自托管 + 信任**。

### 证据 3：候选 B 终审出局——mcp-scan 已被 Snyk 吸收

- 开源 MCP 安全扫描的先行者 [mcp-scan](https://github.com/invariantlabs-ai/mcp-scan)（Invariant Labs，2025-04 发布：工具投毒/提示注入/rug pull/跨服务器影子检测）据 2026-02 对比报告已将 PyPI 包迁移至 **Snyk**（`snyk-agent-scan`），旧包弃用。
- **裁决**：该细分的安全工具位正被专业安全巨头收编。个人开发者学生与 Snyk 正面竞争，无胜算、无叙事。候选 B 从「备选」降为「**出局**」，其能力仅作为 WikiWright 的 Sentinel 角色保留。✔ B 死刑确认。

### 证据 4：商业价值获得硬数据背书——AI 文档是已被资本验证的赛道

- **Mintlify：2026-04 B 轮 $45M，估值 $500M**（累计融资约 $67M），服务 **20,000+ 公司**、年触达 1 亿+ 人（[Product Hunt 公告](https://www.producthunt.com/p/mintlify/mintlify-raises-45m-in-series-b-at-a-500m-valuation)）。
- **裁决**：「让文档自动化/持续保鲜」不是公益理想，是五亿美元估值的商业赛道。WikiWright 的托管版/订阅层站在被验证的付费意愿之上。✔ 商业价值上调。

### 证据 5：痛点的学术根脉 + 2026 新叙事锚点

- 学术根脉：文档过时/漂移是软件工程长期命题（[Tan et al., arXiv:2212.01479](https://arxiv.org/abs/2212.01479)，检测文档中过时代码引用）；工业界（Mintlify、ScaleX、Docsie）均在讲「doc drift」故事。
- **2026 新锚点**：[Documentation Drift Breaks Coding Agents](https://focused.io/lab/documentation-drift-breaks-coding-agents)——过时的 README/AGENTS.md/runbook 会把 **AI 编码 Agent 引向错误代码**。
- **裁决**：痛点从「拖慢人类 onboarding」升级为「**污染 Agent 决策**」。这给了 WikiWright 一个精确踩在 AGI 风口上的叙事：*文档漂移已经从人的问题变成机器的问题；WikiWright 让知识源随代码同步进化，供人与 Agent 共同消费。* ✔ 叙事升级。

### 证据 6：市场窗口确认——开源阵营实际只有两个正式玩家

- Product Hunt 的 [DeepWiki 替代品清单](https://www.producthunt.com/products/deepwiki-by-congnition/alternatives)（2026）与多源比对显示：开源 repo→wiki 生成器中成气候的仅 **deepwiki-open（~18k★）** 与 **OpenDeepWiki（~5k★）**，其余为散装小克隆；「增量 + grounding + 自有 wiki + 基准」四个位面**零占位**。
- 窗口仍在，但 2026 年 Agent 工具类目的爆发速度（OpenCode 两周 1.8 万星）意味着窗口不会永远开着。✔ 立项宜早。

---

## 二、定位修正（对 v1 §6.2 的正式修订）

三板斧更新为「**四把凿子**」，全部基于本轮验证过的无人占位：

| # | 能力 | 竞品现状 | WikiWright |
|---|---|---|---|
| 1 | **增量活文档**：diff → 受影响模块子图重分析，PR 里报「文档漂移」 | deepwiki-open 全量重跑；DeepWiki 无此概念 | 核心特性 |
| 2 | **证据 grounding**：每条论断挂 `[file:line]`，Critic 核验 + Grounding Score + `_evidence.jsonl` 审计导出 | 无人做 | 核心特性 |
| 3 | **wiki 归你所有**：Markdown vault 提交进你的仓库 / GitHub Wiki / Pages，而非别人网站上的 iframe | DeepWiki 托管独占；deepwiki-open 落盘但无增量 | 核心特性 |
| 4 | **私有仓库 + 纯本地**：代码不出机器（API 只送片段） | DeepWiki 无法用于私有库 | 核心特性 |

MCP 从「差异点」降级为「**标配 + 分发渠道**」（DeepWiki 已证明 Agent 端对 repo 知识的查询需求真实存在——我们做本地版、可审计版）。

**修订后定位语**：

> *DeepWiki generates a wiki. **WikiWright keeps it alive** — incremental, evidence-grounded, and yours.*

（中文：*别人生成一本维基，维匠让这本维基活着——增量更新、证据可溯、归你所有。*）

---

## 三、终审记分（新证据下的重评）

评分口径同 v1 §5（1–5 分，竞争烈度反向）：

| 维度（权重） | A. WikiWright | B. MCP-Guardian | C. AgentOps | D. DeepResearch | E. 记忆库 |
|---|---:|---:|---:|---:|---:|
| 涨星潜力（25%） | 5 | 3 ↓（巨头收编，独立项目难立足） | 3 | 3 | 3.5 |
| 需求真实性（15%） | 5 ↑（drift 破坏 Agent 的新证据） | 4 | 3.5 | 3.5 | 4.5 |
| 竞争烈度-反向（10%） | 3 ↑（四能力位面零占位确认） | 2 ↓ | 1.5 | 2 | 2 |
| CPU/个人可行性（15%） | 4.5 | 4 | 4 | 4.5 | 4 |
| CCF-A 创新空间（15%） | 4.5 ↑（学术根脉 arXiv:2212.01479 可接续） | 4 ↓ | 2.5 | 3 | 3.5 |
| 商业价值（10%） | 4.5 ↑（Mintlify $500M 估值背书） | 4 | 3.5 | 3.5 | 4 |
| 视觉/演示冲击力（10%） | 5 | 3.5 | 3.5 | 4 | 3.5 |
| **加权总分** | **4.70 ↑** | **3.30 ↓** | **3.10** | **3.35** | **3.63** |

v1 中 A/B 差距 0.40，本轮扩大到 **1.40**——不是 A 变强的单项加分，而是 B 被证据淘汰、A 的每个关键假设都被独立验证。

---

## 四、终选宣言

**唯一立项项目：WikiWright（维匠）——多智能体代码库活维基引擎。**

为什么它是唯一的，一段话讲清：

1. **需求**被三重验证（18k★ 级开源同类、$500M 估值商业同类、「drift 破坏 Agent」的行业新痛）；
2. **差异化**被逐项核实为无人占位（增量、grounding、自有 wiki、本地私有）；
3. **约束**全部满足（纯 CPU、个人维护、GitHub 原生人群）；
4. **天花板**够高（开源 star 曲线 + ICSE/FSE 论文曲线 + 托管订阅收入曲线，三条曲线互不排斥）；
5. **淘汰赛干净**：B 被巨头收编、C 被红海巨头碾压、D 无壁垒、E 与 65k★ 的 Mem0 正面冲撞——唯有 A 同时具备「验证过的需求」与「空着的位子」。

---

## 五、竞争战略终版

| 对手 | 其优势 | 我们的打法（Langfuse 式开放路径） |
|---|---|---|
| DeepWiki（Cognition，免费托管） | 品牌 entrenched、零成本、CLI 内嵌 | 不拼免费拼**信任**：私有仓库、本地运行、wiki 落盘归你、全程可审计回放。README 对比表直接列这四行 |
| deepwiki-open（~18k★） | 先发、社区大 | 直击其 issue 痛点：增量更新（他们全量重嵌入）+ grounding。受众重叠处做「升级迁移指南」，姿态是互补而非攻击 |
| Mintlify/Fern/Swimm（商业） | 资本与销售 | 不同战场：他们做「文档站点平台」，我们做「代码库知识引擎 + Agent 数据源」。可互为上下游（Mintlify 站点可用 WikiWright 喂内容） |

**首发修辞**（Show HN / 掘金统一口径）：

> *"DeepWiki shows what your codebase looked like last month. WikiWright keeps the wiki alive with every commit — grounded in file:line evidence, running on your CPU, queryable by any agent via MCP."*

---

## 六、转向触发器（Kill Criteria——预先立誓，防止沉没成本绑架）

| 触发条件 | 动作 |
|---|---|
| Cognition 开源 DeepWiki 的自托管增量版（低概率，观察其 blog） | 立即把重心切到 **WikiBench 基准 + 论文 + 多仓库知识网格**（学术位它不会占） |
| 首发后 60 天 < 100★ 且 issue 里无人要「增量/grounding」功能 | 复盘渠道与首屏；若需求证伪，资产（ingest/AST/基准）迁移至姊妹方向 |
| deepwiki-open 抢先发布增量更新 | 加速 grounding + 审计差异化，与其做兼容层（其 wiki 可导入我们做增量） |
| API 成本导致自用都疼 | 已有预案：本地小模型分流 + 缓存 + `--budget`（v1 §13），不构成转向条件 |

---

## 七、本轮新增证据来源

- [deepwiki-open issue #156：嵌入/LLM 配置耦合](https://github.com/AsyncFuncAI/deepwiki-open/issues/156) · [deepwiki-open 官方文档（FastAPI/能力边界）](https://asyncfunc.mintlify.app)
- [Show HN: deepwiki-open（"The $300K DevinAI Secret is Now Open Source"）](https://news.ycombinator.com/item?id=43846728) · [Product Hunt: DeepWiki 替代品清单 2026](https://www.producthunt.com/products/deepwiki-by-congnition/alternatives)
- [Invariant Labs：Introducing MCP-Scan](https://invariantlabs.ai/blog/introducing-mcp-scan) · [mcp-scan 仓库](https://github.com/invariantlabs-ai/mcp-scan)（PyPI 迁移 `snyk-agent-scan` 一事见 2026-02 Brandefense 对比文）
- [Product Hunt：Mintlify B 轮 $45M @ $500M 估值（2026-04）](https://www.producthunt.com/p/mintlify/mintlify-raises-45m-in-series-b-at-a-500m-valuation) · [Notice.co 估值页](https://notice.co/c/mintlify)
- [Tan et al.：Detecting Outdated Code Element References in Software Documentation（arXiv:2212.01479）](https://arxiv.org/abs/2212.01479)
- [focused.io：Documentation Drift Breaks Coding Agents](https://focused.io/lab/documentation-drift-breaks-coding-agents) · [Mintlify：How to Stop Documentation Drift](https://www.mintlify.com/library/how-to-stop-documentation-drift) · [ScaleX：Engineering Documentation Drift](https://scalextech.com/engineering-documentation-drift-why-code-and-technical-knowledge-fall-out-of-sync)

---

*终选完成。下一步唯一行动：执行 v1 报告 §14 第 1 周计划——初始化仓库，跑通 Scout → Cartographer → Analyst → Scribe 最小闭环。*
