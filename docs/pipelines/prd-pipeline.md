---
title: PRD 流水线（图先行）
version: v2.3
date: 2026-08-04
status: active
---

# PRD 流水线（图先行）

| 属性 | 值 |
|------|-----|
| 版本 | v2.3 |
| 适用范围 | prd 任务全流程（Researcher → Visualizer → Writer → Feasibility → Reviewer → 用户确认 → HTML 渲染） |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 评分维度/通过线 `docs/verification/quality-gates.md`；产出文件命名 `docs/rules/sop-writing-standard.md` §2.6；编写规范 `docs/rules/sop-writing-standard.md` |

> 本文件是 **prd 流水线的唯一权威定义**（阶段划分/产出物/任务书模板/上下文预算）。评分维度与通过线见 `docs/verification/quality-gates.md`；编写规范见 `docs/rules/sop-writing-standard.md`（引用规则 W01/W04）。

## 流程概览
```
Researcher（调研） → Visualizer（图先行） → Writer（业务文档） → Feasibility（可行性验证） → Reviewer（评审） → 用户确认 → HTML渲染
```

## 各阶段职责

### Researcher（调研）
- 知识库检索 + API文档分析 + 用户分析 + 参考资料收集
- 产出：`agent_comm/{task_id}/01_research_summary.md`

### Visualizer（图先行）
- 基于调研结果，**先出2组图**（流程图→角色图），全部以 **Mermaid 内联代码块**产出（不导出 PNG，不调用 Figma），遵循 UML 语义约定（活动图 D03 / 状态机 D04，标准见 `docs/rules/prd-diagram-standard.md`）
- 2组图为 PRD 必配，不可省略
- HTML 呈现层：全部图在 HTML 渲染版中用 mermaid.js CDN 直接渲染 MD 权威源（引用规则 D06，禁止静态 PNG，PRD 语境禁用 flowdia），实施配置见 `docs/agents/prd_stages/html_render.md` H06

### 2组标准图

| 序号 | 图类型 | 对应章节 | 内容 | Mermaid 类型 |
|------|--------|---------|------|-------------|
| 1 | 流程图 | 2. 流程与规则 | 核心业务流程：主流程 + 关键分支，**最小颗粒度**（拆到子步骤可独立验证，关键约束一句话上卡） | `flowchart TD`（UML 活动图语义，D03） |
| 2 | 角色关系图 | 2. 流程与规则（补充） | 谁参与、什么角色、系统间关系 | `flowchart LR`（用例关系语义，D02） |

### 子流程描述与状态机图

**2.1 核心业务流程**必须配 Mermaid `flowchart` 图，遵循 UML 活动图语义（stadium 起止/判断菱形带分支标签/分支显式合并，引用规则 D03），且**必须最小颗粒度**——拆到子步骤可独立验证级别、关键业务约束一句话写进节点文案（规则上卡），颗粒度标准与正文 §2.2.x 逐步对齐，引用规则 D05。**2.2.x 子流程**必须配 Mermaid `flowchart TD` 图（UML 活动图语义，D03），辅以简短文字说明（每节 ≤8 行），文字仅作图注与分支补充。状态流转必须配 `stateDiagram-v2` 图（UML 状态机语法，引用规则 D04）。

| 序号 | 图类型 | 对应章节 | 内容 | Mermaid 类型 |
|------|--------|---------|------|-------------|
| 5~N | 子流程图 | 2.2.x 每个子流程 | 子流程完整步骤 + 判断分支 + 异常路径 | `flowchart TD`（UML 活动图语义，D03） |
| N+1 | 状态机图 | 2.3 状态流转 | UML 状态图：初始态、业务状态、终止态、转移事件 + 守卫条件 | `stateDiagram-v2`（D04） |

生成方式：
- 子流程图：Mermaid 内联代码块（`flowchart TD`，D03 活动图语义），每个 2.2.x 子流程一张
- 状态机图：Mermaid 内联代码块（`stateDiagram-v2`，D04），包含初始/终止状态
- 全部图表汇总写入图表索引 `02_diagram_index.md`；PNG 导出仅作为对外分享/存档的可选产物

### Writer Phase 1 — 业务文档（围绕图写文字）

**围绕已有的图填充文字细节**，按 4 章模板编写业务文档部分：

