# -*- coding: utf-8 -*-
"""
ui_standard_render.py — UI 样式与交互规范：MD → HTML 查看器渲染脚本

唯一权威源：docs/rules/ui-standard.md + docs/rules/ui-standard/chapters/*.md
生成物：docs/rules/ui-standard/index.html（禁止手工修改，任何条目变更后必须重跑本脚本）

用法：
  python3 scripts/ui_standard_render.py            # 以项目根目录为基准渲染
  python3 scripts/ui_standard_render.py --root D   # 以 D 为项目根目录（测试用）

退出码：0 = 渲染成功；1 = 失败（缺文件/占位符缺失/条目格式非法），明细打印到 stdout。
"""
import argparse
import datetime
import html
import io
import os
import re
import sys

ENTRY_HEAD = re.compile(r"^### (UI-\d+)\s+(.+?)\s*$", re.M)
FIELD_ROW = re.compile(r"^\|\s*(编号|名称|类型|实测类名|来源页面|状态|收录日期)\s*\|\s*(.*?)\s*\|\s*$")
SECTION_MARKS = ["结构解剖", "样式规格", "状态矩阵", "交互逻辑", "截图", "PRD 引用示例"]
SECTION_RE = re.compile(r"^\*\*(结构解剖|样式规格|状态矩阵|交互逻辑|截图|PRD 引用示例)\*\*[：:]?(.*)$")
IMG_RE = re.compile(r"!\[(.*?)\]\((.*?)\)")
INDEX_ROW = re.compile(r"^\|\s*(UI-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$")


def fail(msg):
    print("FAIL: " + msg)
    sys.exit(1)


def esc(s):
    return html.escape(s, quote=False)


def parse_fields(block):
    fields = {}
    for line in block.splitlines():
        m = FIELD_ROW.match(line.strip())
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def parse_sections(block):
    """返回 {区块名: [内容行,...]}；同一行标记后的余文并入首行。"""
    sections = {k: [] for k in SECTION_MARKS}
    cur = None
    for line in block.splitlines():
        s = line.strip()
        m = SECTION_RE.match(s)
        if m:
            cur = m.group(1)
            # 去掉标记行尾附带的括注（如「（线上实测值）：」），只保留正文余文
            rest = re.sub(r"^[（(][^）)]*[）)][：:]?", "", m.group(2)).strip()
            if rest:
                sections[cur].append(rest)
            continue
        if s.startswith("**") and s.endswith("**"):
            cur = None
            continue
        if cur is not None and s:
            sections[cur].append(s)
    return sections


def render_lines_as_list(lines, ordered=False):
    items = []
    for ln in lines:
        m = re.match(r"^(?:\d+[.、]|-)\s*(.+)$", ln)
        items.append(m.group(1) if m else ln)
    if not items:
        return "<p>（未填写）</p>"
    tag = "ol" if ordered else "ul"
    body = "".join("<li>%s</li>" % esc(x) for x in items)
    return "<%s>%s</%s>" % (tag, body, tag)


def render_shots(lines):
    figs = []
    for ln in lines:
        for alt, src in IMG_RE.findall(ln):
            figs.append(
                '<figure><img src="%s" alt="%s" loading="lazy"/><figcaption>%s</figcaption></figure>'
                % (esc(src), esc(alt), esc(alt))
            )
    if not figs:
        return "<p>（无截图）</p>"
    return '<div class="shots">%s</div>' % "".join(figs)


def render_paras(lines):
    if not lines:
        return "<p>（未填写）</p>"
    return "".join("<p>%s</p>" % esc(x) for x in lines)


def parse_entries(chapter_path):
    """解析一个分章文件，返回 [(编号, 名称, 字段dict, 区块dict)]，顺序保持文件内顺序。"""
    text = io.open(chapter_path, encoding="utf-8").read()
    heads = list(ENTRY_HEAD.finditer(text))
    out = []
    for i, h in enumerate(heads):
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        block = text[start:end]
        out.append((h.group(1), h.group(2), parse_fields(block), parse_sections(block)))
    return out


def chapter_title(path):
    for line in io.open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("# "):
            t = line[2:]
            return t.split("（")[0].strip()
    return os.path.basename(path)


