#!/usr/bin/env python3
"""组件模版管理脚本

用法:
  python3 scripts/component_manager.py list [--category CAT] [--tags T1,T2]
  python3 scripts/component_manager.py add <html_file> --name NAME --category CAT [--desc DESC] [--tags T1,T2]
  python3 scripts/component_manager.py create <name> --category CAT [--desc DESC]
  python3 scripts/component_manager.py remove <name> [--force]
  python3 scripts/component_manager.py info <name>
  python3 scripts/component_manager.py validate <name>
  python3 scripts/component_manager.py sync
"""

import argparse
import os
import re
import shutil
import sys
from datetime import date

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
COMPONENTS_DIR = os.path.join(PROJECT_ROOT, "templates", "components")
REGISTRY_PATH = os.path.join(COMPONENTS_DIR, "registry.yaml")
BASE_STYLES_PATH = os.path.join(COMPONENTS_DIR, "base-styles.css")
TEMPLATE_PATH = os.path.join(PROJECT_ROOT, "templates", "component_template.html")


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        print("错误: registry.yaml 不存在", file=sys.stderr)
        sys.exit(1)
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_registry(data):
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def parse_root_vars(css_text):
    """从 CSS 文本中提取 :root 变量。"""
    root_match = re.search(r":root\s*\{([^}]+)\}", css_text)
    if not root_match:
        return {}
    block = root_match.group(1)
    # 移除注释后再解析
    block = re.sub(r"/\*[^*]*\*/", "", block)
    variables = {}
    for m in re.finditer(r"--([\w-]+)\s*:\s*([^;]+)", block):
        variables[m.group(1)] = m.group(2).strip()
    return variables


def load_base_vars():
    if not os.path.exists(BASE_STYLES_PATH):
        return {}
    with open(BASE_STYLES_PATH, "r", encoding="utf-8") as f:
        return parse_root_vars(f.read())


def validate_html_file(filepath):
    """验证 HTML 文件是否是自包含的。"""
    errors = []
    if not os.path.exists(filepath):
        return ["文件不存在"]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if "<!DOCTYPE html>" not in content.upper() and "<!doctype html>" not in content.lower():
        errors.append("缺少 DOCTYPE 声明")
    if "</html>" not in content.lower():
        errors.append("缺少 </html> 闭合标签")

    # 检查外部依赖
    external_links = re.findall(r'<link[^>]+href=["\'](?!(?:data:|#))[^"\']+["\']', content, re.IGNORECASE)
    external_links = [l for l in external_links if "stylesheet" in l.lower()]
    if external_links:
        errors.append(f"发现外部 CSS 引用: {len(external_links)} 个")

    external_scripts = re.findall(r'<script[^>]+src=["\'](?!(?:data:|#))[^"\']+["\']', content, re.IGNORECASE)
    if external_scripts:
        errors.append(f"发现外部 JS 引用: {len(external_scripts)} 个")

    return errors


def find_component(registry, name):
    for comp in registry.get("components", []):
        if comp["name"] == name:
            return comp
    return None


def get_category_ids(registry):
    return [c["id"] for c in registry.get("categories", [])]


# ===== 命令实现 =====


def cmd_list(args):
    registry = load_registry()
    components = registry.get("components", [])
    category_filter = args.category
    tags_filter = [t.strip() for t in args.tags.split(",")] if args.tags else []

    if category_filter:
        components = [c for c in components if c.get("category") == category_filter]
    if tags_filter:
        components = [
            c
            for c in components
            if any(t in c.get("tags", []) for t in tags_filter)
        ]

    if not components:
        print("组件库为空" + (f"（筛选: category={category_filter}" if category_filter else ""))
        return

    print(f"{'名称':<20} {'分类':<15} {'状态':<10} {'描述':<30}")
    print("-" * 75)
    for c in components:
        print(f"{c['name']:<20} {c.get('category', '?'):<15} {c.get('status', '?'):<10} {c.get('description', '')[:30]:<30}")

    print(f"\n共 {len(components)} 个组件")


def cmd_add(args):
    registry = load_registry()

    if args.category not in get_category_ids(registry):
        print(f"错误: 分类 '{args.category}' 不存在", file=sys.stderr)
        print(f"可选分类: {', '.join(get_category_ids(registry))}")
        sys.exit(1)

    if find_component(registry, args.name):
        print(f"错误: 组件 '{args.name}' 已存在", file=sys.stderr)
        sys.exit(1)

    html_path = os.path.abspath(args.html_file)
    errors = validate_html_file(html_path)
    if errors:
        print("警告: HTML 文件验证发现问题:")
        for e in errors:
            print(f"  - {e}")

    dest_dir = os.path.join(COMPONENTS_DIR, args.category)
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, f"{args.name}.html")
    if os.path.abspath(html_path) != os.path.abspath(dest_file):
        shutil.copy2(html_path, dest_file)
        print(f"已复制到: {dest_file}")
    else:
        print(f"文件已在目标位置: {dest_file}")

    # 检查 CSS 变量一致性
    with open(html_path, "r", encoding="utf-8") as f:
        html_vars = parse_root_vars(f.read())
    base_vars = load_base_vars()
    if base_vars and html_vars:
        conflicts = []
        for k, v in base_vars.items():
            if k in html_vars and html_vars[k] != v:
                conflicts.append(f"  --{k}: 模版={html_vars[k]}, 基准={v}")
        if conflicts:
            print("警告: CSS 变量与 base-styles.css 不一致:")
            print("\n".join(conflicts))

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    entry = {
        "name": args.name,
        "file": f"{args.category}/{args.name}.html",
        "category": args.category,
        "description": args.desc or "",
        "status": "stable",
        "created_at": date.today().isoformat(),
        "tags": tags,
    }
    registry["components"].append(entry)
    registry["updated_at"] = date.today().isoformat()
    save_registry(registry)
    print(f"已注册组件: {args.name} ({args.category})")