```
1. 概述（Chapter 1）
   - 本章要点块（blockquote，3~5 行结论，每章固定）
   - 1.1 业务完整流程 ← 嵌入业务完整流程图（Mermaid 内联，D03 活动图语义）
   - 1.2 背景与目标（含非目标、成功指标）
   - 1.3 范围定义（含前置依赖）
   - 1.4 术语与分类
   （Ch1 整章 ≤80 行）

2. 流程与规则（Chapter 2） ← 嵌入流程图 + 状态机图 + 规则索引
   - 本章要点块
   - 2.1 核心业务流程 ← 图1 主流程图（Mermaid 内联，最小颗粒度 D05 + 活动图语义 D03，索引见 `02_diagram_index.md`）
   - 2.2 子流程详述 ← 每个子流程必须配 Mermaid 图（图5~N，内联），辅以简短文字说明（≤8 行）
   - 2.3 状态流转 ← 嵌入状态机图（图N+1，Mermaid 内联，D04）
   - 2.4 业务规则索引（R01/R02/... 编号，规则只定义一次）
   - 2.5 边界与异常

3. 使用场景（Chapter 3） ← 场景化举例说明系统行为
   - 本章要点块
   - 章节引言：统一示例背景（运营角色 + 店铺 + 站点）
   - 3.x 每个场景只含 4 要素 = 场景背景（≤2 句）+ Mermaid 示意图 + 图注 + 关键规则 + 对应页面
     ⚠️ 禁止「系统行为举例」长段（旧 6 要素已废止）；场景数收紧为 3~5 个
   - 规则只引用编号（R01/R02...），不重复规则内容（与 §2.4 唯一权威源对齐）
   - 场景示意图遵循 D03 活动图语义，HTML 版 mermaid.js 原生渲染（D06）

4. 交互原型（Chapter 4） ← 嵌入式原型 + 全屏
   - 本章要点块
   - 4.x 每个模块 → proto-{name}.html（标题紧下方 iframe 内嵌，文字说明在后）
   - 每个嵌入块含「全屏查看」按钮
   - 标注点说明只写交互逻辑（禁止样式描述）
   - 引用规则 ID，不重复规则
   - 字段定义含数据字段列（inline code）
   - `.anno-table` 后必须紧跟 `<script class="anno-detail-data">` JSON（详尽原型规格）
```

> 篇幅红线：单段落 ≤3 行（引用规则 F11）；全文目标 400~600 行，>700 行 Reviewer 简洁可读维度扣分。

产出：`versions/{v}/prd/{功能名}-prd.md`（完整 PRD，4 章结构，不含技术契约）

### Feasibility（可行性验证）— 强制门禁

Writer Phase 1 完成后，进入**强制可行性验证**阶段。此阶段逐项审查 PRD 中的每个事实性声明，确保所有内容都有据可查。**未通过验证的内容必须删除**，不可保留为"待确认"。

### 验证范围

| 验证类别 | 检查内容 | 验证方法 |
|---------|---------|---------|
| API 声明 | 接口名、网关地址、请求/响应字段 | 逐条对照 `research_summary.md` 中的 API 文档记录 |
| 枚举值 | auditStatus、certType、complianceLabelStatus（示例，非穷举；全集以 `01_research_summary.md` 中的 API 文档记录为准） | 必须来自 API 文档或实际调用返回；如文档未给出具体枚举值，在 PRD 中只写"具体枚举值需对接时确认"，**禁止编造枚举示例** |
| 技术指标 | 文件大小限制、并发数、超时时间、限流阈值 | 必须来自 API 文档或平台公开说明；**禁止凭经验编造具体数值** |
| 业务指标 | "降低XX成本XX%"、"提升XX效率XX%" | 必须有数据来源（用户调研、竞品数据、历史数据）；**禁止编造量化指标** |
| 业务规则 | 状态流转、错误码、权限要求 | 逐条对照调研记录；如调研中未涉及，标注为"需对接时确认" |
| 流程逻辑 | 子流程步骤、触发条件、异常处理 | 流程步骤必须与 API 调用链路一致，不可虚构 API 不支持的流程 |
| 数据结构 | 本地数据表的字段名、类型 | 字段名和类型应来自 API 响应字段或明确标注为"本地定义" |

### 验证流程

