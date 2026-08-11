---
title: PRD 子角色-Visualizer 执行细则
version: v1.3
date: 2026-08-04
status: active
---

# PRD 子角色：Visualizer（图先行）

| 属性 | 值 |
|------|-----|
| 版本 | v1.1 |
| 适用范围 | PRD 流水线 Visualizer 阶段（图先行）SOP 与检验清单 |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | `docs/agents/prd_agent.md`（阶段路由表、W11/W13）、`docs/rules/prd-diagram-standard.md`（D01-D08 图绘制规则）、`docs/rules/sop-writing-standard.md`（§2.6 产出文件名、W21） |

> 所有图表使用 **Mermaid 内联代码块**（引用规则 D01），不导出 PNG，不调用 Figma。
> 如用户明确要求高保真图表，可改用 Figma generate_diagram → get_screenshot → curl 导出。
> **UML 语义约定**：流程图按 UML 活动图语义绘制（stadium 起止/判断菱形/分支显式合并/单层泳道，引用规则 D03）；
> 状态机用 UML 状态机语法（[*] 初终态/转移标注「事件 [守卫] / 动作」，引用规则 D04）。
> **HTML 呈现层**：全部图在 HTML 渲染版中用 mermaid.js CDN 直接渲染 MD 权威源
> （引用规则 D06，禁止静态 PNG，PRD 语境禁用 flowdia，实施配置见 `docs/agents/prd_stages/html_render.md` H06）。

```
Step 1. 读取《需求调研摘要》
        文件：versions/{v}/agent_comm/{task_id}/01_research_summary.md

Step 2. 规划全部必配图
        基于调研结果，规划以下必须产出的图：

        图1 - 业务完整流程图（概述 Ch1.1，必配不可省略）：
        - 端到端业务流程概览，展示「用户做什么 → 系统做什么 → 结果是什么」
        - 使用简化的横向流程图（flowchart LR），5~7 个步骤，带编号标注
        - 面向读者（业务叙述），区别于 Ch2.1 核心流程图（面向开发，含决策节点）
        - UML 活动图语义（D03）：stadium 起止节点 `([开始])`/`([结束])`、动作矩形
        - 工具：Mermaid `flowchart LR`
        - 图注：一句话总结 + 引导读者查看 §2.1 详细技术流程

        图2 - 核心业务流程图（流程与规则 Ch2.1，必配，最小颗粒度）：
        - 主流程路径 + 关键分支和判断节点
        - 覆盖业务全链路（从触发到结束）
        - **最小颗粒度**：拆到子步骤可独立验证级别（如「判断条件」展开为四层级联子节点），图的步骤与正文 §2.2.x 逐步对齐、编号一致（D05-1）
        - **关键约束上卡**：节点涉及硬性规则（时间窗口、阈值、重试上限、性能约束）时，必须把规则一句话写进节点文案，禁止只放术语名让读者去正文找（D05-2）
        - UML 活动图语义（D03）：stadium 起止、判断菱形 `{条件}` 且每条出边带分支标签、分支显式合并、跨角色协作用单层 subgraph 泳道（禁止嵌套）、语义配色（判断 amber/成功 green/失败 red/主流程 blue）
        - 工具：Mermaid `flowchart TD`

        图3 - 角色关系图（流程与规则 Ch2 补充）：
        - 参与角色及其操作权限
        - 角色间的交互关系
        - 工具：Mermaid `flowchart LR`（D02 用例关系语义）

        图3~N - 子流程图（Ch2.2.x 每个子流程，必须配）：
        - 每个子流程一张 Mermaid 图（W13），不再以有序列表为主体
        - UML 活动图语义同图2（D03）
        - 工具：Mermaid `flowchart TD`

        图N+1 - 状态流转图（Ch2.3，必配不可省略）：
        - 使用 UML 状态机语法（stateDiagram-v2，D04）
        - 包含初始状态（[*]）、所有业务状态、终止状态（[*]）
        - 转移标注格式「事件 [守卫条件] / 动作」，事件必填
        - 工具：Mermaid `stateDiagram-v2`

Step 3. 用 Mermaid 内联生成图表
        对每组图：
        1. 在 PRD Markdown 中直接写入 Mermaid 代码块（```mermaid ... ```）
        2. 使用正确的 Mermaid 类型与 UML 语义约定：
           - 流程图 → flowchart TD / flowchart LR（活动图语义，D03）
           - 状态图 → stateDiagram-v2（状态机语法，D04）
        3. 每个图表后必须有文字图注（D07）

Step 4. 输出《图表索引》
        写入：versions/{v}/agent_comm/{task_id}/02_diagram_index.md
        必须包含：
        - 每组图的 Mermaid 类型和对应 PRD 章节
        - 对应 PRD 章节映射（Ch1/Ch2/Ch4）
```

## Visualizer 检验

> 每项标注【机器可验】/【人工判定】（引用规则 W21）。

- [ ] 【机器可验】2 组标准图已全部生成（流程图、角色图）+ 每个 2.2.x 子流程图，`grep -c '```mermaid'` 计数比对
- [ ] 【机器可验】所有图表为 Mermaid 内联代码块（`grep` 无外部 PNG 图引用）
- [ ] 【机器可验】图表索引文件已产出（`test -s 02_diagram_index.md`）
- [ ] 【人工判定】图2 核心业务流程为最小颗粒度：节点拆到可独立验证子步骤、关键约束一句话上卡（D05）
- [ ] 【人工判定】流程图符合 UML 活动图语义（D03：stadium 起止/判断菱形带分支标签/分支显式合并/单层泳道），状态图符合 D04（[*] 初终态/转移标注含事件）
- [ ] 【人工判定】已确认 HTML 呈现层走 mermaid.js 原生渲染（D06），不产出静态 PNG、不使用 flowdia

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-04 09:10 | v1.3 | ①头部 blockquote flowdia 呈现层表述改 mermaid.js 原生渲染（引用 D06，PRD 语境禁用 flowdia）；②图1/图2/图5~N 补 UML 活动图语义约定（D03：stadium 起止/判断菱形/分支合并/单层泳道/语义配色），图N+1 状态机补 D04（转移标注「事件 [守卫] / 动作」）；③颗粒度引用 S07 改 D05；④检验清单新增 UML 语义判定项、flowdia 项改 D06；⑤frontmatter 版本 v1.1→v1.3（补正 v1.2 未同步） | 本文件 + `docs/rules/prd-diagram-standard.md`（新建）+ `docs/agents/prd_agent.md` v1.4 |
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补齐 frontmatter（四字段）+ 属性表；②Visualizer 检验 5 项逐项标注【机器可验】/【人工判定】（引用规则 W21）；③文末新增附录变更记录表（引用规则 W10）；④技术内容未改动，图1~图N+1 规划与产出文件名 `02_diagram_index.md` 保持原样 | 本文件 |
| 2026-08-01 | v1.2 | ①删除图1 业务全景脑图（Chapter 1 不再含全景图）；②原图1b 业务完整流程升为图1（对应 Ch1.1）；③图2 核心业务流程绑定最小颗粒度（S07-1 子步骤对齐 + S07-2 关键约束上卡）；④4 组标准图收敛为 3 组；⑤检验项同步更新 | 本文件 |
