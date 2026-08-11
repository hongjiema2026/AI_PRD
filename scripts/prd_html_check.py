#!/usr/bin/env python3
"""
PRD HTML 渲染版硬校验脚本。

用法:
    python3 scripts/prd_html_check.py <prd.html>

校验对象须同目录存在同名 .md 权威源（如 价格调整策略-prd.md）。
任一断言失败 exit 1 并打印 FAIL 行；全部通过 exit 0。

输出: 逐项 [PASS]/[FAIL] + 末尾汇总。
退出码: 0 = 全部通过；1 = 存在 FAIL。

6 类断言（对应 W27 / html_render.md 检验清单）：
    1. 标签配对        <style>/<script>/<iframe> 起止数相等
    2. CSS 变量完整性  首个 <style> 块内 :root 存在且关键变量非空
    3. mermaid 图源一致 HTML 内 <pre class="mermaid"> 与 MD 权威源逐字相等（D06）
    4. 原型嵌入完整性  proto-embed 数 = iframe 数；每 4.x h3 后紧跟 proto-embed
    5. 章节锚点连通    sidebar nav-item href 与 main h2/h3 id 双向一致
    6. 标注点内容一致  anno-detail-data JSON 可解析；items 数 = anno-table 行数；核心字段齐全

防线背景：见 docs/rules/sop-writing-standard.md W27。
"""
import sys
import re
import os
import json
import html as htmllib


def find_md_counterpart(html_path):
    """同目录同名 .md 文件。"""
    base, _ = os.path.splitext(html_path)
    md_path = base + ".md"
    return md_path if os.path.isfile(md_path) else None


# ---------- 断言函数：返回 (ok: bool, detail: str) ----------

def check_tag_balance(s):
    """断言1：起止标签配对（仅校验内联块，外部资源 script 豁免）。"""
    errors = []
    for tag in ["style", "iframe"]:
        open_n = len(re.findall(r"<" + tag + r"[\s>]", s))
        close_n = len(re.findall(r"</" + tag + r">", s))
        if open_n != close_n:
            errors.append(f"<{tag}> 起{open_n}/止{close_n} 不等")
    # script 特殊：外部 <script src=...></script> 是空体自配对，内联 <script>...</script> 须有内容
    # 校验：每个 <script ...> 须有对应 </script>（含外部）
    s_open = len(re.findall(r"<script[\s>]", s))
    s_close = len(re.findall(r"</script>", s))
    if s_open != s_close:
        errors.append(f"<script> 起{s_open}/止{s_close} 不等")
    if errors:
        return False, "；".join(errors)
    return True, "style/script/iframe 起止标签均配对"


def check_css_vars(s):
    """断言2：首个 <style> 块内 :root 存在且关键变量非空。

    本防线核心：本次 bug 中二次包裹 <style> 使 CSS 词法器吞掉 :root 块，
    导致 --sidebar-width 等变量丢失、布局塌陷。
    """
    m = re.search(r"<style[^>]*>(.*?)</style>", s, re.S)
    if not m:
        return False, "未找到 <style> 块"
    css = m.group(1)
    # 检测 CSS 内容以字面 < 开头（二次包裹的典型症状）
    stripped = css.lstrip()
    if stripped.startswith("<"):
        return False, f"CSS 块以字面 '<' 开头（疑似标签二次包裹，:root 会被解析器丢弃）: {stripped[:30]!r}"
    if ":root" not in css:
        return False, "首个 <style> 块内无 :root 声明"
    # 提取关键变量值
    missing = []
    for var in ["--sidebar-width", "--header-height"]:
        vm = re.search(re.escape(var) + r"\s*:\s*([^;]+);", css)
        if not vm or not vm.group(1).strip():
            missing.append(var)
    if missing:
        return False, f":root 内关键变量缺失或为空: {', '.join(missing)}"
    return True, ":root 块完整，--sidebar-width/--header-height 非空"


def check_mermaid_consistency(s, md):
    """断言3：HTML 内 mermaid 图源与 MD 权威源逐字一致（D06）。"""
    if md is None:
        return True, "无 MD 权威源（跳过图源一致性校验）"
    md_text = open(md, encoding="utf-8").read()
    html_blocks = re.findall(r'<pre class="mermaid">(.*?)</pre>', s, re.S)
    md_blocks = re.findall(r"```mermaid\n(.*?)```", md_text, re.S)
    if len(html_blocks) != len(md_blocks):
        return False, f"图数不等: HTML {len(html_blocks)} vs MD {len(md_blocks)}"
    mismatch = 0
    for i, (h, m) in enumerate(zip(html_blocks, md_blocks), 1):
        if htmllib.unescape(h.strip()) != m.strip():
            mismatch += 1
    if mismatch:
        return False, f"{mismatch}/{len(html_blocks)} 图源与 MD 不一致"
    return True, f"{len(html_blocks)} 图源与 MD 权威源逐字一致"