1. **逐段扫描**：按 PRD 章节顺序，提取每一段中的事实性声明。判定标准：句子中含以下任一要素即为事实性声明——具体数值、枚举值、量化指标、API 字段名、状态值、时间/阈值/限制
2. **溯源比对**：将每个声明与 `research_summary.md` 或其他调研证据逐条对照
3. **分类判定**（边界已封死，按定义机械执行）：
   - ✅ **已验证**：`research_summary.md` 中存在该声明的原文记录（API 文档摘录 / 实际调用返回 / 用户原话），报告中可引用到具体章节或行
   - ⚠️ **需软化**（须**同时满足**两条）：①声明所属对象（类型 / 字段 / 指标）本身已在调研记录中验证存在；②仅具体取值（枚举值 / 数值 / 阈值）缺失 → 改写为"具体枚举值需对接时通过 `{API名}` 返回确认"
   - ❌ **无法验证**（命中任一即判定）：①声明对象本身在调研记录中无任何记录；②数值 / 枚举 / 指标无任何来源 → **直接删除**，不可保留
   - **边界规则**：不同时满足 ⚠️ 两条时一律按 ❌ 处理（宁缺毋滥，禁止折中保留）
4. **执行修改**：对 ⚠️ 和 ❌ 项直接修改 PRD 文件
5. **产出报告**：写入 `agent_comm/{task_id}/03_feasibility_report.md`

### 核心原则
- **宁缺毋滥**：不确定的内容宁可删除，不可保留猜测
- **证据为王**：每个事实性声明都必须能追溯到调研记录
- **编造零容忍**：任何无法溯源的具体数值、枚举值、指标都属于编造，必须处理
- **Reviewer 前置门禁**：可行性验证未通过的 PRD 不得进入 Reviewer 阶段

### 可行性验证报告格式

报告写入 `agent_comm/{task_id}/03_feasibility_report.md`，格式如下：

```markdown
# 可行性验证报告

> 验证日期：{date}
> 验证对象：{prd-file}

## 验证统计
- 总声明数：{N}
- ✅ 已验证：{X}（{X/N}%）
- ⚠️ 已软化：{Y}（已改写为"需对接时确认"）
- ❌ 已删除：{Z}（无调研依据）

## 已验证项（✅）
| # | PRD 位置 | 声明内容 | 证据来源 |
|---|---------|---------|---------|
| 1 | §2.1 流程 | `{apiName}` 存在 | research_summary.md |

## 已软化项（⚠️）
| # | PRD 位置 | 原始内容 | 修改为 |
|---|---------|---------|-------|
| 1 | §2.3 状态流转 | 具体枚举值 | "具体枚举值需对接时确认" |

## 已删除项（❌）
| # | PRD 位置 | 删除内容 | 删除原因 |
|---|---------|---------|---------|
| 1 | §1.2 目标 | "降低XX成本 80%+" | 无数据来源，系编造 |
```

### Reviewer（评审）
- 评分维度与通过线权威定义见 `docs/verification/quality-gates.md` §1/§2.1（≥80 通过，引用规则 W01/W18）
- 产出：`agent_comm/{task_id}/05_prd_review_report.md`

### 用户确认
- Reviewer 通过后暂停，等待用户确认 Markdown 内容无误
- **未获用户确认不得进入 HTML 渲染阶段**

### HTML 渲染
- 仅用户确认后才生成 .html 渲染版本
- 图表呈现：全部图（流程图/状态图/角色图）用 mermaid.js CDN 直接渲染 MD 权威源（引用规则 D06，禁止静态 PNG，PRD 语境禁用 flowdia），实施配置见 `docs/agents/prd_stages/html_render.md` H06
- 产出：`versions/{v}/prd/{功能名}-prd.html`

## 任务书模板

```yaml
task_id: prd_{feature简称}_{timestamp}
type: prd
status: in_progress
pipeline: [Researcher, Visualizer, Writer_Phase1, Feasibility, Writer_Phase2, Reviewer]
input: |
  {用户原始输入}
context:
  version: {target_version}
  knowledge_base: docs/knowledge-base/
  api_docs: docs/knowledge-base/platform-api/
expected_output:
  - versions/{v}/agent_comm/{task_id}/01_research_summary.md
  - versions/{v}/agent_comm/{task_id}/02_diagram_index.md      # 图表索引（3组标准图 + 子流程/状态机，Mermaid 内联）
  - versions/{v}/prd/{功能名}-prd.md                      # 含全部 4 章
  - versions/{v}/agent_comm/{task_id}/03_feasibility_report.md
  - versions/{v}/agent_comm/{task_id}/05_prd_review_report.md
```

