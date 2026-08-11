---
title: UI 样式与交互规范
version: v1.2
date: 2026-08-11
status: active
---

# UI 样式与交互规范

| 属性 | 值 |
|------|-----|
| 版本 | v1.2 |
| 适用范围 | 全项目 PRD 与原型（proto）任务的页面结构/弹窗结构/控件样式/交互逻辑引用 |
| 创建日期 | 2026-08-11 |
| 状态 | active |
| 关联文档 | `docs/agents/ui_standard_agent.md`（维护流程）、`docs/agents/proto_agent.md`（引用硬约束）、`docs/agents/prd_agent.md`（引用约定）、`templates/components/base-styles.css`（原型实现 token） |

> 本文件是 **UI 编号（UI-01 起连续）的唯一权威定义**，已在 `docs/rules/sop-writing-standard.md` §2.5 编号前缀注册表注册；其他文档只写「引用规则 UI-xx」。
> 本文件与 `docs/rules/ui-standard/chapters/*.md` 是规范内容的**唯一权威源**（Markdown）；`docs/rules/ui-standard/index.html` 是由 `scripts/ui_standard_render.py` 生成的**只读查看器**，禁止手工修改。
> 行数说明：§4 索引表随条目增长，本文件不受 500 行上限约束（声明例外，引用 `docs/rules/sop-writing-standard.md` §2.1 例外机制）。

## §1 目的与适用范围

### §1.1 目的

让 PRD 与原型在描述页面结构、弹窗结构、表单控件样式与交互逻辑时**有号可循**：每个已被实测归纳的框架/容器/控件/交互都有全局唯一的 UI-xx 编号，PRD 与原型设计文档引用编号即可，禁止重复描述样式细节。

### §1.2 覆盖范围（四层）

| 层 | 类型值 | 说明 | 分章文件 |
|----|--------|------|----------|
| 页面框架 | `框架` | 整页级结构：后台骨架、列表页、表单页、详情页、看板页 | `chapters/01-page-frameworks.md` |
| 弹窗与容器 | `容器` | 弹窗解剖、抽屉、筛选区、卡片分组等 | `chapters/02-dialogs-containers.md` |
| 控件 | `控件` | 输入/选择/日期/上传/按钮/表格等表单与数据控件 | `chapters/03`~`07`、`09` |
| 交互 | `交互` | 校验、toast、确认、loading、空态等反馈模式 | `chapters/08-feedback.md` 等 |

### §1.3 分工边界（引用规则 W01）

- **本规范**：记录源系统（由实测收录时指定）线上**实测**的样式与交互口径，供 PRD/原型**引用**。
- `templates/components/base-styles.css` + `templates/components/registry.yaml`：约束**新原型的实现 token 与组件模版**，地位不变。
- PRD 内禁止直接描述颜色/字号/间距等样式值（`docs/agents/prd_agent.md`「UI 样式与交互引用」小节），改为引用 UI-xx 编号。

## §2 编号规则

1. **格式**：`UI-` + 数字，从 `UI-01` 起；两位数不够用后自然扩展为三位（`UI-100`），禁止前导补零以外的变形。
2. **连续追加**：新编号 = 当前最大编号 + 1。分配命令（项目根目录执行；只扫分章文件，本文件 §2/§3 的示例编号不计入）：

   ```bash
   grep -rhoE "UI-[0-9]+" docs/rules/ui-standard/chapters/ | sort -t- -k2 -n | tail -1
   ```

   输出当前最大编号（如 `UI-37`），新条目编号即 `UI-38`；无输出表示尚未收录任何条目，首个编号为 `UI-01`。
3. **与章节解耦**：编号全局唯一，条目归属哪个章节由 §4 索引表的「章节文件」列决定；新增条目只追加新号，**禁止插入改号**。
4. **废止不删号**：条目废止时将「状态」改为 `archived` 并在条目首行注明废止原因与替代编号（如有），**禁止删除编号与条目正文**——历史 PRD/原型的引用必须永远可回溯。
5. **状态枚举**：`active`（已线上实测）/ `inferred`（截图推断，待实测确认）/ `archived`（已废止）。

## §3 条目模板（固定 12 字段 + 6 区块）

条目写在对应分章文件内，格式逐字如下（机器可解析，渲染/校验脚本依赖此格式，禁止改动标题层级与区块标记）：

```markdown
### UI-01 单行文本输入框

| 字段 | 值 |
|------|-----|
| 编号 | UI-01 |
| 名称 | 单行文本输入框 |
| 类型 | 控件 |
| 实测类名 | el-input |
| 来源页面 | 示例页面/筛选区 |
| 状态 | active |
| 收录日期 | 2026-08-11 |

**结构解剖**：控件类条目写「无」；框架/容器类必填（分区组成、层级、各分区职责）。

**样式规格**（线上实测值）：
- 高度：32px；字号：14px；边框：1px solid #dcdfe6；圆角：4px
- （每项一条，实测值，禁止写「与默认一致」）

**状态矩阵**：默认 / hover / focus / 禁用 / 错误（逐状态一行，写清视觉差异）

**交互逻辑**：
1. 触发：点击输入框获得焦点，边框变主色
2. 反馈：输入内容实时显示；hover 出现清空按钮
3. 校验：失焦校验，错误时红框 + 下方红字提示
4. 边界：超长输入不换行，横向滚动

**截图**：![UI-01 默认态](assets/ui-01-default.png)

**PRD 引用示例**：「关键字字段使用 UI-01（单行输入，支持清空）」
```

