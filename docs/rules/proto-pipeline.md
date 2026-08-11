---
paths:
  - "versions/**/prototype/**"
  - "versions/**/agent_comm/proto_*/**"
title: 原型设计流水线规则（摘要）
version: v1.2
date: 2026-08-11
status: active
---

# 原型设计流水线规则（摘要）

| 属性 | 值 |
|------|-----|
| 版本 | v1.2 |
| 适用范围 | 原型任务全流程（`versions/**/prototype/**`、`versions/**/agent_comm/proto_*/**`） |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 完整流水线 `docs/pipelines/proto-pipeline.md`；通过线 `docs/verification/quality-gates.md` §1 |

> 本文件是原型设计流水线的**摘要速查版**，不定义完整流程与评分维度——完整流水线见 `docs/pipelines/proto-pipeline.md`，评分维度与通过线见 `docs/verification/quality-gates.md`（引用规则 W01/W04）。

## 核心阶段
Architect（架构设计） → Implementer（页面实现） → Tester（测试验收，评分 ≥90 通过）

## 关键约束
- 原型使用独立 HTML 文件（proto-{name}.html）
- 全景图使用 `.panorama-container` 包裹，含横向滚动和全屏按钮
- 原型 HTML 使用 `.proto-embed` iframe 嵌入 PRD
- 交互流程图/脑图以 Mermaid 内联于设计文档；HTML 页面中呈现的流程图必须使用 flowdia 交互组件，禁止静态 PNG（标准见 `docs/rules/flow-diagram-standard.md`）
- 设计文档必须包含「UI 规范引用映射表」（每个页面框架/弹窗/控件/交互 ↔ UI-xx 编号）；存在未消解「规范缺失」项时禁止进入实现阶段，须先通过 `/manage-ui-standard` 补充（权威定义见 `docs/agents/proto_agent.md` Step 5b）

## 流程红线（强制）

### 计划审批
- **绝对禁止**在 Plan Mode 下自行调用 `ExitPlanMode`
- 必须等待用户**明确批准**后方可退出 Plan Mode 并执行

### 校验流程（Tester 阶段必做）
- 原型修改后**必须**通过浏览器预览验证所有功能路径
- **必须**生成 `agent_comm/{task_id}/03_proto_test_report.md`
- 报告必须包含：测试用例、结果、评分；评分通过线权威定义见 `docs/verification/quality-gates.md` §1
- **禁止**跳过 Tester 阶段直接报告"已完成"

### Git 提交
- **禁止**在用户未明确说"提交"/"commit"时执行 `git commit`
- 提交前必须展示 `git diff` 结果

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 11:15 | v1.2 | ①关键约束新增「UI 规范引用映射表」强制项（缺失阻断，同步 `docs/agents/proto_agent.md` v2.2 Step 5b，引用规则 W26）；②版本 v1.1→v1.2 | 本文件 + `docs/agents/proto_agent.md` v2.2 + `docs/pipelines/proto-pipeline.md` |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段（保留原 `paths` 键）/属性表/头部 blockquote/附录变更记录；②「报告必须包含」行删除内联通过线，改为引用 `docs/verification/quality-gates.md` §1（消除双份定义，引用规则 W01）；③阶段名 Architect→Implementer→Tester 与其余技术内容一字未改 | 本文件 |
