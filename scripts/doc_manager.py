#!/usr/bin/env python3
"""
doc_manager.py - 操作文档管理工具

支持功能：
- init: 初始化操作文档目录结构
- create: 从模板创建操作文档骨架
- review: 生成操作文档评审报告
- validate: 验证操作文档完整性
- list: 列出当前版本的操作文档

用法：
    python3 scripts/doc_manager.py init <version> --feature <功能名>
    python3 scripts/doc_manager.py create <version> --feature <功能名> [--template <模板路径>]
    python3 scripts/doc_manager.py review <version> --doc <文档名>
    python3 scripts/doc_manager.py validate <version> --doc <文档名>
    python3 scripts/doc_manager.py list <version>
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.resolve()
TEMPLATES_DIR = PROJECT_ROOT / "templates"
VERSIONS_DIR = PROJECT_ROOT / "versions"


def get_version_path(version: str) -> Path:
    """获取版本目录路径，支持模糊匹配。"""
    exact = VERSIONS_DIR / version
    if exact.exists():
        return exact

    # 模糊匹配：名称部分匹配
    candidates = [d for d in VERSIONS_DIR.iterdir() if d.is_dir() and version in d.name]
    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        print(f"[错误] 找到多个匹配的版本: {[c.name for c in candidates]}")
        sys.exit(1)

    print(f"[错误] 未找到版本: {version}")
    sys.exit(1)


def cmd_init(args):
    """初始化操作文档目录结构。"""
    version_path = get_version_path(args.version)
    docs_dir = version_path / "docs"
    screenshots_dir = docs_dir / "screenshots"

    docs_dir.mkdir(exist_ok=True)
    screenshots_dir.mkdir(exist_ok=True)

    print(f"[OK] 操作文档目录已初始化")
    print(f"  - 文档目录: {docs_dir}")
    print(f"  - 截图目录: {screenshots_dir}")


def cmd_create(args):
    """从模板创建操作文档骨架。"""
    version_path = get_version_path(args.version)
    docs_dir = version_path / "docs"
    docs_dir.mkdir(exist_ok=True)

    feature = args.feature
    today = datetime.now().strftime("%Y-%m-%d")

    # 确定模板路径
    template_path = args.template or (TEMPLATES_DIR / "doc_template.md")
    if not template_path.exists():
        print(f"[错误] 模板不存在: {template_path}")
        sys.exit(1)

    # 读取模板并替换变量
    content = template_path.read_text(encoding="utf-8")
    content = content.replace("{功能名}", feature)
    content = content.replace("{版本号}", args.version)
    content = content.replace("{日期}", today)
    content = content.replace("{作者}", args.author or "未指定")
    content = content.replace("{状态}", "draft")

    # 写入文档
    doc_filename = f"{feature}-操作手册.md"
    doc_path = docs_dir / doc_filename
    doc_path.write_text(content, encoding="utf-8")

    print(f"[OK] 操作文档骨架已创建: {doc_path}")
    print(f"  - 功能名: {feature}")
    print(f"  - 版本: {args.version}")
    print(f"  - 作者: {args.author or '未指定'}")


def cmd_review(args):
    """生成操作文档评审报告。"""
    version_path = get_version_path(args.version)
    docs_dir = version_path / "docs"
    agent_comm_dir = version_path / "agent_comm"

    # 确定文档路径
    if args.doc.endswith(".md"):
        doc_path = docs_dir / args.doc
    else:
        doc_path = docs_dir / f"{args.doc}.md"

    if not doc_path.exists():
        print(f"[错误] 文档不存在: {doc_path}")
        sys.exit(1)

    content = doc_path.read_text(encoding="utf-8")
    screenshots_dir = docs_dir / "screenshots"

    # 评审维度
    scores = {}
    issues = []

    # 1. 结构完整性（30分）
    structure_score = 30
    required_sections = [
        "## 1. 功能概述",
        "## 2. 操作环境",
        "## 3. 操作步骤",
        "## 4. 常见问题",
    ]
    for section in required_sections:
        if section not in content:
            structure_score -= 7
            issues.append(f"缺少必要章节: {section}")
    scores["结构完整性"] = max(0, structure_score)

    # 2. 截图覆盖率（30分）
    img_count = len(re.findall(r"!\[.*?\]\(.*?\)", content))
    step_headers = len(re.findall(r"^#### 步骤 \d+：", content, re.MULTILINE))
    if step_headers > 0:
        coverage = img_count / step_headers
        screenshot_score = min(30, int(coverage * 30))
        if coverage < 0.8:
            issues.append(f"截图覆盖率偏低: {img_count}/{step_headers} 步骤有截图 ({coverage*100:.0f}%)")
    else:
        screenshot_score = 0
        issues.append("未找到操作步骤")
    scores["截图覆盖率"] = screenshot_score

    # 3. 内容准确性（20分）
    accuracy_score = 20
    placeholder_count = len(re.findall(r"\{[^{}]+\}", content))
    if placeholder_count > 5:
        accuracy_score -= min(15, placeholder_count)
        issues.append(f"文档中仍有 {placeholder_count} 处未填充的占位符")
    scores["内容准确性"] = max(0, accuracy_score)

    # 4. 可操作性（20分）
    usability_score = 20
    if "预期结果" not in content:
        usability_score -= 10
        issues.append("缺少'预期结果'说明")
    if "注意事项" not in content:
        usability_score -= 5
        issues.append("缺少'注意事项'说明")
    if "操作路径" not in content:
        usability_score -= 5
        issues.append("缺少'操作路径'说明")
    scores["可操作性"] = max(0, usability_score)

    total_score = sum(scores.values())

    # 生成评审报告
    report = f"""---
