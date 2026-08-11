#!/usr/bin/env python3
"""
文档园艺工具 — 维护文档新鲜度和一致性

命令:
  scan                       全量扫描，显示所有问题
  scan --version V           仅扫描指定版本
  prune --dry-run            预览将被移除的孤立文件
  prune                      执行移除（需逐文件确认）
  sync-index                 同步 KB 索引 (docs/knowledge-base/index.md)
  sync-metadata --version V  同步 version_metadata.yaml 文件列表
  report                     仅显示摘要
"""

import argparse
import re
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Set

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSIONS_DIR = PROJECT_ROOT / "versions"
KB_DIR = PROJECT_ROOT / "docs" / "knowledge-base"
KB_INDEX = KB_DIR / "index.md"
CONTEXT_FILE = PROJECT_ROOT / "CONTEXT.md"

SEV_ERROR = "error"
SEV_WARN = "warning"
SEV_INFO = "info"
SEV_STALE = "stale"
SEV_ORPHAN = "orphan"


class DocIssue:
    """文档问题"""

    def __init__(self, severity: str, category: str, message: str,
                 path: str = "", suggestion: str = ""):
        self.severity = severity
        self.category = category
        self.message = message
        self.path = path
        self.suggestion = suggestion

    def __repr__(self):
        icons = {
            SEV_ERROR: "[ERROR]", SEV_WARN: "[WARN] ",
            SEV_INFO: "[INFO] ", SEV_STALE: "[STALE]", SEV_ORPHAN: "[ORPHAN]",
        }
        icon = icons.get(self.severity, "[????]")
        extra = f" → {self.suggestion}" if self.suggestion else ""
        return f"{icon} {self.message} ({self.category}){extra}"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """解析 YAML frontmatter"""
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            meta = {}
        return meta, match.group(2)
    return {}, content


def get_version_dirs(version_filter: Optional[str] = None) -> List[Path]:
    """获取版本目录列表"""
    if not VERSIONS_DIR.exists():
        return []
    dirs = []
    for d in sorted(VERSIONS_DIR.iterdir()):
        if d.is_dir() and not d.name.startswith(".") and d.name != "archive":
            if version_filter and d.name != version_filter:
                continue
            dirs.append(d)
    return dirs


def _extract_proto_refs(text: str) -> Set[str]:
    """从文本中提取 proto-*.html 引用"""
    return set(re.findall(r"proto-[\w-]+\.html", text))


def _list_prd_files(version_dir: Path) -> List[Path]:
    """列出版本下的 PRD 文件"""
    prd_dir = version_dir / "prd"
    if not prd_dir.exists():
        return []
    return [f for f in prd_dir.iterdir()
            if f.suffix in (".md", ".html") and not f.name.startswith(".")]


def _list_proto_files(version_dir: Path) -> List[Path]:
    """列出版本下的原型文件"""
    proto_dir = version_dir / "prototype"
    if not proto_dir.exists():
        return []
    return [f for f in proto_dir.rglob("*.html") if not f.name.startswith(".")]


# ──────────────────────────────────────────────
# 扫描函数
# ──────────────────────────────────────────────

def cross_reference_prd_prototype(version_dir: Path) -> List[DocIssue]:
    """双向交叉引用 PRD 和原型文件"""
    issues = []
    prd_files = _list_prd_files(version_dir)
    proto_files = _list_proto_files(version_dir)

    # 收集 PRD 中引用的所有原型文件名
    referenced_protos = set()
    for prd in prd_files:
        if prd.suffix == ".md":
            content = prd.read_text(encoding="utf-8", errors="ignore")
            referenced_protos.update(_extract_proto_refs(content))

    # 也从 version_metadata.yaml 收集引用
    meta_file = version_dir / "version_metadata.yaml"
    if meta_file.exists():
        try:
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
            for pf in meta.get("prototype_files", []):
                if isinstance(pf, str):
                    referenced_protos.add(Path(pf).name)
        except Exception:
            pass

    # 实际存在的原型文件名集合
    actual_protos = {f.name for f in proto_files}

    # PRD 引用了但不存在 → 错误
    for ref in sorted(referenced_protos):
        if ref not in actual_protos:
            issues.append(DocIssue(
                SEV_ERROR, "cross_ref",
                f"PRD 引用的原型文件不存在: {ref}",
                str(version_dir / "prototype" / ref),
                "检查 PRD 中的引用或补充原型文件",
            ))

    # 原型文件存在但未被引用 → 警告
    unreferenced = actual_protos - referenced_protos
    # 排除主原型文件（*-prototype.html）
    unreferenced = {f for f in unreferenced if not f.endswith("-prototype.html")}
    for f in sorted(unreferenced):
        issues.append(DocIssue(
            SEV_WARN, "cross_ref",
            f"原型文件未被 PRD 引用: {f}",
            str(version_dir / "prototype" / f),
            "确认是否为孤立文件，或补充 PRD 引用",
        ))

    return issues


