---
title: 项目安装与环境验收指南（INSTALL）
version: v1.0
date: 2026-08-10
status: active
---

# 项目安装与环境验收指南（INSTALL）

| 属性 | 值 |
|------|-----|
| 版本 | v1.0 |
| 适用范围 | 接收本项目分享包的 Agent / 新机器首次安装；人类用户亦可参考 |
| 创建日期 | 2026-08-10 |
| 状态 | active |
| 关联文档 | `AGENTS.md`（启动序列步骤 0）、`README.md`（人类快速开始）、`scripts/check_env.py`（自检/验收工具） |

> 本文件定义：PM-Workstation 在新环境的**安装清单、安装步骤、Agent 识别映射、验收标准**。
> 本文件不定义：任务调度逻辑（→ `AGENTS.md`）、各流水线细节（→ `docs/pipelines/`）。
> 验收唯一权威命令：`python3 scripts/check_env.py`（全 PASS 且退出码 0 = 安装完成）。

## §1 目的与适用范围

本项目是一个 **Agent 驱动的产品经理工作站**（非传统软件包）："安装"= Python 依赖就绪 + 目录结构完整 + 工具配置指向本机项目根。适用对象：

1. **其他 Agent**：收到本项目（git clone 或压缩包）后，按本文件完成安装、识别入口、执行验收
2. **本机 Agent**：每次会话启动序列步骤 0 执行 `check_env.py`，FAIL 时以本文件 §2 清单向用户展示、§3 步骤执行安装、§5 标准验收
3. 人类用户：可直接按 §3 手动执行

## §2 安装清单

> 首次使用识别命中时，Agent 须将本表展示给用户并等待同意；检查项与 `check_env.py` 七组一一对应。

| 编号 | 检查项 | 通过标准 | 缺失时的安装动作 |
|------|--------|----------|------------------|
| 1 | Python 版本 | `python3 --version` ≥ 3.9 | **用户手动安装**（Agent 不可自动安装 Python，见 §6.1） |
| 2 | Python 依赖 | requests / bs4 / yaml / lxml 可 import | `pip install -r requirements.txt`（建议先建 venv，§3 步骤 2） |
| 3 | 关键目录 | versions/docs/scripts/templates/config/.agents/skills/docs/knowledge-base 存在 | `python3 scripts/init_project.py`（§3 步骤 5） |
| 4 | 关键文件 | AGENTS.md / STATE.md / config/project.yaml 存在 | STATE.md 缺失：`python3 scripts/state_manager.py init`；其余缺失：重新获取项目包 |
| 5 | 项目配置 | project.yaml 可解析且 version.current 非空 | 修复 YAML 语法或补齐 version.current |
| 6 | hooks 可执行权限 | .zcode/hooks 三脚本有执行位（Windows 跳过） | `chmod +x .zcode/hooks/session-start .zcode/hooks/filter-bash-output .zcode/hooks/check-read-size` |
| 7 | settings.json 路径 | .zcode/settings.json 中 Write/Edit 权限路径 = 当前项目根 | 替换为当前项目根绝对路径（§3 步骤 4） |

## §3 安装步骤

> 所有命令均在**项目根目录**执行。Agent 执行前须已获得用户对 §2 清单的同意。

### 步骤 1 · 获取项目

```bash
git clone <仓库地址>          # 或解压分享包后 cd 进入
cd prd_v2                     # 进入项目根目录
```

### 步骤 2 · 安装 Python 依赖

```bash
python3 -m venv .venv && source .venv/bin/activate   # macOS/Linux（可选但推荐）
pip install -r requirements.txt                      # 运行依赖（4 个）
pip install -r requirements-dev.txt                  # 开发依赖（可选，仅跑测试/lint 时需要）
```

### 步骤 3 · hooks 赋可执行权限

```bash
chmod +x .zcode/hooks/session-start .zcode/hooks/filter-bash-output .zcode/hooks/check-read-size
```

### 步骤 4 · 修正 settings.json 权限路径

> 仓库内 `.zcode/settings.json` 的 Write/Edit 权限硬编码了原机器的绝对路径，新机器必须替换为当前项目根，否则文件写入权限不生效。

