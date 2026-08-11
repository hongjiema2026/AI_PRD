---
title: 组件模版管理工作流
version: v1.0
date: 2026-07-28
status: active
---

# 组件模版管理工作流

| 属性 | 值 |
|------|-----|
| 版本 | v1.0 |
| 适用范围 | 组件模版库 list/add/create/remove/edit/info/sync 操作（`templates/components/`） |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 编写规范 `docs/rules/sop-writing-standard.md`；组件复用规则见 `docs/pipelines/proto-pipeline.md` Implementer 段 |

> 本文件是**组件模版管理工作流的唯一权威定义**（操作指令/意图识别）。组件模版管理由 Orchestrator 直接执行，不调度独立 Agent。

## 概述
组件模版管理由 Orchestrator 直接执行，不调度独立 Agent。

## 操作指令

| 操作 | 命令 |
|------|------|
| **查看列表** | `python3 scripts/component_manager.py list [--category CAT] [--tags T1,T2]` |
| **新增组件** | `python3 scripts/component_manager.py add <html_file> --name NAME --category CAT [--desc DESC] [--tags T1,T2]` |
| **创建骨架** | `python3 scripts/component_manager.py create <name> --category CAT [--desc DESC]` |
| **移除组件** | 确认后运行 `python3 scripts/component_manager.py remove <name>` |
| **编辑组件** | 直接编辑 `templates/components/{category}/{name}.html`，修改后运行 `python3 scripts/component_manager.py validate <name>` |
| **查看详情** | `python3 scripts/component_manager.py info <name>` |
| **同步检查** | `python3 scripts/component_manager.py sync` |

## 意图识别规则
- "把xx加到模版库" / "添加组件模版" → component add
- "新建一个xx组件模版" / "创建模版" → component create
- "查看模版库" / "有哪些组件模版" → component list
- "删除xx模版" / "移除模版" → component remove
- "修改xx模版的xx" → component edit
- "查看xx模版详情" → component info

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v1.0 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段/属性表/头部 blockquote/附录变更记录；②操作指令表/意图识别规则一字未改 | 本文件 |
