---
title: PRD 子角色-Writer 执行细则
version: v1.5
date: 2026-08-10
status: active
---

# PRD 子角色：Writer（PRD 编写员）

| 属性 | 值 |
|------|-----|
| 版本 | v1.5 |
| 适用范围 | PRD 流水线 Writer 阶段（PRD 编写）SOP 与检验清单 |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | `docs/agents/prd_agent.md`（F01-F11/W11-W13 权威源）、`docs/agents/prd_stages/html_render.md`（H01-H07 + 检验清单）、`docs/rules/prd-diagram-standard.md`（D01-D08 图绘制规则）、`docs/rules/sop-writing-standard.md`（W14 确认信号、W21 机器可验、W27 HTML 生成校验） |

```
Step 1. 读取《需求调研摘要》和《图表索引》

Step 2. 两阶段写入 PRD（图先行模式）

        ═══ Phase 1 — 业务文档（围绕图写文字） ═══

        写作顺序：先嵌入图，再围绕图写文字。

        ⚠️ 双层阅读结构：每章 `##` 标题下固定先写「本章要点」块（blockquote，3~5 行结论），
        业务读者只读要点即可评审，开发读者继续读正文。

        ⚠️ 篇幅硬上限（违反交 Reviewer 简洁可读维度扣分）：
        - 单段落 ≤3 行≈100 字（引用规则 F11），超出拆列表/表格
        - Ch1 整章 ≤80 行；2.2.x 每个子流程小节 = Mermaid 图 + 简短说明（≤8 行）
        - 全文目标 400~600 行；>700 行扣分（wc -l 可验）

        1. 概述（Chapter 1）
           - 1.1 业务完整流程 ← Mermaid `flowchart LR` 端到端横向流程图（必配，不可省略），
             遵循 UML 活动图语义（stadium 起止/动作矩形，引用规则 D03）
           - 1.2 背景与目标（含非目标、成功指标）
           - 1.3 范围定义（含前置依赖）
           - 1.4 术语与分类（术语表含英文标识符列，分类用列表+inline code）

        2. 流程与规则（Chapter 2）
           - 2.1 核心业务流程 ← Mermaid `flowchart TD` + 文字图注，**最小颗粒度**
             （拆到子步骤可独立验证 + 关键约束上卡，引用规则 D05），
             遵循 UML 活动图语义（判断菱形带分支标签、分支显式合并，引用规则 D03）
           - 2.2 子流程详述 ← 每个子流程必须配 Mermaid 图（flowchart TD，D03），辅以简短文字说明
               ⚠️ 规则 W13：核心流程与每个子流程都必须配图，文字仅作图注补充！
           - 2.3 状态流转 ← Mermaid `stateDiagram-v2` + 状态表格，
             遵循 UML 状态机语法（[*] 初终态、转移标注「事件 [守卫] / 动作」，引用规则 D04）
               ⚠️ 状态机图不可省略！
           - 2.4 业务规则索引（统一定义，编号 R01/R02/...）
               ⚠️ 所有业务规则只在本节定义一次！
               ⚠️ 其他章节引用规则编号，不重复规则内容！
           - 2.5 边界与异常 ← 边界条件和异常处理场景

        3. 使用场景（Chapter 3） ← 场景化举例说明系统行为
           - 章节引言：统一示例背景（运营角色名 + 店铺名 + 站点 + 业务领域）
           - 3.x 每个场景只含 4 要素：场景背景（≤2 句）+ Mermaid 示意图 + 图注 + 关键规则 + 对应页面
               ⚠️ 禁止「系统行为举例」长段（旧 6 要素已废止）
           - 规则只引用编号（R01/R02...），不重复规则内容（与 §2.4 唯一权威源对齐）
           - 场景数量收紧为 3~5 个；覆盖典型业务情境（创建/调整/异常/生命周期等）
           - 场景示意图遵循 UML 活动图语义（引用规则 D03），HTML 版 mermaid.js 原生渲染（引用规则 D06）

        4. 交互原型（Chapter 4） ← 嵌入式原型 + 全屏
           - 4.x 每个模块 → proto-{name}.html（iframe 内嵌）
           - 每个嵌入块含「全屏查看」按钮
           - 扁平化编号：4.1/4.2/4.3...（不用 4.1.1/4.1.2）
           - 引用 Chapter 2 规则 ID，不重复规则
           - 字段定义含「数据字段」列（inline code）

        ═══ Phase 1 完成 → 进入可行性验证门禁 ═══

        Step 3. 编写「交互原型」章节（Chapter 4 核心规则）
        ⚠️ 严格遵循以下编号+原型对应规则：

        a. 「交互原型」在 Chapter 4 下
        b. 每个功能模块使用 4.x 编号（如 4.1, 4.2, 4.3...）
        c. 每个 4.x 章节必须明确标注对应的原型文件名：
           章节标题格式：「4.x {模块名} → proto-{name}.html」
        d. 每个 3.x 章节开头必须有「标注点说明」表格：
           | # | 内容 | 说明 |
           |---|------|------|
           | 1 | {要素} | {设计理由} |
           HTML 渲染时：此表格添加 `class="anno-table" data-section="{N}.x {模块名}"`，
           每行添加 `data-anno="{编号}"`，编号列可点击打开右侧标注抽屉。
        e. 标注点编号 = 原型 HTML 中的 `.annotation-marker` 元素
        f. 交互行为引用规则编号：「引用规则 R01」而非重复规则
        g. 字段定义表含「数据字段」列，使用 inline code
        h. 标注点说明表格只写交互逻辑（设计理由/触发规则），禁止颜色/字号/间距等样式描述
        i. 每个 `.anno-table` 后必须紧跟 `<script class="anno-detail-data" type="application/json" data-section="{与anno-table一致}">` JSON 块，
           包含该章节所有标注点的详尽规格。JSON Schema：
           ```json
           {
             "section": "string — 与 .anno-table[data-section] 一致",
             "items": [{
               "num": "number — 标注编号",
               "title": "string — 区块名称",
               "summary": "string — 概述（1-3句）",
               "fields": [{ "name": "string", "type": "string", "required": "boolean", "rules": "string", "source": "string|null" }],
               "interactions": ["string — 交互规则"],
               "validations": ["string — 校验错误场景 → 提示"],
               "states": ["string — 可选，状态枚举"]
             }]
           }
           ```
           - fields.source：有数据来源或计算规则的字段必须填写，纯手动输入字段填 null
           - 每个 item 必须包含 summary + fields + interactions + validations 四个核心字段
           - JSON item 数量与 `.anno-table tr[data-anno]` 行数完全一致

