---
title: 质量门禁评分标准
version: v2.3
date: 2026-08-11
status: active
---

# 质量门禁评分标准

| 属性 | 值 |
|------|-----|
| 版本 | v2.3 |
| 适用范围 | 全项目所有流水线的评分验收 |
| 创建日期 | 2026-07-10 |
| 最近重写 | 2026-07-28（v2.0 按 SOP 编写规范重构） |
| 状态 | active |

> 本文件是**评分维度、通过线、重试上限的唯一权威来源**（引用规则 W04/W18-W20，完整定义见 `docs/rules/sop-writing-standard.md` §3.5）。
> 其他文档只写「通过线见 `docs/verification/quality-gates.md`」，禁止重复定义维度名或阈值。

## §1 通过线注册表

| 流水线 | 评审角色 | 通过线 | 满分 | 产出文件 |
|--------|---------|--------|------|----------|
| PRD | Reviewer | **≥80** | 100 | `agent_comm/{task_id}/05_prd_review_report.md` |
| 原型 | Tester | **≥90** | 100 | `agent_comm/{task_id}/03_proto_test_report.md` |
| 复原 | Verifier | **≥90**（80-89 有条件通过） | 100 | `agent_comm/{task_id}/03_restore_verification.md` |
| 操作文档 | Reviewer | **≥85** | 100 | `operation_docs/{功能名}-评审报告.md` |
| 知识库 | KB-Reviewer | **≥90** | 100 | 审核结论写入知识文档 frontmatter `review_status` |

> **有条件通过（仅复原流水线）**：评分 80-89 时，Verifier 必须列出全部未通过项并向用户展示，**经用户明确确认后放行**（确认信号见 `docs/rules/sop-writing-standard.md` W15）；用户不确认则按未通过处理。

## §2 评分维度注册表

### §2.1 PRD Reviewer（细则见 `docs/agents/prd_stages/reviewer.md`）

| 维度 | 分值 |
|------|------|
| 概述（Chapter 1，图先行） | 15 |
| 流程与规则（Chapter 2） | 35 |
| 使用场景（Chapter 3） | 5 |
| 交互原型（Chapter 4） | 30 |
| 格式规范（F01-F11 逐项，每条违例扣 1 分，扣完即止） | 10 |
| 简洁可读（本章要点块/场景数 3~5/单段 ≤3 行/全文 ≤700 行） | 5 |

分档处置：`≥80` 通过；`60-79` 返回 Writer 修改；`<60` 返回 Researcher 补充调研。
HTML 呈现附加检查：流程图/状态图静态 PNG 违反 D06 扣 5 分并退回 HTML 渲染阶段（标准见 `docs/rules/prd-diagram-standard.md`）。

### §2.2 原型 Tester（细则见 `docs/agents/proto_agent.md` Tester 段）

| 维度 | 分值 |
|------|------|
| 布局渲染正常 | 25 |
| 交互响应完整 | 25 |
| 组件独立可运行 | 20 |
| 控制台无报错 | 15 |
| 与设计文档一致 | 15 |

分档处置：`≥90` 通过；`70-89` 返回 Implementer 修复；`<70` 返回 Architect 重新设计。

> UI 规范引用验证：设计文档缺「UI 规范引用映射表」或存在未消解「规范缺失」项，计入「与设计文档一致」维度扣 5 分（细则见 `docs/agents/proto_agent.md` Tester Step 5b）。

### §2.3 复原 Verifier（细则见 `docs/agents/restore_agent.md` Verifier 段）

| 维度 | 权重 |
|------|------|
| DOM 结构匹配 | 30% |
| 样式匹配 | 30% |
| 资源完整性 | 20% |
| 交互完整性 | 20% |

分档处置：`≥90` 通过；`80-89` 有条件通过（见 §1 注释）；`<80` 未通过，重试后仍 <80 向用户报告。

### §2.4 操作文档 Reviewer（细则见 `docs/pipelines/doc-pipeline.md`）