def render_entry(eid, name, fields, sections, demos_dir=None):
    status = fields.get("状态", "active")
    badge = {"active": "b-active", "inferred": "b-inferred", "archived": "b-archived"}.get(status, "b-active")
    status_cn = {"active": "active 已实测", "inferred": "inferred 截图推断", "archived": "archived 已废止"}.get(status, status)
    meta_rows = []
    for key in ["类型", "实测类名", "来源页面", "收录日期"]:
        val = fields.get(key, "")
        val_html = "<code>%s</code>" % esc(val) if key == "实测类名" and val else esc(val)
        meta_rows.append("<tr><th>%s</th><td>%s</td></tr>" % (esc(key), val_html))
    # 实时演示块（条件注入）：demos/{eid小写}.html 存在才插入 iframe（v1.1）
    demo_part = ""
    if demos_dir:
        demo_path = os.path.join(demos_dir, "%s.html" % eid.lower())
        if os.path.exists(demo_path):
            demo_part = (
                '<h4>实时演示</h4><div class="demo-wrap"><iframe class="demo-frame" '
                'src="demos/%s.html" data-eid="%s" loading="lazy"></iframe></div>'
                % (eid.lower(), esc(eid.lower()))
            )
    parts = [
        '<section class="entry" id="%s">' % esc(eid.lower()),
        "<h2><span class=\"eid\">%s</span> %s <span class=\"badge %s\">%s</span></h2>"
        % (esc(eid), esc(name), badge, esc(status_cn)),
        '<table class="meta">%s</table>' % "".join(meta_rows),
        "<h4>结构解剖</h4><div class=\"blk\">%s</div>" % render_paras(sections["结构解剖"]),
        "<h4>样式规格（线上实测值）</h4><div class=\"blk\">%s</div>" % render_lines_as_list(sections["样式规格"]),
        "<h4>状态矩阵</h4><div class=\"blk\">%s</div>" % render_lines_as_list(sections["状态矩阵"]),
        "<h4>交互逻辑</h4><div class=\"blk\">%s</div>" % render_lines_as_list(sections["交互逻辑"], ordered=True),
        demo_part,
        "<h4>截图</h4>%s" % render_shots(sections["截图"]),
        "<h4>PRD 引用示例</h4><pre class=\"ref\">%s</pre>" % esc("\n".join(sections["PRD 引用示例"]) or "（未填写）"),
        "</section>",
    ]
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None, help="项目根目录（默认取脚本上两级目录）")
    args = ap.parse_args()
    root = args.root or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    std_dir = os.path.join(root, "docs", "rules", "ui-standard")
    main_md = os.path.join(root, "docs", "rules", "ui-standard.md")
    tpl_path = os.path.join(std_dir, "viewer-template.html")
    out_path = os.path.join(std_dir, "index.html")
    ch_dir = os.path.join(std_dir, "chapters")
    for p, label in [(main_md, "主文档"), (tpl_path, "查看器模板"), (ch_dir, "分章目录")]:
        if not os.path.exists(p):
            fail("缺少%s：%s" % (label, p))

    # 1. 解析主文档 §4 索引表
    main_text = io.open(main_md, encoding="utf-8").read()
    index_rows = []  # (编号, 名称, 类型, 章节文件, 来源页面, 状态)
    for line in main_text.splitlines():
        m = INDEX_ROW.match(line.strip())
        if m:
            index_rows.append(tuple(x.strip() for x in m.groups()))

    # 2. 解析全部分章条目
    entries = []  # (章节文件, 编号, 名称, 字段, 区块)
    for fname in sorted(os.listdir(ch_dir)):
        if not fname.endswith(".md"):
            continue
        path = os.path.join(ch_dir, fname)
        for eid, name, fields, sections in parse_entries(path):
            entries.append((fname, eid, name, fields, sections))

    # 3. 生成侧边导航（按分章分组）
    nav_parts = []
    by_chapter = {}
    for fname, eid, name, fields, sections in entries:
        by_chapter.setdefault(fname, []).append((eid, name, fields.get("状态", "active")))
    for fname in sorted(by_chapter):
        title = chapter_title(os.path.join(ch_dir, fname))
        nav_parts.append('<div class="nav-group"><div class="nav-title">%s</div>' % esc(title))
        for eid, name, status in by_chapter[fname]:
            cls = "nav-item st-%s" % status
            nav_parts.append(
                '<a class="%s" href="#%s"><span class="nid">%s</span><span class="nname">%s</span></a>'
                % (cls, esc(eid.lower()), esc(eid), esc(name))
            )
        nav_parts.append("</div>")
    nav_html = "\n".join(nav_parts)

    # 4. 首页索引行（以主文档 §4 为准）
    row_html = []
    for eid, name, typ, chap, page, status in index_rows:
        row_html.append(
            '<tr><td><a href="#%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
            % (esc(eid.lower()), esc(eid), esc(name), esc(typ), esc(chap), esc(page), esc(status))
        )
    index_html = "\n".join(row_html)

    # 5. 条目区块
    demos_dir = os.path.join(std_dir, "demos")
    entry_html = "\n".join(
        render_entry(eid, name, fields, sections, demos_dir) for _, eid, name, fields, sections in entries
    )

    # 6. 统计
    n_all = len(entries)
    n_act = sum(1 for e in entries if e[3].get("状态") == "active")
    n_inf = sum(1 for e in entries if e[3].get("状态") == "inferred")
    n_arc = sum(1 for e in entries if e[3].get("状态") == "archived")
    stats = "共 %d 条（已实测 %d / 截图推断 %d / 已废止 %d）· 索引表登记 %d 行" % (n_all, n_act, n_inf, n_arc, len(index_rows))

    # 7. 填充模板
    tpl = io.open(tpl_path, encoding="utf-8").read()
    for ph in ["@@GEN_TIME@@", "@@STATS@@", "<!--@@NAV@@-->", "<!--@@INDEX_ROWS@@-->", "<!--@@ENTRIES@@-->"]:
        if ph not in tpl:
            fail("模板缺少占位符：%s" % ph)
    out = (
        tpl.replace("@@GEN_TIME@@", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("@@STATS@@", esc(stats))
        .replace("<!--@@NAV@@-->", nav_html)
        .replace("<!--@@INDEX_ROWS@@-->", index_html)
        .replace("<!--@@ENTRIES@@-->", entry_html)
    )
    io.open(out_path, "w", encoding="utf-8").write(out)
    print("PASS: 渲染完成 %s（条目 %d，索引 %d 行）" % (out_path, n_all, len(index_rows)))
    sys.exit(0)


if __name__ == "__main__":
    main()
