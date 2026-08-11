---
task_id: "{type}_{feature简称}_{timestamp}"
type: kb | prd | proto | version | restore | multi
status: pending | in_progress | blocked | completed | error
created_at: "YYYY-MM-DD HH:MM:SS"
completed_at: null
---

# 任务书 — {任务简述}

## 基本信息

| 字段 | 值 |
|------|-----|
| task_id | {type}_{feature简称}_{timestamp} |
| 类型 | {任务类型} |
| 状态 | pending |
| 创建时间 | YYYY-MM-DD HH:MM:SS |
| 完成时间 | - |

## 用户原始输入

{用户输入的原始内容}

## 用户认知上下文

> Orchestrator 在生成任务书时，读取 `docs/knowledge-base/user-profile/` 中的用户画像和偏好，将相关信息摘要于此，供所有 Agent 参考。

### 用户画像摘要
- 角色：{从 persona.md 读取}
- 领域：{从 persona.md 读取}
- 经验：{从 persona.md 读取}

### 已知输出偏好
- {从 preferences.md 读取已确认偏好}

### 适用术语
- {从 glossary.md 读取相关术语}

## 参考资料

> Orchestrator 在生成任务书时，扫描版本目录下的已有文件，将相关参考资料列于此。

### 已爬取页面（如存在）
- 页面 HTML：`versions/{v}/prototype/restored/{name}/page.html`
- 表格数据：`versions/{v}/prototype/restored/{name}/tables_data.json`
- 页面内容：`versions/{v}/prototype/restored/{name}/page_content.md`

### Figma 设计（如存在）
- 设计上下文：`versions/{v}/prototype/figma_design_context_*.json`
- 参考代码：`versions/{v}/prototype/figma_design_code_*.tsx`
- 截图：`versions/{v}/prototype/figma_screenshot_*.png`

### 已有原型（如存在）
- 设计文档：`versions/{v}/prototype/{name}-prototype.md`
- 组件原型：`versions/{v}/prototype/proto-*.html`
- 组装页面：`versions/{v}/prototype/{name}-prototype.html`

### 已有 PRD（如存在）
- PRD 文档：`versions/{v}/prd/{name}-prd.md`

## 流水线配置

```yaml
pipeline:
  - agent: {agent_name}
    step: 01
    wave: 1              # 可选：同 wave 可并行，缺失则默认顺序执行
    depends_on: []       # 可选：依赖的 step 编号列表
    status: pending
    output_file: null    # Orchestrator 在 Agent 完成后回填实际产出路径（逗号分隔多个文件）
  - agent: {agent_name}
    step: 02
    status: pending
    output_file: null
```

### pipeline 字段说明（schema 权威定义）

| 字段 | 类型 | 必填 | 语义 |
|------|------|------|------|
| `agent` | string | 是 | Agent 名，取值限于 `config/project.yaml` `agents.registry` 已登记项 |
| `step` | string（两位数字） | 是 | 步骤编号，任务书内唯一，按执行顺序递增 |
| `wave` | int | 否 | 波次号。**相同 wave 值的步骤并行调度**；缺失时默认按 step 顺序串行。wave 从 1 开始连续编号 |
| `depends_on` | list[string] | 否 | 依赖的 step 编号列表（如 `[01, 02]`）。依赖步骤全部 completed 后才可调度本步骤；缺失等价于 `[]`（仅受 wave 约束）。`depends_on` 与 `wave` 同时存在时，两者都须满足 |
| `status` | enum | 是 | `pending` / `in_progress` / `blocked` / `completed` / `error` |
| `output_file` | string \| null | 是 | Agent 完成后由 Orchestrator 回填实际产出路径，多文件逗号分隔 |

> **并行冲突约束**：同 wave 的步骤不得写入同一文件；前一子任务 `blocked`/`error` 时，后续所有 wave 步骤全部跳过（规则见 `AGENTS.md` 多任务组合规则）。

### PRD 流水线模板
```yaml
pipeline:
  - agent: prd_agent
    step: 01
    status: pending
    output_file: null
```

### 原型流水线模板
```yaml
pipeline:
  - agent: proto_agent
    step: 01
    status: pending
    output_file: null
```

### Restore → Proto → PRD 流水线模板
```yaml
pipeline:
  - agent: restore_agent
    step: 01
    wave: 1
    depends_on: []
    status: pending
    output_file: null
  - agent: proto_agent
    step: 02
    wave: 2
    depends_on: [01]
    status: pending
    output_file: null
  - agent: prd_agent
    step: 03
    wave: 3
    depends_on: [02]
    status: pending
    output_file: null
```

### Restore → Proto + PRD 并行模板
```yaml
pipeline:
  - agent: restore_agent
    step: 01
    wave: 1
    depends_on: []
    status: pending
    output_file: null
  - agent: proto_agent
    step: 02
    wave: 2
    depends_on: [01]
    status: pending
    output_file: null
  - agent: prd_agent
    step: 03
    wave: 2              # 与 proto_agent 同 wave，可并行
    depends_on: [01]     # 仅依赖 restore
    status: pending
    output_file: null
```

## 期望交付物

1. {交付物1} — {说明，包含文件名和格式}
2. {交付物2} — {说明}

### PRD 交付物模板
1. `versions/{v}/agent_comm/{task_id}/01_research_summary.md` — 需求调研摘要
2. `versions/{v}/prd/{功能名}-prd.md` — PRD 文档（13节完整模板）
3. `versions/{v}/agent_comm/{task_id}/03_prd_review_report.md` — 评审报告（≥80分）

### 原型交付物模板
1. `versions/{v}/prototype/{功能名}-prototype.md` — 原型设计文档（含API数据源、状态模型、组件规格）
2. `versions/{v}/prototype/proto-{组件名}.html` — 各组件独立原型（自包含HTML）
3. `versions/{v}/prototype/{功能名}-prototype.html` — 组装后的完整页面
4. `versions/{v}/agent_comm/{task_id}/03_proto_test_report.md` — 测试报告（≥90分）

## 执行日志

| 步骤 | Agent | 状态 | 时间 | 备注 |
|------|-------|------|------|------|
| 01 | {agent} | pending | - | - |
| git | orchestrator | pending | - | commit-task-complete |

## 反馈收集（任务完成后填写）

> 任务完成后，Orchestrator 在此记录用户反馈，用于持续优化用户认知。

### 本次发现的偏好
- {新发现的输出偏好，如用户明确表扬或修正的格式/风格}

### 用户修正记录
- {用户对本次产出的具体修改意见}

### 满意度
- [ ] 1 完全不符合预期
- [ ] 2 需要大幅修改
- [ ] 3 基本可用，需微调
- [ ] 4 符合预期，少量修改
- [ ] 5 完全满足，可直接使用

### 是否更新用户画像/偏好
- [ ] 是 — 已更新 `docs/knowledge-base/user-profile/` 和 memory 文件
- [ ] 否 — 无新发现

---
*本文件由 PM-Orchestrator 自动生成，Agent 按流水线顺序读取并执行。*