title: 操作文档评审报告
doc: {doc_path.name}
version: {args.version}
date: {datetime.now().strftime("%Y-%m-%d %H:%M")}
---

# 操作文档评审报告

| 项目 | 内容 |
|------|------|
| 评审文档 | {doc_path.name} |
| 版本 | {args.version} |
| 评审时间 | {datetime.now().strftime("%Y-%m-%d %H:%M")} |
| 综合评分 | {total_score}/100 |
| 评审结果 | {'通过' if total_score >= 85 else '不通过'} |

## 评分详情

| 维度 | 满分 | 得分 | 说明 |
|------|------|------|------|
| 结构完整性 | 30 | {scores['结构完整性']} | 必要章节是否齐全 |
| 截图覆盖率 | 30 | {scores['截图覆盖率']} | 步骤是否有对应截图 |
| 内容准确性 | 20 | {scores['内容准确性']} | 占位符是否已填充 |
| 可操作性 | 20 | {scores['可操作性']} | 是否有预期结果和注意事项 |

## 统计信息

- 操作步骤数: {step_headers}
- 截图引用数: {img_count}
- 截图覆盖率: {coverage*100:.0f}% (如有步骤)
- 占位符残留: {placeholder_count}

## 问题清单

"""
    if issues:
        for i, issue in enumerate(issues, 1):
            report += f"{i}. {issue}\n"
    else:
        report += "无问题，文档质量良好。\n"

    report += f"""
## 结论

{'评审通过，文档可发布。' if total_score >= 85 else '评审不通过，请修复上述问题后重新评审。'}

