---
title: PRD 子角色-Researcher 执行细则
version: v1.1
date: 2026-07-28
status: active
---

# PRD 子角色：Researcher（需求调研员）

| 属性 | 值 |
|------|-----|
| 版本 | v1.1 |
| 适用范围 | PRD 流水线 Researcher 阶段（需求调研）SOP 与检验清单 |
| 创建日期 | 2026-07-28 |
| 状态 | active |
| 关联文档 | `docs/agents/prd_agent.md`（阶段路由表）、`docs/rules/sop-writing-standard.md`（§2.6 产出文件名、W21） |

```
Step 1. 读取输入
        - 用户原始需求 / 任务书
        - 用户认知上下文（docs/knowledge-base/user-profile/）

Step 2. 背景调研
        - 项目背景是什么？
        - 解决什么用户痛点？（3句话以内）
        - 业务目标是什么？（量化指标）

Step 3. 用户分析
        - 目标用户画像
        - 用户场景和使用路径
        - 痛点和期望

Step 4. 知识库检索（核心步骤）
        - 扫描 docs/knowledge-base/platform-api/ 获取相关API文档
        - 扫描 docs/knowledge-base/domain/ 获取业务领域知识
        - 扫描 docs/knowledge-base/operations/ 获取运营流程知识
        - 记录可用的API端点、字段、枚举值（使用中文用户界面标签，不使用内部代码标识符）

Step 5. 参考资料收集
        - 如有原型设计文档（versions/{v}/prototype/{name}-prototype.md），读取作为参考
        - 如有已爬取页面数据（versions/{v}/prototype/restored/），读取提取业务信息
        - 如有 Figma 设计上下文（versions/{v}/prototype/figma_*.json），读取设计参考

Step 6. 范围界定
        - 功能范围（做什么/不做什么）
        - 适用范围（站点/店铺类型/业务模式）
        - 依赖项和约束
        - 明确的「非目标」

Step 7. 输出《需求调研摘要》
        写入：versions/{v}/agent_comm/{task_id}/01_research_summary.md
        必须包含：
        - 背景与痛点（3句话以内）
        - 目标用户与场景
        - 可用API端点清单（来自知识库，含端点路径、方法、关键字段）
        - 关键枚举值和字段映射（来自API文档，枚举值必须使用中文用户界面标签）
        - 功能范围（含明确的非目标）
        - 前置依赖
        - 参考资料列表
```

## Researcher 检验

> 每项标注【机器可验】/【人工判定】（引用规则 W21）。

- [ ] 【机器可验】调研摘要包含背景/用户/范围三要素（`grep -c "背景\|用户\|范围" 01_research_summary.md` ≥ 3）
- [ ] 【人工判定】已检索知识库中的API文档（核对摘要中 API 清单来源标注 `docs/knowledge-base/platform-api/`）
- [ ] 【机器可验】可用API端点清单 ≥ 1 个（`grep -c` 端点条目 ≥ 1）
- [ ] 【人工判定】关键枚举值已记录（且使用中文用户界面标签，非内部代码标识符）
- [ ] 【机器可验】明确列出了「非目标」（`grep -c "非目标" 01_research_summary.md` ≥ 1）

## 附录：变更记录

| 日期 | 版本 | 变更内容 | 同步载体 |
|------|------|----------|----------|
| 2026-07-28 | v1.1 | ①按 `docs/rules/sop-writing-standard.md` §2.1 补齐 frontmatter（四字段）+ 属性表；②Researcher 检验 5 项逐项标注【机器可验】/【人工判定】（引用规则 W21）；③文末新增附录变更记录表（引用规则 W10）；④技术内容未改动，Step 1-7 步骤与产出文件名 `01_research_summary.md` 保持原样 | 本文件 |
