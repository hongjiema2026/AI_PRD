#!/usr/bin/env python3
"""
版本管理脚本
用法:
  python3 scripts/version_manager.py release 库存调拨_v1.0.0
  python3 scripts/version_manager.py archive 库存调拨_v0.9.0
  python3 scripts/version_manager.py changelog 库存调拨_v1.0.0
  python3 scripts/version_manager.py list
  python3 scripts/version_manager.py status 库存调拨_v1.0.0
  python3 scripts/version_manager.py switch 购物车优化_v0.2.0
  python3 scripts/version_manager.py diff 库存调拨_v0.9.0 库存调拨_v1.0.0
  python3 scripts/version_manager.py next --desc "库存预警"    # 自动创建下一版本
  python3 scripts/version_manager.py current                   # 查看当前版本
  python3 scripts/version_manager.py bump --level patch        # 小改动升级 X.Y.Z+1
  python3 scripts/version_manager.py bump --level minor        # 中改动升级 X.Y+1.0
  python3 scripts/version_manager.py bump --level major        # 大改动升级 X+1.0.0

版本格式: {名称}_v{major}.{minor}.{patch}
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import yaml
from pathlib import Path
from datetime import datetime
import logging

PROJECT_ROOT = Path(os.environ.get("PM_PROJECT_ROOT") or Path(__file__).resolve().parent.parent).resolve()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)

# ── 元数据读写辅助 ──


def load_metadata(version_dir):
    """读取版本目录下的 version_metadata.yaml，返回 dict"""
    if isinstance(version_dir, str):
        version_dir = PROJECT_ROOT / "versions" / version_dir
    meta_path = Path(version_dir) / "version_metadata.yaml"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_metadata(version_dir, meta):
    """写入版本目录下的 version_metadata.yaml"""
    if isinstance(version_dir, str):
        version_dir = PROJECT_ROOT / "versions" / version_dir
    meta_path = Path(version_dir) / "version_metadata.yaml"
    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False)


def resolve_version_dir(target):
    """根据目录名或元数据版本号定位到 versions/ 下的实际目录。
    返回 Path 对象，找不到则返回 None。
    """
    versions_dir = PROJECT_ROOT / "versions"
    # 1. 精确匹配目录名
    candidate = versions_dir / target
    if candidate.is_dir():
        return candidate
    # 2. 遍历目录，匹配元数据中的 version 字段
    for d in versions_dir.iterdir():
        if not d.is_dir() or d.name in ("archive",) or d.name.startswith("."):
            continue
        meta = load_metadata(d)
        if meta.get("version") == target:
            return d
    return None


def update_state_version(old_name, new_name):
    """更新 STATE.md 中的版本引用（frontmatter + Pipeline 表 + Active Work）"""
    state_path = PROJECT_ROOT / "STATE.md"
    if not state_path.exists():
        return

    content = state_path.read_text(encoding="utf-8")

    # 替换 frontmatter 中的 current_version
    content = content.replace(f"current_version: {old_name}", f"current_version: {new_name}")

    # 替换 Active Work 中的版本名
    content = content.replace(f"**Version**: {old_name}", f"**Version**: {new_name}")

    # 替换 Pipeline Status 表中的版本名（保留 ⭐ 标记）
    content = content.replace(f"| {old_name} ⭐", f"| {new_name} ⭐")
    content = content.replace(f"| {old_name} ", f"| {new_name} ")

    state_path.write_text(content, encoding="utf-8")


# ── 版本名称工具函数（与 create_version.py 保持一致） ──

VERSION_RE = re.compile(r"^(.+)_v(\d+)\.(\d+)\.(\d+)$")
BARE_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(version):
    """解析版本标识 → (name, major, minor, patch)"""
    m = VERSION_RE.match(version)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    m = BARE_VERSION_RE.match(version)
    if m:
        return "", int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None, 0, 0, 0


def get_version_name(version):
    name, *_ = parse_version(version)
    return name


def _sort_key(version):
    """排序键：先按名称分组，同名称内按版本号"""
    name, major, minor, patch = parse_version(version)
    return (name or "zzz", major, minor, patch)


def get_config():
    """读取项目配置"""
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_current_version():
    """获取当前工作版本"""
    config = get_config()
    return config.get("version", {}).get("current", "v0.1.0")


def get_versions():
    """获取所有版本列表（排序）"""
    versions_dir = PROJECT_ROOT / "versions"
    versions = []
    for d in versions_dir.iterdir():
        if d.is_dir() and d.name != "archive":
            meta = d / "version_metadata.yaml"
            if meta.exists():
                versions.append(d.name)
    versions.sort(key=_sort_key)
    return versions


def _next_version(name=""):
    """计算下一个版本号。在同一名称下 minor +1。"""
    if not name:
        name = get_version_name(get_current_version()) or ""

    max_minor = -1
    versions_dir = PROJECT_ROOT / "versions"
    if versions_dir.exists():
        for d in versions_dir.iterdir():
            if not d.is_dir() or d.name in ("archive",):
                continue
            n, major, minor, patch = parse_version(d.name)
            if n == name and minor > max_minor:
                max_minor = minor

    next_minor = max_minor + 1
    return f"{name}_v0.{next_minor}.0"


def _update_config(key_path, value):
    """更新 project.yaml 中的某个值"""
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    config = get_config()
    keys = key_path.split(".")
    obj = config
    for key in keys[:-1]:
        if key not in obj:
            obj[key] = {}
        obj = obj[key]
    obj[keys[-1]] = value
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)


def cmd_release(version):
    """发布版本：创建快照归档"""
    version_path = PROJECT_ROOT / "versions" / version
    if not version_path.exists():
        logging.error(f"[ERROR] 版本不存在: {version}")
        return 1

    # 创建归档快照
    archive_dir = PROJECT_ROOT / "versions" / "archive" / version
    if archive_dir.exists():
        shutil.rmtree(archive_dir)
    shutil.copytree(version_path, archive_dir)
    logging.info(f"[OK] 归档快照创建: versions/archive/{version}/")

    # 更新元数据状态
    meta_path = version_path / "version_metadata.yaml"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        meta["status"] = "released"
        meta["release_date"] = datetime.now().strftime("%Y-%m-%d")
        with open(meta_path, "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

    # 更新全局配置
    config = get_config()
    config["version"]["latest_release"] = version
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    # 生成 CHANGELOG
    generate_changelog(version)

    logging.info(f"[OK] 版本 {version} 发布完成")
    return 0


def cmd_archive(version):
    """归档版本：压缩为 zip"""
    version_path = PROJECT_ROOT / "versions" / version
    if not version_path.exists():
        logging.error(f"[ERROR] 版本不存在: {version}")
        return 1

    archive_file = PROJECT_ROOT / "versions" / "archive" / f"{version}.zip"
    shutil.make_archive(
        str(archive_file.with_suffix("")),
        "zip",
        str(version_path)
    )
    logging.info(f"[OK] 归档压缩包: {archive_file}")

    # 更新元数据
    meta_path = version_path / "version_metadata.yaml"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        meta["status"] = "archived"
        with open(meta_path, "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

    return 0


def generate_changelog(version):
    """生成 CHANGELOG"""
    version_path = PROJECT_ROOT / "versions" / version

    # 扫描 PRD 文件
    prd_files = []
    prd_dir = version_path / "prd"
    if prd_dir.exists():
        prd_files = [f.name for f in prd_dir.iterdir() if f.suffix == ".md"]

    # 扫描原型文件
    proto_files = []
    proto_dir = version_path / "prototype"
    if proto_dir.exists():
        for subdir in ["pages", "restored"]:
            sub = proto_dir / subdir
            if sub.exists():
                proto_files.extend([f"{subdir}/{f.name}" for f in sub.iterdir()])

    # 读取元数据
    meta_path = version_path / "version_metadata.yaml"
    meta = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

    # 生成 CHANGELOG
    changelog_content = f"""# CHANGELOG

