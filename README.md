# PM-Workstation

产品经理通用项目工作站。基于多 Agent 流水线架构，实现知识库管理、需求文档编写、原型设计、版本管理、UI 规范维护和原型复原。

## 核心特性

- **多 Agent 协作**：Orchestrator 总指挥调度，专业 Agent 各司其职
- **版本隔离**：每个版本独立文件夹，PRD 和原型统一管理
- **原型复原**：输入 URL → 计划 → 爬取 → 验证，三步闭环
- **零构建依赖**：原型纯 HTML/CSS/JS，浏览器直接打开
- **全流程检验**：每个 Agent 每次任务都执行检验标准

## 环境要求与安装

### 环境要求

- **Python**: 3.9 或更高版本（`python3 --version` 自检）
- **操作系统**: macOS / Linux / Windows (WSL)
- **工作目录**: 所有脚本需在项目根目录执行

### 一键自动安装（推荐）

复制下面这句话发给当前 AI 工具，它会自动完成全部安装并验收：

> 请按 INSTALL.md 自动安装本机环境并验收至 7 项全 PASS（macOS 需 chmod hooks，Windows 用 WSL 且跳过 chmod）。

### 手动安装步骤

所有命令在**项目根目录**执行。

```bash
# 1. 获取项目并进入目录
git clone <仓库地址>
cd prd_v2

# 2. 创建虚拟环境并安装依赖
python3 -m venv .venv && source .venv/bin/activate   # macOS/Linux（Windows: .venv\Scripts\activate）
pip install -r requirements.txt                       # 运行依赖
pip install -r requirements-dev.txt                   # 开发依赖（可选，跑测试/lint 时需要）

# 3. hooks 赋可执行权限（仅 macOS/Linux；Windows 跳过）
chmod +x .zcode/hooks/session-start .zcode/hooks/filter-bash-output .zcode/hooks/check-read-size

# 4. 修正 settings.json 权限路径（新机器必须做，否则文件写入权限不生效）
#    将 .zcode/settings.json 中 Write/Edit 权限的绝对路径替换为当前项目根

# 5. 验收：7 项全 PASS 且退出码 0 即安装完成
python3 scripts/check_env.py
```

> 第 4 步 settings.json 路径替换的脚本，见 [`INSTALL.md`](INSTALL.md) §3 步骤 4。
> 关键目录/文件缺失时（验收第 3、4 项 FAIL），执行 `python3 scripts/init_project.py "PM-Workstation"` 重建目录、`python3 scripts/state_manager.py init` 补 STATE.md。

## 使用说明

### 用自然语言提需求

在当前 AI 工具中直接用自然语言提出需求，系统会自动识别任务类型并走对应流水线。任务路由共 10 类（9 类单任务 + 1 类组合任务）：

| 任务类型 | 触发示例 | 主要产出位置 |
|----------|----------|--------------|
| `prd` | "写一份购物车优化的 PRD" | `versions/{版本}/prd/{功能名}-prd.md` |
| `proto` | "根据购物车 PRD 出原型" | `versions/{版本}/prototype/proto-*.html` |
| `restore` | "复原这个线上页面做参考" | `versions/{版本}/prototype/restored/{域名}_{时间戳}/` |
| `kb` | "把这份竞品资料入库" | `docs/knowledge-base/{类型}/` + 索引更新 |
| `ui-standard` | "收录这个控件到 UI 规范" | `docs/rules/ui-standard/` |
| `version` | "新建一个版本做库存预警" | `versions/{版本}/` 目录骨架 |
| `doc` | "根据原型写操作手册" | 版本内操作文档（Markdown + docx） |
| `diagram` | "画一张库存调拨的流程图" | flowdia 交互图 |
| `component` | "做个可复用的数据表格组件" | `templates/components/` 组件模版 |
| `multi` | "写 PRD 然后出原型" | 按顺序调度多个 Agent |

### 典型场景

**场景 1 · 写一份新 PRD**

> "帮我写一份购物车优化的 PRD，目标是降低结算页跳出率 15%"

流水线：调研 → 图先行 → 撰写 → 可行性验证 → 评审 → 你确认后生成 HTML 渲染版。产出 PRD 正文 + 评审报告（评分 ≥80 才通过）+ HTML 渲染版，均在 `versions/{版本}/prd/` 下。

