---
name: proto-design
description: 交互原型设计，含原型HTML生成、交互逻辑定义、PRD嵌入。当用户说"原型"/"prototype"/"交互设计"时触发。
---

# 原型设计 Skill

> 本文件为引用壳（引用规则 W03）。Architect/Implementer/Tester 三阶段细则、文件命名规范、自包含 HTML 规范与标注点对应规则的唯一权威源是 `docs/agents/proto_agent.md`；评分与通过线的唯一权威源是 `docs/verification/quality-gates.md` §2.2。

## 角色与触发场景

负责原型架构设计、HTML/CSS/JS 实现和交互测试，内部流水线为 Architect → Implementer → Tester。触发场景：用户提出原型 / prototype / 交互设计。完整角色定义见 `docs/agents/proto_agent.md` §2。

## 执行流程（摘要）

| 子角色 | 一句话职责 | 定义位置 |
|--------|-----------|----------|
| Architect | 收集参考资料、设计架构与组件拆分，输出原型设计文档 | `docs/agents/proto_agent.md` Architect 段 |
| Implementer | 按来源映射实现自包含 `proto-*.html` 组件并组装页面 | `docs/agents/proto_agent.md` Implementer 段 |
| Tester | 浏览器渲染/交互/结构测试并评分，输出测试报告 | `docs/agents/proto_agent.md` Tester 段 |

> 文件命名规范（`{功能名}-prototype.md` / `proto-{name}.html`）、自包含 HTML 规范、标注点对应规则（`.annotation-marker` 与 postMessage 机制）、组件模版库复用纪律：完整定义见 `docs/agents/proto_agent.md`（引用规则 W01，禁止在本文内联）。

## 加载资源

1. 读取 Proto Agent 完整定义：`docs/agents/proto_agent.md`
2. 读取 Pipeline 流程：`docs/pipelines/proto-pipeline.md`
3. 读取 PRD（如存在）：`versions/{v}/prd/{功能名}-prd.md`
4. 读取组件模版库：`templates/components/registry.yaml` + `templates/components/base-styles.css`

## 完成标志

- `{功能名}-prototype.md` 设计文档存在且非空
- `proto-*.html` 组件原型与 `{功能名}-prototype.html` 组装页面存在
- `03_proto_test_report.md` 存在且评分 ≥90（评分维度与通过线见 `docs/verification/quality-gates.md` §1、§2.2）

## 失败信号

写入 `versions/{v}/agent_comm/{task_id}/BLOCKED.md`，内容包含 `block_reason` 和 `required_input`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v2.0 | ①按 SOP 编写规范 W03 改引用壳，删除内联的命名规范表、自包含 HTML 规范、标注点对应规则与评分表全文；②权威源统一指向 `docs/agents/proto_agent.md` 与 `docs/verification/quality-gates.md` §2.2；③消除与 agent 文档双份维护漂移 | 本文件 |
