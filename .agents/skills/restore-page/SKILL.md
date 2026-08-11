---
name: restore-page
description: 原型页面复原，从线上页面截图/HTML还原为可交互原型。当用户说"复原"/"restore"/"还原"时触发。
---

# 原型复原 Skill

> 本文件为引用壳（引用规则 W03）。Planner / Crawler / Verifier / KB-Extractor 子角色细则、页面获取模式与登录处理表的唯一权威源是 `docs/agents/restore_agent.md`；评分与通过线的唯一权威源是 `docs/verification/quality-gates.md` §2.3。

## 角色与触发场景

负责将在线页面复原为本地可运行的 HTML/CSS/JS 原型，**核心原则：抓取现有代码，禁止重新编码**。触发场景：用户提出复原 / restore / 还原。完整角色定义见 `docs/agents/restore_agent.md` §2。

## 执行流程（摘要）

| 子角色 | 一句话职责 | 定义位置 |
|--------|-----------|----------|
| Planner | 预请求/结构/资源/登录门槛分析，输出复原计划 | `docs/agents/restore_agent.md` Planner 段 |
| Crawler | 登录处理、抓取页面、下载资源、清洗去噪，生成多文件版与单文件版 | `docs/agents/restore_agent.md` Crawler 段 |
| Verifier | DOM/样式/资源/交互四维对比评分并输出验证报告 | `docs/agents/restore_agent.md` Verifier 段 |
| KB-Extractor | 可选知识提取（按 `restore.kb_extraction.enabled` 开关） | `docs/agents/restore_agent.md` KB-Extractor 段 |

> 页面获取模式（`requests` / `playwright` / `auto`）、登录处理六场景表、组件模版映射（仅建议不修改产出）：完整定义见 `docs/agents/restore_agent.md`（引用规则 W01，禁止在本文内联）。

## 加载资源

1. 读取 Restore Agent 完整定义：`docs/agents/restore_agent.md`
2. 读取项目配置：`config/project.yaml` → `restore` 段
3. 读取 KB 提取模板（如启用）：`templates/kb_extraction_template.md`

## 完成标志

- `01_restore_plan.md` 存在且非空；`versions/{v}/prototype/restored/{domain}_{ts}/` 下存在复原页面文件
- `03_restore_verification.md` 存在且总匹配度 ≥90；80-89 为有条件通过，须经用户确认放行（信号判定引用规则 W15；评分维度与通过线见 `docs/verification/quality-gates.md` §1、§2.3）

## 失败信号

写入 `versions/{v}/agent_comm/{task_id}/BLOCKED.md`，内容包含 `block_reason` 和 `required_input`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v2.0 | ①按 SOP 编写规范 W03 改引用壳，删除内联的各阶段步骤细则、获取模式表与登录处理表全文；②权威源统一指向 `docs/agents/restore_agent.md` 与 `docs/verification/quality-gates.md` §2.3；③消除与 agent 文档双份维护漂移 | 本文件 |
