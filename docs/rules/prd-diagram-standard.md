---
title: PRD 图绘制标准（Mermaid UML 语义约定）
version: v1.0
date: 2026-08-04
status: active
---

# PRD 图绘制标准（Mermaid UML 语义约定）

| 属性 | 值 |
|------|-----|
| 版本 | v1.0 |
| 适用范围 | PRD 流水线全部产出图（MD 权威源 + HTML 呈现），覆盖 `templates/prd_template.md` 全部图位 |
| 创建日期 | 2026-08-04 |
| 状态 | active |
| 关联文档 | `docs/agents/prd_agent.md`（W11/W13 引用本文件）、`docs/agents/prd_stages/html_render.md`（H06 引用 D06）、`docs/rules/flow-diagram-standard.md`（proto/diagram 存量 HTML 流程图呈现标准）、`docs/rules/sop-writing-standard.md`（§2.5 编号注册表） |

> 本文件是 **PRD 流水线图绘制规则（D01-D08）的唯一权威定义**（已在 `docs/rules/sop-writing-standard.md` §2.5 编号前缀注册表注册），其他文档只写「引用规则 Dxx」。
> 制定背景：本机无 Java/Docker，PlantUML 本地渲染不可行、在线渲染有业务数据外泄风险，故图源载体保持 Mermaid，但绘制语义严格对齐 UML（活动图/状态机）。
> **边界**：proto/diagram/doc 工作流的图源与 flowdia 呈现不在本文件范围，见 `docs/rules/flow-diagram-standard.md` v1.4 起适用范围声明。

## §1 目的与核心原则

### §1.1 目的

让 PRD 中的流程图、状态机图在 Mermaid 载体上严格遵循 UML 语义：读者看到起止节点、判断菱形、泳道、初终态即可按 UML 习惯零成本阅读。

### §1.2 核心原则

| 原则 | 含义 | 违反后果 |
|------|------|----------|
| 语义对齐 UML | 流程图按 UML 活动图语义绘制，状态图用 UML 状态机语法 | 违反 = D08 清单不通过，Reviewer 退回 |
| 载体单一 | 图源只用 Mermaid 受限语法集，禁止混用其他图语法 | 违反 = D01 不通过 |
| MD 唯一权威源 | HTML 呈现与 MD 图源同一份代码，禁止双份维护 | 违反 = D06 不通过 |

## §2 术语定义

| 术语 | 含义 |
|------|------|
| 活动图语义 | UML Activity Diagram 的节点语义：起止圆角端点、动作矩形、判断菱形、泳道分区、分支显式合并 |
| 状态机语法 | UML State Machine 语法：`[*]` 初终态、转移标注 `事件 [守卫] / 动作` |
| 受限语法集 | 本文件 D02 枚举的 Mermaid 图类型与 D03/D04 约定的画法，之外的 Mermaid 特性不使用 |

## §3 规则定义（D01-D08）

**D01 图源载体**：PRD 中所有图必须使用 Mermaid 内联代码块（` ```mermaid ... ``` `），禁止外部 PNG/JPG 引用，禁止 PlantUML/Graphviz 等其他图语法。机器可验：`grep -nE "!\[.*\]\(.*\.(png|jpg)" <prd.md>` 结果为空。

**D02 图类型映射**（枚举封死，引用规则 W07）：

| 图 | 对应章节 | Mermaid 类型 | UML 语义 |
|----|---------|-------------|----------|
| 业务完整流程 | §1.1 | `flowchart LR` | 活动图（简化，5~7 步） |
| 核心业务流程 | §2.1 | `flowchart TD` | 活动图（最小颗粒度，引用 D05） |
| 子流程图 | §2.2.x（每个子流程） | `flowchart TD` | 活动图 |
| 状态流转 | §2.3 | `stateDiagram-v2` | 状态机 |
| 使用场景示意图 | §3.x | `flowchart LR` 或 `flowchart TD` | 活动图 |
| 角色关系图 | Ch2 补充 | `flowchart LR` | 用例关系语义 |
| 架构图 | Ch5 补充 | `flowchart LR` | 组件关系语义 |

**D03 活动图语义约定**（`flowchart` 载体强制画法）：

1. **起止节点**：起点/终点必须用 stadium 形 `A([开始])` / `Z([结束])`，每图恰 1 个起点；业务流有显式终点时必须画出
2. **判断节点**：必须用菱形 `B{条件}`；每条出边必须有分支标签（`-->|命中|` / `-->|未命中|` 或具体条件值），禁止无标签出边
3. **分支合并**：判断引出的分支路径必须显式汇入同一后继节点或各自终止，禁止分支悬空
4. **动作节点**：矩形 `C[动作]`，文案 = 动词短语；涉及业务规则时附规则编号（如 `C["创建活动<br/>R07"]`）。节点文案引用规则ID时，HTML 渲染版须支持鼠标悬停显示规则描述（实施见 `docs/agents/prd_stages/html_render.md` H08）
5. **泳道分区**：跨角色/系统协作时用**单层** `subgraph` 分区；⛔ 禁止嵌套 subgraph 跨簇串联（教训来源：`docs/rules/flow-diagram-standard.md` S08-1，dagre 排序错乱）；无泳道需求时不用 subgraph
6. **样式语义**：判断节点 amber（`#e6a23c`）、正常/成功 green（`#52C41A`）、失败/熔断 red（`#F5222D`）、主流程 blue（`#409eff`）、外部/人工 gray（`#909399`）；用 `classDef` 统一声明，禁止逐节点硬编码散落

