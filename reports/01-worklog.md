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

<!-- 新条目从这里向下追加 -->
