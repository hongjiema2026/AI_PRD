---
title: 交互式流程图标准（flowdia）
version: v1.4
date: 2026-08-04
status: active
---

# 交互式流程图标准（flowdia）

| 属性 | 值 |
|------|-----|
| 版本 | v1.4 |
| 适用范围 | proto/diagram 等工作流 HTML 产出中的流程图呈现（操作文档 docx 为显式例外；**PRD 流水线自 v1.4 起迁出**，见头部 blockquote） |
| 创建日期 | 2026-07-23 |
| 状态 | active |
| 关联文档 | `docs/rules/sop-writing-standard.md`（SOP 编写规范）、`docs/rules/prd-diagram-standard.md`（PRD 流水线图绘制标准，D01-D08） |

> 本文件是 **proto/diagram 等工作流 HTML 产出中流程图呈现的标准**：规则编号 S01-S09 只在本文件定义，其他文档引用编号（引用规则 W01/W02）。
> **PRD 流水线迁出声明（v1.4）**：PRD 的图源与 HTML 呈现标准自 2026-08-04 起由 `docs/rules/prd-diagram-standard.md` 定义（Mermaid UML 语义约定 + mermaid.js 原生渲染，D01-D08），本文件不再适用于 PRD 产出；存量 PRD HTML 中的 flowdia 组件保留维护不追溯。
> **显式例外**：操作文档（doc-pipeline）最终交付 docx 静态文档，无法内嵌交互组件——其流程图以 Mermaid 源码为权威源、PNG 仅作 docx 呈现，见 `docs/pipelines/doc-pipeline.md`。
> 组件模板：`templates/flowdia/`（`flowdia.css` + `flowdia.js` + `example.html`）
> 参考实现：`versions/eBayPLP广告策略_v0.1.0/prd/eBayPLP广告策略-prd.html`（图 1-2、图 2-1，存量 PRD 产物，仅作组件维护参考）

## 总则

1. **proto/diagram 等 HTML 产出中的流程图不使用静态 PNG 截图呈现**，必须使用 flowdia 交互式组件（实体卡片 + SVG 连线）渲染。
2. **PRD 流水线不适用本标准**（v1.4 起迁出）：PRD 的图源与呈现见 `docs/rules/prd-diagram-standard.md`（D01-D08）；本文件语境下 Mermaid 仍是各 MD 源文件的权威源，flowdia 仅作 HTML 呈现层，内容必须与 Mermaid 图保持一致（节点、分支、标签一一对应）。
3. 非流程类图（架构图、角色关系图、状态流转图）不在本标准范围内，可继续使用现有呈现方式。

## S01：结构规范

每张流程图由以下部分组成：

```
.diagram-card
  └─ .fd-scroll（窄屏横向滚动容器）
      └─ .flowdia（position:relative 的 CSS Grid 容器）
          ├─ <svg class="fd-svg">（连线层，JS 动态绘制）
          ├─ .fd-lane（泳道条，grid-column:1/-1）
          ├─ .fn[data-id]（实体卡片节点，grid-area 定位）
          └─ <script class="fd-edges" type="application/json">（边配置）
```

- 每张图用 `grid-template-areas` 声明式布局，列数 6~12，列间距 40px、行间距 34px
- 容器 `min-width ≥ 980px`，外套 `.fd-scroll` 保证窄屏可横向滚动
- 复杂流程用泳道条（`.fd-lane`）分区：标题 + 跟随式说明文字（`margin-left:2px` + 分隔线，**禁止右对齐**，右半区留空供跨区连线通过）

## S02：配色语义体系

| 语义 | 主题类 | 主色 | 用途 |
|------|--------|------|------|
| 采集/子流程 | `t-orange` | `#FA8C16` | 数据采集、独立子流程节点 |
| 主流程 | `t-blue` | `#409eff` | 主流程步骤节点 |
| 熔断/危险 | `t-red` | `#F5222D` | 熔断、暂停、失败路径、安全阀 |
| 正常/恢复 | `t-green` | `#52C41A` | 正常执行、成功、恢复路径 |
| 判断节点 | `t-amber` | `#e6a23c` | 决策/校验节点（配「判断」徽章） |
| 外部输入 | `t-gray` | `#909399` | 外部系统、起始节点、回环连线 |
| 人工操作 | `t-manual` | `#c0392b` | 人工补录/介入节点（虚线边框） |

连线颜色与**源节点语义**一致；分支出口用结果语义色（成功绿 / 失败红）。

## S03：节点规范

- 卡片结构：图标（`.fn-ico` 26px 圆角方块）+ 标题 + 副标题 + 标签 chips
- **判断节点**：`t-amber` + 右上角「判断」徽章（`.fn-badge`）
- **主流程步骤**：左上角序号徽章（`.fn-num` 圆形，从 1 递增）
- **安全阀/闸口节点**：`t-red t-gate`（2.5px 加粗边框）+ 红色「安全阀」徽章
- 同一张图内同层节点高度对齐（Grid `align-items:stretch`）

