---
title: 检验清单（每次任务必检）
version: v1.6
date: 2026-08-11
status: active
---

# 检验清单（每次任务必检）

| 属性 | 值 |
|------|-----|
| 版本 | v1.6 |
| 适用范围 | 全部任务类型（通用检验项）+ PRD / proto / doc 任务专项检验项 |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | `docs/verification/quality-gates.md`（评分维度与通过线）、`docs/rules/sop-writing-standard.md`（编写规范）、`docs/rules/prd-diagram-standard.md`（PRD 图绘制 D01-D08） |

> 本文件是**逐项检验清单的权威源之一**（与各 agent 文档 §4 并列，引用规则 W04）。评分维度与通过线**不在本文件定义**，见 `docs/verification/quality-gates.md`。
> 标注口径（引用规则 W21）：每项末尾标注【机器可验】（附检查命令，项目根目录执行）或【人工判定】（附判定要点）。

## 通用检验项（所有任务类型）
- [ ] **代码已同步**：任务启动前已执行 `git pull origin main`，本地为最新代码 —— 【机器可验】`git rev-parse HEAD` = `git rev-parse origin/main`
- [ ] 任务书文件存在且完整 —— 【机器可验】`test -f <任务书路径>`
- [ ] 被调度的 Agent 产出了预期输出文件 —— 【机器可验】按 `docs/rules/sop-writing-standard.md` §2.6 注册表逐个 `test -f agent_comm/{task_id}/<编号文件>`
- [ ] 阻塞任务已解决（如适用） —— 【人工判定】核对任务书依赖项状态
- [ ] 最终报告包含交付物清单和检验结果 —— 【人工判定】读最终报告，核对两要素齐全
- [ ] 用户可定位到所有产出文件 —— 【人工判定】报告中产出路径完整可复制打开
- [ ] 版本上下文正确（target_version 与用户意图一致） —— 【人工判定】对照 `STATE.md` 版本表与用户指令

## PRD 任务检验项

### 图先行检查
- [ ] 业务完整流程图使用 Mermaid `flowchart LR` 内联（端到端横向流程，5~7 步）→ 对应 PRD Chapter 1「概述」§1.1 —— 【人工判定】`grep -n "flowchart LR" <prd.md>` 定位 §1.1 图，人工数节点 5~7 步
- [ ] 业务完整流程图为简化业务叙述（区别于 §2.1 技术流程），带编号标注和图注 —— 【人工判定】读图确认叙述口径简化、编号标注与图注齐全
- [ ] 主流程图使用 Mermaid flowchart 内联 → 对应 PRD Chapter 2「流程与规则」§2.1 —— 【机器可验】`grep -n "flowchart" <prd.md>` 在 §2.1 章节内有命中
- [ ] 流程图符合 UML 活动图语义（D03）：stadium 起止节点、判断菱形且出边带分支标签、分支显式合并、泳道为单层 subgraph —— 【机器可验】`grep -c "(\[" <prd.md>` ≥ 2 且 `grep -c "\-\->|" <prd.md>` ≥ 1；【人工判定】分支合并与泳道逐图核对
- [ ] 状态图符合 UML 状态机语法（D04）：含 `[*]` 初态、转移标注含事件（守卫条件 `[...]`） —— 【机器可验】`grep -c "\[\*\]" <prd.md>` ≥ 1
- [ ] §2.1 核心业务流程为最小颗粒度（D05）：节点拆到可独立验证子步骤、关键约束一句话上卡，与 §2.2.x 逐步对齐 —— 【人工判定】图步骤与正文 §2.2.x 逐步比对，编号一致；逐节点核对含规则一句话
- [ ] HTML 版流程图/状态图用 mermaid.js CDN 原生渲染 MD 权威源（D06），非静态 PNG、未使用 flowdia —— 【机器可验】`grep -c 'class="mermaid"' <prd.html>` ≥ 1 且 `grep -nE "!\[.*\]\(.*png" <prd.html>` 零命中且 `grep -c "flowdia" <prd.html>` = 0
- [ ] 所有 Mermaid 代码块语法正确（可在 HTML 渲染版中正常显示） —— 【机器可验】Playwright 打开 HTML 页面，控制台零 mermaid parse error
- [ ] HTML 渲染版已引入 mermaid.js CDN —— 【机器可验】`grep -nE "cdn[^\"']*mermaid|mermaid[^\"']*cdn" <prd.html>` 有命中
- [ ] 每张图表后有文字图注（F06/D07） —— 【人工判定】逐图核对图注存在

