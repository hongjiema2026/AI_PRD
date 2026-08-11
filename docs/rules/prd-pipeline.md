---
paths:
  - "versions/**/prd/**"
  - "versions/**/agent_comm/prd_*/**"
title: PRD 流水线规则（摘要）
version: v1.2
date: 2026-08-04
status: active
---

# PRD 流水线规则（摘要）

| 属性 | 值 |
|------|-----|
| 版本 | v1.2 |
| 适用范围 | PRD 任务全流程（`versions/**/prd/**`、`versions/**/agent_comm/prd_*/**`） |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 完整流水线 `docs/pipelines/prd-pipeline.md`；检验清单 `docs/verification/checklists.md`；通过线 `docs/verification/quality-gates.md` §1 |

> 本文件是 PRD 流水线的**摘要速查版**，不定义完整流程与评分维度——完整流水线见 `docs/pipelines/prd-pipeline.md`，评分维度与通过线见 `docs/verification/quality-gates.md`（引用规则 W01/W04）。

## 核心阶段
Researcher → Visualizer → Writer → Feasibility → Reviewer → 用户确认 → HTML渲染

## 关键约束
- 可行性验证是强制门禁：编造零容忍，未通过不得进入下一阶段
- 三文件同步：MD + 主HTML + 独立原型HTML 必须同步修改
- PRD 结构为 4 章：概述 / 流程与规则 / 使用场景 / 交互原型（技术契约与质量属性章节已移除）
- 全景图允许多级展开（W11.0）；核心流程与每个子流程均须配图（W13）
- HTML 版流程图/状态图必须 mermaid.js 原生渲染且符合 UML 语义约定（活动图 D03 / 状态机 D04 / 呈现 D06，标准见 `docs/rules/prd-diagram-standard.md`），禁止静态 PNG，PRD 语境禁用 flowdia
- 检验清单见 `docs/verification/checklists.md`

## 流程红线（强制）

### 计划审批
- **绝对禁止**在 Plan Mode 下自行调用 `ExitPlanMode`
- 必须等待用户**明确批准**后方可退出 Plan Mode 并执行

### 门禁检查
- 可行性验证（Feasibility）**未通过**前，**禁止**进入 Reviewer 阶段
- Reviewer 评分 **< 80 分**时，**禁止**进入 HTML 渲染阶段
- **禁止**跳过任何阶段直接执行后续阶段

### 三文件同步
- 修改 PRD 内容时，**必须同步**修改以下三个文件：
  1. MD 文件：`versions/{v}/prd/{功能名}-prd.md`
  2. 主 HTML：`versions/{v}/prd/{功能名}-prd.html`
  3. 独立原型 HTML：`versions/{v}/prototype/proto-*.html`
- **禁止**只修改其中一个文件就报告完成

### Git 提交
- **禁止**在用户未明确说"提交"/"commit"时执行 `git commit`
- 提交前必须展示 `git diff` 结果

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-04 09:10 | v1.2 | ①关键约束中 flowdia 条款改「mermaid.js 原生渲染 + UML 语义约定（D03/D04/D06），禁止静态 PNG，PRD 语境禁用 flowdia」，标准迁指 `docs/rules/prd-diagram-standard.md` | 本文件 + `docs/rules/prd-diagram-standard.md`（新建） |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段（保留原 `paths` 键）/属性表/头部 blockquote/附录变更记录；②核对产出文件名引用与规范 §2.6 注册表：本文件未直接引用编号文件名（`05_prd_review_report.md`/`03_feasibility_report.md`），无需修正；③核心阶段/关键约束/流程红线等技术内容一字未改 | 本文件 |