## S04：布线规范（核心，最易踩坑）

### 路由优先级

1. **肘形布线（orthPath，8-10px 圆角）为默认**：跨泳道、跨区域、扇出分流一律用直角肘形
2. **S 曲线仅限同行/同列短对角连接**（如右侧相邻的斜向节点）
3. **上下垂直相邻节点用 `kind:"down"` 垂直下落**（源底部→目标顶部），⛔ 禁止走横向 S 曲线从目标左侧进入
4. 特殊路由由 `kind` 声明：`gate`（跨区域垂直下行+净空横移）、`channel`（右侧空列通道）、`fan`（多分支扇出，每分支独立竖向通道 `lane`）、`loop`（底部回环）、`up-left`（上绕）、`down`（垂直下落，支持 `sx/tx` 偏移）

### 硬性禁令

- ⛔ 线条**不得穿过**任何节点卡片、序号/判断徽章、泳道条文字
- ⛔ 横向干线必须在卡片顶上方 **≥26px 净空**通过（序号徽章上探 11px + 15px 余量）
- ⛔ 标签**不得遮挡箭头头部**和线条本体关键拐点。落地做法：标签默认放路径 **15%-45% 区段**（`lx:0.15~0.45`，远离两端箭头）；垂直线上的标签必须水平偏移 **≥28px**（`ox`）；改完必须 **2x 放大截图**核验箭头零遮挡
- ⛔ 多条线不得汇聚于同一进出点形成"打结"；同一节点的相邻进线/出线在底部进入时横向错开 ≥30px

### 交叉处理

- 拓扑上可避免的交叉 → 必须改道消除（换通道、换进入边）
- 拓扑必然交叉（最多 1 处）→ 主千线用**加粗实线**（`solid:true, w≥2.6`）"跨越"虚线，交叉点远离箭头头部

### 流向表达

- 普通连线：虚线流动动画（`stroke-dasharray:7 6` + dashoffset 滚动），流动方向即数据方向
- 关键千线（安全阀供数等）：加粗实线（`solid:true`）
- 回环线：浅灰稀疏虚线（`fd-loop`），从底部回环进入目标底部
- 箭头：9.6×7.6 流线型三角，`round` 接合，颜色随线条；**固定尺寸（`markerUnits="userSpaceOnUse"`），不随线宽缩放**——⛔ 禁止默认的 `strokeWidth` 模式，否则粗线（w≥3）箭头会膨胀成大三角并与线身脱节
- 所有线条 `stroke-linecap/linejoin: round`

## S05：交互规范

1. **悬停链路高亮**：鼠标悬停任一节点 → 其直接上下游节点与连线全亮（连线加粗至 3.2px），其余元素淡出至 16% 透明度
2. 卡片 hover：`translateY(-3px)` + 阴影加深，缓动 `cubic-bezier(.34,1.3,.44,1)`
3. 进场：节点阶梯式渐入（55ms 间隔），连线/标签延迟淡入；JS 加 `.fd-arm` 门控，无 JS 时直接可见
4. `prefers-reduced-motion`：禁用流动动画与过渡
5. 连线由 JS 按节点实际坐标动态测算，`ResizeObserver` + `window.load` 自适应重绘
6. 图注末尾附交互提示：「💡 悬停任一节点可高亮其上下游链路，箭头虚线流动方向即数据流向。」

## S06：边配置格式

在 `.flowdia` 内嵌 `<script type="application/json" class="fd-edges">`：

```json
[
  {"f":"源id", "t":"目标id", "c":"#颜色"},
  {"f":"a", "t":"b", "c":"#52C41A", "label":"成功", "oy":-13},
  {"f":"x", "t":"y", "c":"#F5222D", "kind":"gate", "w":3.4, "solid":true, "label":"可信供数", "strong":true}
]
```

| 字段 | 说明 |
|------|------|
| `f` / `t` | 源/目标节点的 `data-id`（必填） |
| `c` | 连线颜色（默认 `#9aa4b2`） |
| `label` | 流向标签文字 |
| `kind` | `gate` / `channel` / `fan` / `loop` / `up-left` / `down`（默认自动） |
| `enter` | `bottom` 从目标底部进入 |
| `solid` / `w` | 实线 / 线宽（默认虚线 2.2px） |
| `strong` | 标签加粗放大（关键千线用） |
| `lx` / `ox` / `oy` | 标签沿线位置比例（默认 0.5，避箭头用 0.15~0.45）/ X / Y 偏移 px |
| `sx` / `tx` | `down` 专用：源底部 / 目标顶部落点 X 偏移 |
| `lane` / `fy` | fan 专用：竖向通道偏移 / 出口高度比例 |