**D04 状态机约定**（`stateDiagram-v2` 强制画法）：

1. 必须含初始态 `[*] --> 状态A`；有终态时必须含 `状态N --> [*]`
2. 转移标注格式：`状态A --> 状态B : 事件 [守卫条件] / 动作`，事件必填，守卫条件用 `[条件]`，无动作时省略 `/ 动作`
3. 状态名使用中文界面标签（对齐 F03 枚举口径）
4. §2.3 状态机图不可省略；图后必须配状态转移表（状态 | 触发条件 | 下一状态 | 备注）

**D05 颗粒度与规则表达**（自 `docs/rules/flow-diagram-standard.md` S07 迁移，语义不变）：

1. 主流程必须拆到「子步骤可独立验证」级别；图的步骤与 §2.2.x 正文逐步对齐、编号一致
2. 关键业务约束（时间窗口/阈值/重试上限）必须一句话写进节点文案，禁止只放术语名让读者去正文找
3. 复杂规则正文配图解：一句话规则 + 判断步骤，图中节点与正文互相索引

**D06 HTML 呈现**：HTML 渲染版中流程图/状态图直接用 mermaid.js CDN 运行时渲染 MD 中的 Mermaid 权威源（初始化配置见 `docs/agents/prd_stages/html_render.md` H06）；禁止静态 PNG 截图；PRD 语境禁止使用 flowdia 组件（flowdia 仅供 proto/diagram 存量 HTML 维护，见 `docs/rules/flow-diagram-standard.md` v1.4 适用范围）。

**D07 图注强制**：每个图代码块后必须紧跟一行斜体图注，格式 `*图 N-M：{图名}。{一句话总结}。*`（对齐 F06）。

**D08 检查清单**（Writer/Reviewer 必检，标注口径引用规则 W21）：

| # | 检查项 | 类型 | 检查方法 |
|---|--------|------|----------|
| 1 | 图源全部 Mermaid 内联、无外部图片引用 | 【机器可验】 | `grep -nE "!\[.*\]\(.*\.(png|jpg)" <prd.md>` 结果为空 |
| 2 | 活动图含 stadium 起止节点、判断菱形带分支标签 | 【机器可验】 | `grep -c "(\[" <prd.md>` ≥ 2；`grep -c "\-\->\|" <prd.md>` ≥ 1 |
| 3 | 状态图含 `[*]` 初态且转移标注含事件 | 【机器可验】 | `grep -c "\[\*\]" <prd.md>` ≥ 1；`grep -c "stateDiagram-v2" <prd.md>` ≥ 1 |
| 4 | 泳道为单层 subgraph，无嵌套跨簇串联 | 【机器可验】 | `grep -c "subgraph" <prd.md>` 命中处目检无嵌套 |
| 5 | 活动图分支已显式合并、语义配色符合 D03-6 | 【人工判定】 | 逐图核对分支汇聚与 classDef 配色 |
| 6 | 图步骤与 §2.2.x 正文逐步对齐（D05-1） | 【人工判定】 | 图节点与正文子流程编号逐步比对 |
| 7 | 每图有图注（D07/F06） | 【机器可验】 | 每个 ` ``` ` 闭合块后目检斜体图注行 |

## §4 检验清单

| # | 检验项 | 类型 | 检查方法 |
|---|--------|------|----------|
| 1 | frontmatter 四字段齐全 | 【机器可验】 | `head -8 docs/rules/prd-diagram-standard.md \| grep -c "^title:\|^version:\|^date:\|^status:"` = 4 |
| 2 | 文末含附录变更记录且本次行带时间 | 【机器可验】 | `grep -nE "^\| 2026-08-04 [0-9]{2}:[0-9]{2} \|" docs/rules/prd-diagram-standard.md` 命中 |
| 3 | 章节无四级标题、全文 ≤500 行 | 【机器可验】 | `grep -c "^####" docs/rules/prd-diagram-standard.md` = 0；`wc -l` ≤ 500 |

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-04 09:10 | v1.0 | ①首次发布：PRD 图源 = Mermaid 受限语法集（D01）+ 图类型映射（D02）+ 活动图 UML 语义约定（D03：stadium 起止/判断菱形/分支合并/单层泳道/语义配色）+ 状态机 UML 语法约定（D04）+ 颗粒度规则（D05，自 flow-diagram-standard S07 迁移）+ HTML mermaid.js 原生渲染（D06，PRD 语境弃用 flowdia）+ 图注强制（D07）+ 检查清单（D08） | 本文件（新建）+ `docs/rules/sop-writing-standard.md` §2.5（注册 D 前缀） |
