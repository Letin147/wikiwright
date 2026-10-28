# WikiWright 操作手册与实施规范

> **文档编号**：MANUAL-02 · **域**：规范方法（`manual/`） · **维护规则**：约束条件变更须留版本痕迹；「自我进化」新规范按 §11.3 沉淀进本文件
> 配套：`plan/01`（何时做）、`prompts/03`（怎么下指令）、`reports/`（做了什么）
> 建立日期：2026-10-28 · 当前版本：v1.0

---

## 1. 本手册用途与使用法

- **每次开发前**：扫一遍 §7 约束总表（贴在显示器旁也行）；
- **每阶段开始前**：读 §2 找到本阶段的成功指标与门禁；
- **每个实验完成后**：按 §13 模板把记录追加进 `reports/` 当前卷——**没有日志的实验等于没做**；
- **每周日**：执行 §12 目录卫生三命令 + §11.2 记忆维护。

---

## 2. 阶段划分与成功指标（Stage Gate）

| 阶段 | 进入条件 | 技术成功指标 | 项目成功指标 | 退出条件（门禁） |
|---|---|---|---|---|
| **v0.1**（W1–W2） | 账号/API 就绪 | 单页 wiki 生成成功；引用锚定抽检 50 条正确率 ≥90%；全程 CPU 完成 | PyPI 可装；CI 三平台绿 | DoD 全勾 + 金仓库回归建立 |
| **v0.2**（W3–W4） | v0.1 门禁通过 | Grounding Score ≥90%；8 角色全图；增量成本比 ≤30%（改 5% 文件时） | 静默发布；HF Space demo 上线；dogfood 2 个真实仓库并留记录 | 自用无明显阻断体验 |
| **v0.3**（W5–W6） | v0.2 门禁通过 | MCP 四工具 20 连测 100% 成功；PR 漂移评论误报 ≤1/10；`--budget` 生效 | **五渠道首发**；v0.3.0 发布 | 首发 24h 内全部评论已回复 |
| **v0.4**（W7–W8+） | 首发完成 | WikiBench v0（30 仓库）跑出首组数字；QA 准确率 > 直接读码基线 | 复盘报告完成；论文选题定稿 | 数字可复现（两次运行一致） |

**正收益判定（每次实验通用）**：目标指标达标 **且** API 成本在预算内 **且** 未引入新约束违例 → 正收益；否则按 §13 模板的「问题分析」记录，失败也如实入库。

---

## 3. 数据集与金仓库

### 3.1 开发期金仓库（固定 3 个，禁止换）

| 仓库 | 选它理由 | 用途 |
|---|---|---|
| `pallets/click` | 小型（<100 文件），结构经典，MIT/BSD | 冒烟测试、快速迭代 |
| `pallets/flask` | 中型，分层清晰 | 主力开发对象 |
| `encode/httpx` | 中型，现代 async 风格 | 回归防过拟合 |

**回归机制**：锁定 commit hash，快照对比——wiki 结构/引用/图不因代码未变而变（非确定性检测）。

### 3.2 WikiBench 数据集（v0.4 建，先定 schema）

- 语料：分层抽 100 仓库（语言=Python 起步；规模小/中/大；领域多样），**只用 MIT/Apache/BSD 许可仓库**；
- 标注单元（JSONL，每行一题）：

```json
{"repo": "owner/name", "commit": "<hash>", "question": "该项目的重试策略在哪里实现？",
 "answer": "…", "evidence": ["src/x.py:120-150"], "difficulty": "easy|mid|hard", "annotator": "id"}
```

- 指标：Grounding Precision（论断有真证据比例）、QA Accuracy、Update Cost（增量/全量 token 比）、Human Utility（Likert，N≥20）。
- 标注规则：每题双标，分歧第三仲裁；禁止用生成 wiki 的同一模型出题（防循环验证）。

---

## 4. 包结构管理（一致性由结构+门禁双重保障）

