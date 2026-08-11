#!/usr/bin/env python3
"""
项目架构 Linter — 校验项目结构完整性

命令:
  check          全量检查，输出所有发现
  check --json   JSON 格式输出
  fix            自动修复安全项（创建缺失目录、补充权限）
  report         汇总报告（仅统计计数）
"""

import argparse
import json
import os
import re
import stat
import sys
import yaml
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config" / "project.yaml"
STATE_FILE = PROJECT_ROOT / "STATE.md"
ENTRY_FILE = PROJECT_ROOT / "AGENTS.md"  # ZCode/跨平台入口（原 CLAUDE.md）
VERSIONS_DIR = PROJECT_ROOT / "versions"

# 严重性常量
SEV_ERROR = "error"
SEV_WARN = "warning"
SEV_INFO = "info"

# 必须存在的目录（ZCode 适配后的新结构）
REQUIRED_DIRS = [
    "scripts",
    "docs/pipelines",
    "docs/verification",
    "docs/knowledge-base",
    "docs/agents",
    "docs/rules",
    ".agents/skills",
    ".zcode/hooks",
    "versions",
    "templates",
    "config",
]

# 忽略扫描的目录（遗留归档，不参与结构校验）
IGNORED_DIRS = {"_legacy_claude", ".git", "node_modules", "__pycache__"}

# config/project.yaml 必填键路径
REQUIRED_CONFIG_KEYS = [
    ("project", "name"),
    ("version", "current"),
    ("agents", "registry"),
    ("templates",),
    ("paths",),
    ("rules",),
]

# version_metadata.yaml 必填字段
REQUIRED_META_FIELDS = ["version", "created_at", "status", "author"]
VALID_STATUSES = ["draft", "in_progress", "released", "archived"]

# AGENTS.md 必须章节（来自 docs/rules/entry-guard.md）
CLAUDE_REQUIRED_SECTIONS = [
    "启动序列",
    "版本上下文",
    "任务路由",
    "多任务组合规则",
    "SOP 步骤",
    "Compact 指令",
    "通信协议",
    "当前版本",
    "编辑规范",
]

# STATE.md 必须章节
STATE_REQUIRED_SECTIONS = [
    "## Active Work",
    "## Pipeline Status",
    "## Recent Decisions",
]

# STATE.md frontmatter 必填键
STATE_REQUIRED_FM_KEYS = ["last_updated", "current_version", "session_count"]

CLAUDE_MAX_LINES = 80  # AGENTS.md 行数上限（沿用旧名，避免大范围重命名）


class Finding:
    """单条检查发现"""

    def __init__(self, severity: str, category: str, message: str,
                 path: str = "", fixable: bool = False):
        self.severity = severity
        self.category = category
        self.message = message
        self.path = path
        self.fixable = fixable

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "path": self.path,
            "fixable": self.fixable,
        }

    def __repr__(self):
        icons = {SEV_ERROR: "[ERROR]", SEV_WARN: "[WARN] ", SEV_INFO: "[INFO] "}
        icon = icons.get(self.severity, "[????]")
        fix_tag = " 🔧" if self.fixable else ""
        return f"{icon} {self.message} ({self.category}){fix_tag}"


# ──────────────────────────────────────────────
# 检查函数
# ──────────────────────────────────────────────

def check_required_directories() -> List[Finding]:
    """验证必须存在的目录"""
    findings = []
    for dir_rel in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_rel
        if not dir_path.exists():
            findings.append(Finding(
                SEV_ERROR, "directory",
                f"目录缺失: {dir_rel}/",
                str(dir_path), fixable=True,
            ))
    return findings


