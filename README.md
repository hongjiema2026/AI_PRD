# PM-Workstation

产品经理通用项目工作站。基于多 Agent 流水线架构，实现知识库管理、需求文档编写、原型设计、版本管理和原型复原。

## 核心特性

- **多 Agent 协作**：Orchestrator 总指挥调度，专业 Agent 各司其职
- **版本隔离**：每个版本独立文件夹，PRD 和原型统一管理
- **原型复原**：输入 URL → 计划 → 爬取 → 验证，三步闭环
- **零构建依赖**：原型纯 HTML/CSS/JS，浏览器直接打开
- **全流程检验**：每个 Agent 每次任务都执行检验标准

## 快速开始

### 1. 初始化项目

```bash
python3 scripts/init_project.py "你的项目名称"
```

### 2. 创建新版本

```bash
python3 scripts/create_version.py v1.0.0
```

可选基于上一版本创建：

```bash
python3 scripts/create_version.py v1.1.0 --baseline v1.0.0
```

### 3. 复原页面原型

```bash
# 无需登录
python3 scripts/restore_pipeline/main.py https://example.com/page

# 需要账号密码
python3 scripts/restore_pipeline/main.py https://example.com/page \
  --username your_name --password your_pass

# 需要验证码
python3 scripts/restore_pipeline/main.py https://example.com/page \
  --username your_name --password your_pass --captcha 1234

# 提供 Cookie（复杂登录场景）
python3 scripts/restore_pipeline/main.py https://example.com/page \
  --cookie "session_id=xxx; token=yyy"
```

### 4. 版本管理

```bash
# 发布版本（创建归档 + CHANGELOG）
python3 scripts/version_manager.py release v1.0.0

# 归档版本（压缩为 zip）
python3 scripts/version_manager.py archive v0.1.0

# 生成 CHANGELOG
python3 scripts/version_manager.py changelog v1.0.0

# 列出所有版本
python3 scripts/version_manager.py list
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
    └─→ PM-Restore-Agent（复原工程师）
          └─ Planner → Crawler → Verifier
```

每个 Agent 都有明确的**职责、能力、SOP、检验标准**。

## 项目结构

```
.
├── AGENTS.md                    # 总指挥 Agent 定义（ZCode/跨平台入口）
├── .agents/                     # 跨平台标准目录（ZCode/Codex 等识别）
│   ├── skills/                  # 5 个 Skill（自包含调度入口）
│   │   ├── prd-write/          #   PRD 编写
│   │   ├── proto-design/       #   原型设计
│   │   ├── restore-page/       #   原型复原
│   │   ├── manage-kb/          #   知识库管理
│   │   └── manage-version/     #   版本管理
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

## 复原流水线详解

```
输入 URL
    │
    ▼
[Planner] 分析页面结构 → 生成《复原计划.md》
    │                           ├─ DOM 区块清单
    │                           ├─ 资源清单
    │                           ├─ 登录需求检测
    │                           └─ 验证检查点（10-15项）
    │
    ▼
[如需登录] Orchestrator 向用户请求凭证
    │       （账号密码 / 验证码 / Cookie）
    ▼
[Crawler] 抓取 DOM + 下载资源 + 清洗去噪
    │       ├─ 保存原始 HTML
    │       ├─ 下载 CSS/JS/图片/字体
    │       ├─ 路径改写为相对路径
    │       ├─ 去除广告/追踪脚本
    │       ├─ 生成多文件版（index.html + assets/）
    │       └─ 生成单文件版（index_inline.html）
    │
    ▼
[Verifier] 按检查点逐项验证
    │        ├─ DOM 结构匹配度（≥85%）
    │        ├─ 样式匹配度（≥90%）
    │        ├─ 资源完整性（100%）
    │        └─ 交互完整性（≥80%）
    │
    ▼
[判定]
    ├─ 总匹配度 ≥ 90%: PASS
    ├─ 总匹配度 80-89%: CONDITIONAL PASS
    └─ 总匹配度 < 80%: FAIL（最多重试3次）
```

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

## 环境要求

- **Python**: 3.9 或更高版本
- **操作系统**: macOS / Linux / Windows (WSL)
- **工作目录**: 所有脚本需在项目根目录执行

## 依赖安装

```bash
# 推荐使用虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

> 面向 Agent 的完整安装 / 首次使用识别 / 环境验收指南见 [INSTALL.md](INSTALL.md)。

## 许可证

MIT
