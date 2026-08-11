#!/usr/bin/env python3
"""
环境自检脚本 — 首次使用识别 + 安装后验收（只读，无副作用）

用法:
  python3 scripts/check_env.py

输出: 逐项 [PASS]/[FAIL]/[SKIP] + 修复提示，末尾汇总
退出码: 0 = 全部通过；1 = 存在 FAIL（判定为首次使用 / 环境缺失）

检查项口径的唯一权威源: INSTALL.md §2（安装清单）与 §5（验收标准）
触发流程见 AGENTS.md「启动序列」步骤 0
"""

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_ROOT / ".zcode" / "settings.json"
CONFIG_FILE = PROJECT_ROOT / "config" / "project.yaml"

# requirements.txt 的运行依赖（import 名, pip 名）
REQUIRED_DEPS = [
    ("requests", "requests"),
    ("bs4", "beautifulsoup4"),
    ("yaml", "pyyaml"),
    ("lxml", "lxml"),
]

REQUIRED_DIRS = [
    "versions",
    "docs",
    "docs/knowledge-base",
    "scripts",
    "templates",
    "config",
    ".agents/skills",
]

REQUIRED_FILES = [
    "AGENTS.md",
    "STATE.md",
    "config/project.yaml",
]

HOOK_SCRIPTS = [
    "session-start",
    "filter-bash-output",
    "check-read-size",
]

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"


def check_python_version():
    v = sys.version_info
    if v >= (3, 9):
        return PASS, f"Python {v.major}.{v.minor}.{v.micro}（要求 ≥ 3.9）", ""
    return FAIL, f"Python {v.major}.{v.minor}.{v.micro} 低于 3.9", \
        "Python 需用户手动安装（Agent 不可自动安装），见 INSTALL.md §6"


def check_deps():
    missing = []
    for import_name, pip_name in REQUIRED_DEPS:
        try:
            if importlib.util.find_spec(import_name) is None:
                missing.append(pip_name)
        except ImportError:
            missing.append(pip_name)
    if not missing:
        return PASS, "运行依赖齐全（requests / beautifulsoup4 / pyyaml / lxml）", ""
    return FAIL, f"缺失依赖: {', '.join(missing)}", \
        "pip install -r requirements.txt（建议先建 venv，见 INSTALL.md §3 步骤 2）"


def check_dirs():
    missing = [d for d in REQUIRED_DIRS if not (PROJECT_ROOT / d).is_dir()]
    if not missing:
        return PASS, f"关键目录齐全（{len(REQUIRED_DIRS)} 个）", ""
    return FAIL, f"缺失目录: {', '.join(missing)}", \
        "python3 scripts/init_project.py 重建目录结构（见 INSTALL.md §3 步骤 5）"


def check_files():
    missing = [f for f in REQUIRED_FILES if not (PROJECT_ROOT / f).is_file()]
    if not missing:
        return PASS, f"关键文件齐全（{len(REQUIRED_FILES)} 个）", ""
    if "STATE.md" in missing:
        return FAIL, f"缺失文件: {', '.join(missing)}", \
            "python3 scripts/state_manager.py init 重建 STATE.md；其余缺失说明仓库不完整，重新获取项目包"
    return FAIL, f"缺失文件: {', '.join(missing)}", \
        "仓库不完整，重新获取项目包（见 INSTALL.md §3 步骤 1）"


def check_config():
    if not CONFIG_FILE.is_file():
        return FAIL, "config/project.yaml 不存在", "仓库不完整，重新获取项目包"
    try:
        import yaml  # 延迟导入：缺 pyyaml 时由 check_deps 报告，此处不崩溃
    except ImportError:
        return FAIL, "无法解析 project.yaml（缺 pyyaml）", "pip install -r requirements.txt"
    try:
        data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return FAIL, f"project.yaml 解析失败: {e}", "对照 git 仓库修复 YAML 语法"
    current = (data or {}).get("version", {}).get("current")
    if current:
        return PASS, f"project.yaml 可解析，当前版本: {current}", ""
    return FAIL, "project.yaml 缺 version.current 字段", "对照 config/project.yaml 模板补齐 version.current"


def check_hooks():
    if os.name == "nt":
        return SKIP, "Windows 无文件可执行位概念，跳过 hooks 权限检查", ""
    hooks_dir = PROJECT_ROOT / ".zcode" / "hooks"
    not_exec = [h for h in HOOK_SCRIPTS
                if not (hooks_dir / h).is_file() or not os.access(hooks_dir / h, os.X_OK)]
    if not not_exec:
        return PASS, f"hooks 可执行（{len(HOOK_SCRIPTS)} 个）", ""
    return FAIL, f"hooks 缺失或无执行权限: {', '.join(not_exec)}", \
        "chmod +x .zcode/hooks/session-start .zcode/hooks/filter-bash-output .zcode/hooks/check-read-size"


def check_settings_paths():
    """settings.json 中 Write/Edit 权限硬编码绝对路径必须等于当前项目根。

    项目分享到他机后路径前缀不匹配 —— 此为「首次使用」的主要触发信号。
    """
    if not SETTINGS_FILE.is_file():
        return FAIL, ".zcode/settings.json 不存在", "仓库不完整，重新获取项目包"
    try:
        settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return FAIL, f"settings.json 解析失败: {e}", "修复 .zcode/settings.json 的 JSON 语法"
    allow = settings.get("permissions", {}).get("allow", [])
    pattern = re.compile(r"^(?:Write|Edit)\((.+)/\*\*\)$")
    recorded = {m.group(1) for entry in allow if (m := pattern.match(str(entry)))}
    if not recorded:
        return FAIL, "settings.json 未配置 Write/Edit 路径权限", \
            "按 INSTALL.md §3 步骤 4 补 Write/Edit 权限并指向当前项目根"
    expected = str(PROJECT_ROOT)
    mismatched = sorted(p for p in recorded if p != expected)
    if not mismatched:
        return PASS, "settings.json 权限路径与当前项目根一致", ""
    return FAIL, f"权限路径指向旧项目根: {'; '.join(mismatched)}", \
        f"将 .zcode/settings.json 中 Write/Edit 权限路径替换为: {expected}（见 INSTALL.md §3 步骤 4）"


CHECKS = [
    ("Python 版本", check_python_version),
    ("Python 依赖", check_deps),
    ("关键目录", check_dirs),
    ("关键文件", check_files),
    ("项目配置", check_config),
    ("hooks 可执行权限", check_hooks),
    ("settings.json 路径", check_settings_paths),
]


def main():
    results = []
    for name, fn in CHECKS:
        try:
            status, detail, hint = fn()
        except Exception as e:  # 单项异常不中断整体检查
            status, detail, hint = FAIL, f"检查执行异常: {e}", "人工排查该项"
        results.append((name, status, detail, hint))
        line = f"[{status}] {name} — {detail}"
        if status == FAIL and hint:
            line += f"\n       修复: {hint}"
        print(line)

    n_fail = sum(1 for r in results if r[1] == FAIL)
    n_pass = sum(1 for r in results if r[1] == PASS)
    n_skip = sum(1 for r in results if r[1] == SKIP)
    print("-" * 60)
    print(f"汇总: {n_pass} PASS / {n_fail} FAIL / {n_skip} SKIP（共 {len(results)} 项）")
    if n_fail:
        print("判定: 首次使用或环境缺失。请将失败项对应安装清单展示给用户（口径 INSTALL.md §2），"
              "用户同意后按 INSTALL.md §3 执行安装，完成后重跑本脚本验收。")
        return 1
    print("判定: 环境就绪，可进入正常启动序列。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
