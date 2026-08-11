---
name: manage-kb
description: 知识库管理，包括知识条目的创建/搜索/更新。当用户说"知识库"/"KB"/"knowledge"时触发。
---

# 知识库管理 Skill

> 本文件为引用壳（引用规则 W03）。KB-Writer / KB-Crawl-Handler / KB-Reviewer 子角色细则、知识库模板与命名规范的唯一权威源是 `docs/agents/kb_agent.md`；评分细则与通过线的唯一权威源是 `docs/verification/quality-gates.md` §2.5。

## 角色与触发场景

负责项目知识库的整理、分类、索引和检索，确保知识跨版本沉淀和复用。触发场景：用户提出知识库 / KB / knowledge。完整角色定义见 `docs/agents/kb_agent.md` §2。

## 执行流程（摘要）

| 子角色 | 一句话职责 | 定义位置 |
|--------|-----------|----------|
| KB-Writer | 内容分析、按模板格式化、写入分类目录并更新索引 | `docs/agents/kb_agent.md` KB-Writer 段 |
| KB-Crawl-Handler | 接收爬虫提取任务，审核并标准化归档爬虫知识文档 | `docs/agents/kb_agent.md` KB-Crawl-Handler 段 |
| KB-Reviewer | 格式/内容/索引审核并输出审核报告 | `docs/agents/kb_agent.md` KB-Reviewer 段 |

> 知识库模板（frontmatter 字段、章节结构）、文件命名（`{类型}_{主题}_{日期}.md` / `crawl_{类型}_{domain}_{日期}.md`）、标签体系（`config/project.yaml` `kb.allowed_tags` 与 `kb.categories`）：完整定义见 `docs/agents/kb_agent.md`（引用规则 W01，禁止在本文内联）。

## 加载资源

1. 读取 KB Agent 完整定义：`docs/agents/kb_agent.md`
2. 读取知识库索引：`docs/knowledge-base/index.md`
3. 读取用户画像（术语对齐）：`docs/knowledge-base/user-profile/glossary.md`
4. 读取 KB 标签系统：`config/project.yaml` → `kb.allowed_tags` 和 `kb.categories`

## 完成标志

- 知识文档已写入 `docs/knowledge-base/{类型}/` 目录
- `docs/knowledge-base/index.md` 已更新且包含该条目
- KB-Reviewer 审核报告存在且评分 ≥90（评分维度与通过线见 `docs/verification/quality-gates.md` §1、§2.5）

## 失败信号

写入 `versions/{v}/agent_comm/{task_id}/BLOCKED.md`，内容包含 `block_reason` 和 `required_input`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v2.0 | ①按 SOP 编写规范 W03 改引用壳，删除内联的知识库模板代码、子角色步骤细则与检验清单全文；②权威源统一指向 `docs/agents/kb_agent.md` 与 `docs/verification/quality-gates.md` §2.5；③消除与 agent 文档双份维护漂移 | 本文件 |