```text
src/wikiwright/
├── core/            # 引擎纯逻辑：状态定义、计划、合并 —— 禁 import 任何 IO 框架
│   ├── state.py     # 全局 TypedDict 状态（唯一真源）
│   └── contracts.py # 各角色输入/输出的 pydantic 模型
├── agents/          # 8 角色，一人一文件 + prompts/（每个角色一个 .md 提示词）
│   ├── scout.py  cartographer.py  analyst.py  historian.py
│   ├── sentinel.py  scribe.py  critic.py  curator.py
│   └── registry.py  # 角色注册表：新增角色只改这里（插件式）
├── graph/           # LangGraph 编排：build.py（构图）、checkpoints.py
├── ingest/          # 克隆、打包、AST、分块、内容寻址缓存
├── wiki/            # 渲染、mermaid、交叉链接、增量合并
├── mcp/             # MCP server：search / ask / get_diagram / changes
├── models/          # 模型路由：API / Ollama / 嵌入（ONNX INT8）
├── eval/            # WikiBench、指标计算、消融脚本
├── cli/             # typer 命令 + TUI（薄壳）
└── web/             # FastAPI（薄壳，服务 Web 与 MCP）
```

**依赖方向（import-linter 强制）**：`cli/web/mcp → agents → core`；`agents → ingest/wiki/models`（仅通过 core 契约）；**禁止**：core import 任何上层；agents 互相 import。

**结构一致性检查清单**（每个 PR 自查）：① 新文件落位符合上表职责；② 无循环依赖（CI 检测）；③ 新增公开函数有类型标注+docstring；④ prompts 改动独立 commit；⑤ 测试文件镜像 src 路径（`tests/agents/test_scribe.py` ↔ `src/wikiwright/agents/scribe.py`）。

---

## 5. 框架与依赖锁定（防技术栈漂移）

| 层 | 锁定选型 | 变更规则 |
|---|---|---|
| 编排 | LangGraph 1.x（+LangChain 仅 I/O 工具层） | 升级走 ADR + 回归全绿 |
| LLM 接入 | OpenAI 兼容接口（GLM/DeepSeek/Qwen）+ Ollama 可选 | 禁绑任何厂商私有 SDK 进 core |
| 嵌入/重排 | bge-small / bge-reranker ONNX INT8 | 禁引 GPU 依赖 |
| 解析 | tree-sitter（可选件，缺失时降级正则） | 降级路径必须有测试 |
| Web | FastAPI + Jinja（阶段三才引前端框架） | **禁**在 v0.4 前引 React/Vue |
| 存储 | SQLite + 文件系统（**禁**引外部数据库服务/vector DB 服务） | 本地优先是产品定位，不是省钱妥协 |
| 质量 | ruff/pytest/pre-commit/import-linter/mypy(宽松) | 零警告门禁 |

---

## 6. 命名规范总表（全局一致，禁止随意）

| 对象 | 规范 | 示例 |
|---|---|---|
| Python 文件/函数 | snake_case | `cartographer.py` / `build_module_map()` |
| 类 | PascalCase | `GroundingReport` |
| 分支 | `feat/ww-<slug>` `fix/ww-<slug>` | `feat/ww-incremental-curator` |
| Issue 标题 | `[域] 动词+对象` | `[agent] Critic 对装饰器函数误报 ⚠` |
| Commit | Conventional Commits | `fix(curator): 只重分析受影响子图` |
| 实验 | `EXP-NN`（连续编号，不复用） | `EXP-06` |
| 报告卷 | `reports/NN-worklog.md` | `reports/01-worklog.md` |
| ADR | `docs/adr/NNNN-<slug>.md` | `docs/adr/0001-add-tree-sitter.md` |
| Wiki 输出（用户侧） | 小写连字符 md | `modules/request-handling.md` |
| 配置键 | `wikiwright.toml` 内 kebab-case | `[model] analyst-tier = "flash"` |

---

## 7. 约束条件总表（C-01 起，编号引用，改动留痕）