### 流程图完整性检查（Chapter 2 专项，必检）
- [ ] 2.1 核心业务流程有 Mermaid flowchart 内联 —— 【机器可验】`grep -n "flowchart" <prd.md>` 在 §2.1 章节内有命中
- [ ] 2.1 核心业务流程有 Mermaid flowchart 内联；2.2.x 子流程有清晰的文字描述（复杂子流程可选配图） —— 【人工判定】逐个 2.2.x 小节核对文字描述清晰
- [ ] 2.3 状态流转有 Mermaid stateDiagram 内联（如适用），缺失扣 5 分 —— 【机器可验】`grep -c "stateDiagram" <prd.md>` ≥ 1；「如适用」的适用性由 Reviewer 判定
- [ ] 所有流程图和状态机图有文字图注 —— 【人工判定】逐图核对图注存在
- [ ] 全文检索确认 PRD Markdown 中无外部 PNG 流程图引用残留（流程图位置不允许出现 `![...](...png)`，违反 W11） —— 【机器可验】`grep -nE "!\[.*\]\(.*png" <prd.md>` 在流程图位置零命中

### 章节完整性检查
- [ ] PRD 包含全部 4 章（概述 / 流程与规则 / 使用场景 / 交互原型），技术契约由开发团队负责，PM 不产出 —— 【机器可验】`grep -nE "^## " <prd.md>` 输出为 4 章标题且无「技术契约」
- [ ] Chapter 1（概述）含：业务完整流程（§1.1 Mermaid `flowchart LR`）、背景与目标、非目标、成功指标、范围定义、术语表（含英文标识列） —— 【人工判定】逐项核对（`grep -nE "^### " <prd.md>` 辅助定位小节）
- [ ] Chapter 2（流程与规则）含：核心流程、子流程、状态流转、业务规则索引（R01/R02/...）、边界与异常 —— 【人工判定】逐项核对小节齐全
- [ ] Chapter 3（使用场景）含：统一示例背景、场景数 3~5 个、每个场景只含 4 要素（场景背景≤2句 + 示意图+图注 + 关键规则 + 对应页面）、无「系统行为举例」长段 —— 【人工判定】逐个 3.x 场景核对 4 要素与场景数；场景覆盖典型业务情境
- [ ] Chapter 3 使用场景只引用规则编号（R01/R02...），不重复规则内容 —— 【机器可验】`grep -n "引用规则 R" <prd.md>` 在 §3 区间有命中；人工抽查无规则全文复述
- [ ] Chapter 4（交互原型）：每个 4.x 模块有 → proto-{name}.html 对应标注 —— 【机器可验】`grep -oE "proto-[a-z0-9-]+\.html" <prd.md> | sort -u` 与 `ls versions/{v}/prototype/` 输出比对一致
- [ ] HTML 版每个 4.x 小节标题紧下方使用 `.proto-embed` 包裹 iframe 嵌入原型（非纯链接），含「全屏查看」按钮 —— 【机器可验】`grep -c "proto-embed" <prd.html>` = 4.x 小节数，且 `grep -c "全屏查看" <prd.html>` ≥ 1
- [ ] 每个 4.x 小节包含「标注点说明」表格（标注 # + 内容 + 说明） —— 【机器可验】`grep -c "anno-table" <prd.html>` = 4.x 小节数
- [ ] 标注点编号、数量与独立原型 HTML 中的 `.annotation-marker` 元素完全一致（默认隐藏，PRD 全屏可切换） —— 【机器可验】`grep -c "annotation-marker" <proto.html>` 与 PRD 对应 4.x 小节标注数比对一致
- [ ] 标注点说明表格使用 `.anno-table` class + `data-section` + `data-anno`，编号列和原型标注圆圈可点击打开右侧抽屉 —— 【机器可验】`grep -c "anno-table" <prd.html>` = `grep -c "data-section" <prd.html>`；点击行为 Playwright 抽验
- [ ] 每个 `.anno-table` 后有对应的 `<script class="anno-detail-data">` JSON，`data-section` 值一致 —— 【机器可验】`grep -c "anno-detail-data" <prd.html>` = `grep -c "anno-table" <prd.html>`
- [ ] JSON 中每个 item 的 fields 数组包含 name/type/required/rules/source 五个字段 —— 【机器可验】脚本解析 `anno-detail-data` JSON 逐 item 校验五字段（`grep -c '"source"' <prd.html>` = item 总数可作快检）
- [ ] 来源/计算列（source）：有数据来源或计算规则的字段必须填写，纯手动输入字段可填 null —— 【人工判定】逐字段核对填写口径
- [ ] JSON item 数量与 `.anno-table tr[data-anno]` 行数完全一致 —— 【机器可验】脚本比对 JSON item 数与 `grep -c "data-anno" <prd.html>` 行数
- [ ] 每个 item 必须包含 summary + fields + interactions + validations 四个核心字段 —— 【机器可验】脚本解析 JSON 校验四字段（`grep -c '"interactions"' <prd.html>` = item 总数可作快检）
- [ ] 双层阅读结构：每章含「本章要点」块（blockquote 3~5 行结论） —— 【机器可验】`grep -c "本章要点" <prd.md>` ≥ 5
- [ ] 简洁可读（F11 + 篇幅上限）：全文 ≤700 行；单段落 ≤3 行 —— 【机器可验】`wc -l <prd.md>` ≤ 700；【人工判定】通读核对无连续 4 行以上正文段落
- [ ] PM 调研的 API 信息记录在可行性验证报告中，不写入 PRD —— 【人工判定】对照报告与 PRD 核对归属