## S07：颗粒度与规则表达规范（v1.1 新增）

> 来源：业务流程图连续两轮被评「颗粒度不够细」「规则没说明白」。

1. **主流程必须拆到「子步骤可独立验证」级别**：不要把多步业务链压成一个粗节点。例：「判断条件」应展开为四层级联 4 个子节点（平台级→店铺级→SKU级→Listing级），各带条件明细 chips 与规则编号（R06/R07…）；图的步骤须与正文执行流程章节（如 §2.2.4）逐步对齐、编号一致
2. **关键业务约束必须「上卡」**：节点涉及硬性规则（时间窗口、阈值、重试上限、性能约束）时，必须把规则**一句话写进卡片副标题**（如「可拉截止点 = 当前之后下一个 15:00（含）」），⛔ 禁止只放术语名 chips（如只写「15:00 日切窗口」）让读者去正文找
3. **复杂规则正文配图解**：一句话规则 + 两步判断法 + 时间轴/示例表，图中卡片与正文图解互相索引
4. 成组子节点表达：flowdia 用同色系卡片组 + 泳道副标题；mermaid 用同色 classDef + 编号（②a-②d），见 S08

## S08：Mermaid 权威源注意事项（v1.1 新增）

> 来源：mermaid 侧两轮排序/索引事故。

1. ⛔ **避免嵌套 subgraph 的跨簇串联**：节点链穿过嵌套子图时 dagre 排序会错乱（链首节点被排到链尾）。成组改为**平铺节点 + 同色 classDef + 编号**（如 ②a-②d 琥珀色组），不用嵌套 subgraph
2. **linkStyle 索引必须随边重数**：mermaid 按边定义顺序从 0 编号，增减/重排边后索引全变。改边后必须重数（含 subgraph 内边、`A-->B-->C` 链式按单条累加），否则红色加粗等样式会染错边
3. **分支结果染色与 flowdia 语义对齐**：成功绿 `linkStyle N stroke:#52c41a`、失败红 `stroke:#c0392b`、安全阀供数红色加粗 `stroke-width:4px`
4. 节点文案与 flowdia 卡片一一对应（含规则行），同步修改后重渲染 svg/png 及全部存档产物

## S09：质量检查清单（Reviewer 必检）

> 标注口径（引用规则 W21）：【机器可验】项附检查命令（`<html>`/`<md>` 为被检产出文件路径，项目根目录执行）；线条/标签/配色语义等视觉核验类项为【人工判定】，附判定要点。

- [ ] 流程图使用 flowdia 组件，非静态 PNG —— 【机器可验】`grep -c "flowdia" <html>` ≥ 1，且 `grep -nE "!\[.*\]\(.*png\)" <md>` 在流程图位置零命中
- [ ] 节点/分支/标签与 MD 中 Mermaid 权威源一致 —— 【人工判定】逐图比对节点、分支、标签一一对应
- [ ] 配色符合 S02 语义体系，判断节点有「判断」徽章，主流程步骤有序号徽章 —— 【人工判定】对照 S02 色表逐节点核色；辅助命令：`grep -oE "t-(orange|blue|red|green|amber|gray|manual)" <html> | sort -u` 输出须全部在 S02 注册主题类内，`grep -c "fn-badge\|fn-num" <html>` 核对徽章数量
- [ ] 无线条穿过节点/徽章/文字；横向干线净空 ≥26px —— 【人工判定】2x 放大截图逐线核验
- [ ] 标签不遮挡箭头（2x 放大截图逐箭头核验；标签在路径 15%-45% 区段或已偏移让位） —— 【人工判定】2x 放大截图逐箭头核验
- [ ] 箭头为固定尺寸，粗线无「大三角」膨胀脱节 —— 【机器可验】`grep -c 'markerUnits="userSpaceOnUse"' <html>` ≥ 1；粗线箭头外观 2x 截图复核
- [ ] 垂直相邻节点用 `down` 路由，无横向 S 曲线入侧 —— 【人工判定】2x 截图核验；辅助命令：`grep -o '"kind":"down"' <html>` 核对边配置
- [ ] 主流程颗粒度与正文执行流程章节逐步对齐（S07） —— 【人工判定】图步骤与正文章节逐步比对，编号一致
- [ ] 关键业务约束已一句话上卡，无裸术语 chips（S07） —— 【人工判定】逐卡核对副标题含规则一句话
- [ ] mermaid 无嵌套 subgraph 跨簇串联；linkStyle 索引已重数（S08） —— 【人工判定】`grep -n "subgraph" <md>` 核对嵌套结构，改边后重数 linkStyle 索引
- [ ] 交叉 ≤1 处且为实线跨越虚线 —— 【人工判定】2x 截图核验交叉点
- [ ] 悬停节点能正确高亮上下游链路 —— 【机器可验】Playwright 悬停 `.fn` 节点后断言其上下游连线加粗至 3.2px、其余元素透明度 16%（先按本节「截图验证方法」注入 fd-in/fd-done）
- [ ] 窄屏可横向滚动；无 JS 报错 —— 【机器可验】`grep -c "fd-scroll" <html>` ≥ 1；起本地服务（`python3 -m http.server <port>`）后 Playwright 窄视口打开页面，控制台零 error
- [ ] 图注含交互提示语 —— 【机器可验】`grep -c "悬停任一节点可高亮其上下游链路" <html>` ≥ 1

