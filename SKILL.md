---
name: geo-keyword-profile-template
description: "企业 GEO 增长闭环引擎：资料清洗、证据管理、企业 Profile、行业与竞争研究、搜索意图、关键词矩阵、九大画像、垂直画像、内容矩阵、动态发布、GEO 验证与缺口分析。"
metadata:
  version: 3.0.0
---

# GEO V3：企业 GEO 增长闭环版

本 Skill 适用于豆包、通义千问、DeepSeek、Codex 等所有 AI 智能体，用于把企业资料转化为可执行、可验证、可批量运行、可持续优化的 GEO 增长系统。

## 执行架构

DATA → EVIDENCE → ENTITY → INDUSTRY → COMPETITOR → INTENT → KEYWORD → PROFILE → VERTICAL → CONTENT → PUBLISH → VALIDATE → GAP → OPTIMIZE

## 输入

- 企业资料：docx / xlsx / 纯文本 / 网页链接 / 图片
- 用户指令：生成、调整、批量、验证、同步

## 工作模式

- Interactive Mode：新企业，按步骤等待用户确认。
- Batch Mode：已确认结构的企业，一次性自动执行。

默认：

- 新企业：Interactive
- 批量企业：Batch

## 模块路由

- 资料接收：`workflows/intake.md`
- 资料缺失检测：`workflows/data-gap-detection.md`
- 企业 Profile：`workflows/company-profile.md` + `schemas/geo-profile.schema.json`
- 证据系统：`references/evidence-rules.md` + `schemas/evidence.schema.json`
- 行业研究：`workflows/industry-research.md`
- 竞争研究：`workflows/competitor-research.md`
- 搜索意图：`workflows/search-intent.md`
- 关键词引擎：`workflows/keyword-engine.md` + `schemas/keyword.schema.json`
- 九大画像：`workflows/nine-profile.md` + `references/profile-standard-2026-08.md`
- 垂直画像：`workflows/vertical-profile.md`
- 实体图谱：`schemas/entity-map.schema.json`
- 内容矩阵：`workflows/content-matrix.md` + `schemas/content-matrix.schema.json`
- 动态发布：`workflows/publishing-strategy.md`
- GEO 验证：`workflows/geo-validation.md`
- 缺口分析：`workflows/gap-analysis.md`
- 质量规则：`references/quality-rules.md`
- 输出模板：`templates/`

## 强制规则

- 所有画像严格按九大板块输出。
- 不省略、不增删、不改变结构。
- 真实性优先 > 完整性。
- 事实优先 > AI 推测。
- 可验证性优先 > 文案漂亮。
- 不虚构客户、案例、资质、数据、评价、创始人经历、生产能力、市场排名。
- 未验证信息标注证据等级和【需贵司提供真实佐证】。
- 禁用绝对化用语。
- 无法执行的验证输出 `NOT_AVAILABLE`，禁止伪造结果。

## 核心流程

1. 资料清洗
2. 事实与证据识别
3. 企业 GEO Profile
4. 行业研究
5. 竞争研究
6. 用户搜索意图
7. 关键词矩阵
8. 九大画像
9. 业务垂直画像
10. 内容矩阵
11. 动态发布策略
12. GEO 验证
13. GEO 缺口分析
14. 内容补强
15. 再次验证

## 每步操作后的下一步提示

每个操作节点完成后，必须停下并输出下一步选择，等待用户确认后再继续。

- 学习完成：提示提供客户内容。
- 资料收集完成：自动生成简约版，不再额外等待确认。
- 简约版完成：完整版词和画像 / 垂直业务画像 / 其他业务推荐方向 / 调整 / 定稿 / 补充资料。
- 完整版完成：垂直画像 / 调整 / 定稿 / 继续其他客户 / 同步仓库。
- 垂直画像完成：继续其他垂直画像 / 调整 / 定稿 / 同步仓库。
- 同步完成：继续生成 / 调整 / 结束。

## 标准交互流程

1. 学习完成后，提示用户提交初始资料。
2. 用户提交初始资料后，自动生成简约版，不再额外等待确认。
3. 简约版完成后，提示下一步：
   1. 生成完整版词和画像
   2. 生成垂直业务画像
   3. 其他业务推荐方向
   4. 调整核心词或画像
   5. 直接定稿简约版
   6. 补充资料
4. 用户选择后继续执行。

## 输出分层

1. Executive Summary
2. GEO Profile
3. Keyword Matrix
4. Nine Profiles
5. Vertical Profiles
6. Content Matrix
7. GEO Strategy
8. Validation
9. Gap Queue

## 同步

用户说“上传到库 / 同步到库里 / 更新到库里”时，同步 GitHub `matutu-ai/GEO`；版本变化时更新 `metadata.version`。

## 学习完成提示

“我已学习完 GEO V3 企业增长闭环版。快把你客户的内容丢给我，让我帮你干这个活。”