### 交互行为检查（PRD HTML 必检）
- [ ] 桌面端侧栏可通过 ☰ 按钮收起/展开，收起状态 localStorage 持久化（刷新保持）；移动端仍为抽屉模式 —— 【机器可验】Playwright 点击 ☰ 后刷新页面，断言收起状态保持；`grep -c "localStorage" <prd.html>` ≥ 1 辅助
- [ ] 侧栏收起后主内容区 `max-width: none` 随浏览器实际宽度自适应，且无横向滚动条（flex 布局下 `.main-content` 必须有 `min-width: 0`） —— 【机器可验】`grep -c "min-width: 0\|min-width:0" <prd.html>` ≥ 1；Playwright 断言页面无横向滚动条
- [ ] 「全屏查看」为页面内弹窗（`proto-fullscreen-overlay`），代码中**不存在** `window.open` —— 【机器可验】`grep -c "proto-fullscreen-overlay" <prd.html>` ≥ 1 且 `grep -c "window.open" <prd.html>` = 0
- [ ] 全屏弹窗内可切换「📍 显示标注 / 隐藏标注」，原型 `body.show-annotations` 正确增减；Esc 可关闭弹窗 —— 【机器可验】Playwright 触发切换断言 `show-annotations` class 增减，按 Esc 断言弹窗关闭
- [ ] postMessage 协议字段为 `toggle-annotations` + `on`、`annotation-clicked` + `number`（与原型监听一致，禁止写成 `show`） —— 【机器可验】`grep -n "postMessage" <prd.html>` 逐行核对字段名，`grep -c "toggle-annotations\|annotation-clicked" <prd.html>` ≥ 2
- [ ] 点击原型 `.annotation-marker` → 右侧抽屉打开，且按 `e.source` + `data-num` + `data-page` 双条件精确定位（不跨章节错配） —— 【机器可验】Playwright 点击标注断言抽屉打开且内容匹配；`grep -n "data-num\|data-page" <prd.html>` 辅助核对定位条件
- [ ] 标注抽屉 z-index 高于全屏弹窗（全屏时抽屉浮于其上可用）；宽度 50vw（移动端 100vw） —— 【机器可验】`grep -nE "z-index" <prd.html>` 比对抽屉与弹窗数值大小，`grep -c "50vw" <prd.html>` ≥ 1
- [ ] 抽屉每个标注项含四要素详情（📋 字段说明 / 📏 规则说明 / 🔀 判断逻辑 / 🖱 交互说明），默认收起、选中项展开 —— 【人工判定】Playwright 截图核对四要素齐全、收起/展开行为正确