def find_orphan_prototypes(version_dir: Path) -> List[DocIssue]:
    """检测孤立的原型文件"""
    issues = []
    proto_dir = version_dir / "prototype"
    if not proto_dir.exists():
        return issues

    # 收集所有引用源
    all_refs = set()

    # 从 PRD 收集
    for prd in _list_prd_files(version_dir):
        if prd.suffix == ".md":
            all_refs.update(_extract_proto_refs(prd.read_text(encoding="utf-8", errors="ignore")))

    # 从主原型 HTML 收集
    for f in proto_dir.glob("*-prototype.html"):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            all_refs.update(_extract_proto_refs(content))
        except Exception:
            pass

    # 从 metadata 收集
    meta_file = version_dir / "version_metadata.yaml"
    if meta_file.exists():
        try:
            meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
            for pf in meta.get("prototype_files", []):
                if isinstance(pf, str):
                    all_refs.add(Path(pf).name)
        except Exception:
            pass

    # 检查 pages/ 和 components/ 下的文件
    for subdir in ["pages", "components"]:
        sub_path = proto_dir / subdir
        if not sub_path.exists():
            continue
        for f in sub_path.glob("*.html"):
            if f.name not in all_refs:
                issues.append(DocIssue(
                    SEV_ORPHAN, "orphan",
                    f"孤立文件: prototype/{subdir}/{f.name}",
                    str(f),
                    "prune 移除或 version_metadata.yaml 补录",
                ))

    return issues


def check_stale_tasks(version_dir: Path) -> List[DocIssue]:
    """检查 agent_comm/ 中的过期任务"""
    issues = []
    comm_dir = version_dir / "agent_comm"
    if not comm_dir.exists():
        return issues

    now = datetime.now()

    for task_dir in sorted(comm_dir.iterdir()):
        if not task_dir.is_dir() or task_dir.name.startswith("."):
            continue

        task_file = task_dir / "00_task.md"
        if not task_file.exists():
            issues.append(DocIssue(
                SEV_WARN, "stale_task",
                f"任务目录缺少 00_task.md: {task_dir.name}",
                str(task_dir),
            ))
            continue

        content = task_file.read_text(encoding="utf-8", errors="ignore")
        meta, _ = parse_frontmatter(content)

        status = meta.get("status", "unknown")
        created_at = meta.get("created_at", "")

        # 检查 BLOCKED 文件
        if (task_dir / "BLOCKED.md").exists():
            issues.append(DocIssue(
                SEV_INFO, "stale_task",
                f"任务被阻塞: {task_dir.name}",
                str(task_dir / "BLOCKED.md"),
            ))

        # 检查过期
        if status in ("in_progress", "pending") and created_at:
            try:
                created = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                if (now - created) > timedelta(hours=24):
                    hours = int((now - created).total_seconds() / 3600)
                    issues.append(DocIssue(
                        SEV_STALE, "stale_task",
                        f"任务超过 24h 未完成 ({hours}h): {task_dir.name} (status: {status})",
                        str(task_dir),
                        "检查是否需要重置或关闭",
                    ))
            except (ValueError, TypeError):
                pass

        # 检查已完成但缺完成标记
        completion_marker = f"<!-- AGENT_COMPLETE:"
        if status == "completed" and completion_marker not in content:
            # 检查是否有产出文件
            outputs = [f for f in task_dir.iterdir()
                       if f.is_file() and f.name != "00_task.md" and not f.name.startswith(".")]
            if not outputs:
                issues.append(DocIssue(
                    SEV_WARN, "stale_task",
                    f"已完成任务无产出文件: {task_dir.name}",
                    str(task_dir),
                ))

    return issues