| 维度 | 分值 | 说明 |
|------|------|------|
| 结构完整性 | 30 | 章节对齐 `operation_docs/templates/操作文档编写参考模版.docx`（功能介绍/操作说明/次功能/常见问题，规则 OD03） |
| 截图覆盖率 | 30 | 必填字段截图列无空缺（OD09）；每操作条目 ≥1 图（OD08/OD13） |
| 内容准确性 | 20 | 与线上页面/PRD 一致 |
| docx 同步 | 20 | docx 与 Markdown 源一致（docx mtime ≥ Markdown mtime，生成后未手工改 docx） |

通过线 `≥85`；占位符 `{...}` 残留 `≤5` 处。各维度分值与 `scripts/operation_doc_manager.py` review 子命令硬编码一致（30/30/20/20）。

### §2.5 KB-Reviewer（细则见 `docs/agents/kb_agent.md` KB-Reviewer 段）

| 维度 | 分值 | 检查要点 |
|------|------|----------|
| 格式规范 | 25 | frontmatter 完整；标题层级 H1→H2→H3 无跳级；标签在 `config/project.yaml` `kb.allowed_tags` 内 |
| 内容质量 | 30 | 摘要 ≤100 字；日期有效；正文与摘要一致 |
| 溯源完整 | 25 | 来源 URL 标注；`crawl_metadata` 完整（爬虫条目）；截图/复原原型链接有效 |
| 索引同步 | 20 | `docs/knowledge-base/index.md` 含该条目；链接可跳转 |

分档处置：`≥90` 通过（写入 `review_status: approved`）；`<90` 返回 KB-Writer 修改。

## §3 未通过处理

- 任何流水线的自动返工循环统一**最多 2 次**（首次 + 2 次返工 = 3 次尝试；引用规则 W20）
- 返工后仍未通过的，暂停流水线并向用户报告：未通过维度、扣分项、已尝试的修复
- 禁止绕过评分直接报告「已完成」

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 11:15 | v2.3 | ①§2.2 补「UI 规范引用验证」扣分口径（缺表/未消解缺失扣 5 分计入一致性维度，不改五维分值，同步 `docs/agents/proto_agent.md` v2.2 Tester Step 5b，引用规则 W26）；②版本 v2.2→v2.3 | 本文件 + `docs/agents/proto_agent.md` v2.2 |
| 2026-08-10 09:25 | v2.2 | ①§2.4 补「分值」列（30/30/20/20，与 `operation_doc_manager.py` review 硬编码一致，补齐 W18 分值要求）；②截图覆盖率说明改「必填字段截图列无空缺、每操作条目 ≥1 图」（用户裁决落地，引用 OD08/OD09/OD13）；③结构完整性说明模版名更新为 `操作文档编写参考模版.docx`；④frontmatter 与属性表版本统一 v2.2（补正 v2.0/v2.1 漂移） | 本文件 + `docs/pipelines/doc-pipeline.md` v2.0 |
| 2026-08-04 09:10 | v2.1 | ①§2.1 PRD Reviewer 维度 6→7：格式规范 15→10（F01-F11、每条扣 1）、新增「简洁可读 5」（要点块/场景数/段落长度/总行数）；②HTML 附加检查 H06 表述改 D06（静态 PNG，标准迁指 prd-diagram-standard.md） | 本文件 + `docs/agents/prd_stages/reviewer.md` v1.4 + `docs/agents/prd_agent.md` v1.4 |
| 2026-07-28 | v2.0 | ①按 `docs/rules/sop-writing-standard.md` 重构结构（frontmatter + 附录）；②PRD 评审报告文件名 `03_` → `05_`（对齐规范 §2.6 注册表）；③PRD Reviewer 维度名与 reviewer.md 统一（概述/流程与规则/交互原型/质量属性/格式规范，含分值）；④复原通过线 `≥80%` → `≥90`（80-89 有条件通过，定义放行条件）；⑤新增 KB-Reviewer 评分细则表（25+30+25+20，≥90）；⑥重试「2-3 次」统一为「最多 2 次」；⑦原型 Tester 维度名与 proto_agent.md 对齐（布局/交互/组件独立/控制台/一致性） | 本文件 + `docs/pipelines/prd-pipeline.md` + `docs/agents/prd_stages/reviewer.md` + `docs/使用指南.md` |
