# -*- coding: utf-8 -*-
"""
ui_standard_check.py — UI 样式与交互规范：提交前强制校验（5 项断言）

断言口径唯一权威定义：docs/rules/ui-standard.md §5。
  1. 编号全局唯一（分章 ### UI- 标题与索引表均无重复）
  2. 索引表 ↔ 分章条目一一对应（编号集合一致）
  3. 条目引用的截图文件存在于 docs/rules/ui-standard/assets/
  4. 条目必填字段齐全（7 行字段表 + 6 区块标记；类型/状态枚举合法；框架/容器类结构解剖非「无」）
  5. MD ↔ 查看器 HTML 同步（index.html 存在，且每个 active/inferred 编号有对应 id 区块）

用法：
  python3 scripts/ui_standard_check.py            # 项目根目录执行
  python3 scripts/ui_standard_check.py --root D   # 指定项目根（测试用）

退出码：0 = 全部 PASS；1 = 任一 FAIL（明细打印到 stdout）。
"""
import argparse
import io
import os
import re
import sys

ENTRY_HEAD = re.compile(r"^### (UI-\d+)\s+(.+?)\s*$", re.M)
FIELD_ROW = re.compile(r"^\|\s*(编号|名称|类型|实测类名|来源页面|状态|收录日期)\s*\|\s*(.*?)\s*\|\s*$")
SECTION_MARKS = ["结构解剖", "样式规格", "状态矩阵", "交互逻辑", "截图", "PRD 引用示例"]
SECTION_RE = re.compile(r"^\*\*(结构解剖|样式规格|状态矩阵|交互逻辑|截图|PRD 引用示例)\*\*[：:]?(.*)$")
IMG_RE = re.compile(r"!\[.*?\]\((assets/[^)]+)\)")
INDEX_ROW = re.compile(r"^\|\s*(UI-\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|\s*$")
VALID_TYPE = {"框架", "容器", "控件", "交互"}
VALID_STATUS = {"active", "inferred", "archived"}
REQUIRED_FIELDS = ["编号", "名称", "类型", "实测类名", "来源页面", "状态", "收录日期"]

failures = []


def report(ok, label, detail=""):
    print(("%s  %s%s" % ("PASS" if ok else "FAIL", label, ("：" + detail) if detail else "")))
    if not ok:
        failures.append(label)