def validate_kb_index() -> List[DocIssue]:
    """交叉验证 KB 索引与实际文件"""
    issues = []
    if not KB_INDEX.exists():
        issues.append(DocIssue(SEV_ERROR, "kb_index", "KB 索引文件不存在"))
        return issues

    content = KB_INDEX.read_text(encoding="utf-8")

    # 从索引中提取引用的文件名
    index_refs = set(re.findall(r"\(([a-zA-Z0-9_/][a-zA-Z0-9_/\-\.]+\.md)\)", content))

    # 扫描实际文件（排除 index.md 和非 .md 文件）
    actual_files = set()
    for f in KB_DIR.rglob("*.md"):
        if f.name == "index.md" or f.name.startswith("."):
            continue
        rel = str(f.relative_to(KB_DIR))
        actual_files.add(rel)

    # 索引引用但文件缺失
    for ref in sorted(index_refs):
        if ref not in actual_files:
            issues.append(DocIssue(
                SEV_ERROR, "kb_index",
                f"KB 索引引用的文件不存在: {ref}",
                str(KB_DIR / ref),
                "从 index.md 移除该条目",
            ))

    # 文件存在但索引未引用
    for f in sorted(actual_files):
        if f not in index_refs:
            issues.append(DocIssue(
                SEV_WARN, "kb_index",
                f"KB 文件未被索引引用: {f}",
                str(KB_DIR / f),
                "sync-index 自动补录，或手动添加到 index.md",
            ))

    return issues


def check_metadata_sync(version_dir: Path) -> List[DocIssue]:
    """验证 version_metadata.yaml 文件列表与实际文件一致"""
    issues = []
    meta_file = version_dir / "version_metadata.yaml"
    if not meta_file.exists():
        return issues

    try:
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
    except Exception:
        return issues

    # PRD 文件同步
    meta_prd = set(meta.get("prd_files", []))
    actual_prd = {str(f.relative_to(version_dir))
                  for f in _list_prd_files(version_dir)}

    for f in sorted(meta_prd - actual_prd):
        issues.append(DocIssue(
            SEV_ERROR, "metadata",
            f"metadata 列出的 PRD 文件不存在: {f}",
            str(version_dir / f),
            "sync-metadata 更新",
        ))
    for f in sorted(actual_prd - meta_prd):
        issues.append(DocIssue(
            SEV_WARN, "metadata",
            f"PRD 文件未在 metadata 中记录: {f}",
            str(version_dir / f),
            "sync-metadata 自动补录",
        ))

    # 原型文件同步
    meta_proto = set(meta.get("prototype_files", []))
    actual_proto = {str(f.relative_to(version_dir))
                    for f in _list_proto_files(version_dir)}

    for f in sorted(meta_proto - actual_proto):
        issues.append(DocIssue(
            SEV_ERROR, "metadata",
            f"metadata 列出的原型文件不存在: {f}",
            str(version_dir / f),
            "sync-metadata 更新",
        ))
    for f in sorted(actual_proto - meta_proto):
        issues.append(DocIssue(
            SEV_WARN, "metadata",
            f"原型文件未在 metadata 中记录: {f}",
            str(version_dir / f),
            "sync-metadata 自动补录",
        ))

    return issues


def check_context_freshness() -> List[DocIssue]:
    """检查 CONTEXT.md 是否过期"""
    issues = []
    if not CONTEXT_FILE.exists():
        return issues

    content = CONTEXT_FILE.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(content)

    last_updated = meta.get("last_updated", "")
    if last_updated:
        try:
            updated = datetime.strptime(str(last_updated), "%Y-%m-%d")
            if (datetime.now() - updated) > timedelta(days=30):
                days = (datetime.now() - updated).days
                issues.append(DocIssue(
                    SEV_STALE, "stale",
                    f"CONTEXT.md 已 {days} 天未更新（上次: {last_updated}）",
                    str(CONTEXT_FILE),
                    "更新 CONTEXT.md 的 last_updated 和相关章节",
                ))
        except (ValueError, TypeError):
            pass
    else:
        issues.append(DocIssue(
            SEV_WARN, "stale",
            "CONTEXT.md 缺少 last_updated 字段",
            str(CONTEXT_FILE),
        ))

    return issues