def check_config_yaml() -> List[Finding]:
    """验证 config/project.yaml 结构"""
    findings = []
    if not CONFIG_FILE.exists():
        findings.append(Finding(SEV_ERROR, "config", "config/project.yaml 不存在"))
        return findings

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        findings.append(Finding(SEV_ERROR, "config", f"config/project.yaml 解析失败: {e}"))
        return findings

    for key_path in REQUIRED_CONFIG_KEYS:
        value = config
        ok = True
        for key in key_path:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                ok = False
                break
        if not ok:
            findings.append(Finding(
                SEV_ERROR, "config",
                f"config/project.yaml 缺少必填字段: {'.'.join(key_path)}",
                str(CONFIG_FILE),
            ))

    # 验证 agents.registry 每个条目有 name/file/description
    registry = config.get("agents", {}).get("registry", [])
    if isinstance(registry, list):
        for i, agent in enumerate(registry):
            if not isinstance(agent, dict):
                continue
            for field in ["name", "file", "description"]:
                if field not in agent or not agent[field]:
                    findings.append(Finding(
                        SEV_WARN, "config",
                        f"agents.registry[{i}] 缺少字段: {field}",
                        str(CONFIG_FILE),
                    ))

    return findings


def check_version_structures() -> List[Finding]:
    """验证每个版本目录结构"""
    findings = []
    if not VERSIONS_DIR.exists():
        return findings

    for d in sorted(VERSIONS_DIR.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name == "archive":
            continue

        # 必须子目录
        for subdir in ["prd", "prototype", "agent_comm"]:
            if not (d / subdir).exists():
                findings.append(Finding(
                    SEV_ERROR, "version",
                    f"版本 {d.name} 缺少子目录: {subdir}/",
                    str(d / subdir), fixable=True,
                ))

        # 必须文件
        meta_file = d / "version_metadata.yaml"
        if not meta_file.exists():
            findings.append(Finding(
                SEV_ERROR, "version",
                f"版本 {d.name} 缺少 version_metadata.yaml",
                str(meta_file),
            ))
            continue

        # 验证 metadata 内容
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
        except Exception:
            findings.append(Finding(
                SEV_ERROR, "version",
                f"版本 {d.name} 的 version_metadata.yaml 解析失败",
                str(meta_file),
            ))
            continue

        for field in REQUIRED_META_FIELDS:
            if field not in meta:
                findings.append(Finding(
                    SEV_WARN, "version",
                    f"版本 {d.name} 的 metadata 缺少字段: {field}",
                    str(meta_file),
                ))

        status = meta.get("status", "")
        if status and status not in VALID_STATUSES:
            findings.append(Finding(
                SEV_WARN, "version",
                f"版本 {d.name} 的 status 值无效: {status}",
                str(meta_file),
            ))

    return findings


def check_agent_definitions() -> List[Finding]:
    """验证 agent 定义文件"""
    findings = []

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return findings

    registry = config.get("agents", {}).get("registry", [])
    if not isinstance(registry, list):
        return findings

    for agent in registry:
        if not isinstance(agent, dict):
            continue
        name = agent.get("name", "")
        file_rel = agent.get("file", "")
        if not file_rel:
            continue

        agent_path = PROJECT_ROOT / file_rel
        if not agent_path.exists():
            findings.append(Finding(
                SEV_ERROR, "agent",
                f"Agent 定义文件不存在: {file_rel} (agent: {name})",
                str(agent_path),
            ))
            continue

        # 检查必须章节
        content = agent_path.read_text(encoding="utf-8")
        has_role = "角色定义" in content or "角色" in content
        has_sop = "SOP" in content
        if not has_role:
            findings.append(Finding(
                SEV_WARN, "agent",
                f"Agent {name} 定义缺少「角色」相关章节",
                str(agent_path),
            ))
        if not has_sop:
            findings.append(Finding(
                SEV_WARN, "agent",
                f"Agent {name} 定义缺少「SOP」相关章节",
                str(agent_path),
            ))

    return findings


def check_pipeline_docs() -> List[Finding]:
    """验证流水线文档引用"""
    findings = []

    # 从 AGENTS.md 提取引用的 pipeline 文档
    if ENTRY_FILE.exists():
        entry_content = ENTRY_FILE.read_text(encoding="utf-8")
        # 匹配 docs/pipelines/xxx.md
        pipeline_refs = re.findall(r"docs/pipelines/[\w-]+\.md", entry_content)
        pipeline_refs = list(set(pipeline_refs))
        for ref in pipeline_refs:
            if not (PROJECT_ROOT / ref).exists():
                findings.append(Finding(
                    SEV_WARN, "pipeline",
                    f"AGENTS.md 引用的流水线文档不存在: {ref}",
                    str(PROJECT_ROOT / ref),
                ))

    # 验证 pipeline 文档中引用的 agent 名
    pipelines_dir = PROJECT_ROOT / "docs" / "pipelines"
    if pipelines_dir.exists():
        for pf in pipelines_dir.glob("*.md"):
            content = pf.read_text(encoding="utf-8")
            # 检查 agent 名称引用
            agent_refs = re.findall(r"[:\s](\w+)[_\-]agent", content)
            for ref in set(agent_refs):
                # 检查是否在 registry 中
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f) or {}
                    registry_names = [
                        a.get("name", "") for a in config.get("agents", {}).get("registry", [])
                        if isinstance(a, dict)
                    ]
                    if ref not in registry_names:
                        findings.append(Finding(
                            SEV_INFO, "pipeline",
                            f"{pf.name} 引用了未注册的 agent: {ref}",
                            str(pf),
                        ))
                except Exception:
                    pass

    return findings