### 业务规则去重检查
- [ ] Chapter 2.4（业务规则索引）包含所有跨模块规则的统一定义 —— 【人工判定】对照全文核对跨模块规则均已收录
- [ ] 整篇 PRD 中无重复规则定义（每条规则仅在 2.4 出现一次） —— 【机器可验】`grep -oE "R[0-9]{2}" <prd.md> | sort | uniq -c` 核对每条规则的定义段仅出现于 §2.4
- [ ] Chapter 3/4（使用场景 / 交互原型）引用规则 ID（如「引用规则 R01」），而非重复规则内容 —— 【机器可验】`grep -n "引用规则 R" <prd.md>` 有命中；人工抽查无规则全文复述

### 可行性验证检查（PRD 任务必检，Feasibility 阶段产出）
- [ ] 可行性验证报告存在：`agent_comm/{task_id}/03_feasibility_report.md` —— 【机器可验】`test -f agent_comm/{task_id}/03_feasibility_report.md`
- [ ] PRD 中的所有 API 声明都能在 `01_research_summary.md` 中找到对应记录 —— 【人工判定】逐条 API 声明对照调研记录
- [ ] PRD 中不存在无调研依据的具体数值（文件大小、并发数、限流阈值等） —— 【人工判定】逐处数值核对调研依据
- [ ] PRD 中不存在无调研依据的量化指标（"降低XX成本XX%"） —— 【人工判定】`grep -nE "降低.*%|提升.*%" <prd.md>` 命中行逐条核对调研依据
- [ ] PRD 中的枚举值要么来自调研记录，要么表述为"具体枚举值需对接时确认" —— 【人工判定】逐处枚举核对来源
- [ ] 可行性验证报告中 ❌ 已删除项确实已从 PRD 中移除 —— 【人工判定】对照报告逐项核对
- [ ] 可行性验证报告中 ⚠️ 已软化项已改写为"需对接时确认" —— 【人工判定】对照报告逐项核对（`grep -c "需对接时确认" <prd.md>` 辅助）
- [ ] 可行性报告的已验证项保留在报告中供开发团队参考，不流入 PRD —— 【人工判定】对照报告与 PRD 核对归属

### API 调研检查（技术契约已移除，PM 不产出此章节）
- [ ] PRD 中不包含技术契约章节（PM 不产出 API 契约、数据模型、字段映射、错误处理） —— 【机器可验】`grep -nE "技术契约|API 契约|字段映射" <prd.md>` 零命中
- [ ] API 调研结果记录在可行性验证报告（`03_feasibility_report.md`）中 —— 【机器可验】`grep -n "API" agent_comm/{task_id}/03_feasibility_report.md` 有命中

### 格式规范检查（F01-F10 逐项）
- [ ] F01: 所有 API 名称使用 `inline code` 格式 —— 【人工判定】抽读全文核对
- [ ] F02: 所有字段标识符使用 `inline code` 格式 —— 【人工判定】抽读全文核对
- [ ] F03: 所有枚举值使用 `inline code` 格式 —— 【人工判定】抽读全文核对
- [ ] F04: ≤2 行数据使用列表而非表格 —— 【人工判定】逐表核对行数
- [ ] F05: 所有表格列数 ≤ 7 —— 【机器可验】脚本逐表统计首行 `|` 分隔的列数均 ≤ 7
- [ ] F06: 每张图片引用后含文字图注 —— 【人工判定】逐图核对图注存在
- [ ] F07: 标题层级不超过 3 级（## / ###） —— 【机器可验】`grep -c "^####" <prd.md>` = 0
- [ ] F08: 条件规则使用粗体前缀（**条件**：... → **结果**：...） —— 【机器可验】`grep -n "条件：" <prd.md>` 命中行均含 `**条件**` 粗体前缀
- [ ] F09: 每个表格有列标题行 —— 【机器可验】脚本逐表核对首行后紧跟 `|---` 分隔行
- [ ] F10: 无重复业务规则 —— 【机器可验】`grep -oE "R[0-9]{2}" <prd.md> | sort | uniq -c` 核对定义唯一（同「业务规则去重检查」）

### PRD 三文件同步检查（强执行）
修改 PRD 内容时，**必须同步修改以下三个文件**，缺一不可：
- [ ] **MD 文件**：`versions/{v}/prd/{功能名}-prd.md` —— 【机器可验】`test -f versions/{v}/prd/{功能名}-prd.md`
- [ ] **主 HTML**：`versions/{v}/prd/{功能名}-prd.html`（含侧边栏导航） —— 【机器可验】`test -f versions/{v}/prd/{功能名}-prd.html`
- [ ] **独立原型 HTML**：`versions/{v}/prototype/proto-*.html`（标注点编号） —— 【机器可验】`ls versions/{v}/prototype/proto-*.html` 非空

