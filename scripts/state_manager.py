#!/usr/bin/env python3
"""
STATE.md Manager — 管理项目跨会话状态文件

命令:
  init                           初始化 STATE.md（如已存在则跳过）
  read                           输出当前 STATE.md 内容
  update-version <version>       更新 current_version 字段
  record-decision <text>         追加决策到 Recent Decisions
  refresh                        扫描所有版本，重建 Pipeline Status 表
"""

import sys
import os
import re
import yaml
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(os.environ.get("PM_PROJECT_ROOT") or Path(__file__).resolve().parent.parent).resolve()
STATE_FILE = PROJECT_ROOT / "STATE.md"
CONTEXT_FILE = PROJECT_ROOT / "CONTEXT.md"
CONFIG_FILE = PROJECT_ROOT / "config" / "project.yaml"
VERSIONS_DIR = PROJECT_ROOT / "versions"


def read_file(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_file(path: Path, content: str):
    # S4: 带锁写入，服务端多任务并发安全（scripts 目录在 sys.path，可直接 import utils）
    from utils.filelock import safe_write
    safe_write(str(path), content)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML frontmatter，返回 (metadata_dict, body_text)"""
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}
        return meta, match.group(2)
    return {}, content


def build_frontmatter(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, str):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def init_state():
    """初始化 STATE.md"""
    if STATE_FILE.exists():
        print("STATE.md already exists, skipping init.")
        return

    # 从 config 读取当前版本
    config_content = read_file(CONFIG_FILE)
    current_version = ""
    try:
        config = yaml.safe_load(config_content)
        current_version = (config or {}).get("version", {}).get("current", "")  # S7: 配置实际嵌套在 version.current
    except Exception:
        pass

    today = datetime.now().strftime("%Y-%m-%d")
    meta = {
        "last_updated": today,
        "current_version": current_version,
        "session_count": 0,
    }

    body = """# Project State

## Active Work
- **Version**: {version}
- **Status**: (unknown — run `refresh` to update)
- **Last task**: (none)
- **Next suggested**: (run `refresh` to detect)

## Pipeline Status by Version
| Version | PRD | Prototype | Restore | Agent Tasks | Status |
|---------|-----|-----------|---------|-------------|--------|
| (run `python3 scripts/state_manager.py refresh` to populate) |

## Recent Decisions
- [{date}] Initialized STATE.md

## Blocked Items
(none currently)

## Known Issues
(none reported)
""".format(version=current_version, date=today)

    content = build_frontmatter(meta) + "\n" + body
    write_file(STATE_FILE, content)
    print(f"STATE.md created at {STATE_FILE}")


def read_state():
    """输出当前 STATE.md"""
    content = read_file(STATE_FILE)
    if not content:
        print("STATE.md not found. Run `init` first.")
        return
    print(content)


def update_version(version: str):
    """更新 current_version"""
    content = read_file(STATE_FILE)
    if not content:
        print("STATE.md not found. Run `init` first.")
        return

    meta, body = parse_frontmatter(content)
    meta["current_version"] = version
    meta["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # 更新 Active Work 段
    body = re.sub(
        r"(\*\*Version\*\*:\s).*",
        f"\\1{version}",
        body
    )

    content = build_frontmatter(meta) + "\n" + body
    write_file(STATE_FILE, content)
    print(f"Updated current_version to: {version}")


def record_decision(text: str):
    """追加决策到 Recent Decisions"""
    content = read_file(STATE_FILE)
    if not content:
        print("STATE.md not found. Run `init` first.")
        return

    meta, body = parse_frontmatter(content)
    meta["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    today = datetime.now().strftime("%Y-%m-%d")
    decision_line = f"- [{today}] {text}"

    # 在 Recent Decisions 段追加
    if "## Recent Decisions" in body:
        parts = body.split("## Recent Decisions", 1)
        # 在第一个子标题之前插入
        after = parts[1]
        # 找下一个 ## 标题的位置
        next_section = re.search(r"\n## ", after)
        if next_section:
            insert_pos = next_section.start()
            body = parts[0] + "## Recent Decisions" + after[:insert_pos] + decision_line + "\n" + after[insert_pos:]
        else:
            body = parts[0] + "## Recent Decisions" + after.rstrip() + "\n" + decision_line + "\n"
    else:
        body += f"\n## Recent Decisions\n{decision_line}\n"

    content = build_frontmatter(meta) + "\n" + body
    write_file(STATE_FILE, content)
    print(f"Recorded decision: {decision_line}")


def scan_version(version_dir: Path) -> dict:
    """扫描单个版本目录，返回状态信息"""
    info = {
        "name": version_dir.name,
        "has_prd": False,
        "has_proto": False,
        "has_restore": False,
        "agent_tasks": 0,
        "status": "unknown",
    }

    # 检查 PRD
    prd_dir = version_dir / "prd"
    if prd_dir.exists():
        prd_files = [f for f in prd_dir.iterdir() if f.suffix in (".md", ".html") and not f.name.startswith(".")]
        info["has_prd"] = len(prd_files) > 0

    # 检查 Prototype
    proto_dir = version_dir / "prototype"
    if proto_dir.exists():
        proto_files = [f for f in proto_dir.iterdir()
                       if f.suffix in (".html", ".png") and not f.name.startswith(".")]
        info["has_proto"] = len(proto_files) > 0
        # 检查 restored 目录
        restored_dir = proto_dir / "restored"
        if restored_dir.exists() and any(restored_dir.iterdir()):
            info["has_restore"] = True

    # 检查 agent_comm 任务
    comm_dir = version_dir / "agent_comm"
    if comm_dir.exists():
        task_dirs = [d for d in comm_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        info["agent_tasks"] = len(task_dirs)

    # 读取 version_metadata.yaml
    meta_file = version_dir / "version_metadata.yaml"
    if meta_file.exists():
        try:
            meta_content = yaml.safe_load(read_file(meta_file))
            info["status"] = meta_content.get("status", "unknown") if isinstance(meta_content, dict) else "unknown"
        except Exception:
            pass

    return info


def refresh():
    """扫描所有版本，重建 Pipeline Status 表"""
    content = read_file(STATE_FILE)
    if not content:
        print("STATE.md not found. Run `init` first.")
        return

    meta, body = parse_frontmatter(content)
    meta["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    # 读取当前版本
    current_version = meta.get("current_version", "")

    # 扫描所有版本
    versions = []
    if VERSIONS_DIR.exists():
        for d in sorted(VERSIONS_DIR.iterdir()):
            if d.is_dir() and not d.name.startswith(".") and d.name != "archive":
                versions.append(scan_version(d))

    # 构建表格
    table_lines = [
        "| Version | PRD | Prototype | Restore | Agent Tasks | Status |",
        "|---------|-----|-----------|---------|-------------|--------|",
    ]
    for v in versions:
        marker = " ⭐" if v["name"] == current_version else ""
        prd = "✅" if v["has_prd"] else "⏳"
        proto = "✅" if v["has_proto"] else "⏳"
        restore = "✅" if v["has_restore"] else "—"
        table_lines.append(
            f"| {v['name']}{marker} | {prd} | {proto} | {restore} | {v['agent_tasks']} | {v['status']} |"
        )

    table = "\n".join(table_lines)

    # 替换 Pipeline Status 段
    pattern = r"## Pipeline Status by Version\n.*?(?=\n## |\Z)"
    replacement = f"## Pipeline Status by Version\n{table}\n"

    if re.search(pattern, body, re.DOTALL):
        body = re.sub(pattern, replacement, body, flags=re.DOTALL)
    else:
        body += f"\n{replacement}"

    # 更新 Active Work 段
    active_info = next((v for v in versions if v["name"] == current_version), None)
    if active_info:
        body = re.sub(
            r"(\*\*Version\*\*:\s).*",
            f"\\1{current_version}",
            body
        )
        body = re.sub(
            r"(\*\*Status\*\*:\s).*",
            f"\\1{active_info['status']}",
            body
        )

    content = build_frontmatter(meta) + "\n" + body
    write_file(STATE_FILE, content)
    print(f"Refreshed STATE.md with {len(versions)} versions.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        init_state()
    elif command == "read":
        # S5: --json 输出结构化 frontmatter + 正文（服务端调用用）
        if "--json" in sys.argv:
            import json
            content = read_file(STATE_FILE)
            if not content:
                print(json.dumps({"error": "STATE.md not found"}, ensure_ascii=False))
                sys.exit(1)
            meta, body = parse_frontmatter(content)
            print(json.dumps({"meta": meta, "body": body}, ensure_ascii=False, indent=2, default=str))
        else:
            read_state()
    elif command == "update-version":
        if len(sys.argv) < 3:
            print("Usage: state_manager.py update-version <version>")
            sys.exit(1)
        update_version(sys.argv[2])
    elif command == "record-decision":
        if len(sys.argv) < 3:
            print("Usage: state_manager.py record-decision <text>")
            sys.exit(1)
        record_decision(" ".join(sys.argv[2:]))
    elif command == "refresh":
        refresh()
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