def check_state_md() -> List[Finding]:
    """验证 STATE.md 结构"""
    findings = []
    if not STATE_FILE.exists():
        findings.append(Finding(SEV_ERROR, "state", "STATE.md 不存在"))
        return findings

    content = STATE_FILE.read_text(encoding="utf-8")

    # 解析 frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if fm_match:
        try:
            meta = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            meta = {}
        for key in STATE_REQUIRED_FM_KEYS:
            if key not in meta:
                findings.append(Finding(
                    SEV_WARN, "state",
                    f"STATE.md frontmatter 缺少字段: {key}",
                    str(STATE_FILE),
                ))

        # 检查 current_version 一致性
        state_version = meta.get("current_version", "")
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            config_version = config.get("version", {}).get("current", "")
            if state_version and config_version and state_version != config_version:
                findings.append(Finding(
                    SEV_WARN, "state",
                    f"STATE.md current_version ({state_version}) 与 config/project.yaml ({config_version}) 不一致",
                    str(STATE_FILE),
                ))
        except Exception:
            pass
    else:
        findings.append(Finding(
            SEV_ERROR, "state", "STATE.md 缺少 frontmatter",
            str(STATE_FILE),
        ))

    # 检查必须章节
    for section in STATE_REQUIRED_SECTIONS:
        if section not in content:
            findings.append(Finding(
                SEV_WARN, "state",
                f"STATE.md 缺少章节: {section}",
                str(STATE_FILE),
            ))

    return findings


def check_claude_md() -> List[Finding]:
    """验证 AGENTS.md 行数和必须章节（函数名沿用旧名避免大范围重命名）"""
    findings = []
    if not ENTRY_FILE.exists():
        findings.append(Finding(SEV_ERROR, "entry_md", "AGENTS.md 不存在"))
        return findings

    content = ENTRY_FILE.read_text(encoding="utf-8")
    lines = content.split("\n")
    line_count = len(lines)

    if line_count > CLAUDE_MAX_LINES:
        findings.append(Finding(
            SEV_WARN, "entry_md",
            f"AGENTS.md 当前 {line_count} 行（超出限制 {CLAUDE_MAX_LINES} 行）",
            str(ENTRY_FILE),
        ))
    else:
        findings.append(Finding(
            SEV_INFO, "entry_md",
            f"AGENTS.md 当前 {line_count} 行（余量 {CLAUDE_MAX_LINES - line_count} 行）",
            str(ENTRY_FILE),
        ))

    for section in CLAUDE_REQUIRED_SECTIONS:
        if section not in content:
            findings.append(Finding(
                SEV_WARN, "entry_md",
                f"AGENTS.md 缺少必须章节: {section}",
                str(ENTRY_FILE),
            ))

    return findings


def check_hooks_executable() -> List[Finding]:
    """验证 .zcode/hooks/ 脚本有执行权限"""
    findings = []
    hooks_dir = PROJECT_ROOT / ".zcode" / "hooks"
    if not hooks_dir.exists():
        return findings

    # ZCode hook 脚本无扩展名（参照 superpowers 约定），检查所有普通文件
    for f in hooks_dir.iterdir():
        if f.name.endswith(".json") or not f.is_file():
            continue
        mode = os.stat(f).st_mode
        if not (mode & stat.S_IXUSR):
            findings.append(Finding(
                SEV_WARN, "hooks",
                f"Hook 脚本无执行权限: {f.name}",
                str(f), fixable=True,
            ))

    return findings


