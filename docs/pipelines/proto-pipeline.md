---
title: 原型流水线
version: v1.1
date: 2026-08-11
status: active
---

# 原型流水线

| 属性 | 值 |
|------|-----|
| 版本 | v1.1 |
| 适用范围 | proto 任务全流程（Architect → Implementer → Tester） |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 评分维度/通过线 `docs/verification/quality-gates.md` §1/§2.2；摘要速查 `docs/rules/proto-pipeline.md`；编写规范 `docs/rules/sop-writing-standard.md` |

> 本文件是 **proto 原型流水线的唯一权威定义**（阶段划分/产出物/任务书模板/上下文预算）。评分维度与通过线不在本文件重述，见 `docs/verification/quality-gates.md`（引用规则 W01/W04）。

## 流程概览
```
Architect（设计） → Implementer（实现） → Tester（测试）
```

## 各阶段职责

### Architect（设计）
- 参考页面/Figma/API文档 + **扫描组件模版库**
- 产出：设计文档 + 状态模型 + **组件来源映射表** + **UI 规范引用映射表** + 组件规划 + 交互流程图

### Implementer（实现）
- **reuse 组件优先从模版库复制定制**，new 组件从模版骨架创建
- 产出：独立组件原型（proto-*.html） + 组装页面

### Tester（测试）
- 独立文件验证 + 组装页面测试 + **组件来源验证** + **UI 规范引用验证** + PRD一致性（评分 ≥90 通过，权威定义见 `docs/verification/quality-gates.md` §1/§2.2）
- 产出：`agent_comm/{task_id}/03_proto_test_report.md`

## 典型 multi 任务顺序
```
restore（爬取参考页面）→ proto（原型设计）→ prd（PRD编写，内含图先行）
```

注：diagram 已内嵌为 PRD 流水线的 Visualizer 阶段，不再作为独立步骤。multi 中如需补充额外图表，可追加 diagram 子任务。

## 任务书模板

```yaml
task_id: proto_{feature简称}_{timestamp}
type: proto
status: in_progress
pipeline: [Architect, Implementer, Tester]
input: |
  {用户原始输入}
context:
  version: {target_version}
  prd_file: versions/{v}/prd/{功能名}-prd.md
  component_registry: templates/components/registry.yaml
expected_output:
  - versions/{v}/prototype/{功能名}-prototype.md      # 设计文档（交互流程图/功能脑图以 Mermaid 内联其中）
  - versions/{v}/prototype/proto-{组件名}.html         # 各组件原型
  - versions/{v}/prototype/{功能名}-prototype.html     # 组装页面
  - versions/{v}/agent_comm/{task_id}/03_proto_test_report.md
```

> 📐 图表规范：交互流程图、功能脑图一律 Mermaid 内联于设计文档（不导出 PNG）；若流程图需在 HTML 页面中呈现，必须按《交互式流程图标准》使用 flowdia 交互组件（禁止静态 PNG），见 `docs/rules/flow-diagram-standard.md`。

## 波次规划

原型流水线各阶段依赖紧密（Architect → Implementer → Tester），无天然并行点。并行优势体现在 multi 任务组合中（见 CLAUDE.md 多任务组合规则）。

## 上下文估算

> 预算按**行数**执行（KB 估算已废弃）；水位控制见 `AGENTS.md` 上下文水位管理（唯一权威定义）。

| 阶段 | 加载上限（行） | 必须加载 | 可延迟 |
|------|---------|---------|--------|
| Architect | ≤300 | PRD + component registry + 设计文档 + UI 规范索引表（仅 §4） | 其他版本文件 |
| Implementer | ≤500 | 设计文档 + component 模板 + base-styles | PRD 全文 |
| Tester | ≤250 | 原型 HTML + 测试标准 | 设计文档 |

### 渐进式加载规则
1. 进入阶段时仅加载该阶段的 required 内容
2. 前阶段产出通过 `agent_comm/{task_id}/` 文件路径引用，按需读取
3. 禁止一次读取完整 pipeline 文档 — 只读当前阶段章节
4. 每阶段加载行数遵循 `AGENTS.md` 上下文水位管理（>800 行停载非必需，>1500 行主动 compact）

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 11:15 | v1.1 | ①Architect 产出新增「UI 规范引用映射表」、Tester 职责新增「UI 规范引用验证」（同步 `docs/agents/proto_agent.md` v2.2 Step 5b，引用规则 W26）；②上下文估算 Architect 行补「UI 规范索引表（仅 §4）」；③版本 v1.0→v1.1 | 本文件 + `docs/agents/proto_agent.md` v2.2 + `docs/rules/proto-pipeline.md` + `docs/verification/quality-gates.md` + `docs/verification/checklists.md` |
| 2026-07-28 | v1.0 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段/属性表/头部 blockquote/附录变更记录；②Tester 评分处补权威源引用 `docs/verification/quality-gates.md` §1/§2.2（≥90 通过，维度不重述，引用规则 W01）；③阶段名与产出文件名（`03_proto_test_report.md`）核对与规范 §2.6 注册表一致，流程步骤/模板/上下文预算一字未改 | 本文件 |
