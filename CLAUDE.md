# PM-Workstation · 项目工作手册

> 本文件是 PM-Workstation 的**总目录**，按"使用手册"组织。Claude 工具每次启动时加载；新成员可作为项目导览。详细执行细节外置到 `docs/` 各级文档；本文件只做导航。

---

## 阅读指引

首次进入从「第 1 章」顺序读（5 分钟）；接到具体任务跳「第 3 章」；排查流程问题看「第 6 章」；查命令翻「第 7 章」；了解结构看「第 8 章」。

---

## 第 1 章 · 快速开始

每次会话开始按序执行：

0. 环境自检（首次使用识别）：`python3 scripts/check_env.py` 全 PASS 才继续；FAIL 则按 [`AGENTS.md`](AGENTS.md) 启动序列步骤 0 走首次安装流程（清单/步骤/验收见 [`INSTALL.md`](INSTALL.md)）
1. `git pull origin main` — 拉取最新代码
2. 读 [`STATE.md`](STATE.md) — 当前活跃版本、决策、阻塞项
3. 读 [`config/project.yaml`](config/project.yaml) — 版本、配置、规则
4. 读 [`.agents/memory/MEMORY.md`](.agents/memory/MEMORY.md) — 用户偏好与项目反馈
5. 读 [`AGENTS.md`](AGENTS.md) — 调度逻辑、SOP、卡点①/②；随后按意图进入第 3 章任务路由

---

## 第 2 章 · 版本上下文

PM-Workstation 是**多版本并行**的工作站，每个需求独立成版。

- **当前活跃版本**：`config/project.yaml` 的 `version.current`（不写死）
- **格式与目录**：`{name}_v{major}.{minor}.{patch}`（semver）→ `versions/{name}_vX.Y.Z/` 含 `prd/`、`prototype/`、`agent_comm/`、`CHANGELOG.md`
- **匹配规则**：指定版本（如"库存调拨_v1.0"）→ 用该版本；只说名称 → 匹配最新；未指定 → `python3 scripts/version_manager.py list` 展示选择

---

## 第 3 章 · 任务手册

9 类标准任务，每类有独立 Skill / Pipeline / Agent。Claude 按意图选一类，按指引进入详细文档。

| 任务 | 入口命令 | Agent / 流水线 | 详细文档 |
|------|---------|---------------|----------|
| PRD 编写 | `/prd-write` | prd agent | [`docs/agents/prd_agent.md`](docs/agents/prd_agent.md) |
| 原型设计 | `/proto-design` | proto agent | [`docs/agents/proto_agent.md`](docs/agents/proto_agent.md) |
| 页面复原 | `/restore-page` | restore agent | [`docs/agents/restore_agent.md`](docs/agents/restore_agent.md) |
| 知识库 | `/manage-kb` | kb agent | [`docs/agents/kb_agent.md`](docs/agents/kb_agent.md) |
| UI 规范 | `/manage-ui-standard` | ui-standard agent | [`docs/agents/ui_standard_agent.md`](docs/agents/ui_standard_agent.md) |
| 版本管理 | — | 直接执行（Orchestrator） | [`docs/pipelines/version-workflow.md`](docs/pipelines/version-workflow.md) |
| 文档管理 | — | doc pipeline | [`docs/pipelines/doc-pipeline.md`](docs/pipelines/doc-pipeline.md) |
| 图表生成 | — | diagram pipeline | [`docs/pipelines/diagram-workflow.md`](docs/pipelines/diagram-workflow.md) |
| 组件开发 | — | component pipeline | [`docs/pipelines/component-workflow.md`](docs/pipelines/component-workflow.md) |
| **多任务组合** | — | 总指挥调度 | [`AGENTS.md`](AGENTS.md) 多任务规则 |

---

## 第 4 章 · 工作流程（SOP）

任何文件编辑任务的标准流程。**卡点①/② 是硬门禁**——违反即视为流程事故。

```
用户提出需求 → 探索环境 → 输出执行计划  ← 卡点①  →（批准）→ git pull → 写文件 → commit
→ 展示变更摘要  ← 卡点②  →（审查通过）→ state refresh → 完成
```

完整 SOP、卡点判定、批准信号词清单见 [`AGENTS.md`](AGENTS.md) 「文件变更流程」段。

---

## 第 5 章 · 多任务组合

| 模式 | 规则 | 典型场景 |
|------|------|----------|
| 串行（默认） | 按声明顺序执行，前失败后跳过 | 任何依赖型任务链 |
| 波次并行 | 任务书 `wave` 字段声明同 wave 步骤并行 | `restore + kb`（无依赖）、`proto + prd`（proto 有 restored 页面时） |

子任务产出统一写入 `agent_comm/{task_id}/`。

---

## 第 6 章 · 硬规则与红线

**违反以下规则即视为流程事故**。每条规则的**为什么**写在 `.agents/memory/feedback_*.md`，**怎么落地**写在 `docs/pipelines/`。

| # | 规则 | 一句话要求 |
|---|------|-----------|
| 1 | 编造零容忍 | 所有事实性声明必须溯源验证 |
| 2 | PRD 三文件同步 | MD + 主 HTML + 独立原型 HTML 必须同步修改 |
| 3 | 任务完成自动提交 | 用 `git_helper.py commit-task-complete`，不等用户提醒 |
| 4 | 可行性验证门禁 | PRD 流水线必须通过 Feasibility 阶段 |
| 5 | 原型 iframe 禁用 `loading="lazy"` | 预览环境不触发会空白 |
| 6 | `versions.zip` 永远不提交 | `.gitignore` 已排除，本地备份 |
| 7 | 流程图呈现规范 | HTML 流程图必须 flowdia 交互组件，禁止静态 PNG（标准：`docs/rules/flow-diagram-standard.md`） |

