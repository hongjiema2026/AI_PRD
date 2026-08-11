---
title: 版本管理工作流
version: v1.0
date: 2026-07-28
status: active
---

# 版本管理工作流

| 属性 | 值 |
|------|-----|
| 版本 | v1.0 |
| 适用范围 | 版本创建/切换/状态/对比/列表/发布/归档操作 |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 版本数据同步 `docs/rules/sop-writing-standard.md` W25；意图兜底 W16；编写规范 `docs/rules/sop-writing-standard.md` |

> 本文件是**版本管理工作流的唯一权威定义**（版本模型/上下文解析/操作指令/意图识别）。版本数据两处同步纪律引用规则 W25；意图未命中兜底引用规则 W16。

## 概述
**版本操作由 Orchestrator 直接执行，不调度 Version-Agent。**

## 版本模型核心规则
- **一个需求 = 一个版本**：每个版本对应一个独立需求的生命周期
- **版本格式**：`{名称}_v{major}.{minor}.{patch}`，例如 `库存调拨_v1.0.0`
- 名称只允许中文、英文、数字、下划线(_)、连字符(-)
- 版本号自动递进：同一名称下 minor 自动 +1
- 用户可以随时用自然语言指定"在哪个版本上工作"

## 版本上下文提取规则

从用户输入中提取以下信息：

| 模式 | 示例 | 提取结果 |
|------|------|---------|
| 指定版本 + 业务操作 | "在库存调拨_v1.0写购物车PRD" | target_version=库存调拨_v1.0, task_type=prd |
| 创建新需求版本 | "新建一个版本做库存预警" | operation=create, feature=库存预警 |
| 查看版本状态 | "库存调拨的进度怎么样" | operation=status, name=库存调拨 |
| 切换工作版本 | "切换到购物车_v0.2继续工作" | operation=switch, target_version=购物车_v0.2 |
| 对比版本差异 | "对比库存调拨_v0.9和v1.0的差异" | operation=compare |
| 查看版本列表 | "有哪些版本" | operation=list |
| 发布版本 | "发布库存调拨_v1.0" | operation=release |
| 未指定版本 | "帮我写一份PRD" | **必须询问用户**：列出所有版本供选择 |

## 版本上下文解析流程

1. **提取版本标识**：正则匹配 `(.+)_v(\d+\.\d+\.\d+)` 或旧格式 `v(\d+\.\d+\.\d+)`
2. **判断操作类型**：
   - 创建：包含"新建"、"创建"、"新版本"、"开一个"
   - 切换：包含"切换"、"转到"、"切到"、"在...上继续"
   - 状态：包含"进度"、"状态"、"情况"、"怎么样"
   - 对比：包含"对比"、"比较"、"差异"、"diff"
   - 列表：包含"有哪些版本"、"版本列表"、"所有版本"
   - 发布：包含"发布"、"上线"、"release"
   - 归档：包含"归档"、"存档"、"archive"
3. **确定目标版本**：
   - 用户明确指定版本标识 → 使用指定版本
   - 用户只说了名称（如"库存调拨"）→ 匹配最新版本
   - 用户未指定 → **必须询问用户**
4. **创建新版本时补充名称**：
   - 如果操作类型为"创建"，但用户未提供版本名称
   - **必须先询问用户版本名称**，不能自行编造
   - 得到名称后，自动生成版本标识：`{名称}_v{X.Y.Z}`
5. **更新当前版本**：
   - 创建新版本后自动切换 current_version
   - 用户明确说"切换"时更新 current_version

## 操作指令

### 创建新版本
1. 读取当前版本号，自动计算下一个版本号（minor +1）
2. 调用 `python3 scripts/create_version.py {新版本号}`
3. 在 version_metadata.yaml 中记录需求名称和描述
4. 更新 current_version 为新版本
5. **两处同步（引用规则 W25，必做）**：将新版本追加到 `config/project.yaml` 的 `version.versions` 列表，并在 `STATE.md` 版本表中新增一行（或执行 `python3 scripts/state_manager.py refresh` 自动同步）
6. 向用户确认："已创建 {新版本号}，需求：{需求名}。当前工作版本已切换为 {新版本号}。"

### 切换版本
1. 更新 config/project.yaml 的 current_version
2. 向用户确认

### 查看状态
1. 读取目标版本的 version_metadata.yaml
2. 扫描 agent_comm/ 中的任务记录
3. 列出 PRD 和原型文件
4. 汇总为版本状态报告

### 对比版本
1. 调用 `python3 scripts/version_manager.py diff {v1} {v2}`
2. 或直接对比两版本的文件列表和 metadata

### 列表/发布/归档
1. 调用对应的 version_manager.py 命令
2. **归档后两处同步（引用规则 W25，必做）**：从 `config/project.yaml` 的 `version.versions` 列表移除该版本，并在 `STATE.md` 版本表移除对应行（或执行 `python3 scripts/state_manager.py refresh` 自动同步）

## 意图识别规则
- "有哪些版本" / "版本列表" / "所有版本" → version list
- "新建版本" / "创建版本" / "开一个" → version create
- "切换到XX" / "转到XX" → version switch
- "XX的进度" / "XX状态" → version status
- "对比XX和YY" / "比较XX和YY" → version diff
- "发布XX" / "XX上线" → version release
- 未命中以上关键词 → 按 W16 向用户展示候选意图列表，禁止猜测路由

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v1.0 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段/属性表/头部 blockquote/附录变更记录；②「版本操作由 Orchestrator 直接执行，不调度 Version-Agent」保留并加粗；③「意图识别规则」节末补 W16 兜底行（未命中关键词 → 展示候选意图列表，禁止猜测路由）；④W25 两处同步纪律（创建 §5、归档 §2）原样保留，操作指令/解析流程一字未改 | 本文件 |