**场景 2 · 根据 PRD 做原型**

> "根据刚写的购物车 PRD 出原型"

流水线：架构设计 → 代码实现 → 交互测试。产出组件原型（`proto-*.html`，浏览器直接打开）+ 组装页面 + 测试报告（评分 ≥90 才通过），均在 `versions/{版本}/prototype/` 下。

**场景 3 · 复原线上页面做参考**

```bash
# 无需登录
python3 scripts/restore_pipeline/main.py https://example.com/page

# 需要账号密码
python3 scripts/restore_pipeline/main.py https://example.com/page \
  --username your_name --password your_pass

# 或用 Cookie（复杂登录场景）
python3 scripts/restore_pipeline/main.py https://example.com/page \
  --cookie "session_id=xxx; token=yyy"
```

复原结果在 `versions/{版本}/prototype/restored/` 下，浏览器打开 `index.html` 查看。

### 命令速查

```bash
# 项目初始化
python3 scripts/init_project.py "你的项目名称"

# 版本管理
python3 scripts/version_manager.py list                    # 列出所有版本
python3 scripts/version_manager.py current                 # 查看当前版本
python3 scripts/create_version.py v1.1.0 --baseline v1.0.0  # 基于上一版本创建
python3 scripts/version_manager.py release v1.0.0          # 发布版本（归档 + CHANGELOG）

# 开发（可选，需先 pip install -r requirements-dev.txt）
make test          # 运行测试
make lint          # 代码检查
make check         # lint + format + test 全检查
```

## Agent 架构

```
PM-Orchestrator（总指挥）
    │
    ├─→ PM-KB-Agent（知识库管家）
    │     └─ KB-Writer / KB-Reviewer
    │
    ├─→ PM-PRD-Agent（需求工程师）
    │     └─ Researcher → Writer → Reviewer
    │
    ├─→ PM-Proto-Agent（原型工程师）
    │     └─ Architect → Implementer → Tester
    │
    ├─→ PM-Version-Agent（版本管理员）
    │
    ├─→ PM-UIStandard-Agent（UI 规范管理员）
    │
    └─→ PM-Restore-Agent（复原工程师）
          └─ Planner → Crawler → Verifier
```

每个 Agent 都有明确的**职责、能力、SOP、检验标准**，定义见 `docs/agents/`。

## 项目结构

```
.
├── AGENTS.md                    # 总指挥 Agent 定义（ZCode/跨平台入口）
├── .agents/                     # 跨平台标准目录（ZCode/Codex 等识别）
│   ├── skills/                  # 6 个 Skill（自包含调度入口）
│   │   ├── prd-write/          #   PRD 编写
│   │   ├── proto-design/       #   原型设计
│   │   ├── restore-page/       #   原型复原
│   │   ├── manage-kb/          #   知识库管理
│   │   ├── manage-version/     #   版本管理
│   │   └── manage-ui-standard/ #   UI 规范维护
│   └── memory/                 # 跨会话记忆
├── .zcode/                      # ZCode 项目级配置
│   ├── settings.json           #   权限 + Hook 注册
│   └── hooks/                  #   SessionStart / Bash 过滤 / Read 水位
├── docs/
│   ├── agents/                  # Agent 指令文档（被 Skill 引用）
│   │   ├── orchestrator.md      #   总指挥
│   │   ├── kb_agent.md          #   知识库管家
│   │   ├── prd_agent.md         #   需求工程师
│   │   ├── prd_stages/          #   PRD 子阶段（researcher/visualizer/writer/reviewer/html_render）
│   │   ├── proto_agent.md       #   原型工程师
│   │   ├── version_agent.md     #   版本管理员
│   │   ├── ui_standard_agent.md #   UI 规范管理员
│   │   └── restore_agent.md     #   复原工程师
│   ├── rules/                   # 编辑防护规则
│   ├── pipelines/               # 流水线流程
│   ├── verification/            # 检验规则
│   └── knowledge-base/          # 跨版本知识库
├── _legacy_claude/              # 遗留归档（Claude Code 时代，不再被读取）
├── config/
│   └── project.yaml             # 全局配置
├── versions/                    # 版本管理中心
│   ├── {name}_v{X.Y.Z}/         # 每个版本独立文件夹
│   │   ├── prd/                 # 需求文档
│   │   ├── prototype/           # 原型文件
│   │   │   ├── restored/        # 复原页面
│   │   │   ├── pages/           # 手写页面
│   │   │   ├── components/      # 组件库
│   │   │   └── assets/          # 静态资源
│   │   ├── agent_comm/          # Agent 通信记录
│   │   └── version_metadata.yaml
│   └── archive/                 # 归档快照
├── scripts/
│   ├── init_project.py          # 项目初始化
│   ├── create_version.py        # 创建版本
│   ├── version_manager.py       # 版本管理
│   ├── check_env.py             # 环境自检/验收
│   ├── project_linter.py        # 结构校验
│   └── restore_pipeline/        # 复原流水线
│       ├── main.py              # 入口
│       ├── planner.py           # 计划生成
│       ├── crawler.py           # 爬虫执行
│       ├── verifier.py          # 验证对比
│       └── auth_handler.py      # 登录处理
└── templates/
    ├── prd_template.md          # PRD 模板
    ├── component_template.html  # 组件模板
    └── version_metadata_template.yaml
```

