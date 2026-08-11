#!/usr/bin/env python3
"""
创建新版本脚本
用法:
  python3 scripts/create_version.py 库存调拨_v1.0.0
  python3 scripts/create_version.py 库存调拨_v1.0.0 --baseline 库存预警_v0.9.0
  python3 scripts/create_version.py 购物车优化  # 自动附加版本号

版本格式: {名称}_v{major}.{minor}.{patch}
名称只允许中文、英文、数字、下划线、连字符
"""

import argparse
import os
import re
import shutil
import sys
import yaml
from pathlib import Path
import logging

# S7: 无 basicConfig 时 logging 默认 WARNING，info 级日志全部静默
logging.basicConfig(level=logging.INFO, format="%(message)s")

PROJECT_ROOT = Path(os.environ.get("PM_PROJECT_ROOT") or Path(__file__).resolve().parent.parent).resolve()

VERSION_DIRS = [
    "prd",
    "prototype/restored",
    "prototype/pages",
    "prototype/components",
    "prototype/assets/css",
    "prototype/assets/js",
    "prototype/assets/images",
    "agent_comm",
]


# ── 版本名称工具函数 ──

VERSION_PATTERN = re.compile(r"^(.+)_v(\d+)\.(\d+)\.(\d+)$")
BARE_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def validate_version_name(name):
    """验证版本名称部分，只允许中文、英文、数字、下划线、连字符"""
    if not name or len(name) > 80:
        raise ValueError("版本名称不能为空或超过 80 个字符")
    # 允许中文、英文、数字、下划线、连字符
    if not re.match(r'^[\w一-鿿\-]+$', name):
        raise ValueError(
            f"版本名称包含非法字符: {name}\n"
            "只允许中文、英文、数字、下划线(_)、连字符(-)"
        )
    return name


def validate_version(version):
    """验证完整版本标识，格式: {名称}_v{X.Y.Z} 或 vX.Y.Z（兼容旧版）"""
    version = version.strip()

    # 新格式：名称_vX.Y.Z
    m = VERSION_PATTERN.match(version)
    if m:
        name = validate_version_name(m.group(1))
        return f"{name}_v{m.group(2)}.{m.group(3)}.{m.group(4)}"

    # 旧格式兼容：vX.Y.Z
    m = BARE_VERSION_PATTERN.match(version)
    if m:
        return f"v{m.group(1)}.{m.group(2)}.{m.group(3)}"

    raise ValueError(
        f"版本格式错误: {version}\n"
        "正确格式: {名称}_v{X.Y.Z}，例如: 库存调拨_v1.0.0"
    )


def parse_version(version):
    """解析版本标识，返回 (name, major, minor, patch)"""
    m = VERSION_PATTERN.match(version)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
    # 旧格式兜底
    m = BARE_VERSION_PATTERN.match(version)
    if m:
        return "", int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None, 0, 0, 0


def extract_version_suffix(version):
    """提取版本号后缀用于排序，如 '库存调拨_v1.0.0' → (1, 0, 0)"""
    _, major, minor, patch = parse_version(version)
    return (major, minor, patch)


def get_version_name(version):
    """获取版本名称部分"""
    name, *_ = parse_version(version)
    return name


def get_next_version(name=None):
    """计算下一个版本号。
    如果提供了 name，则计算该名称的下一个版本号；
    否则基于当前版本的名称计算。
    """
    config = get_config()
    current = config.get("version", {}).get("current", "v0.1.0")

    if name is None:
        name = get_version_name(current)

    # 找到该名称下已有版本的最新 minor
    versions_dir = PROJECT_ROOT / "versions"
    max_minor = -1
    if versions_dir.exists():
        for d in versions_dir.iterdir():
            if not d.is_dir() or d.name in ("archive",):
                continue
            n, major, minor, patch = parse_version(d.name)
            if n == name and minor > max_minor:
                max_minor = minor

    next_minor = max_minor + 1
    return f"{name}_v0.{next_minor}.0"


def version_exists(version):
    """检查版本是否已存在"""
    return (PROJECT_ROOT / "versions" / version).exists()


def get_current_version():
    """从配置读取当前版本"""
    config = get_config()
    return config.get("version", {}).get("current", "v0.1.0")