三文件中章节编号、标注点编号、交叉引用必须完全一致。

## 原型任务检验项（proto 任务必检）
- [ ] 设计文档中的交互流程图/功能脑图为 Mermaid 内联，未导出 PNG —— 【机器可验】`grep -nE "!\[.*\]\(.*png" <设计文档>` 零命中且 `grep -c '```mermaid' <设计文档>` ≥ 1
- [ ] 原型 HTML 及相关页面中呈现的流程图使用 flowdia 交互组件，非静态 PNG（标准见 `docs/rules/flow-diagram-standard.md`） —— 【机器可验】`grep -c "flowdia" <proto.html>` ≥ 1（含流程图的页面）
- [ ] 设计文档包含「UI 规范引用映射表」且无未消解「规范缺失」项（proto_agent Step 5b） —— 【机器可验】`grep -c "UI 规范引用映射表" <设计文档>` ≥ 1 且 `grep -c "规范缺失" <设计文档>` = 0
- [ ] 映射表中的 UI-xx 编号在规范索引中真实存在 —— 【机器可验】提取设计文档全部 `UI-[0-9]+` 编号，逐个 `grep` `docs/rules/ui-standard.md` §4 索引表均有命中

## 操作文档检验项（doc 任务必检）

> 编写规则明细 OD01-OD14 唯一权威定义见 `docs/pipelines/doc-pipeline.md` §3；该文件 §4 另有 17 项完整检验清单，本段为任务级必检子集。