def parse_entries(ch_dir):
    """返回 {编号: {"name":…, "chapter":…, "fields":{…}, "sections":{…}, "shots":[…]}}"""
    entries = {}
    dup = []
    for fname in sorted(os.listdir(ch_dir)):
        if not fname.endswith(".md"):
            continue
        text = io.open(os.path.join(ch_dir, fname), encoding="utf-8").read()
        heads = list(ENTRY_HEAD.finditer(text))
        for i, h in enumerate(heads):
            eid, name = h.group(1), h.group(2)
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            block = text[h.end():end]
            fields, sections, shots = {}, {k: [] for k in SECTION_MARKS}, []
            cur = None
            for line in block.splitlines():
                s = line.strip()
                shots += IMG_RE.findall(s)  # 截图引用可能出现在任何行（含标记行），必须最先收集
                fm = FIELD_ROW.match(s)
                if fm:
                    fields[fm.group(1)] = fm.group(2).strip()
                sm = SECTION_RE.match(s)
                if sm:
                    cur = sm.group(1)
                    # 去掉标记行尾附带的括注（如「（线上实测值）：」），只保留正文余文
                    rest = re.sub(r"^[（(][^）)]*[）)][：:]?", "", sm.group(2)).strip()
                    if rest:
                        sections[cur].append(rest)
                    continue
                if cur and s:
                    sections[cur].append(s)
            if eid in entries:
                dup.append(eid)
            entries[eid] = {"name": name, "chapter": fname, "fields": fields, "sections": sections, "shots": shots}
    return entries, dup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    root = args.root or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    main_md = os.path.join(root, "docs", "rules", "ui-standard.md")
    std_dir = os.path.join(root, "docs", "rules", "ui-standard")
    ch_dir = os.path.join(std_dir, "chapters")
    assets_dir = os.path.join(std_dir, "assets")
    index_html = os.path.join(std_dir, "index.html")

    if not os.path.exists(main_md) or not os.path.isdir(ch_dir):
        print("FAIL  规范文件缺失：%s 或 %s 不存在" % (main_md, ch_dir))
        sys.exit(1)

    main_text = io.open(main_md, encoding="utf-8").read()
    index_ids = [m.group(1) for m in (INDEX_ROW.match(l.strip()) for l in main_text.splitlines()) if m]
    entries, dup_entries = parse_entries(ch_dir)

    # 断言 1：编号全局唯一
    dup_index = sorted({x for x in index_ids if index_ids.count(x) > 1})
    ok = not dup_entries and not dup_index
    detail = []
    if dup_entries:
        detail.append("分章重复 %s" % ",".join(sorted(dup_entries)))
    if dup_index:
        detail.append("索引重复 %s" % ",".join(dup_index))
    report(ok, "断言1 编号全局唯一（分章 %d 条，索引 %d 行）" % (len(entries), len(index_ids)), "；".join(detail))

    # 断言 2：索引 ↔ 条目同步
    eset, iset = set(entries), set(index_ids)
    ok = eset == iset
    detail = []
    only_e = sorted(eset - iset)
    only_i = sorted(iset - eset)
    if only_e:
        detail.append("有条目未登记索引 %s" % ",".join(only_e))
    if only_i:
        detail.append("索引行无对应条目 %s" % ",".join(only_i))
    report(ok, "断言2 索引表与分章条目一一对应", "；".join(detail))

    # 断言 3：截图存在
    missing = []
    for eid, e in sorted(entries.items()):
        for rel in e["shots"]:
            if not os.path.exists(os.path.join(std_dir, rel)):
                missing.append("%s→%s" % (eid, rel))
    report(not missing, "断言3 截图文件全部存在（assets/）", "缺失 %s" % ",".join(missing))

    # 断言 4：必填字段与区块
    bad = []
    for eid, e in sorted(entries.items()):
        f, s = e["fields"], e["sections"]
        miss_f = [k for k in REQUIRED_FIELDS if not f.get(k)]
        if miss_f:
            bad.append("%s 缺字段 %s" % (eid, ",".join(miss_f)))
            continue
        if f["编号"] != eid:
            bad.append("%s 字段表编号与标题不一致" % eid)
        if f["类型"] not in VALID_TYPE:
            bad.append("%s 类型非法（%s）" % (eid, f["类型"]))
        if f["状态"] not in VALID_STATUS:
            bad.append("%s 状态非法（%s）" % (eid, f["状态"]))
        miss_s = [k for k in SECTION_MARKS if k not in s or (k != "结构解剖" and not s[k])]
        if miss_s:
            bad.append("%s 缺区块 %s" % (eid, ",".join(miss_s)))
        if f.get("类型") in ("框架", "容器"):
            body = "".join(s.get("结构解剖", [])).strip()
            if not body or body == "无":
                bad.append("%s 为%s类，结构解剖必填" % (eid, f["类型"]))
    report(not bad, "断言4 条目必填字段与区块齐全", "；".join(bad))

    # 断言 5：MD ↔ HTML 同步
    if not os.path.exists(index_html):
        report(False, "断言5 MD↔HTML 同步", "查看器不存在：%s（运行 python3 scripts/ui_standard_render.py 生成）" % index_html)
    else:
        html_text = io.open(index_html, encoding="utf-8").read()
        live_ids = [eid for eid, e in entries.items() if e["fields"].get("状态") in ("active", "inferred")]
        missing_ids = [eid for eid in sorted(live_ids) if ('id="%s"' % eid.lower()) not in html_text]
        html_count = len(re.findall(r'class="entry" id="ui-\d+"', html_text))
        ok = not missing_ids and html_count == len(entries)
        detail = []
        if missing_ids:
            detail.append("HTML 缺条目区块 %s" % ",".join(missing_ids))
        if html_count != len(entries):
            detail.append("HTML 条目数 %d ≠ MD 条目数 %d" % (html_count, len(entries)))
        if not ok:
            detail.append("修复：python3 scripts/ui_standard_render.py 重新渲染")
        report(ok, "断言5 MD↔HTML 同步（MD %d 条 ↔ HTML %d 块）" % (len(entries), html_count), "；".join(detail))

    print("-" * 60)
    if failures:
        print("RESULT: FAIL（%d 项）%s" % (len(failures), "；".join(failures)))
        sys.exit(1)
    print("RESULT: ALL PASS（5/5）")
    sys.exit(0)


if __name__ == "__main__":
    main()
