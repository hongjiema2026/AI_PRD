---
name: prd-write
description: PRD需求文档编写，含调研→图先行→撰写→可行性验证→评审完整流水线。当用户说"写PRD"/"需求文档"/"PRD"时触发。
---

# PRD 编写 Skill

> 本文件为引用壳（引用规则 W03）。角色细则、格式规范 F01-F11、写作规范 W11-W13 的唯一权威源是 `docs/agents/prd_agent.md`；流水线流程的唯一权威源是 `docs/pipelines/prd-pipeline.md`；评分与通过线的唯一权威源是 `docs/verification/quality-gates.md` §2.1；图绘制规则的唯一权威源是 `docs/rules/prd-diagram-standard.md`（D01-D08）。

## 角色与触发场景

负责需求分析、PRD 编写和评审，内部流水线为 Researcher → Visualizer → Writer → Feasibility → Reviewer。触发场景：用户提出写 PRD / 需求文档 / PRD。完整角色定义见 `docs/agents/prd_agent.md` §2。

## 执行流程（摘要）

| 子角色 | 一句话职责 | 定义位置 |
|--------|-----------|----------|
| Researcher | 调研背景/用户/场景/竞品/API 与数据源 | `docs/agents/prd_stages/researcher.md` |
| Visualizer | 图先行：流程图→角色图→架构图 | `docs/agents/prd_stages/visualizer.md` |
| Writer（Phase 1） | 基于调研撰写 PRD 前 2 章 | `docs/agents/prd_stages/writer.md` |
| Feasibility | 可行性验证（强制门禁） | `docs/agents/prd_stages/reviewer.md` |
| Writer（Phase 2） | 完成 PRD 全部 5 章 | `docs/agents/prd_stages/writer.md` |
| Reviewer | 完整性/格式规范/可行性评分评审 | `docs/agents/prd_stages/reviewer.md` |
| 用户确认 | Markdown 产出物确认（信号判定引用规则 W14） | `docs/rules/sop-writing-standard.md` §3.4 |
| HTML 渲染 | 用户确认后生成 HTML 渲染版 | `docs/agents/prd_stages/html_render.md` |

> 阶段路由与加载时机、禁止一次加载全部阶段文件：完整定义见 `docs/agents/prd_agent.md` §3。格式规范 F01-F11、写作规范 W11-W13：完整定义见 `docs/agents/prd_agent.md`（引用规则 W01，禁止在本文内联）。

## 完成标志

- `01_research_summary.md`、`*-prd.md`（5 章齐全）文件存在且非空
- `05_prd_review_report.md` 存在且评分 ≥80（评分维度与通过线见 `docs/verification/quality-gates.md` §1、§2.1）
- 用户已确认 Markdown 内容（信号判定引用规则 W14）；确认后 HTML 渲染版已生成

## 失败信号

写入 `versions/{v}/agent_comm/{task_id}/BLOCKED.md`，内容包含 `block_reason` 和 `required_input`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-04 09:10 | v2.1 | ①两处「F01-F10」→「F01-F11」（prd_agent v1.4 新增 F11）；②头部引用壳补图绘制规则权威源 `docs/rules/prd-diagram-standard.md`（D01-D08） | 本文件 + `docs/agents/prd_agent.md` v1.4 |
| 2026-07-28 | v2.0 | ①按 SOP 编写规范 W03 改引用壳，删除内联的格式规范 F01-F10、写作规范 W11-W13 与阶段细则全文；②权威源统一指向 `docs/agents/prd_agent.md`、`docs/pipelines/prd-pipeline.md`、`docs/verification/quality-gates.md` §2.1；③消除与 agent 文档双份维护漂移 | 本文件 |