def check_templates() -> List[Finding]:
    """验证模板文件存在"""
    findings = []
    if not CONFIG_FILE.exists():
        return findings

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception:
        return findings

    templates = config.get("templates", {})
    if isinstance(templates, dict):
        for key, path_rel in templates.items():
            if isinstance(path_rel, str) and not (PROJECT_ROOT / path_rel).exists():
                findings.append(Finding(
                    SEV_WARN, "templates",
                    f"模板文件不存在: {path_rel} (key: {key})",
                    str(PROJECT_ROOT / path_rel),
                ))

    return findings


# ──────────────────────────────────────────────
# 执行 & 修复 & 报告
# ──────────────────────────────────────────────

def run_all_checks() -> List[Finding]:
    """执行全部检查"""
    findings = []
    findings += check_required_directories()
    findings += check_config_yaml()
    findings += check_version_structures()
    findings += check_agent_definitions()
    findings += check_pipeline_docs()
    findings += check_state_md()
    findings += check_claude_md()
    findings += check_hooks_executable()
    findings += check_templates()
    return findings


def fix_safe_issues(findings: List[Finding]) -> int:
    """自动修复可安全修复的项"""
    fixed = 0
    for f in findings:
        if not f.fixable:
            continue

        path = Path(f.path)

        if f.category == "directory":
            path.mkdir(parents=True, exist_ok=True)
            # 如果是 agent_comm 等目录，补 .gitkeep
            gitkeep = path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
            fixed += 1

        elif f.category == "hooks":
            os.chmod(str(path), os.stat(str(path)).st_mode | stat.S_IXUSR)
            fixed += 1

        elif f.category == "version":
            if path.suffix == "":
                path.mkdir(parents=True, exist_ok=True)
                gitkeep = path / ".gitkeep"
                if not gitkeep.exists():
                    gitkeep.touch()
                fixed += 1

    return fixed


def print_report(findings: List[Finding], verbose: bool = True):
    """打印报告"""
    if verbose:
        for f in findings:
            print(f)
        print()

    # 统计
    errors = [f for f in findings if f.severity == SEV_ERROR]
    warns = [f for f in findings if f.severity == SEV_WARN]
    infos = [f for f in findings if f.severity == SEV_INFO]
    fixable = [f for f in findings if f.fixable]

    print(f"总计: {len(findings)} 项 | {len(errors)} 错误 | {len(warns)} 警告 | {len(infos)} 信息 | {len(fixable)} 可自动修复")


def print_json(findings: List[Finding]):
    """JSON 格式输出"""
    data = {"findings": [f.to_dict() for f in findings]}
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="项目架构 Linter — 校验项目结构完整性",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("check", help="全量检查")
    sub.add_parser("fix", help="自动修复安全项")
    sub.add_parser("report", help="仅显示摘要")

    parser.add_argument("--json", action="store_true", help="JSON 格式输出（仅 check）")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "check":
        findings = run_all_checks()
        if args.json:
            print_json(findings)
        else:
            print_report(findings, verbose=True)
        sys.exit(1 if any(f.severity == SEV_ERROR for f in findings) else 0)

    elif args.command == "fix":
        findings = run_all_checks()
        fixable = [f for f in findings if f.fixable]
        if not fixable:
            print("[OK] 无可自动修复的项")
            sys.exit(0)

        fixed = fix_safe_issues(findings)
        print(f"[OK] 修复完成：处理 {fixed} 项")

        # 修复后再检查一次
        remaining = run_all_checks()
        errors = [f for f in remaining if f.severity == SEV_ERROR]
        if errors:
            print(f"\n仍有 {len(errors)} 个错误需要手动处理：")
            for e in errors:
                print(f"  {e}")
        sys.exit(1 if errors else 0)

    elif args.command == "report":
        findings = run_all_checks()
        print_report(findings, verbose=False)
        sys.exit(1 if any(f.severity == SEV_ERROR for f in findings) else 0)


if __name__ == "__main__":
    main()