| # | 约束 | 理由 | 检查方式 |
|---|---|---|---|
| C-01 | 纯 CPU，无 GPU/训练 | 资源现实 | CI 无 torch-cuda 类依赖 |
| C-02 | Python 3.10–3.12；v0.4 前只解析 Python 代码库 | scope 铁律 | CI 矩阵 |
| C-03 | v0.1 交付 ≤2 周；每 EXP ≤1 天 | 防烂尾 | plan §4 |
| C-04 | 双周发版节奏 | 社区活性 | release 记录 |
| C-05 | API 预算开发期 ≤¥150/月，`--budget` 硬上限 | 成本失控防线 | `wikiwright status` 成本报表 |
| C-06 | MIT 许可；仅分析 MIT/Apache/BSD 仓库进基准 | 法律干净 | ingest 许可预检 |
| C-07 | 本地优先：核心路径无云依赖 | 定位差异点 | 架构审查 |
| C-08 | 每条 wiki 论断锚定 `commit:path[:symbol]`，行号仅展示层 | 行号漂移防线 | Critic 单测 |
| C-09 | 金仓库回归：代码未变 → wiki diff 为空 | 非确定性防线 | CI 回归 job |
| C-10 | 温度：Critic/Cartographer=0，其余 ≤0.3 | 稳定性 | 配置锁定 |
| C-11 | 新依赖必须 ADR；禁引数据库服务/重型前端(v0.4 前)/厂商私有 SDK | 防漂移 | dependabot+review |
| C-12 | 禁止提交：`wiki/` 输出、缓存、构建产物、`.env`、任何 key | 目录卫生 | CI 卫生检查+gitignore |
| C-13 | 报告滚动：单卷 >1500 行即冻结开新卷 `NN+1-worklog.md` | 防文档碎片 | 收卷时人工执行 |
| C-14 | 实验必须记日志（§13 模板），失败也记，禁止造假 | 证据链 | reports 审阅 |
| C-15 | 域隔离：六域文件夹职责见 §12，违者移位 | 防污染 | 每周自审 |
| C-16 | 主干常绿：CI 红当日修或回滚 | 可靠 | branch protection |
| C-17 | 公开渠道沟通双语文本准确，不夸大指标 | 口碑 | 发布前 checklist |
| C-18 | issue 24h 响应（哪怕只说「收到，周末处理」） | 社区信任 | 每日 30min 值班 |
| C-19 | 月度竞品巡逻（Kill Criteria 监测） | 战略 | plan §10 |
| C-20 | 任何「能不能顺便加个…」先过 §8 三问 | 防脱轨 | 准入流程 |

---

## 8. 防偏题防脱轨机制

**主题边界（IN-SCOPE / OUT-OF-SCOPE）**：

- ✅ IN：repo→wiki 生成与**增量维护**、证据 grounding、MCP 暴露、基准评测、CLI/TUI/Action 体验、Python 代码库解析。
- ❌ OUT（进 Icebox）：Web 协作平台、多用户账号系统、非 Python 语言、模型训练/微调、自动改代码的 PR 机器人、通用 chat 界面、移动端。

**新需求三问（全过才准入 issue）**：

1. 它是否让「活维基：增量、grounding、归你所有」更强？
2. 个人是否可维护（≤200 行增量或一个角色文件）？
3. 是否 CPU+预算约束内可跑？

**准入流程**：想法 → Icebox 放 7 天 → 仍想做 → 开 issue 打标签 → 入某版本 milestone → 才动手。

---

## 9. 证据一致性闭环（本项目的信任生命线）

七步链路，任何一环断裂即视为 bug：

```text
代码事实(文件+AST)
  →① Analyst 结构化理解(引用 path:symbol)
  →② Scribe 撰写论断(内联 [path:line] 展示锚)
  →③ Critic 核验(检索+AST 双通道，未锚定打 ⚠)
  →④ Grounding Report(每页评分 + _evidence.jsonl 全量导出)
  →⑤ 锚点规范(commit hash + path + symbol 唯一标识；行号每次渲染时重算)
  →⑥ 增量更新时 Curator 重校受影响锚点
  →⑦ replay 可回放任意一次运行核对上述全链
```

**禁止**：无锚点的肯定性论断；用「大概/通常」修饰代码事实；Critic 跳过（超时也要降级标记，不许静默通过）。

---

## 10. 日志与可复现规范

- **滚动卷规则（C-13）**：`reports/01-worklog.md` 超过 1500 行 → 顶部加「已封卷」标记与日期 → 新开 `reports/02-worklog.md`，卷首继承「当前状态」块。**禁止**每次实验新建文件。
- **可复现三要素**（每个 EXP 记录必含）：① `uv.lock` 快照（或注明「与 EXP-NN 相同」）；② 模型名+版本+温度；③ 输入仓库+commit hash。随机源（如有）记录种子。
- **实验记录模板**：见 §13，追加制，不改旧记录（写错了补一条勘误）。

---

## 11. 记忆体系（长短期记忆 + 工作记忆 + 自我进化）

### 11.1 长期记忆（跨会话、跨月）

- 仓库内文档：`docs/`（决策史）、`plan/01` §8（里程碑史）、`reports/` 全部卷（实验史）——对人类与 AI 都可见可查；
- AI 侧：ZCode 持久 memory（`project-wikiwright` 条目）存项目级事实，每次大节点更新。

### 11.2 短期/工作记忆（每天）

