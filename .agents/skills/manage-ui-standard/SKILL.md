---
name: manage-ui-standard
description: UI 样式与交互规范维护，包括规范条目的实测收录/截图录入/缺失补充/废止。当用户说"UI规范"/"样式规范"/"交互规范"/"控件库"/"页面框架"，或发网址/截图要求收录控件时触发。
---

# UI 样式与交互规范维护 Skill

> 本文件为引用壳（引用规则 W03）。UI-Observer / UI-Analyst / UI-Writer / UI-Reviewer 子角色细则、实测脚本集、触发模式与调度接口的唯一权威源是 `docs/agents/ui_standard_agent.md`；编号规则/条目模板/检验口径的唯一权威源是 `docs/rules/ui-standard.md`。

## 角色与触发场景

负责《UI 样式与交互规范》的条目全生命周期维护：线上实测收录、截图快速录入、proto 流水线缺失补充、修改与废止。触发场景：用户提出 UI规范 / 样式规范 / 交互规范 / 控件库 / 页面框架，或发网址、截图要求收录控件。完整角色定义见 `docs/agents/ui_standard_agent.md`。

## 执行流程（摘要）

| 子角色 | 一句话职责 | 定义位置 |
|--------|-----------|----------|
| UI-Observer | 线上实测：浏览器观察交互 + computed style 取值 + 截图 | `docs/agents/ui_standard_agent.md` UI-Observer 段 |
| UI-Analyst | 截图录入：识别控件、比对现有库、新条目标 inferred | `docs/agents/ui_standard_agent.md` UI-Analyst 段 |
| UI-Writer | 分配编号（机械命令）、写条目、同步索引、重跑渲染 | `docs/agents/ui_standard_agent.md` UI-Writer 段 |
| UI-Reviewer | 跑 check 脚本 5 断言 + 人工抽查 | `docs/agents/ui_standard_agent.md` UI-Reviewer 段 |

> 触发模式四选一：A 网址增量 / B 截图录入 / C proto 缺失补充 / D 维护编辑（废止标 archived 不删号）。判定表见 `docs/agents/ui_standard_agent.md`「触发模式」（引用规则 W01，禁止在本文内联）。

## 加载资源

1. 读取 Agent 完整定义：`docs/agents/ui_standard_agent.md`
2. 读取规范主文档：`docs/rules/ui-standard.md`（§2 编号规则 / §3 条目模板 / §4 索引表）
3. 按模式读取对应分章文件：`docs/rules/ui-standard/chapters/`

## 完成标志

- 条目已写入对应分章文件且已登记主文档 §4 索引表
- `python3 scripts/ui_standard_render.py` 已重跑（index.html 同步）
- `python3 scripts/ui_standard_check.py` 输出 `RESULT: ALL PASS（5/5）`

## 失败信号

写入 `versions/{v}/agent_comm/{task_id}/BLOCKED.md`，内容包含 `block_reason` 和 `required_input`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 | v1.0 | 首次发布：引用壳（W03 模式），权威源指向 `docs/agents/ui_standard_agent.md` 与 `docs/rules/ui-standard.md` | 本文件 |