Step 4. 关联原型
        - 每个功能模块章节内标注对应原型文件路径（「4.x {模块名} → proto-{name}.html」标题即对应关系，不再维护附录对照表）

Step 5. 输出 PRD Markdown 文件
        写入：versions/{v}/prd/{功能名}-prd.md
        命名规范：{功能英文短名}-prd.md

        ⚠️ 此步骤完成后必须暂停，等待用户确认：
        - 向用户展示 PRD 文件路径和核心内容摘要
        - 等待用户反馈（确认通过 / 提出修改意见）
        - 根据用户意见修改 PRD Markdown
        - 循环此步骤直到用户确认（确认信号判定见 `docs/rules/sop-writing-standard.md` W14，与卡点①共用同一判定表，唯一权威定义）

Step 6. 用户确认通过后，输出 HTML 渲染版本
        写入：versions/{v}/prd/{功能名}-prd.html
        仅在用户确认 Markdown 版本无误后才执行此步骤
        ⚠️ HTML 渲染规范详见 docs/agents/prd_stages/html_render.md
        ⚠️ 流程图/状态图（§1.1 / §2.1 / §2.2.x 所有子流程 / §2.3 / §3.x 场景图）在 HTML 版直接用
        mermaid.js CDN 渲染 MD 权威源（引用规则 D06，禁止静态 PNG，PRD 语境禁用 flowdia）；
        Writer 只需保证 Markdown 中的 Mermaid 权威源正确、完整且符合 D03/D04 语义约定
        ⚠️ 生成后必须执行 `python3 scripts/prd_html_check.py <prd.html>` 全部断言 PASS
        才可进入卡点②（引用规则 W27；断言清单见 html_render.md 检验清单）