## 复原流水线

三步闭环：**Planner**（分析页面结构 + 生成复原计划 + 登录需求检测）→ **Crawler**（抓取 DOM + 下载资源 + 清洗去噪 + 生成多文件版/单文件版）→ **Verifier**（按检查点逐项验证）。

判定标准：DOM 结构匹配度 ≥85%、样式 ≥90%、资源完整性 100%、交互 ≥80%；总匹配度 ≥90% PASS，80-89% 条件通过，<80% FAIL（最多重试 3 次）。

> 流水线完整流程图与各阶段细节，见 [`操作使用说明书.html`](操作使用说明书.html) 第五章「操作流程」与 [`docs/agents/restore_agent.md`](docs/agents/restore_agent.md)。

## 检验标准

每个 Agent 每次任务执行后必须执行检验：

| Agent | 检验项 | 通过标准 |
|-------|--------|---------|
| Orchestrator | 任务书完整性、Agent 输出存在、阻塞已解决 | 全部通过 |
| KB-Agent | 文件格式、标签数量、索引更新 | 评分 ≥ 90 |
| PRD-Agent | 章节完整性、验收标准可测试 | 评分 ≥ 80 |
| Proto-Agent | 渲染正常、交互响应、控制台无报错 | 评分 ≥ 90 |
| Version-Agent | 目录结构完整、元数据正确 | 全部通过 |
| Restore-Agent | DOM≥85%、样式≥90%、资源100% | 总匹配度 ≥ 80 |

## 文档与帮助

| 文档 | 位置 | 打开方法 | 用途 |
|------|------|----------|------|
| **操作使用说明书.html** | 项目根目录 | 浏览器双击，或终端 `open 操作使用说明书.html`（macOS）/ `start 操作使用说明书.html`（Windows） | 9 章交互式完整手册（含左侧目录导航，推荐新手）；章节：认识 PM-Workstation / 快速开始 / 功能模块与 Agent / 任务路由与触发 / 操作流程 / 命令速查 / 版本管理 / 质量与检验 / 常见问题 |
| **INSTALL.md** | 项目根目录 | 文本编辑器或 Markdown 预览 | 安装清单 / 安装步骤 / Agent 识别映射 / 验收标准的**权威源**（验收命令 `python3 scripts/check_env.py`） |
| **docs/使用指南.md** | `docs/` 目录 | 文本编辑器或 Markdown 预览 | 面向人类的入门教程：环境搭建 + 5 个典型场景 + 命令速查 |
| **AGENTS.md** | 项目根目录 | 文本编辑器或 Markdown 预览 | 总指挥 Agent 的执行路由与 SOP（启动序列、卡点①/②、任务路由表），AI 工具启动时自动读取 |

> Claude 工具用户额外参考 [`CLAUDE.md`](CLAUDE.md)（Claude 专属入口）。

## 许可证

MIT