```bash
python3 - <<'EOF'
import json, re
from pathlib import Path
root = Path.cwd()
p = root / ".zcode" / "settings.json"
s = json.loads(p.read_text(encoding="utf-8"))
def fix(entry):
    m = re.match(r"^(Write|Edit)\(.+/\*\*\)$", str(entry))
    return f"{m.group(1)}({root}/**)" if m else entry
s["permissions"]["allow"] = [fix(e) for e in s["permissions"]["allow"]]
p.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("已指向:", root)
EOF
```

### 步骤 5 · 修复目录/文件结构（仅 §2 编号 3/4 失败时）

```bash
python3 scripts/init_project.py "PM-Workstation"   # 重建缺失目录（不动已有文件）
python3 scripts/state_manager.py init              # 仅 STATE.md 缺失时
```

### 步骤 6 · 验收

```bash
python3 scripts/check_env.py    # 7 PASS / 0 FAIL，退出码 0
```

## §4 Agent 识别映射

| 文件 / 目录 | 作用 | 何时读取 |
|-------------|------|----------|
| `AGENTS.md` | 总指挥入口：SOP、卡点①/②、任务路由、启动序列 | 任何 Agent 启动必读（最高优先级） |
| `CLAUDE.md` | Claude 工具专属入口（项目手册导航） | Claude Code / Desktop 启动时 |
| `.zcode/settings.json` | ZCode 权限 + hooks 注册 | 工具自动加载，勿手改（除 §3 步骤 4） |
| `.agents/skills/*/SKILL.md` | 5 个 Skill 入口（prd-write / proto-design / restore-page / manage-kb / manage-version） | 命中任务类型时触发 |
| `STATE.md` | 跨会话状态（当前版本、阻塞项） | 启动序列步骤 1 |
| `config/project.yaml` | 当前版本、路径、规则配置 | 启动序列步骤 2 |
| `.agents/memory/MEMORY.md` | 用户偏好与项目反馈索引 | 启动序列 |
| `README.md` | 人类快速开始 | 参考，非 Agent 权威源 |

> 启动序列固定顺序：步骤 0 环境自检（`check_env.py`）→ 读 STATE.md → 读 config/project.yaml → 意图分类（详见 `AGENTS.md`「启动序列」）。

## §5 验收标准

| 编号 | 验收项 | 机器可验命令 | 通过标准 |
|------|--------|--------------|----------|
| 1 | 整体环境 | `python3 scripts/check_env.py; echo $?` | 7 PASS / 0 FAIL 且退出码 0【机器可验】 |
| 2 | 版本上下文 | `python3 scripts/version_manager.py current` | 输出版本名（与 project.yaml version.current 一致）【机器可验】 |
| 3 | 结构完整 | `python3 scripts/project_linter.py run` | 无 error 级发现【机器可验】 |
| 4 | 测试套件（可选） | `pip install -r requirements-dev.txt && make test` | pytest 全绿【机器可验】 |

> 验收 FAIL 时：Agent 汇报失败项与修复提示并停止，**禁止进入意图分类**（AGENTS.md 启动序列步骤 0 硬门禁）。

## §6 常见问题

1. **Python 未安装或 < 3.9**：Agent 不可自动安装 Python，须提示用户手动安装（macOS: `brew install python@3.11`；或 python.org 安装包），装完重跑验收
2. **路径含中文/空格**（如本项目 `工作文件`）：所有 shell 命令路径加双引号；Python 脚本内部用 pathlib 不受影响
3. **pip 权限不足**：使用 venv（§3 步骤 2）或 `pip install --user -r requirements.txt`
4. **Windows**：hooks 检查自动 SKIP（无需 chmod）；建议 WSL 环境获得完整体验
5. **lxml 安装失败**：先 `pip install --upgrade pip` 再重试（ wheels 覆盖主流平台）
6. **settings.json 替换后仍 FAIL**：确认 Write 与 Edit 两条权限均已替换，且路径无尾部空格
7. **可选能力**：页面复原/原型预览的浏览器自动化依赖 Playwright（脚本侧：`pip install playwright && playwright install chromium`；主会话侧：Playwright MCP），属工具侧配置，不在本安装范围内，缺失不阻断验收

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-10 | v1.0 | 首次创建：安装清单 §2 / 安装步骤 §3 / Agent 识别映射 §4 / 验收标准 §5，配套环境自检脚本与入口启动序列步骤 0 | 本文件 + `scripts/check_env.py` + `AGENTS.md` + `CLAUDE.md` + `README.md` |