# ──────────────────────────────────────────────
# 扫描 & 修复
# ──────────────────────────────────────────────

def scan_version(version_dir: Path) -> List[DocIssue]:
    """扫描单个版本"""
    issues = []
    issues += cross_reference_prd_prototype(version_dir)
    issues += find_orphan_prototypes(version_dir)
    issues += check_stale_tasks(version_dir)
    issues += check_metadata_sync(version_dir)
    return issues


def scan_all(version_filter: Optional[str] = None) -> List[DocIssue]:
    """全量扫描"""
    issues = []
    for vd in get_version_dirs(version_filter):
        issues += scan_version(vd)
    issues += validate_kb_index()
    issues += check_context_freshness()
    return issues


def prune_orphans(version_filter: Optional[str] = None,
                  dry_run: bool = True) -> int:
    """移除孤立文件"""
    issues = []
    for vd in get_version_dirs(version_filter):
        issues += find_orphan_prototypes(vd)

    orphan_issues = [i for i in issues if i.severity == SEV_ORPHAN]
    if not orphan_issues:
        print("[OK] 无孤立文件")
        return 0

    removed = 0
    for issue in orphan_issues:
        file_path = Path(issue.path)
        if dry_run:
            print(f"[DRY-RUN] 将移除: {file_path}")
            removed += 1
        else:
            confirm = input(f"移除 {file_path}? [y/N]: ").strip().lower()
            if confirm == "y":
                file_path.unlink()
                print(f"[REMOVED] {file_path}")
                removed += 1
            else:
                print(f"[SKIP] {file_path}")

    return removed


def sync_kb_index() -> int:
    """同步 KB 索引：补录未索引的 .md 文件到方法论分类"""
    if not KB_INDEX.exists():
        print("[ERROR] KB 索引文件不存在")
        return 0

    # 扫描 methodology 目录下的实际文件
    methodology_dir = KB_DIR / "methodology"
    actual_methodology = set()
    if methodology_dir.exists():
        for f in methodology_dir.glob("*.md"):
            if not f.name.startswith("."):
                actual_methodology.add(f.name)

    # 读取当前索引内容
    content = KB_INDEX.read_text(encoding="utf-8")

    # 提取索引中已有的 methodology 文件名
    existing_refs = set(re.findall(r"\(methodology/([a-zA-Z0-9_\-]+\.md)\)", content))

    # 找到未索引的文件
    new_files = actual_methodology - existing_refs
    if not new_files:
        print("[OK] KB 索引已是最新")
        return 0

    # 读取每个新文件的 frontmatter 获取描述
    new_entries = []
    for fname in sorted(new_files):
        fpath = methodology_dir / fname
        try:
            fcontent = fpath.read_text(encoding="utf-8")
            meta, _ = parse_frontmatter(fcontent)
            title = meta.get("title", fname)
            desc = meta.get("description", title)
            # 截取第一句作为简述
            short_desc = desc.split("。")[0] if "。" in desc else desc
            new_entries.append(
                f"| [{fname}](methodology/{fname}) | {short_desc}（📝 手动录入） | {meta.get('date', 'unknown')} |"
            )
        except Exception:
            new_entries.append(
                f"| [{fname}](methodology/{fname}) | (待补充描述)（📝 手动录入） | unknown |"
            )

    # 在 methodology 表末尾追加新行
    lines = content.split("\n")
    insert_idx = None
    in_methodology_table = False
    for i, line in enumerate(lines):
        if "### 方法论 (methodology)" in line:
            in_methodology_table = True
        elif in_methodology_table and line.startswith("### "):
            # 下一个子标题前插入
            insert_idx = i
            break
        elif in_methodology_table and line.strip() == "" and i > 0:
            # 空行可能是表格结束
            prev_lines = [lines[j].strip() for j in range(max(0, i - 3), i)]
            if any(l.startswith("|") for l in prev_lines):
                insert_idx = i
                break

    if insert_idx is None:
        # 找不到合适的插入位置，追加到文件末尾
        print("[WARN] 无法确定插入位置，请手动添加以下条目到 index.md：")
        for entry in new_entries:
            print(f"  {entry}")
        return 0

    # 在插入位置前添加新行
    for entry in new_entries:
        lines.insert(insert_idx, entry)
        insert_idx += 1

    KB_INDEX.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] 已同步 {len(new_entries)} 个条目到 KB 索引")
    return len(new_entries)