## {version} ({meta.get('release_date', 'N/A')})

### 版本描述
{meta.get('description', '无')}

### PRD 文档
"""
    for pf in prd_files:
        changelog_content += f"- {pf}\n"

    changelog_content += "\n### 原型页面\n"
    for ptf in proto_files:
        changelog_content += f"- {ptf}\n"

    changelog_content += f"\n### 负责人\n{meta.get('author', 'N/A')}\n"

    # 写入
    changelog_path = version_path / "CHANGELOG.md"
    changelog_path.write_text(changelog_content, encoding="utf-8")
    logging.info(f"[OK] CHANGELOG 生成: {changelog_path}")


def cmd_changelog(version):
    """生成指定版本的 CHANGELOG"""
    version_path = PROJECT_ROOT / "versions" / version
    if not version_path.exists():
        logging.error(f"[ERROR] 版本不存在: {version}")
        return 1

    generate_changelog(version)
    return 0


def cmd_list(json_mode=False):
    """列出所有版本。S5: json_mode 输出结构化数组（服务端调用用）"""
    versions = get_versions()
    if json_mode:
        import json
        rows = []
        for v in versions:
            meta_path = PROJECT_ROOT / "versions" / v / "version_metadata.yaml"
            row = {"version": v, "status": "unknown", "created_at": None, "description": ""}
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = yaml.safe_load(f) or {}
                row.update({
                    "status": meta.get("status", "unknown"),
                    "created_at": meta.get("created_at"),
                    "description": meta.get("description", ""),
                })
            rows.append(row)
        print(json.dumps(rows, ensure_ascii=False, indent=2, default=str))
        return 0
    if not versions:
        logging.info("暂无版本")
        return 0

    logging.info(f"{'版本':<12} {'状态':<12} {'创建日期':<12} {'描述'}")
    logging.info("-" * 60)

    for v in versions:
        meta_path = PROJECT_ROOT / "versions" / v / "version_metadata.yaml"
        status = "unknown"
        date = "N/A"
        desc = ""
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f)
            status = meta.get("status", "unknown")
            date = meta.get("created_at", "N/A")
            desc = meta.get("description", "")[:30]

        logging.info(f"{v:<12} {status:<12} {date:<12} {desc}")

    return 0


def cmd_status(version):
    """查看版本详细状态"""
    if not version:
        version = get_current_version()

    version_path = PROJECT_ROOT / "versions" / version
    if not version_path.exists():
        logging.error(f"[ERROR] 版本不存在: {version}")
        return 1

    # 读取元数据
    meta_path = version_path / "version_metadata.yaml"
    meta = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = yaml.safe_load(f)

    is_current = (version == get_current_version())

    lines = [
        f"# 版本状态: {version} {'(当前工作版本)' if is_current else ''}",
        "",
        "## 基本信息",
        f"- 状态: {meta.get('status', 'unknown')}",
        f"- 描述: {meta.get('description', '无')}",
        f"- 创建日期: {meta.get('created_at', 'N/A')}",
        f"- 发布日期: {meta.get('release_date', '未发布')}",
        f"- 负责人: {meta.get('author', 'N/A')}",
        f"- 上一版本: {meta.get('dependencies', {}).get('previous_version', '无')}",
        "",
    ]

    # 版本演进历史
    history = meta.get("version_history", [])
    if history:
        lines.append("## 版本演进")
        lines.append("| 版本 | 日期 | 级别 |")
        lines.append("|------|------|------|")
        for entry in history:
            lines.append(
                f"| {entry.get('version', '?')} "
                f"| {entry.get('date', 'N/A')} "
                f"| {entry.get('level', '?')} |"
            )
        lines.append("")

    # PRD 文件
    prd_dir = version_path / "prd"
    prd_files = []
    if prd_dir.exists():
        prd_files = [f for f in prd_dir.iterdir()
                     if f.suffix == ".md" and f.name != ".gitkeep"]
    lines.append("## PRD 文档")
    if prd_files:
        for pf in prd_files:
            lines.append(f"- {pf.name}")
    else:
        lines.append("_暂无_")
    lines.append("")

    # 原型文件
    proto_dir = version_path / "prototype"
    proto_pages = []
    proto_restored = []
    if proto_dir.exists():
        pages_dir = proto_dir / "pages"
        if pages_dir.exists():
            proto_pages = [f for f in pages_dir.iterdir()
                           if f.suffix in (".html", ".jsx", ".tsx")
                           and f.name != ".gitkeep"]
        restored_dir = proto_dir / "restored"
        if restored_dir.exists():
            proto_restored = [d for d in restored_dir.iterdir()
                              if d.is_dir()]
    lines.append("## 原型文件")
    if proto_pages:
        lines.append("### 页面")
        for p in proto_pages:
            lines.append(f"- pages/{p.name}")
    if proto_restored:
        lines.append("### 复原页面")
        for r in proto_restored:
            lines.append(f"- restored/{r.name}/")
    if not proto_pages and not proto_restored:
        lines.append("_暂无_")
    lines.append("")

    # 任务历史
    comm_dir = version_path / "agent_comm"
    tasks = []
    if comm_dir.exists():
        for task_dir in comm_dir.iterdir():
            if task_dir.is_dir():
                task_md = task_dir / "00_task.md"
                if task_md.exists():
                    # 提取任务摘要
                    content = task_md.read_text(encoding="utf-8")
                    task_type = "unknown"
                    task_status = "unknown"
                    fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
                    if fm_match:
                        try:
                            fm = yaml.safe_load(fm_match.group(1))
                            task_type = fm.get("type", "unknown")
                            task_status = fm.get("status", "unknown")
                        except yaml.YAMLError:
                            pass
                    tasks.append({
                        "dir": task_dir.name,
                        "type": task_type,
                        "status": task_status,
                    })
    lines.append("## 任务历史")
    if tasks:
        lines.append(f"| 任务ID | 类型 | 状态 |")
        lines.append(f"|--------|------|------|")
        for t in tasks:
            lines.append(f"| {t['dir']} | {t['type']} | {t['status']} |")
    else:
        lines.append("_暂无任务记录_")

    report = "\n".join(lines)
    print(report)
    return 0


def cmd_switch(version):
    """切换当前工作版本"""
    version_path = PROJECT_ROOT / "versions" / version
    if not version_path.exists():
        logging.error(f"[ERROR] 版本不存在: {version}")
        logging.info(f"可用版本: {', '.join(get_versions())}")
        return 1

    old = get_current_version()
    _update_config("version.current", version)
    logging.info(f"[OK] 已切换: {old} → {version}")
    return 0


def cmd_diff(v1, v2):
    """对比两个版本的差异"""
    if not v2:
        # 只给了一个参数，对比该版本与上一版本
        v2 = v1
        meta_path = PROJECT_ROOT / "versions" / v2 / "version_metadata.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f)
            v1 = (meta.get("dependencies", {})
                  .get("previous_version", ""))
            if not v1:
                logging.error("[ERROR] 无法确定上一版本")
                return 1
        else:
            logging.error(f"[ERROR] 版本不存在: {v2}")
            return 1

    def _list_files(version):
        """列出版本中的关键文件"""
        vpath = PROJECT_ROOT / "versions" / version
        files = {"prd": [], "prototype": [], "other": []}
        if not vpath.exists():
            return files

        prd_dir = vpath / "prd"
        if prd_dir.exists():
            files["prd"] = [f.name for f in prd_dir.iterdir()
                            if f.suffix == ".md" and f.name != ".gitkeep"]

        proto_dir = vpath / "prototype"
        if proto_dir.exists():
            for sub in ["pages", "restored", "components"]:
                sub_dir = proto_dir / sub
                if sub_dir.exists():
                    for f in sub_dir.iterdir():
                        if not f.name.startswith("."):
                            files["prototype"].append(f"{sub}/{f.name}")

        # agent_comm 下的任务目录
        comm_dir = vpath / "agent_comm"
        if comm_dir.exists():
            for d in comm_dir.iterdir():
                if d.is_dir() and not d.name.startswith("."):
                    files["other"].append(f"task/{d.name}")

        return files

    files1 = _list_files(v1)
    files2 = _list_files(v2)

    print(f"# 版本对比: {v1} → {v2}\n")

    # PRD 对比
    print("## PRD 文档")
    prd1 = set(files1["prd"])
    prd2 = set(files2["prd"])
    if prd2 - prd1:
        print("新增:")
        for f in sorted(prd2 - prd1):
            print(f"  + {f}")
    if prd1 - prd2:
        print("移除:")
        for f in sorted(prd1 - prd2):
            print(f"  - {f}")
    if not (prd2 - prd1) and not (prd1 - prd2):
        print("  无变化")

    # 原型对比
    print("\n## 原型文件")
    proto1 = set(files1["prototype"])
    proto2 = set(files2["prototype"])
    if proto2 - proto1:
        print("新增:")
        for f in sorted(proto2 - proto1):
            print(f"  + {f}")
    if proto1 - proto2:
        print("移除:")
        for f in sorted(proto1 - proto2):
            print(f"  - {f}")
    if not (proto2 - proto1) and not (proto1 - proto2):
        print("  无变化")

    # 元数据对比
    print("\n## 元数据")
    meta1_path = PROJECT_ROOT / "versions" / v1 / "version_metadata.yaml"
    meta2_path = PROJECT_ROOT / "versions" / v2 / "version_metadata.yaml"
    m1 = {}
    m2 = {}
    if meta1_path.exists():
        with open(meta1_path, "r", encoding="utf-8") as f:
            m1 = yaml.safe_load(f) or {}
    if meta2_path.exists():
        with open(meta2_path, "r", encoding="utf-8") as f:
            m2 = yaml.safe_load(f) or {}

    for key in ["description", "status", "created_at", "release_date", "author"]:
        val1 = m1.get(key, "N/A")
        val2 = m2.get(key, "N/A")
        changed = "→" if str(val1) != str(val2) else " "
        print(f"  {changed} {key}: {val1} → {val2}")

    return 0


def cmd_current():
    """查看当前工作版本"""
    current = get_current_version()
    logging.info(f"当前工作版本: {current}")
    return 0


def _resolve_name(name_hint):
    """根据名称提示，查找最匹配的已有版本名称。
    策略：
    1. 精确匹配 → 返回该名称
    2. 已有名称是 hint 的前缀 → 返回已有名称（如 hint="库存预警"，已有"库存预警"）
    3. hint 是已有名称的前缀 → 返回已有名称（如 hint="库存"，已有"库存预警"）
    4. 都不匹配 → 返回 hint 本身（作为新名称）
    """
    if not name_hint:
        return get_version_name(get_current_version()) or ""

    versions_dir = PROJECT_ROOT / "versions"
    if not versions_dir.exists():
        return name_hint

    existing_names = set()
    for d in versions_dir.iterdir():
        if not d.is_dir() or d.name in ("archive",):
            continue
        ename, *_ = parse_version(d.name)
        if ename:
            existing_names.add(ename)

    # 精确匹配
    if name_hint in existing_names:
        return name_hint

    # 已有名称是 hint 的前缀（hint="库存预警" → 已有"库存预警"）
    for ename in existing_names:
        if ename.startswith(name_hint) or name_hint.startswith(ename):
            return ename

    # hint 是已有名称的前缀（hint="库存" → 已有"库存预警"）
    for ename in existing_names:
        if name_hint.startswith(ename):
            return ename

    return name_hint


def cmd_bump(version, level):
    """版本号升级：根据改动级别 bump 对应版本位，并重命名目录"""
    if level not in ("patch", "minor", "major"):
        logging.error(f"[ERROR] 无效级别: {level}，可选: patch / minor / major")
        return 1

    # 1. 定位目标版本目录
    if not version:
        version = get_current_version()
    target_dir = resolve_version_dir(version)
    if not target_dir:
        logging.error(f"[ERROR] 版本不存在: {version}")
        return 1

    old_dirname = target_dir.name
    meta = load_metadata(target_dir)
    old_version = meta.get("version", old_dirname)
    name, major, minor, patch = parse_version(old_version)

    if name is None:
        logging.error(f"[ERROR] 无法解析版本号: {old_version}")
        return 1

    # 2. 计算新版本号
    if level == "patch":
        new_version = f"{name}_v{major}.{minor}.{patch + 1}"
    elif level == "minor":
        new_version = f"{name}_v{major}.{minor + 1}.0"
    elif level == "major":
        new_version = f"{name}_v{major + 1}.0.0"

    new_dirname = new_version

    # 3. 检查目标目录是否已存在
    versions_dir = PROJECT_ROOT / "versions"
    new_dir_path = versions_dir / new_dirname
    if new_dir_path.exists():
        logging.error(f"[ERROR] 目标目录已存在: versions/{new_dirname}/")
        return 1

    # 4. git mv 重命名目录
    try:
        subprocess.run(
            ["git", "mv", str(target_dir), str(new_dir_path)],
            check=True, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT),  # S3: git mv 必须在仓库工作区内执行
        )
    except subprocess.CalledProcessError as e:
        logging.error(f"[ERROR] git mv 失败: {e.stderr}")
        return 1

    # 5. 更新元数据
    meta["version"] = new_version
    history_entry = {
        "version": new_version,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "level": level,
        "previous": old_version,
    }
    meta.setdefault("version_history", []).append(history_entry)
    save_metadata(new_dir_path, meta)

    # 6. 同步 config/project.yaml
    config = get_config()
    is_current = (old_dirname == config.get("version", {}).get("current") or
                  old_version == config.get("version", {}).get("current"))

    if is_current:
        config["version"]["current"] = new_version
        vname = get_version_name(new_version)
        if vname:
            config["version"]["name"] = vname

    # 更新 versions 列表
    vlist = config.get("version", {}).get("versions", [])
    config["version"]["versions"] = [
        new_version if v == old_dirname or v == old_version else v
        for v in vlist
    ]
    # 如果旧名不在列表中但新名需要加入
    if new_version not in config["version"]["versions"]:
        config["version"]["versions"].append(new_version)

    # S4: config 写入加文件锁（服务端并发）
    from utils.filelock import file_lock
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    with file_lock(str(config_path) + ".lock"):
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    # 7. 同步 STATE.md
    update_state_version(old_dirname, new_version)

    logging.info(f"[OK] 版本升级: {old_dirname} → {new_version} ({level})")
    if is_current:
        logging.info(f"[OK] 当前工作版本已更新为 {new_version}")
    return 0


def cmd_next(description=""):
    """自动创建下一个版本。
    从 description 提取名称，智能匹配已有版本，递进版本号。
    """
    name = None
    if description:
        name = _resolve_name(description.split()[0])

    new_version = _next_version(name=name)

    # 检查是否已存在
    if (PROJECT_ROOT / "versions" / new_version).exists():
        logging.error(f"[ERROR] 版本已存在: {new_version}")
        return 1

    # 调用 create_version.py（S3: 用当前解释器而非依赖 PATH 上的 python3，并传递项目根）
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "create_version.py"), new_version],
        capture_output=True, text=True,
        env={**os.environ, "PM_PROJECT_ROOT": str(PROJECT_ROOT)},
    )

    if result.returncode != 0:
        logging.error(f"[ERROR] 创建版本失败: {result.stderr}")
        return 1

    # 写入需求描述
    if description:
        meta_path = PROJECT_ROOT / "versions" / new_version / "version_metadata.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            meta["description"] = description
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

    logging.info(f"[OK] 版本 {new_version} 已创建（基于 {get_current_version()}）")
    logging.info(f"[OK] 当前工作版本已切换到 {new_version}")
    if description:
        logging.info(f"[OK] 需求描述: {description}")
    return 0


def main():
    parser = argparse.ArgumentParser(description="版本管理")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # release
    p_release = subparsers.add_parser("release", help="发布版本")
    p_release.add_argument("version", help="版本号")

    # archive
    p_archive = subparsers.add_parser("archive", help="归档版本")
    p_archive.add_argument("version", help="版本号")

    # changelog
    p_cl = subparsers.add_parser("changelog", help="生成 CHANGELOG")
    p_cl.add_argument("version", help="版本号")

    # list
    p_list = subparsers.add_parser("list", help="列出所有版本")
    p_list.add_argument("--json", action="store_true", help="JSON 结构化输出")

    # status
    p_status = subparsers.add_parser("status", help="查看版本详细状态")
    p_status.add_argument("version", nargs="?", help="版本号（默认当前版本）")

    # switch
    p_switch = subparsers.add_parser("switch", help="切换当前工作版本")
    p_switch.add_argument("version", help="目标版本号")

    # diff
    p_diff = subparsers.add_parser("diff", help="对比两个版本差异")
    p_diff.add_argument("v1", help="版本1（若只提供一个版本，自动对比其上一版本）")
    p_diff.add_argument("v2", nargs="?", help="版本2")

    # current
    subparsers.add_parser("current", help="查看当前工作版本")

    # bump
    p_bump = subparsers.add_parser("bump", help="版本号升级（patch/minor/major）")
    p_bump.add_argument("--level", "-l", required=True,
                        choices=["patch", "minor", "major"],
                        help="升级级别: patch=小改动, minor=中改动, major=大改动")
    p_bump.add_argument("--version", "-v", default="",
                        help="目标版本（默认当前版本）")

    # next
    p_next = subparsers.add_parser("next", help="自动创建下一个版本")
    p_next.add_argument("--desc", "-d", default="", help="需求描述")

    args = parser.parse_args()

    if args.command == "release":
        return cmd_release(args.version)
    elif args.command == "archive":
        return cmd_archive(args.version)
    elif args.command == "changelog":
        return cmd_changelog(args.version)
    elif args.command == "list":
        return cmd_list(json_mode=getattr(args, "json", False))
    elif args.command == "status":
        return cmd_status(args.version)
    elif args.command == "switch":
        return cmd_switch(args.version)
    elif args.command == "diff":
        return cmd_diff(args.v1, args.v2)
    elif args.command == "current":
        return cmd_current()
    elif args.command == "next":
        return cmd_next(args.desc)
    elif args.command == "bump":
        return cmd_bump(args.version, args.level)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
