---
paths:
  - "operation_docs/**"
title: 操作文档流水线规则（摘要）
version: v1.2
date: 2026-08-10
status: active
---

# 操作文档流水线规则（摘要）

| 属性 | 值 |
|------|-----|
| 版本 | v1.2 |
| 适用范围 | 操作文档任务全流程（`operation_docs/**`） |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 完整流水线 `docs/pipelines/doc-pipeline.md`；评审细则与通过线 `docs/verification/quality-gates.md` §2.4；样式权威源 `operation_docs/templates/操作文档编写参考模版.docx` |

> 本文件是操作文档流水线的**摘要速查版**，不定义完整流程与评分维度——完整流水线见 `docs/pipelines/doc-pipeline.md`，评分维度与通过线见 `docs/verification/quality-gates.md` §2.4（引用规则 W01/W04）。

## 核心阶段
Explorer（线上页面探索与截图采集） → Planner（结构规划） → Writer（Markdown 编写） → Reviewer（评审，评分 ≥85 通过） → docx 生成

## 关键约束
- 编写规则明细 OD01-OD14（文档头/章节体系/编号/三段式/字段表/批量表/截图/禁忌）唯一权威定义见 `docs/pipelines/doc-pipeline.md` §3，本文件不重述
- 文档结构对齐 `操作文档编写参考模版.docx`：功能介绍 / 操作说明 / 次功能（可选） / 常见问题；文档头固定 4 行（OD02）；章节 = 中文数字顿号、条目 = 阿拉伯数字顿号（OD03）
- 字段说明使用四列表格：字段/操作 | 是否必填 | 说明 | 截图；**必填字段截图列不得空缺**，非必填允许空缺（OD09）
- 批量操作使用三列表格：功能 | 说明 | 截图（OD10）
- 流程图以 Mermaid 源码为权威源（保留在 Markdown 源文件），PNG 仅作 docx 呈现——docx 为《交互式流程图标准》（flowdia）的显式例外，见 `docs/rules/flow-diagram-standard.md` 适用范围
- 评审评分 ≥ 85 分（权威定义见 `docs/verification/quality-gates.md` §2.4）
- 占位符 `{...}` 残留 ≤ 5 处

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-10 09:25 | v1.2 | ①模版引用名单点更新：【图片任务】.docx → `操作文档编写参考模版.docx`（文件已归位 `operation_docs/templates/`）；②关键约束新增 OD01-OD14 规则明细引用行（W01 不重述）；③截图口径放宽为「必填字段截图列不得空缺」（对齐用户裁决与模版实际）；④补批量操作三列表约束行（对齐 checklists） | 本文件 + `docs/pipelines/doc-pipeline.md` v2.0 |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段（保留原 `paths` 键）/属性表/头部 blockquote/附录变更记录；②评审评分 ≥85 处补权威定义引用 `docs/verification/quality-gates.md` §2.4（引用规则 W02）；③核心阶段/关键约束等技术内容一字未改 | 本文件 |