> **格式硬性要求**：① 条目标题固定 `### UI-xx 名称`；② 字段表 7 行齐全且键名一字不差；③ 6 个加粗区块标记（结构解剖/样式规格/状态矩阵/交互逻辑/截图/PRD 引用示例）齐全；④ 截图文件放入 `docs/rules/ui-standard/assets/`，命名公式 `ui-{编号小写}-{状态}.png`；⑤ 一个条目可贴多张截图。

## §4 UI 编号索引表

> 每条条目在此登记一行（新增条目时同步追加，引用规则 W11 同步纪律）。「章节文件」列填分章文件名。

| 编号 | 名称 | 类型 | 章节文件 | 来源页面 | 状态 |
|------|------|------|----------|----------|------|
| （暂无条目，使用 `/manage-ui-standard` 收录） | | | | | |

## §5 检验清单

> 唯一执行入口：`python3 scripts/ui_standard_check.py`（项目根目录执行），5 项全 PASS 才允许提交。

| # | 检验项 | 类型 | 检查方法 |
|---|--------|------|----------|
| 1 | 编号全局唯一，无重复、无跳号复用 | 【机器可验】 | 脚本断言 1（提取全部 `### UI-` 标题与索引表编号比对） |
| 2 | 索引表与分章条目一一对应 | 【机器可验】 | 脚本断言 2（索引行数 = 条目数，且编号集合一致） |
| 3 | 条目引用的截图文件存在于 `assets/` | 【机器可验】 | 脚本断言 3（解析 `](assets/...)` 引用逐个 `test -f`） |
| 4 | 条目必填字段齐全（7 行字段表 + 6 区块标记；框架/容器类结构解剖非「无」） | 【机器可验】 | 脚本断言 4 |
| 5 | MD 与查看器 HTML 同步 | 【机器可验】 | 脚本断言 5（`index.html` 中每个 active/inferred 编号存在对应 `id="ui-xx"` 区块且数量一致） |

## §6 维护方式

- 新增/修改/废止条目、发网址增量盘点、发截图录入、proto 缺失补充：统一走 `/manage-ui-standard`，流程权威定义见 `docs/agents/ui_standard_agent.md`。
- **任何条目变更后必须重跑渲染**：`python3 scripts/ui_standard_render.py`，使 `index.html` 与 MD 同步（断言 5 会拦截未同步的提交）。
- 查看器本地预览：项目根目录执行 `python3 -m http.server 8000` 后访问 `http://localhost:8000/docs/rules/ui-standard/index.html`。

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-08-11 | v1.2 | 实时演示全覆盖：在 v1.1 试点 8 个基础上铺开剩余 20 个（UI-01/02/03/05/06/08/09/10/12/14/15/16/17/18/19/20/22/23/24/25），28 条目 demo 100% 覆盖；新增 UI-19（toast 四类型）、UI-01/25（框架）、UI-02/03（筛选区/批量栏）、UI-20/24（模态/表单弹窗含关闭边界）等 | `docs/rules/ui-standard/demos/`（+20 个 demo）+ `docs/rules/ui-standard/index.html`（重生成，28 处演示 iframe） |
| 2026-08-11 | v1.1 | 新增「实时演示」能力：查看器条目支持按需注入 iframe 演示块（`demos/ui-xx.html` 存在才注入，无则跳过）；试点 8 个（UI-04/07/11/13/21/26/27/28，覆盖输入/按钮/表格/标签/反馈/选择/日期/导航 7 类）；演示统一实测口径主色 `#1a73e8`；`render.py` 增 `demos_dir` 注入逻辑 + `viewer-template.html` 增 `.demo-wrap/.demo-frame` 样式与 `postMessage` 高度自适应 | 本文件 + `scripts/ui_standard_render.py` + `docs/rules/ui-standard/viewer-template.html` + `docs/rules/ui-standard/index.html`（重生成）+ `docs/rules/ui-standard/demos/`（新建 `_lib/` 三件套 + 8 个 demo） |
| 2026-08-11 11:15 | v1.0 | 首次发布：§1-§6 骨架 + 9 个分章文件 + 查看器（`index.html` 渲染管线）+ 维护 Agent（`docs/agents/ui_standard_agent.md`）；编号前缀 UI 已在 `docs/rules/sop-writing-standard.md` §2.5 注册 | 本文件 + `docs/rules/ui-standard/` + `docs/agents/ui_standard_agent.md` + `.agents/skills/manage-ui-standard/SKILL.md` + `scripts/ui_standard_check.py` + `scripts/ui_standard_render.py` |