### 截图验证方法（v1.1 新增）

1. `file://` 协议被 Playwright 禁用 → 项目根起本地服务 `python3 -m http.server <port>` 再访问
2. flowdia 有进场门控（`.fd-arm`）：截图前先注入 `document.querySelectorAll('.flowdia').forEach(d=>d.classList.add('fd-in','fd-done'))`，否则节点透明不可见
3. 宽图（min-width > 容器）需滚动 `.fd-scroll`（`s.scrollLeft = s.scrollWidth`）分段截图，左右两侧都要检
4. 标签/箭头遮挡类问题必须 2x 放大裁剪目标区域核验，禁止只看整图

## 实施指引

1. 复制 `templates/flowdia/flowdia.css` 全文到页面 `<style>`，复制 `flowdia.js` 全文到页面底部 `<script>`
2. 参照 `templates/flowdia/example.html` 编写节点与边配置
3. 按 S04 规划布线：先画草图确定通道，再写 `grid-template-areas`
4. 完成后按 S09 清单自检，并用 2x 截图逐项核对

## v1.1 踩坑记录（2026-07-21 · eBayPLP 业务流程图 9 轮评审）

| # | 踩坑点 | 修复方案 | 落点 |
|---|--------|---------|------|
| 1 | 边加粗后箭头膨胀成大三角、与线脱节 | flowdia.js marker 加 `markerUnits="userSpaceOnUse"` | S04 流向表达 |
| 2 | 「成功/失败」标签遮挡箭头（2 轮返工） | 标签移路径 15%-45% 区段 + 垂直线 `ox≥28px` + 2x 放大核验 | S04 禁令 / S09 清单 |
| 3 | 垂直相邻节点走横向 S 曲线入卡片左侧 | 新增 `kind:"down"` 垂直下落路由 | S04 路由 / S06 字段 |
| 4 | 主流程颗粒度不足（2 轮「不够细」） | 拆到可独立验证子步骤，与正文 §2.x 逐步对齐 | S07-1 |
| 5 | 15:00 日切窗口只写术语名，规则没上图 | 关键约束一句话写进卡片副标题 | S07-2 |
| 6 | mermaid 嵌套 subgraph 跨簇串联致节点排序错乱 | 平铺节点 + 同色分组 + 编号替代嵌套 | S08-1 |
| 7 | 增减边后 linkStyle 索引失配染错边 | 改边后强制重数索引；成功绿/失败红染色 | S08-2/3 |
| 8 | 截图验证：fd-arm 门控节点不可见、宽图截不全、file:// 被禁 | 注入 fd-in/fd-done、fd-scroll 分段截图、本地 http 服务 | S09 验证方法 |

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-04 09:10 | v1.4 | ①适用范围收缩：PRD 流水线迁出（图源与呈现标准迁至 `docs/rules/prd-diagram-standard.md` D01-D08），本标准仅适用 proto/diagram 等 HTML 产出；②总则第 2 条改写（删除「Mermaid 仍是 PRD Markdown 权威源」表述）；③参考实现标注为存量 PRD 产物（仅作组件维护参考）；S01-S09 技术内容未改 | 本文件 + `docs/rules/prd-diagram-standard.md`（新建）+ `docs/agents/prd_stages/html_render.md` v1.3 |
| 2026-07-28 | v1.3 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补 frontmatter/属性表/附录变更记录，原头部「更新记录」行移入本表；②核对适用范围：`grapesjs` 引用已剔除，确认零残留；③S09 检查清单 14 项逐项标注【机器可验】（附检查命令）/【人工判定】（引用规则 W21）；④正文技术内容（S01-S09、实施指引、踩坑记录）一字未改 | 本文件 |
| 2026-07-23 | v1.2 | ①v1.1 整合 eBayPLP 业务流程图 9 轮评审踩坑（见「v1.1 踩坑记录」节）；②v1.2 适用范围扩至全项目所有 SOP 层，并显式声明操作文档 docx 例外 | 本文件 |
