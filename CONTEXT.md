---
last_updated: 2026-08-11
---

# Project Context

## Business Context
- **领域**: （待补充）
- **当前重点**: （待补充）

## User Profile Summary
- **角色**: 产品经理
- **语言**: 中文
- **输出偏好**: （持续积累中，详见 `.agents/memory/feedback_preferences.md`）

## Architecture Decisions
- 多 Agent 编排架构，文件通信（非 API）
- 零构建原型（纯 HTML/CSS/JS，可直接浏览器打开）
- 图表 Mermaid 内联为权威源；HTML 流程图用 flowdia 交互组件呈现（禁止静态 PNG），标准见 `docs/rules/flow-diagram-standard.md`
- Playwright（持久化浏览器 profile）用于需登录的页面截图
- 「图先行」PRD 流程：4 张标准图 → 围绕图写文字
- 强制可行性验证门禁：编造零容忍
- GSD/Harness 对齐：AGENTS.md 拆解为路由 + STATE.md 跨会话状态

## Knowledge Base Status
| 类别 | 状态 |
|------|------|
| （初始化，无数据） | — |
