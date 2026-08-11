---
name: manage-version
description: 版本管理，创建/切换/列出项目版本。当用户说"版本管理"/"创建版本"/"切换版本"时触发。
---

# 版本管理 Skill

> 版本操作由 **Orchestrator 直接执行**（不调度独立 Agent）。完整定义见 `docs/pipelines/version-workflow.md`，本文只做触发入口与摘要。

## 角色与触发场景

负责版本创建、切换、状态查询、对比、发布、归档和 CHANGELOG 生成。核心规则：**一个需求 = 一个版本**。

## 支持的操作（摘要）

| 操作 | 命令 | 自然语言示例 |
|------|------|-------------|
| 创建 | `version_manager.py next --desc "描述"` | "新建一个版本做库存预警" |
| 切换 | `version_manager.py switch v0.2.0` | "切换到v0.2" |
| 状态 | `version_manager.py status v0.1.0` | "v0.1的进度怎么样" |
| 对比 | `version_manager.py diff v0.1 v0.2` | "对比v0.1和v0.2" |
| 列表 | `version_manager.py list` | "有哪些版本" |
| 当前 | `version_manager.py current` | "当前是哪个版本" |
| 发布 | `version_manager.py release v0.1.0` | "发布v0.1" |
| 归档 | `version_manager.py archive v0.1.0` | "归档v0.1" |
| CHANGELOG | `version_manager.py changelog v0.1.0` | "生成v0.1的changelog" |

> 版本上下文提取模式（用户话术 → 操作映射）、版本号校验规则、创建后必须同步 `config/project.yaml` 与 `STATE.md` 的纪律：完整定义见 `docs/pipelines/version-workflow.md`。

## 执行流程（摘要）

```
Step 1. 接收版本操作指令（操作类型 + 版本号 + 需求描述）
Step 2. 版本号校验（格式 vX.Y.Z / 是否已存在 / 语义合理性）
Step 3. 调用 scripts/version_manager.py 执行
Step 4. 同步全局配置与 STATE.md（create → current_version；release → latest_release）
Step 5. 输出结果
```

## 加载资源

1. 读取版本工作流（唯一权威源）：`docs/pipelines/version-workflow.md`
2. 读取全局配置：`config/project.yaml`（当前版本、版本列表）

## 完成标志

- 操作对应的文件已创建/更新
- `config/project.yaml` 与 `STATE.md` 已同步（创建/切换/发布/归档时）

## 失败信号

写入 `agent_comm/{task_id}/BLOCKED.md`，内容包含 `block_reason` 和 `required_input`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v2.0 | ①按 SOP 编写规范 W03 改引用壳，删除与已删除文档 version_agent.md 的内联重复与死链引用；②权威源统一为 `docs/pipelines/version-workflow.md`；③补「创建/归档必须同步 project.yaml 与 STATE.md」纪律（引用规则 W25） | 本文件 + `config/project.yaml`（registry 移除 version 条目）+ `CLAUDE.md` 第 3 章 + version_agent.md（已删除） |