- [ ] 截图已采集到 `operation_docs/screenshots/{功能名}/`，且数量 ≥ 文档引用数 —— 【机器可验】`ls operation_docs/screenshots/{功能名}/ | wc -l` ≥ `grep -c "screenshots/" <md>`
- [ ] `00-流程图.png` 由 Mermaid 权威源生成（非页面截图），且 Mermaid 源码保留在 Markdown 源文件中（docx 为 flowdia 标准显式例外，OD07） —— 【人工判定】核对 PNG 为渲染产物；`grep -c '```mermaid' <md>` ≥ 1 辅助
- [ ] Markdown 文档存在：`operation_docs/markdown/{功能名}.md` —— 【机器可验】`test -f operation_docs/markdown/{功能名}.md`
- [ ] **docx 文档存在**：`operation_docs/docx/{功能名}.docx`（最终交付，必须存在） —— 【机器可验】`test -f operation_docs/docx/{功能名}.docx`
- [ ] 文档头固定 4 行齐全：`# 【{功能名}】` + `更新时间：` + `有疑问可咨询产品经理@` + `持续更新中....`（OD02） —— 【机器可验】`grep -c "更新时间：\|有疑问可咨询产品经理@\|持续更新中" <md>` = 3，且首行匹配 `^# 【.+】$`
- [ ] 文档结构严格对齐 `operation_docs/templates/操作文档编写参考模版.docx`：一、功能介绍 / 二、操作说明 / 三、{次功能}（可选） / 四、常见问题（OD03） —— 【机器可验】`grep -nE "^## 一、|^## 二、|^## 四、" <md>` 命中 3 行且行号递增
- [ ] 操作条目/要点编号连续唯一：条目 `### N、` 章内从 1 连续递增，要点 `X.Y` 无跳号无重号（OD04/OD14） —— 【机器可验】`grep -oE "^### [0-9]+、" <md> | grep -oE "[0-9]+"` 输出为连续自然数列；【人工判定】抽读 `X.Y` 编号序列查跳号/重号
- [ ] 字段说明使用四列表格：字段/操作 | 是否必填 | 说明 | 截图；「是否必填」取值仅 `是`/`否`（OD09） —— 【机器可验】`grep -n "是否必填" <md>` 命中，脚本核对表格列数 = 4 且第 2 列值集合 ⊆ {是, 否}
- [ ] 必填字段截图列无空缺（「是否必填 = 是」的行截图列必有图片引用；非必填字段允许空缺，OD09） —— 【人工判定】逐行核对必填行截图列
- [ ] 批量操作使用三列表格：功能 | 说明 | 截图（OD10） —— 【机器可验】脚本核对批量操作表格列数 = 3（无批量操作章节时豁免，人工确认）
- [ ] 无空内容条目：每个 `###` 标题下至少有 1 个要点或 1 张表（OD14） —— 【人工判定】抽查全部 `###` 标题下内容
- [ ] 每步操作都有对应截图且关键按钮/区域已红框标注（OD13） —— 【人工判定】逐步核对截图/标注齐全
- [ ] 占位符 `{...}` 残留 ≤ 5 处 —— 【机器可验】`grep -oE "\{[^}]+\}" <md> | wc -l` ≤ 5
- [ ] 评审报告存在且评分 ≥ 85 分（`operation_docs/{功能名}-评审报告.md`，通过线权威定义见 `docs/verification/quality-gates.md` §2.4） —— 【机器可验】`test -f operation_docs/{功能名}-评审报告.md`，且报告内评分数值 ≥ 85

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 11:15 | v1.6 | ①原型任务检验项 +2：UI 规范引用映射表存在且无未消解缺失、UI-xx 编号在索引表真实存在（同步 `docs/agents/proto_agent.md` v2.2 Step 5b，引用规则 W26）；②版本 v1.5→v1.6 | 本文件 + `docs/agents/proto_agent.md` v2.2 |
| 2026-08-10 09:25 | v1.5 | ①操作文档检验项 10→14 项：新增文档头 4 行（OD02）/编号连续唯一（OD04）/必填字段截图列无空缺（OD09，用户裁决口径）/无空内容条目（OD14）4 项；②结构对齐项模版名更新为 `操作文档编写参考模版.docx`，grep 修正为 `^## 一、`（补正原 `^一、` 匹配不到 Markdown 标题的既存 bug）；③段首补 OD 权威源引用行；④frontmatter 与属性表版本统一 v1.5（补正 v1.2/v1.4 漂移）；⑤附录历史行按 W10 重排为日期降序 | 本文件 + `docs/pipelines/doc-pipeline.md` v2.0 |
| 2026-08-04 09:10 | v1.4 | ①图先行检查：flowdia 两项（组件渲染 + S09 布线核验）删除，改 D06 mermaid.js 原生渲染检查（`class="mermaid"` ≥1 且无 PNG 无 flowdia）；②新增 D03 活动图语义与 D04 状态机语法检查项；S07 引用改 D05；③Chapter 3 检查项 6 要素废止改 4 要素 + 场景数 3~5；④新增「本章要点块」「简洁可读（F11 + ≤700 行）」两项；⑤frontmatter 与属性表版本 v1.1→v1.4（补正 v1.2/v1.3 未同步）；proto/doc 段 mermaid/flowdia 项不动（范围外） | 本文件 + `docs/rules/prd-diagram-standard.md`（新建）+ `docs/agents/prd_stages/reviewer.md` v1.4 |
| 2026-08-01 | v1.3 | ①章节完整性「4 章」→「5 章」（新增使用场景）；②新增 Chapter 3 使用场景检查项（6 要素 + 规则只引用编号 + 统一示例背景）；③原交互原型/质量属性顺延为 Chapter 4/5，全部 §3.x/§4.x 引用同步更新 | 本文件 |
| 2026-08-01 | v1.2 | ①图先行检查删除业务全景图项（flowchart LR / panorama-container）；②§1.2 业务完整流程随重编号改 §1.1；③新增 §2.1 最小颗粒度检查项（S07：节点拆到子步骤 + 关键约束上卡 + 与 §2.2.x 逐步对齐）；④Chapter 1 章节完整性同步去全景图、§1.1 改为业务完整流程 | 本文件 |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter/属性表/头部 blockquote/附录变更记录；②全部 checkbox 项末尾标注【机器可验】（附检查命令）/【人工判定】（附判定要点），引用规则 W21；③`research_summary.md` 修正为 `01_research_summary.md`（对齐规范 §2.6 注册表）；④图先行检查项中 `docs/rules/flow-diagram-standard.md` 路径补反引号（§2.4）；⑤评审报告评分项补通过线引用 `docs/verification/quality-gates.md` §2.4；⑥各检验项的技术判定内容未改 | 本文件 |
