---
title: 图表绘制工作流
version: v1.0
date: 2026-07-28
status: active
---

# 图表绘制工作流

| 属性 | 值 |
|------|-----|
| 版本 | v1.0 |
| 适用范围 | diagram 任务（流程图/脑图/架构图/时序图/状态图/ER 图），由 Orchestrator 直接执行 |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | 流程图呈现标准 `docs/rules/flow-diagram-standard.md`；组件模板 `templates/flowdia/`；编写规范 `docs/rules/sop-writing-standard.md` |

> 本文件是**图表绘制工作流的唯一权威定义**（图表类型与工具映射/各类型操作流程/Figma 源文件管理）。
> **前置条件**：需 Figma MCP 工具（`generate_diagram`/`use_figma`/`get_screenshot`）可用；不可用时脑图/架构图等改走 Mermaid + mmdc 渲染 PNG（参考 `versions/eBayPLP广告策略_v0.1.0/prototype/.mermaid/` 工作流）。

## 概述
图表绘制由 Orchestrator 直接通过 Figma MCP 工具执行，不调度 Agent。

> **流程图呈现标准（2026-07-20 起，适用于全项目所有流水线）**：凡在 HTML 页面中呈现的流程图（PRD 渲染版、独立流程图页面、proto 等任何 HTML 产出），
> 默认使用 flowdia 交互式组件产出（实体卡片 + SVG 连线 + 悬停链路高亮），不使用静态 PNG 截图。
> 标准文档：`docs/rules/flow-diagram-standard.md`；组件模板：`templates/flowdia/`。
> Figma PNG 导出仅作为对外分享/存档的可选产物（操作文档 docx 为例外，见标准适用范围）。

## 图表类型与工具映射

| 类型 | HTML 呈现（默认） | Figma 导出（可选） | Mermaid 语法 |
|------|------|------|-------------|
| 流程图 | **flowdia 组件**（templates/flowdia/） | `generate_diagram` | flowchart TD/LR |
| 脑图 | PNG + 灯箱 | `use_figma`（FigJam Plugin API） | N/A |
| 架构图 | PNG + 灯箱 | `generate_diagram` | flowchart LR |
| 时序图 | PNG + 灯箱 | `generate_diagram` | sequenceDiagram |
| 状态图 | PNG + 灯箱 | `generate_diagram` | stateDiagram-v2 |
| ER 图 | PNG + 灯箱 | `generate_diagram` | erDiagram |

## 各类型操作流程

### 流程图（flowchart）
1. 用 `generate_diagram` 将业务逻辑转为 Mermaid 语法（作为权威源），生成到 FigJam
2. **HTML 呈现**：按 `docs/rules/flow-diagram-standard.md` 使用 flowdia 组件实现交互式流程图
   - 复制 `templates/flowdia/flowdia.css` / `flowdia.js`，参照 `example.html` 编写节点与边配置
   - 节点/分支/标签与 Mermaid 权威源一一对应
3. 如需 PNG 存档：用 `get_screenshot` 导出高清 PNG（maxDimension=2000），curl 下载到 `versions/{v}/prototype/` 目录
4. 命名规范：`flow-{序号}-{流程名称}.png`
5. ⚠️ 存档 PNG **禁止嵌入 HTML 页面作为流程图呈现**（流程图在 HTML 中只能走 flowdia 组件）；PNG 仅用于对外分享/存档，分享时底部附 Figma 源链接

### 脑图（mindmap）
1. 用 `use_figma` 在 FigJam 中通过 Plugin API 创建脑图节点和连线
2. 导出 PNG 同上
3. 命名规范：`mindmap-{主题名称}.png`

### 架构图/时序图/状态图/ER 图
1. 用 `generate_diagram` + 对应 Mermaid 语法类型生成
2. 导出与嵌入同上

## Figma 源文件管理
- 所有图表源文件保存在 FigJam 文件中（以版本命名）
- 在 version_metadata.yaml 中记录 Figma 文件 URL
- 非流程类图（脑图/架构图/时序图/状态图/ER 图，即上表除流程图外的全部类型）PNG 导出后嵌入 HTML（`<img>` + 灯箱），实现「Figma 编辑 → 重新导出 → HTML 自动更新」；流程图不适用此模式，HTML 中只能走 flowdia 组件

## 意图识别规则
- "画一个流程图" / "画流程图" / "生成流程图" → diagram flowchart
- "画脑图" / "生成思维导图" / "画一个脑图" → diagram mindmap
- "画架构图" → diagram 架构图
- "画时序图" → diagram 时序图

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v1.0 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter 四字段/属性表/头部 blockquote/附录变更记录；②头部 blockquote 新增前置条件声明（依赖 Figma MCP 工具；不可用时脑图/架构图等改走 Mermaid + mmdc 渲染 PNG，参考 `versions/eBayPLP广告策略_v0.1.0/prototype/.mermaid/` 工作流）；③工具映射表/操作流程/命名规范/意图识别一字未改 | 本文件 |