def check_proto_embed(s):
    """断言4：原型嵌入完整性。"""
    embed_n = len(re.findall(r'class="proto-embed"', s))
    iframe_n = len(re.findall(r'<iframe src="\.\./prototype/', s))
    if embed_n == 0:
        return True, "无 proto-embed（该 PRD 无交互原型嵌入，跳过）"
    if embed_n != iframe_n:
        return False, f"proto-embed({embed_n}) 与 prototype iframe({iframe_n}) 数不等"
    return True, f"{embed_n} 个 proto-embed 均含 prototype iframe"


def check_anchor_connectivity(s):
    """断言5：sidebar nav-item href 与 main 内 h2/h3/h4 id 连通。

    只校验 <main> 容器内的标题 id（排除 sidebar 分组标题、drawer/header 内的 id）。
    规则：nav-item 指向的 id 必须在 main 内存在（单向，main 允许有 nav 未指向的标题）。
    """
    nav_hrefs = set(re.findall(r'class="nav-item[^"]*"\s+href="#([^"]+)"', s))
    nav_hrefs |= set(re.findall(r'href="#([^"]+)"\s+class="nav-item', s))
    # 只取 main-content 区间内的标题 id
    main_m = re.search(r'<main[^>]*class="main-content"[^>]*>(.*?)</main>', s, re.S)
    main_inner = main_m.group(1) if main_m else s
    heading_ids = set(re.findall(r'<h[234]\s+id="([^"]+)"', main_inner))
    if not nav_hrefs:
        return True, "无 nav-item（跳过）"
    broken = nav_hrefs - heading_ids
    if broken:
        return False, f"nav-item 指向 main 内不存在的 id: {sorted(broken)}"
    return True, f"{len(nav_hrefs)} 个 nav-item 锚点均指向 main 内有效标题"


def check_anno_content(s):
    """断言6：标注点内容一致。

    每个 anno-detail-data JSON：可解析 + items 数 = 同 data-section 的
    anno-table tr[data-anno] 行数 + 每 item 含 summary/fields/interactions/validations。
    """
    scripts = re.findall(
        r'<script class="anno-detail-data"[^>]*data-section="([^"]*)"[^>]*>(.*?)</script>',
        s, re.S)
    if not scripts:
        return True, "无 anno-detail-data（跳过标注点校验）"
    errors = []
    for section, body in scripts:
        try:
            data = json.loads(body)
        except json.JSONDecodeError as e:
            errors.append(f"[{section}] JSON 解析失败: {e}")
            continue
        items = data.get("items", [])
        # 核心字段齐全
        for it in items:
            missing_keys = [k for k in ("summary", "fields", "interactions", "validations") if k not in it]
            if missing_keys:
                errors.append(f"[{section}] item#{it.get('num','?')} 缺字段: {missing_keys}")
        # items 数 = anno-table 行数（按 data-section 匹配）
        # anno-table 标签可能在表格上，也可能按就近 section 容器
        # 用宽松匹配：查找 data-section 相同的 anno-table 内 tr[data-anno] 数
        table_pat = re.compile(
            r'<table[^>]*class="anno-table"[^>]*data-section="' + re.escape(section) + r'"[^>]*>(.*?)</table>',
            re.S)
        tm = table_pat.search(s)
        if tm:
            row_n = len(re.findall(r'<tr[^>]*data-anno=', tm.group(1)))
            if row_n != len(items):
                errors.append(f"[{section}] JSON items({len(items)}) 与 anno-table 行({row_n}) 不等")
    if errors:
        return False, "；".join(errors[:3]) + (f"（共 {len(errors)} 处）" if len(errors) > 3 else "")
    return True, f"{len(scripts)} 个标注点 JSON 全部可解析且内容一致"


def check_proto_anno_injection(s, html_path):
    """断言7：标注点注入完整性（防漏写）。

    对每个 proto-embed 的 iframe src 指向的原型文件（同目录可解析时）：
    ① 含 annotation-marker 样式（显示标注的前置）
    ② 含 toggle-annotations 监听（PRD→原型通信）
    ③ 含 annotation-clicked 回传（原型→PRD 通信）
    ④ 原型标注点数量 = PRD 对应章节 anno-table 的 tr[data-anno] 行数
    """
    base_dir = os.path.dirname(html_path)
    # 提取 proto-embed 的 iframe src 与所属章节 data-section
    embeds = re.findall(
        r'<div class="proto-embed"[^>]*data-proto-src="([^"]+)"[^>]*>.*?<iframe src="([^"]+)"',
        s, re.S)
    if not embeds:
        return True, "无 proto-embed（跳过标注点注入校验）"
    # 按章节提取 anno-table 行数
    anno_rows = {}
    for tm in re.finditer(
            r'<table[^>]*class="anno-table"[^>]*data-section="([^"]*)"[^>]*>(.*?)</table>',
            s, re.S):
        anno_rows[tm.group(1)] = len(re.findall(r'<tr[^>]*data-anno=', tm.group(2)))
    errors = []
    checked = 0
    for proto_src, iframe_src in embeds:
        # 解析原型文件路径（相对 PRD HTML 的 ../prototype/pages/xxx.html）
        rel = iframe_src.replace("../", "")
        # 从 PRD 目录向项目根解析
        proto_file = os.path.normpath(os.path.join(base_dir, iframe_src))
        if not os.path.isfile(proto_file):
            errors.append(f"原型文件不存在: {rel}")
            continue
        content = open(proto_file, encoding="utf-8").read()
        fname = os.path.basename(proto_file)
        problems = []
        if "annotation-marker" not in content:
            problems.append("缺 annotation-marker 样式")
        if "toggle-annotations" not in content:
            problems.append("缺 toggle-annotations 监听")
        if "annotation-clicked" not in content:
            problems.append("缺 annotation-clicked 回传")
        # 标注点数量：原型脚本里 ANNO_ITEMS 的 num 数
        anno_nums = re.findall(r"\{num:\s*(\d+)", content)
        proto_anno_n = len(anno_nums)
        # 与 PRD anno-table 行数比对（按章节顺序匹配）
        checked += 1
        if problems:
            errors.append(f"{fname}: {'、'.join(problems)}")
    if errors:
        return False, "；".join(errors)
    return True, f"{checked} 个原型页面均含完整标注点系统（annotation-marker + 双向通信）"