## 波次规划

PRD 流水线各阶段依赖紧密（Researcher → Visualizer → Writer → Feasibility → Reviewer），无天然并行点。并行优势体现在 multi 任务组合中（见 CLAUDE.md 多任务组合规则）。

## 上下文估算

> 预算按**行数**执行（KB 估算已废弃）；水位控制与豁免规则见 `AGENTS.md` 上下文水位管理（唯一权威定义）。

| 阶段 | 加载上限（行） | 必须加载 | 可延迟 |
|------|---------|---------|--------|
| Researcher | ≤400 | KB 索引 + API 文档 + research_summary 模板 | 其他版本 PRD |
| Visualizer | ≤200 | research_summary（前阶段产出） | 完整 PRD |
| Writer | ≤650 | 4 张图 + research_summary + prd_template.md | 其他版本文件 |
| Feasibility | ≤500 | Writer 产出 + research_summary | 原型文件 |
| Reviewer | ≤400 | 完整 PRD + checklists.md | 原型文件 |
| HTML 渲染 | 不限（代码级规范豁免） | 完整 PRD + html_render.md + 所有原型 HTML | research/feasibility |

### 渐进式加载规则
1. 进入阶段时仅加载该阶段的 required 内容
2. 前阶段产出通过 `agent_comm/{task_id}/` 文件路径引用，按需读取
3. 禁止一次读取完整 pipeline 文档 — 只读当前阶段章节
4. 每阶段加载行数遵循 `AGENTS.md` 上下文水位管理（>800 行停载非必需，>1500 行主动 compact）；`docs/agents/prd_stages/html_render.md` 为代码级规范，整读豁免

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-04 09:10 | v2.3 | ①Visualizer 节与两张图规划表补 UML 语义约定（D02 类型映射/D03 活动图/D04 状态机），flowdia 呈现表述改 mermaid.js 原生渲染（D06），颗粒度引用 S07 改 D05；②Writer Phase 1 结构块：每章补「本章要点」块、Ch3 场景 6 要素废止改 4 要素（场景数 3~5）、Ch4 标注点说明限交互逻辑、5.4 仅真阻塞项、文末补篇幅红线（F11 + 400~600 行目标）；③HTML 渲染节 flowdia/PNG 表述改 D06 mermaid 原生渲染（全图种） | 本文件 + `docs/rules/prd-diagram-standard.md`（新建）+ `docs/agents/prd_stages/writer.md` v1.4 |
| 2026-07-28 | v2.0 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段/属性表/头部 blockquote/附录变更记录（结构对齐规范）；②全文产出文件名核对与规范 §2.6 注册表一致（`03_feasibility_report.md`/`05_prd_review_report.md` 统一，无旧写法残留）；③Feasibility 三态判定（✅/⚠️/❌）已操作化为机械判定式（此前完成，本次保留原样）；④上下文估算表已行数化（保持）；⑤Reviewer 段删除内联维度分值，改为引用 `docs/verification/quality-gates.md` §1/§2.1（消除双份定义，引用规则 W01）；⑥验证范围表「等」开放列举改为封闭示例口径（W06）；⑦4组标准图/子流程描述与状态机图/验证范围/验证流程/核心原则/可行性验证报告格式 6 处四级标题降为三级（规范 §2.1 禁止四级标题） | 本文件 |
| 2026-08-01 | v2.1 | ①删除业务全景图/脑图（Chapter 1 不再含全景图，原 §1.2 业务完整流程升为 §1.1，§1.3/1.4/1.5 顺次上移）；②4组标准图收敛为 3 组（流程图→角色图→架构图）；③§2.1 核心业务流程绑定最小颗粒度（拆到子步骤可独立验证 + 关键约束上卡，引用 S07）；④HTML 渲染章节号随重编号同步（§1.2→§1.1） | 本文件 |
| 2026-08-01 | v2.2 | ①新增 Chapter 3「使用场景」（场景背景+系统行为举例+Mermaid示意图+关键规则+对应页面，规则只引用编号不重复）；②原交互原型/质量属性顺延为 Ch4/Ch5；③PRD 结构由 4 章扩为 5 章 | 本文件 |