**流程红线（绝对禁止）**：

- 在 Plan Mode 下编辑文件或调用 `ExitPlanMode`（未等用户明确批准）
- 未展示 `git diff` 就执行 `git commit`
- 多文件修改一次性完成后再汇报（应逐步汇报）
- 用户未审查通过就执行 `state_manager.py refresh`
- 自纠：发现自己可能违规 → 立即停止汇报，不绕过

完整红线定义见 [`docs/rules/entry-guard.md`](docs/rules/entry-guard.md) 「流程红线」段。

---

## 第 7 章 · 工具脚本速查

| 用途 | 命令 | 触发时机 |
|------|------|----------|
| 列出版本 | `python3 scripts/version_manager.py list` | 用户未指定版本时（AGENTS.md 版本上下文） |
| 当前版本 | `python3 scripts/version_manager.py current` | 启动序列 / 需确认版本上下文时 |
| 新建版本 | `python3 scripts/version_manager.py next --desc "..."` | 用户提出新需求且明确要开新版本时 |
| 切换版本 | `python3 scripts/version_manager.py switch vX.Y.Z` | 用户明确说「切换/转到」某版本时 |
| 任务完成提交 | `python3 scripts/git_helper.py commit-task-complete <task_id> <type> <version>` | 每个任务/阶段变更完成后（SOP 流程） |
| 刷新 STATE | `python3 scripts/state_manager.py refresh` | 仅卡点②审查通过后（硬门禁） |
| 任务书校验 | `python3 scripts/task_validator.py <任务书路径>` | 每次生成任务书后、调度 Agent 前 |
| 文档体检 | `python3 scripts/doc_manager.py check` | 修改 SOP 文档后；或用户说「文档体检」 |
| 文档整理 | `python3 scripts/doc_gardener.py run` | 仅用户明确要求时（不自动运行） |
| 项目 lint | `python3 scripts/project_linter.py run` | SOP 文档批量变更的验收阶段；或用户要求时 |

---

## 第 8 章 · 项目结构

| 路径 | 作用 |
|------|------|
| `AGENTS.md` | Agent 总指挥（任务分解、SOP、卡点①/②） |
| `STATE.md` | 跨会话状态（版本进度、决策、阻塞项） |
| `CONTEXT.md` | 项目背景快照（业务上下文 + 架构决策） |
| `config/project.yaml` | 项目配置（版本、模板、规则、KB 标签） |
| `.agents/skills/{name}/SKILL.md` | Skill 入口（按任务类型触发） |
| `.agents/memory/` | 记忆与反馈（user / feedback / project / reference） |
| `docs/agents/` · `docs/pipelines/` · `docs/rules/` · `docs/verification/` | Agent 指令 / 流水线 / 编辑规范 / 检验规则 |
| `docs/knowledge-base/` | 知识库（用户画像、方法论、平台 API、爬取缓存） |
| `templates/` | 模板（PRD、原型、组件、KB、版本元数据） |
| `scripts/` | 管理脚本（version / state / git_helper / restore_pipeline / doc_*） |
| `versions/{name}_vX.Y.Z/` · `agent_comm/{task_id}/` | 每个需求的版本目录 / Agent 通信记录 |
| `_legacy_claude/` | 历史归档（仅作参考，不再更新） |

---

## 第 9 章 · Compact 指令

会话进入 compact 时，保留：当前任务类型、当前版本上下文（`config/project.yaml` 的 `version.current`）、`agent_comm/{task_id}/` 进度、待用户决策的卡点、关键约束（编造零容忍 / 可行性门禁 / PRD 三文件同步 / versions.zip 不提交）。

---

## 附录

- **工具归属**：Claude 读 `CLAUDE.md`；ZCode / Codex 读 [`AGENTS.md`](AGENTS.md)
- **历史归档**：2026-06-22 之前的入口文件在 [`_legacy_claude/`](_legacy_claude/)
- **记忆系统**：所有偏好与决策见 [`.agents/memory/MEMORY.md`](.agents/memory/MEMORY.md) 索引
- **本手册的编辑规范**：见 [`docs/rules/entry-guard.md`](docs/rules/entry-guard.md)

### 变更记录

| 日期 | 变更内容 | 同步载体 |
|------|----------|----------|
| 2026-08-11 | ①第 3 章任务表新增「UI 规范」行（`/manage-ui-standard` → `docs/agents/ui_standard_agent.md`），任务类 8 类→9 类（同步 `AGENTS.md` v2.5，引用规则 W23） | 本文件 + `AGENTS.md` + `docs/agents/ui_standard_agent.md` |
| 2026-08-10 | ①第 1 章启动列表补步骤 0 环境自检（首次使用识别；细节权威源为 AGENTS.md 启动序列 + INSTALL.md §2/§3/§5）；②头部 blockquote 3 行并 1 行、步骤 5/6 合并，保持总行数 ≤160（entry-guard §2.3） | 本文件 + `AGENTS.md` + `INSTALL.md` + `scripts/check_env.py` |
| 2026-07-28 | ①第 3 章任务表 9 类改 8 类：GrapesJS 协作移出正式路由（规划文档移至 `docs/superpowers/plans/`）、版本管理改指 `docs/pipelines/version-workflow.md`（version_agent 已删除）；②第 7 章脚本表补触发时机列并新增 `task_validator.py` 行；③按规范例外二补本变更记录 | 本文件 + `AGENTS.md` + `config/project.yaml` |