- `reports/` 当前卷**顶部「当前状态」块**：现在在哪周/哪个 EXP、卡在哪、下一步一句话。每次收工前更新——这是跨会话的接力棒（handoff）；
- 每日开场仪式即「读当前状态块」（plan §5）。

### 11.3 自我进化 skill（沉淀规则）

- **三次法则**：同一操作/坑/解释出现第 3 次 → 必须沉淀：属于操作规范的进本手册新 §，属于可复用指令的进 `prompts/03` 新 EXP 或模板节；
- 沉淀时在本文件 §16 记一行变更日志（日期+条款号+一句话）；
- 反向清理：规范被证明无效可在变更日志注明后废止，但不删除原文（保留决策史）。

---

## 12. 域隔离与目录卫生

| 域 | 文件夹 | 允许放 | 禁止放 |
|---|---|---|---|
| 报告（研究决策） | `docs/` | 策划/终选/ADR/契约文档 | 过程性日志 |
| 计划 | `plan/` | 本计划文档及其后续修订 | 代码、数据 |
| 方法 | `manual/` | 操作手册、方法论 playbook | 实验记录 |
| 指令 | `prompts/` | EXP 指令、AI 提示词资产 | 结果数据 |
| 日志 | `reports/` | 滚动工作卷、实验记录、复盘 | 代码 |
| 代码 | `src/` `tests/` `examples/` `web/` | 源码与测试 | 文档、缓存、输出 |

**每日收尾三命令（Git Bash）**：

```bash
git status --short            # 无未解释的散文件
find . -name "*.tmp" -o -name "__pycache__" -not -path "./.venv/*"   # 中间产物清零（配合 .gitignore）
wikiwright status 2>/dev/null || true   # 缓存与成本在预算内
```

临时文件一律进系统临时目录或 `.cache/`（已 gitignore），**永不**落在仓库根。

---

## 13. 实验/实现总结分析模板（每次实验后复制此模板追加进 reports 当前卷）

```markdown
## EXP-NN：<标题>（YYYY-MM-DD）
- 目标：
- 前置条件核对：
- 过程摘要（关键决策 ≤5 条）：
- 结果（对照验收标准逐条：达标/未达标 + 数字）：
- 成本（token/¥/耗时）：
- 是否正收益：是/否 —— 依据（§2 正收益判定）
- 问题与坑（含报错原文关键行）：
- 下一步（≤2 条）：
```

---

## 14. 小白新生指南：如何用这套体系管理生产一个项目

1. **别背体系，走流程**：每天只接触四个文件——早上读 `plan/01` §9 和 `reports/` 当前卷状态块，白天按 `prompts/03` 下指令，晚上按 §13 模板记日志，周日 30 分钟更新 `plan/01` §8。
2. **一切有模板**：不知道怎么写，就抄模板（EXP 指令、日志、ADR、复盘）；模板不会让你出彩，但保证你不脱轨。
3. **不懂的代码不进库**：AI 生成的每一段，让它自己解释一遍（指令见 `prompts/03` §1 规范），解释不通就重写或简化。
4. **失败是素材不是耻辱**：C-14 要求失败实验照样记录——复盘里的坑比成功更有价值（面试讲项目时尤其如此）。
5. **每周只问三个问题**：DoD 达标了吗？目录干净吗？下周只做一件事的话做什么？

---

## 15. 资源/模型/框架速查（所需什么，一张表）

| 类别 | 清单 |
|---|---|
| 模型（角色路由） | Cartographer/Historian/Sentinel→便宜档(GLM-4-Flash 级)；Analyst/Scribe/Critic→主力档(GLM-4.x/DeepSeek 级，Critic 温度 0)；Curator→规则+便宜档；嵌入 bge-small ONNX |
| 框架 | LangGraph 1.x、LangChain(I/O)、typer/rich/textual、FastAPI、MCP 官方 SDK(v2)、tree-sitter(可选) |
| 平台 | GitHub、PyPI、HF Space、Gitee、五首发渠道（plan §2.4） |
| 账号密钥 | GitHub PAT、LLM API key、HF token、PyPI token（全部环境变量/Secrets，永不入库） |
| 数据 | 金仓库×3、WikiBench(30→100)、badcase 库（`manual/04` §8） |

---

## 16. 变更日志（规范自我进化的留痕）

| 日期 | 条款 | 变更 |
|---|---|---|
| 2026-10-28 | 全文 | v1.0 建立 |