def cmd_create(args):
    registry = load_registry()

    if args.category not in get_category_ids(registry):
        print(f"错误: 分类 '{args.category}' 不存在", file=sys.stderr)
        print(f"可选分类: {', '.join(get_category_ids(registry))}")
        sys.exit(1)

    if find_component(registry, args.name):
        print(f"错误: 组件 '{args.name}' 已存在", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(TEMPLATE_PATH):
        print("错误: component_template.html 不存在", file=sys.stderr)
        sys.exit(1)

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    # 替换占位符
    template = template.replace("{组件名}", args.name)
    template = template.replace("{组件描述}", args.desc or f"{args.name} 组件")
    template = template.replace("{版本号}", "1.0.0")
    template = template.replace("{作者}", "PM-Workstation")
    template = template.replace("{日期}", date.today().isoformat())
    template = template.replace("{标题}", args.name)
    template = template.replace("{内容区域}", "<!-- 在此编写组件内容 -->")
    template = template.replace("{主按钮}", "确认")
    template = template.replace("{次按钮}", "取消")

    dest_dir = os.path.join(COMPONENTS_DIR, args.category)
    os.makedirs(dest_dir, exist_ok=True)
    dest_file = os.path.join(dest_dir, f"{args.name}.html")
    with open(dest_file, "w", encoding="utf-8") as f:
        f.write(template)
    print(f"已创建骨架: {dest_file}")

    entry = {
        "name": args.name,
        "file": f"{args.category}/{args.name}.html",
        "category": args.category,
        "description": args.desc or "",
        "status": "draft",
        "created_at": date.today().isoformat(),
        "tags": [],
    }
    registry["components"].append(entry)
    registry["updated_at"] = date.today().isoformat()
    save_registry(registry)
    print(f"已注册组件: {args.name} (状态: draft)")
    print(f"提示: 编辑文件后运行 validate 检查合规性")


def cmd_remove(args):
    registry = load_registry()
    comp = find_component(registry, args.name)
    if not comp:
        print(f"错误: 组件 '{args.name}' 不存在", file=sys.stderr)
        sys.exit(1)

    if not args.force:
        print(f"即将删除组件: {comp['name']}")
        print(f"  文件: templates/components/{comp['file']}")
        print(f"  分类: {comp['category']}")
        print(f"  描述: {comp.get('description', '')}")
        confirm = input("确认删除? (y/N): ").strip().lower()
        if confirm != "y":
            print("已取消")
            return

    filepath = os.path.join(COMPONENTS_DIR, comp["file"])
    if os.path.exists(filepath):
        os.remove(filepath)
        print(f"已删除文件: {filepath}")

    registry["components"] = [c for c in registry["components"] if c["name"] != args.name]
    registry["updated_at"] = date.today().isoformat()
    save_registry(registry)
    print(f"已移除组件: {args.name}")


def cmd_info(args):
    registry = load_registry()
    comp = find_component(registry, args.name)
    if not comp:
        print(f"错误: 组件 '{args.name}' 不存在", file=sys.stderr)
        sys.exit(1)

    print(f"名称:   {comp['name']}")
    print(f"文件:   templates/components/{comp['file']}")
    print(f"分类:   {comp.get('category', '?')}")
    print(f"状态:   {comp.get('status', '?')}")
    print(f"描述:   {comp.get('description', '')}")
    print(f"创建:   {comp.get('created_at', '?')}")
    print(f"标签:   {', '.join(comp.get('tags', []))}")

    filepath = os.path.join(COMPONENTS_DIR, comp["file"])
    if os.path.exists(filepath):
        print(f"\n文件大小: {os.path.getsize(filepath)} bytes")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        lines = content.count("\n") + 1
        print(f"行数: {lines}")
    else:
        print("\n⚠ 文件不存在!")


def cmd_validate(args):
    registry = load_registry()
    comp = find_component(registry, args.name)
    if not comp:
        print(f"错误: 组件 '{args.name}' 不存在", file=sys.stderr)
        sys.exit(1)

    filepath = os.path.join(COMPONENTS_DIR, comp["file"])
    all_pass = True

    # 1. 文件存在性
    print("[1/5] 文件存在性...", end=" ")
    if os.path.exists(filepath):
        print("✓")
    else:
        print("✗ 文件不存在")
        all_pass = False
        return

    # 2. 自包含验证
    print("[2/5] 自包含验证...", end=" ")
    errors = validate_html_file(filepath)
    if errors:
        print("✗")
        for e in errors:
            print(f"  - {e}")
        all_pass = False
    else:
        print("✓")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 3. CSS 变量一致性
    print("[3/5] CSS 变量一致性...", end=" ")
    html_vars = parse_root_vars(content)
    base_vars = load_base_vars()
    if base_vars and html_vars:
        conflicts = []
        for k, v in base_vars.items():
            if k in html_vars and html_vars[k] != v:
                conflicts.append(f"--{k}: 文件={html_vars[k]}, 基准={v}")
        if conflicts:
            print(f"✗ {len(conflicts)} 个冲突")
            for c in conflicts:
                print(f"  - {c}")
            all_pass = False
        else:
            # 检查是否包含核心变量
            core_vars = [
                "color-primary", "color-bg-page", "color-text-primary",
                "color-border", "radius-sm", "radius-md",
            ]
            missing = [v for v in core_vars if v not in html_vars]
            if missing:
                print(f"⚠ 缺少核心变量: {', '.join('--' + v for v in missing)}")
            else:
                print("✓")
    elif not html_vars:
        print("⚠ 未找到 :root 变量定义")
    else:
        print("⚠ base-styles.css 不存在，跳过对比")

    # 4. 标注点系统（组件阶段不要求，组装原型时添加）
    print("[4/5] 标注点系统...", end=" ")
    has_annotation = "has-annotation" in content
    has_point = "annotation-point" in content
    if has_annotation and has_point:
        points = re.findall(r'class="annotation-point[^"]*"[^>]*>(\d+)', content)
        print(f"✓ ({len(points)} 个标注点)")
    elif has_annotation or has_point:
        print("⚠ 标注点系统不完整")
    else:
        print("✓（组件阶段无标注点，组装原型时添加）")

    # 5. 注册表信息完整
    print("[5/5] 注册表信息...", end=" ")
    required_fields = ["name", "file", "category", "status", "created_at"]
    missing_fields = [f for f in required_fields if f not in comp or not comp[f]]
    if missing_fields:
        print(f"✗ 缺少字段: {', '.join(missing_fields)}")
        all_pass = False
    else:
        print("✓")

    print()
    if all_pass:
        print("验证通过 ✓")
    else:
        print("验证未通过 ✗ — 请修复上述问题")
        sys.exit(1)


def cmd_sync(args):
    registry = load_registry()
    registered_files = {c["file"] for c in registry.get("components", [])}

    # 扫描文件
    found_files = set()
    for category_dir in os.listdir(COMPONENTS_DIR):
        cat_path = os.path.join(COMPONENTS_DIR, category_dir)
        if not os.path.isdir(cat_path):
            continue
        for fname in os.listdir(cat_path):
            if fname.endswith(".html"):
                found_files.add(f"{category_dir}/{fname}")

    # 未注册的文件
    unregistered = found_files - registered_files
    # 注册但文件丢失
    missing = registered_files - found_files

    if not unregistered and not missing:
        print("注册表与文件系统完全同步 ✓")
        return

    if unregistered:
        print(f"未注册的文件 ({len(unregistered)} 个):")
        for f in sorted(unregistered):
            print(f"  - {f}")
        print()

    if missing:
        print(f"注册但文件丢失 ({len(missing)} 个):")
        for f in sorted(missing):
            print(f"  - {f}")


def main():
    parser = argparse.ArgumentParser(description="组件模版管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # list
    p_list = subparsers.add_parser("list", help="列出所有组件")
    p_list.add_argument("--category", default=None)
    p_list.add_argument("--tags", default=None)

    # add
    p_add = subparsers.add_parser("add", help="从现有 HTML 文件注册组件")
    p_add.add_argument("html_file", help="源 HTML 文件路径")
    p_add.add_argument("--name", required=True, help="组件名称")
    p_add.add_argument("--category", required=True, help="分类 ID")
    p_add.add_argument("--desc", default=None, help="描述")
    p_add.add_argument("--tags", default=None, help="标签（逗号分隔）")

    # create
    p_create = subparsers.add_parser("create", help="创建新组件骨架")
    p_create.add_argument("name", help="组件名称")
    p_create.add_argument("--category", required=True, help="分类 ID")
    p_create.add_argument("--desc", default=None, help="描述")

    # remove
    p_remove = subparsers.add_parser("remove", help="移除组件")
    p_remove.add_argument("name", help="组件名称")
    p_remove.add_argument("--force", action="store_true", help="跳过确认")

    # info
    p_info = subparsers.add_parser("info", help="查看组件详情")
    p_info.add_argument("name", help="组件名称")

    # validate
    p_validate = subparsers.add_parser("validate", help="验证组件合规性")
    p_validate.add_argument("name", help="组件名称")

    # sync
    subparsers.add_parser("sync", help="同步检查")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "list": cmd_list,
        "add": cmd_add,
        "create": cmd_create,
        "remove": cmd_remove,
        "info": cmd_info,
        "validate": cmd_validate,
        "sync": cmd_sync,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