Step 7. 输出自检清单（初稿）
        写入：versions/{v}/agent_comm/{task_id}/04_prd_draft.md
```

## Writer 检验

> 每项标注【机器可验】/【人工判定】（引用规则 W21）。

- [ ] 【机器可验】PRD 包含全部 4 章 + 附录（概述/流程与规则/使用场景/交互原型，`grep "^## "` 覆盖 4 章标题）
- [ ] 【机器可验】每章含「本章要点」块（`grep -c "本章要点" <prd.md>` ≥ 4）
- [ ] 【机器可验】Chapter 1 以业务完整流程图开篇（§1.1 Mermaid `flowchart LR`，遵循 D03 stadium 起止），含非目标和成功指标（`grep -c '```mermaid'` ≥ 1 于 Ch1 区间；`grep -c "(\["` ≥ 1 于 Ch1 区间）
- [ ] 【人工判定】Chapter 2.1 核心流程有 Mermaid 图且符合 D03 活动图语义（判断菱形带分支标签、分支显式合并）；Chapter 2.2 每个子流程均有 Mermaid 图（W13，文字仅作图注补充）
- [ ] 【机器可验】Chapter 2.3 状态流转有状态机图（`grep -c "stateDiagram-v2"` ≥ 1 且 `grep -c "\[\*\]"` ≥ 1）
- [ ] 【机器可验】Chapter 2.4 业务规则索引完整，规则编号 R01/R02/...（`grep -c "R[0-9]"` ≥ 1）
- [ ] 【人工判定】Chapter 3 场景数 3~5 个，每个场景只含 4 要素（场景背景≤2句/示意图+图注/关键规则/对应页面），无「系统行为举例」长段
- [ ] 【机器可验】Chapter 4 每个 4.x 模块有明确的 `→ proto-{name}.html` 对应标注（`grep -c "→ proto-"` 与 4.x 章节数一致）
- [ ] 【机器可验】每个功能模块包含「标注点说明」表格（`grep -c "标注点说明"` 与 4.x 章节数一致）
- [ ] 【人工判定】标注点编号与原型 HTML 中的 annotation-point 一致（与 proto-*.html 逐一比对）；标注点说明只写交互逻辑、无样式描述
- [ ] 【机器可验】附录变更记录日期列含时间（格式 `YYYY-MM-DD HH:mm`）且按时间降序排列（最新行在最上；`grep -E "^\| [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}" <prd.md>` 命中数 = 变更记录行数）
- [ ] 【机器可验】文件命名符合 `{功能名}-prd.md` 规范（文件名正则匹配）
- [ ] 【机器可验】全文 ≤700 行（`wc -l <prd.md>` ≤ 700；目标 400~600 行）
- [ ] 【人工判定】单段落 ≤3 行（F11，通读全文逐段核对，连续 4 行以上无断行的正文段落即违规）
- [ ] 【人工判定】**三文件同步**：MD、主 HTML、独立原型 HTML 三文件的章节编号、标注点编号、交叉引用完全一致
- [ ] 【机器可验】**HTML 渲染版结构校验**：生成 HTML 后执行 `python3 scripts/prd_html_check.py <prd.html>` 全部断言 PASS（引用规则 W27；6 类断言见 html_render.md 检验清单：标签配对/CSS变量/图源一致/原型嵌入/锚点连通/标注点内容）
- [ ] 【人工判定】**无重复规则**：每条业务规则只在 Chapter 2.4 定义一次（整篇搜索规则编号出现次数）
- [ ] 【机器可验】**附录「相关规范」链接**：附录含「A. 相关规范」小节且含指向 `docs/rules/ui-standard/index.html` 的相对路径链接（`grep -c "相关规范" <prd.md>` ≥ 1 且 `grep -c "ui-standard/index.html" <prd.md>` ≥ 1）

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 17:00 | v1.7 | ①检验清单新增「附录「相关规范」链接」项【机器可验】（附录含 A. 相关规范小节 + ui-standard/index.html 相对路径链接，grep 双条件）；②对齐模板 v4.2 附录结构（新增 A. 相关规范、变更记录重编号 B） | 本文件 + `templates/prd_template.md` v4.2 + `docs/agents/prd_stages/html_render.md` v1.8 + `scripts/prd_html_check.py` |
| 2026-08-10 15:30 | v1.6 | ①检验清单删「附录包含业务规则完整索引」项（附录 A 随模板 v4.1 移除，与 §2.4 重复违 F10 去重），新增「附录变更记录日期含时间 YYYY-MM-DD HH:mm 且降序」项（检验项 17→17）；②对齐模板附录单节结构（仅变更记录） | 本文件 + `templates/prd_template.md` v4.1 + `docs/agents/prd_stages/html_render.md` |
| 2026-08-10 14:20 | v1.5 | ①Step 6 追加「生成 HTML 后必须执行 `scripts/prd_html_check.py` 全 PASS 才可进入卡点②」（引用 W27）；②检验清单新增第 17 项【机器可验】HTML 渲染版结构校验（现共 17 项）；③属性表版本 v1.1→v1.5 补正、关联文档补 W27；④修正历史漂移：v1.4 检验清单项由变更记录自述的口径对齐为实际值 | 本文件 + `scripts/prd_html_check.py`（新建）+ `docs/agents/prd_stages/html_render.md` v1.4 + `docs/rules/sop-writing-standard.md` W27 |
| 2026-08-04 09:10 | v1.4 | ①Step 2 新增双层阅读「本章要点」块要求 + 篇幅硬上限块（F11 单段 ≤3 行 / Ch1 ≤80 行 / 2.2.x ≤15 行 / 全文目标 400~600、>700 扣分）；②Ch3 场景 6 要素废止改 4 要素（禁「系统行为举例」长段）、场景数 3~8 收紧为 3~5；③各章图补 UML 语义约定（引用 D03/D04/D05），Step 6 flowdia 表述改 mermaid.js 原生渲染（引用 D06）；④Step 3-h 附录原型组件对照表要求删除，改标注点说明只写交互逻辑；Step 4 同步；⑤检验清单：删附录三表项改「业务规则完整索引」一表，新增要点块/场景数/总行数/单段长度 4 项；⑥frontmatter 版本 v1.1→v1.4（补正 v1.2/v1.3 未同步） | 本文件 + `docs/agents/prd_agent.md` v1.4 + `templates/prd_template.md` v4.0 + `docs/rules/prd-diagram-standard.md` |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补齐 frontmatter（四字段）+ 属性表；②Writer 检验 12 项逐项标注【机器可验】/【人工判定】（引用规则 W21）；③文末新增附录变更记录表（引用规则 W10）；④技术内容未改动，Step 5 用户确认卡点的 W14 引用保持原位 | 本文件 |
| 2026-08-01 | v1.2 | ①删除 §1.1 业务全景图，原 §1.2 业务完整流程升为 §1.1，§1.3/1.4/1.5 顺次上移为 §1.2/1.3/1.4；②§2.1 核心业务流程绑定最小颗粒度（拆到子步骤可独立验证 + 关键约束上卡，引用 S07）；③Ch1 检验项同步更新（mermaid ≥1 于 Ch1） | 本文件 |
| 2026-08-01 | v1.3 | ①新增 Chapter 3「使用场景」（场景背景+系统行为举例+Mermaid示意图+关键规则+对应页面，规则只引用编号不重复）；②原交互原型/质量属性顺延为 Ch4/Ch5（§4.x/§5.x 子节号同步）；③Step3 交互原型核心规则从 Chapter 3 改为 Chapter 4；④检验项「4 章」→「5 章」、「Chapter 3/3.x」→「Chapter 4/4.x」 | 本文件 |
