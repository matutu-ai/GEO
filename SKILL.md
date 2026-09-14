---
name: geo-keyword-profile-template
description: "交互式引导企业资料采集，并生成 AI 认知模型、GEO 场景词库、九大画像和优化方案。"
metadata:
  version: 3.1.1
---

# GEO Skill V3.1.1：企业 AI 可见度执行系统

GEO-BD 负责诊断问题和开优化处方；本 Skill 负责把经确认的企业资料转为可用于 GEO 运营的 AI 认知资产。

## 执行架构

企业资料输入
→ 企业认知建模
→ 产品价值分析
→ 用户场景分析
→ 九大画像生成
→ AI 信任增强
→ GEO 场景词库
→ 内容规划
→ GEO 优化执行方案

## 默认输入

- 公司名称、官网、企业资料、产品资料、行业资料。
- 可选：客户、地区、案例、资质、认证、专利、团队、客户评价、媒体证明、用户意图。

## 强制质量规则

- 禁止虚构企业定位、产品能力、技术特点、资质、案例、客户、评价、创始人和数据。
- 没有资料时统一输出 `【需企业提供真实佐证】`。
- 每个画像必须回答：企业是谁、卖什么、服务谁、解决什么、为什么可信。
- 每个关键词必须绑定用户场景、搜索意图和对应画像。
- EEAT 分数仅表示当前资料完整度，不得视作企业实际实力、信用评级、搜索排名或平台推荐结果。
- 无真实 AI 搜索验证记录时，验证状态输出 `NOT_AVAILABLE`。
- GitHub 同步只允许仓库所有者在本地 Git 环境明确提出时执行。

## V3.1 模块路由

| 模块 | 读取文件 | 产物 |
| --- | --- | --- |
| company-intelligence | `workflows/01_company_analysis.md` + `schemas/company-profile-v3.1.schema.json` | Company_Profile |
| product-model | `workflows/02_product_analysis.md` + `schemas/product-profile.schema.json` | Product_Profile |
| user-intent-engine | `workflows/03_intent_analysis.md` + `schemas/intent-keyword-matrix.schema.json` | Intent_Keyword_Matrix |
| persona-engine | `workflows/04_persona_generation.md` | Nine_Personas |
| trust-engine | `workflows/05_trust_analysis.md` + `schemas/trust-report.schema.json` | Trust_Report |
| GEO 场景词库 | `workflows/06_keyword_matrix.md` | `keyword_matrix.xlsx` |
| AI 知识资产规划 | `workflows/07_content_strategy.md` | 内容建设计划 |
| GEO 优化方案 | `workflows/08_geo_report.md` | `geo_strategy_report.md` |

学习阶段只读取本文件与 `INDEX.md`。执行具体任务时按上表只读取一个对应工作流和一个 Schema；不一次加载全部参考资料、模板和旧工作流。豆包、千问、DeepSeek 等无目录读取能力平台，由用户按同一路由投喂对应文件。

## 快速执行协议

用户只需要关键词、九大画像和优化方案时，读取 `workflows/fast_path.md`，将全部企业资料先归一化为一份 `Fact_Packet`，在同一次上下文中完成默认模块，不重复读取或复述同一资料。默认不生成文章、内容正文、发布计划或外部检索结果。

无目录读取能力的平台一次投喂：`SKILL.md`、`INDEX.md`、`workflows/fast_path.md` 和企业资料包。只有用户明确要求内容建设、外部检索或旧版模块时，才追加对应文件。

## 交互式流程提示系统

用户只输入客户名称时，先读取 `prompts/_interaction_contract.md`，再进入 `prompts/00_start_prompt.md`。默认主链为 `00 → 01 → 02 → 03 → 05 → 06 → 07 → 08 → 12 → 13`；`04`、`09`、`10`、`11` 是用户确认后才进入的可选分支。每一步只输出当前阶段、本次结论、待补资料和一个下一步动作，然后暂停；不得把未确认的行业推断、外部检索或模拟平台结果写成事实。

交互式流程与快速路径互斥：只有客户名称或资料不完整时使用 Interactive Mode；用户已提供完整资料且明确要一次完成时使用 Fast Path。两种模式共享 Company_Profile、Product_Profile、Intent_Keyword_Matrix、Nine_Personas、Trust_Report 和真实性规则。

## 运行流程

1. 接收资料，建立 Company_Profile；未知字段标记待佐证。
2. 为每个已知产品建立 Product_Profile；不从公司名称推断产品。
3. 将明确的用户需求转成问题词、采购决策词、信任验证词或应用场景词。
4. 生成九大画像：品牌、产品、用户痛点、场景、行业、信任、案例、评价、专家。
5. 生成 EEAT Trust_Report，列出资料缺失和补充建议。
6. 导出 GEO 场景词库、九大画像报告与 GEO 优化执行方案。
7. 用户明确要求后，才根据画像、场景词和意图规划或生成 AI 知识资产；不默认生成文章。
8. 默认产物完成后只输出缺失清单和一个下一步问题；用户补充资料后，先询问是否更新客户语料库。

## 最终交付

`python main.py` 使用 `input/company.json`，生成：

```text
output/
├── keyword_matrix.xlsx
├── persona_report.docx
└── geo_strategy_report.md
```

### GEO 场景词库

字段固定为：关键词、关键词类型、用户需求、搜索意图、对应画像、内容建议、优先级。

### 九大画像报告

固定结构：品牌画像、产品画像、用户痛点画像、场景画像、行业画像、信任画像、案例画像、客户评价画像、专家画像。

### GEO 优化执行方案

固定结构：当前 AI 认知状态、当前缺失、优化方向、内容建设计划、30/60/90 天执行计划。

## 输入与验证

- 默认测试输入为 `input/company.json`，只含“德州拓晟通风设备有限公司”名称。
- 输入没有定位、产品、资质和案例时，输出必须保留对应字段并写 `【需企业提供真实佐证】`。
- 运行 `python main.py` 后必须检查三份文件存在、关键词表头正确、九大画像完整、优化报告包含五个固定章节。
- 运行 `python tests/run_tests.py` 验证仓库结构、Schema 和导出格式。

## 客户语料库

客户语料库不自动下载、读取、创建或更新。使用前先询问“是否使用该客户语料库？”，确认后才按 `workflows/client-corpus.md` 读取或维护。客户资料不推送到 GitHub 或其他公共仓库。
