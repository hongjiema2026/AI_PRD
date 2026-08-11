#!/usr/bin/env python3
"""
项目初始化脚本
用法: python3 scripts/init_project.py [项目名称]
"""

import os
import sys
import yaml
from pathlib import Path
import logging

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

KB_DIRS = [
    "user-research",
    "competitor",
    "data",
    "methodology",
]


def create_directories():
    """创建项目目录结构"""
    # 版本目录（v0.1.0 初始版本）
    version_path = PROJECT_ROOT / "versions" / "v0.1.0"
    for d in VERSION_DIRS:
        (version_path / d).mkdir(parents=True, exist_ok=True)
        # 添加 .gitkeep 保持空目录
        gitkeep = version_path / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    # 知识库目录
    kb_path = PROJECT_ROOT / "docs" / "knowledge-base"
    for d in KB_DIRS:
        (kb_path / d).mkdir(parents=True, exist_ok=True)
        gitkeep = kb_path / d / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("")

    # 归档目录
    (PROJECT_ROOT / "versions" / "archive").mkdir(parents=True, exist_ok=True)

    logging.info("[OK] 目录结构创建完成")


def init_config(project_name):
    """初始化项目配置"""
    config_path = PROJECT_ROOT / "config" / "project.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    # S7: config 为空 dict 时 config["project"] 不存在会 KeyError
    config.setdefault("project", {})["name"] = project_name
    from datetime import date
    config["project"]["created_at"] = date.today().isoformat()
    config.setdefault("version", {})["current"] = "v0.1.0"

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, sort_keys=False)

    logging.info(f"[OK] 项目配置更新: {project_name}")


def init_version_metadata():
    """创建初始版本元数据"""
    template_path = PROJECT_ROOT / "templates" / "version_metadata_template.yaml"
    target_path = PROJECT_ROOT / "versions" / "v0.1.0" / "version_metadata.yaml"

    if template_path.exists():
        content = template_path.read_text(encoding="utf-8")
        content = content.replace("{版本号}", "v0.1.0")
        from datetime import date
        content = content.replace("{创建日期}", date.today().isoformat())
        content = content.replace("{创建者}", "PM-Agent")
        content = content.replace("{版本描述}", "项目初始化版本")
        content = content.replace("{上一版本号}", "null")
        target_path.write_text(content, encoding="utf-8")
        logging.info("[OK] 初始版本元数据创建完成")


def init_knowledge_base_index():
    """创建知识库索引"""
    index_path = PROJECT_ROOT / "docs" / "knowledge-base" / "index.md"
    if not index_path.exists():
        content = """# 知识库索引

## 分类目录

### 用户研究 (user-research)
_暂无条目_

### 竞品分析 (competitor)
_暂无条目_

### 数据洞察 (data)
_暂无条目_

### 方法论 (methodology)
_暂无条目_

---

## 快速检索

按标签：
- #user-research
- #competitor
- #data
- #methodology
- #requirement
- #design
- #tech
- #business

---

*最后更新: 自动*
"""
        index_path.write_text(content, encoding="utf-8")
        logging.info("[OK] 知识库索引创建完成")


def main():
    project_name = sys.argv[1] if len(sys.argv) > 1 else "PM-Workstation"

    logging.info(f"=== 初始化项目: {project_name} ===\n")

    create_directories()
    init_config(project_name)
    init_version_metadata()
    init_knowledge_base_index()

    logging.info("\n=== 初始化完成 ===")
    logging.info(f"项目路径: {PROJECT_ROOT}")
    logging.info(f"当前版本: v0.1.0")
    logging.info("\n下一步建议:")
    logging.info("1. 编辑 config/project.yaml 完善项目信息")
    logging.info("2. 在 docs/knowledge-base/ 开始沉淀知识")
    logging.info("3. 使用 create_version.py 创建新版本")


if __name__ == "__main__":
    main()