---
*本报告由 doc_manager.py 自动生成*
"""

    # 写入评审报告
    report_dir = agent_comm_dir / f"doc_{args.doc.replace('-操作手册', '').replace('.md', '')}_{datetime.now().strftime('%Y%m%d')}"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "03_doc_review_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"[OK] 评审报告已生成: {report_path}")
    print(f"  - 综合评分: {total_score}/100")
    print(f"  - 评审结果: {'通过' if total_score >= 85 else '不通过'}")
    if issues:
        print(f"  - 发现问题: {len(issues)} 项")


def cmd_validate(args):
    """验证操作文档完整性。"""
    version_path = get_version_path(args.version)
    docs_dir = version_path / "docs"

    if args.doc.endswith(".md"):
        doc_path = docs_dir / args.doc
    else:
        doc_path = docs_dir / f"{args.doc}.md"

    if not doc_path.exists():
        print(f"[错误] 文档不存在: {doc_path}")
        sys.exit(1)

    content = doc_path.read_text(encoding="utf-8")
    screenshots_dir = docs_dir / "screenshots"

    checks = {
        "文档文件存在": True,
        "包含功能概述": "## 1. 功能概述" in content,
        "包含操作环境": "## 2. 操作环境" in content,
        "包含操作步骤": "## 3. 操作步骤" in content,
        "包含常见问题": "## 4. 常见问题" in content,
        "截图目录存在": screenshots_dir.exists(),
    }

    # 检查截图文件是否都存在
    img_refs = re.findall(r"!\[.*?\]\((.*?)\)", content)
    missing_imgs = []
    for ref in img_refs:
        # 处理相对路径
        if ref.startswith("../"):
            img_path = docs_dir.parent / ref.replace("../", "")
        elif ref.startswith("./"):
            img_path = docs_dir / ref.replace("./", "")
        else:
            img_path = docs_dir / ref

        if not img_path.exists():
            missing_imgs.append(ref)

    checks["截图文件都存在"] = len(missing_imgs) == 0

    print(f"验证结果: {doc_path.name}")
    print("-" * 40)
    all_pass = True
    for check, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check}")
        if not passed:
            all_pass = False

    if missing_imgs:
        print(f"\n  缺失的截图文件:")
        for img in missing_imgs:
            print(f"    - {img}")

    if all_pass:
        print(f"\n[OK] 所有检查项通过")
    else:
        print(f"\n[FAIL] 存在未通过项，请修复后重试")
        sys.exit(1)


def cmd_list(args):
    """列出当前版本的操作文档。"""
    version_path = get_version_path(args.version)
    docs_dir = version_path / "docs"

    if not docs_dir.exists():
        print(f"[信息] 版本 {args.version} 暂无操作文档")
        return

    md_files = sorted(docs_dir.glob("*.md"))
    html_files = sorted(docs_dir.glob("*.html"))
    screenshots = list((docs_dir / "screenshots").glob("*.png")) if (docs_dir / "screenshots").exists() else []

    print(f"版本 {args.version} 的操作文档:")
    print("-" * 40)

    if md_files:
        print(f"\nMarkdown 文档 ({len(md_files)}):")
        for f in md_files:
            print(f"  - {f.name}")

    if html_files:
        print(f"\nHTML 文档 ({len(html_files)}):")
        for f in html_files:
            print(f"  - {f.name}")

    if screenshots:
        print(f"\n截图文件 ({len(screenshots)}):")
        for f in sorted(screenshots):
            print(f"  - {f.name}")

    if not md_files and not html_files:
        print("  暂无文档")


def main():
    parser = argparse.ArgumentParser(
        description="操作文档管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 scripts/doc_manager.py init eBay议价策略_v0.1.0
  python3 scripts/doc_manager.py create eBay议价策略_v0.1.0 --feature eBay议价策略
  python3 scripts/doc_manager.py review eBay议价策略_v0.1.0 --doc eBay议价策略-操作手册
  python3 scripts/doc_manager.py validate eBay议价策略_v0.1.0 --doc eBay议价策略-操作手册
  python3 scripts/doc_manager.py list eBay议价策略_v0.1.0
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # init
    init_parser = subparsers.add_parser("init", help="初始化操作文档目录")
    init_parser.add_argument("version", help="版本号（支持模糊匹配）")

    # create
    create_parser = subparsers.add_parser("create", help="创建操作文档骨架")
    create_parser.add_argument("version", help="版本号（支持模糊匹配）")
    create_parser.add_argument("--feature", required=True, help="功能名称")
    create_parser.add_argument("--template", help="自定义模板路径")
    create_parser.add_argument("--author", help="作者名称")

    # review
    review_parser = subparsers.add_parser("review", help="生成评审报告")
    review_parser.add_argument("version", help="版本号（支持模糊匹配）")
    review_parser.add_argument("--doc", required=True, help="文档名称（不含扩展名或含 .md）")

    # validate
    validate_parser = subparsers.add_parser("validate", help="验证文档完整性")
    validate_parser.add_argument("version", help="版本号（支持模糊匹配）")
    validate_parser.add_argument("--doc", required=True, help="文档名称（不含扩展名或含 .md）")

    # list
    list_parser = subparsers.add_parser("list", help="列出操作文档")
    list_parser.add_argument("version", help="版本号（支持模糊匹配）")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "create": cmd_create,
        "review": cmd_review,
        "validate": cmd_validate,
        "list": cmd_list,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