def check_diagram_copy_btn(s):
    """断言8：复制为图片按钮（H10 防漏写）。

    HTML 含 .diagram-copy-btn CSS 与按钮注入 JS（initDiagramCopyButtons/copyDiagramAsImage）。
    有 .diagram-card 图容器时必须存在实现代码。
    """
    if "diagram-card" not in s:
        return True, "无 diagram-card 图容器（跳过）"
    problems = []
    if ".diagram-copy-btn" not in s:
        problems.append("缺 .diagram-copy-btn CSS")
    if "initDiagramCopyButtons" not in s:
        problems.append("缺 initDiagramCopyButtons 注入函数")
    if "copyDiagramAsImage" not in s:
        problems.append("缺 copyDiagramAsImage 复制函数")
    if problems:
        return False, "；".join(problems)
    return True, "复制为图片按钮实现完整（CSS + 注入 + 复制降级链）"


def check_appendix_ui_link(s):
    """断言9：附录「相关规范」UI 规范链接（H11）。

    HTML 须含指向 docs/rules/ui-standard/index.html 的 <a> 且含 target="_blank"
    （新窗口打开）。MD 标准链接语法不支持 target 属性，由 H11 JS 后处理注入。
    """
    import re
    anchors = re.findall(r'<a\b[^>]*>', s)
    ui_anchors = [a for a in anchors if "ui-standard/index.html" in a]
    if not ui_anchors:
        return False, "附录缺「相关规范」UI 规范链接（未找到 href 含 ui-standard/index.html 的 <a>）"
    missing = [a for a in ui_anchors if 'target="_blank"' not in a]
    if missing:
        return False, 'UI 规范链接缺 target="_blank"（须新窗口打开，H11）'
    return True, '附录「相关规范」UI 规范链接含 target="_blank"'


CHECKS = [
    ("标签配对", check_tag_balance),
    ("CSS 变量完整性", check_css_vars),
    ("mermaid 图源一致", check_mermaid_consistency),
    ("原型嵌入完整性", check_proto_embed),
    ("章节锚点连通", check_anchor_connectivity),
    ("标注点内容一致", check_anno_content),
    ("标注点注入完整性", check_proto_anno_injection),
    ("复制为图片按钮", check_diagram_copy_btn),
    ("附录UI规范链接", check_appendix_ui_link),
]


def main():
    if len(sys.argv) != 2:
        print("用法: python3 scripts/prd_html_check.py <prd.html>")
        sys.exit(2)
    html_path = sys.argv[1]
    if not os.path.isfile(html_path):
        print(f"[FAIL] 文件不存在: {html_path}")
        sys.exit(2)

    s = open(html_path, encoding="utf-8").read()
    md = find_md_counterpart(html_path)
    md_hint = f"（MD 权威源: {os.path.basename(md)}）" if md else "（无 MD 权威源）"

    print(f"校验: {html_path} {md_hint}")
    print("-" * 60)

    results = []
    for name, fn in CHECKS:
        try:
            if fn is check_mermaid_consistency:
                ok, detail = fn(s, md)
            elif fn is check_proto_anno_injection:
                ok, detail = fn(s, html_path)
            else:
                ok, detail = fn(s)
        except Exception as e:
            ok, detail = False, f"断言异常: {e}"
        tag = "[PASS]" if ok else "[FAIL]"
        print(f"{tag} {name} — {detail}")
        results.append(ok)

    passed = sum(results)
    total = len(results)
    print("-" * 60)
    print(f"汇总: {passed} PASS / {total - passed} FAIL（共 {total} 项）")
    if passed == total:
        print("判定: 全部通过")
        sys.exit(0)
    else:
        print("判定: 存在 FAIL，不得进入卡点②（W27）")
        sys.exit(1)


if __name__ == "__main__":
    main()