def get_config():
    """读取项目配置"""
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def compare_versions(v1, v2):
    """比较两个版本号，返回 1(v1>v2) / 0(=) / -1(<)"""
    _, a_major, a_minor, a_patch = parse_version(v1)
    _, b_major, b_minor, b_patch = parse_version(v2)
    a = (a_major, a_minor, a_patch)
    b = (b_major, b_minor, b_patch)
    if a > b:
        return 1
    elif a < b:
        return -1
    return 0


def create_version_structure(version):
    """创建版本目录结构"""
    version_path = PROJECT_ROOT / "versions" / version
    version_path.mkdir(parents=True, exist_ok=True)

    for d in VERSION_DIRS:
        (version_path / d).mkdir(parents=True, exist_ok=True)
        gitkeep = version_path / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    logging.info(f"[OK] 版本目录创建: {version}")


def copy_baseline(version, baseline):
    """从基线版本复制内容"""
    baseline_path = PROJECT_ROOT / "versions" / baseline
    target_path = PROJECT_ROOT / "versions" / version

    if not baseline_path.exists():
        logging.warning(f"[WARN] 基线版本不存在: {baseline}，跳过复制")
        return

    # 复制 prd/ 和 prototype/（排除 agent_comm/）
    for src_dir in ["prd", "prototype"]:
        src = baseline_path / src_dir
        dst = target_path / src_dir
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            logging.info(f"[OK] 复制 {src_dir}/ 从 {baseline}")


def generate_metadata(version, baseline=None):
    """生成版本元数据"""
    template_path = PROJECT_ROOT / "templates" / "version_metadata_template.yaml"
    target_path = PROJECT_ROOT / "versions" / version / "version_metadata.yaml"

    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        content = content.replace("{版本号}", version)
        content = content.replace("{创建日期}", _get_today())
        content = content.replace("{创建者}", "PM-Agent")
        content = content.replace("{版本描述}", "")
        current = get_current_version()
        content = content.replace("{上一版本号}", baseline or current)
        # 清除可能残留的占位符
        import re
        content = re.sub(r'\{[^}]+\}', '', content)
        target_path.write_text(content, encoding="utf-8")
        logging.info(f"[OK] 版本元数据生成: {version}")


def update_config(version):
    """更新全局配置中的当前版本"""
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    config = get_config()

    config["version"]["current"] = version

    # 同步更新 version name
    name = get_version_name(version)
    if name:
        config["version"]["name"] = name

    # S4: config 写入加文件锁（服务端并发）
    from utils.filelock import file_lock
    with file_lock(str(config_path) + ".lock"):
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    logging.info(f"[OK] 全局配置更新: current_version = {version}")


def main():
    parser = argparse.ArgumentParser(description="创建新版本")
    parser.add_argument("version", help="版本标识 (格式: {名称}_v{X.Y.Z}，例如: 库存调拨_v1.0.0)")
    parser.add_argument("--baseline", help="基线版本标识")
    parser.add_argument("--desc", "-d", default="", help="版本描述")
    args = parser.parse_args()

    try:
        version = validate_version(args.version)
    except ValueError as e:
        logging.error(f"[ERROR] {e}")
        return 1

    if version_exists(version):
        logging.error(f"[ERROR] 版本已存在: {version}")
        return 1

    logging.info(f"=== 创建版本: {version} ===\n")

    create_version_structure(version)

    if args.baseline:
        copy_baseline(version, args.baseline)

    generate_metadata(version, args.baseline)

    # 如果有描述，写入 metadata
    if args.desc:
        meta_path = PROJECT_ROOT / "versions" / version / "version_metadata.yaml"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            meta["description"] = args.desc
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(meta, f, allow_unicode=True, sort_keys=False)

    update_config(version)

    name = get_version_name(version)
    logging.info(f"\n=== 版本 {version} 创建完成 ===")
    logging.info(f"名称: {name}")
    logging.info(f"路径: versions/{version}/")
    logging.info("\n可用操作:")
    logging.info(f"- 编写 PRD: versions/{version}/prd/")
    logging.info(f"- 设计原型: versions/{version}/prototype/")

    return 0


def _get_today():
    from datetime import date
    return date.today().isoformat()


if __name__ == "__main__":
    sys.exit(main())