def sync_version_metadata(version_dir: Path) -> int:
    """同步 version_metadata.yaml 的文件列表"""
    meta_file = version_dir / "version_metadata.yaml"
    if not meta_file.exists():
        print(f"[ERROR] {meta_file} 不存在")
        return 0

    try:
        meta = yaml.safe_load(meta_file.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"[ERROR] 解析 {meta_file} 失败: {e}")
        return 0

    updated = 0

    # 同步 prd_files
    actual_prd = sorted(str(f.relative_to(version_dir))
                        for f in _list_prd_files(version_dir))
    if set(meta.get("prd_files", [])) != set(actual_prd):
        meta["prd_files"] = actual_prd
        updated += 1

    # 同步 prototype_files
    actual_proto = sorted(str(f.relative_to(version_dir))
                          for f in _list_proto_files(version_dir))
    if set(meta.get("prototype_files", [])) != set(actual_proto):
        meta["prototype_files"] = actual_proto
        updated += 1

    if updated:
        with open(meta_file, "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        print(f"[OK] 已同步 {version_dir.name} 的 metadata ({updated} 个字段)")
    else:
        print(f"[OK] {version_dir.name} 的 metadata 已是最新")

    return updated


def print_report(issues: List[DocIssue], verbose: bool = True):
    """打印报告"""
    if verbose:
        for i in issues:
            print(i)
        if issues:
            print()

    counts = {}
    for sev in [SEV_ERROR, SEV_WARN, SEV_STALE, SEV_ORPHAN, SEV_INFO]:
        counts[sev] = sum(1 for i in issues if i.severity == sev)

    total = len(issues)
    print(f"总计: {total} 项 | {counts[SEV_ERROR]} 错误 | {counts[SEV_WARN]} 警告 | "
          f"{counts[SEV_STALE]} 过期 | {counts[SEV_ORPHAN]} 孤立 | {counts[SEV_INFO]} 信息")


def main():
    parser = argparse.ArgumentParser(
        description="文档园艺工具 — 维护文档新鲜度和一致性",
    )
    sub = parser.add_subparsers(dest="command")

    p_scan = sub.add_parser("scan", help="全量扫描")
    p_scan.add_argument("--version", help="仅扫描指定版本")

    p_prune = sub.add_parser("prune", help="移除孤立文件")
    p_prune.add_argument("--dry-run", action="store_true", default=True, help="仅预览（默认）")
    p_prune.add_argument("--force", action="store_true", help="跳过确认")

    p_sync = sub.add_parser("sync-index", help="同步 KB 索引")

    p_meta = sub.add_parser("sync-metadata", help="同步 version_metadata.yaml")
    p_meta.add_argument("--version", required=True, help="指定版本")

    sub.add_parser("report", help="仅显示摘要")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "scan":
        issues = scan_all(args.version)
        print_report(issues)
        sys.exit(1 if any(i.severity == SEV_ERROR for i in issues) else 0)

    elif args.command == "prune":
        removed = prune_orphans(dry_run=args.dry_run)
        print(f"\n处理 {removed} 个孤立文件")

    elif args.command == "sync-index":
        sync_kb_index()

    elif args.command == "sync-metadata":
        vdir = VERSIONS_DIR / args.version
        if not vdir.exists():
            print(f"[ERROR] 版本目录不存在: {args.version}")
            sys.exit(1)
        sync_version_metadata(vdir)

    elif args.command == "report":
        issues = scan_all()
        print_report(issues, verbose=False)
        sys.exit(1 if any(i.severity == SEV_ERROR for i in issues) else 0)


if __name__ == "__main__":
    main()
