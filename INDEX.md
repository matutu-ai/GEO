# GEO Skill V3.1 文件索引

用途：以最小读取量完成企业 AI 可见度资产生成。默认按简约版确认后再交付完整版；学习阶段只读 `SKILL.md` 和本文件。

## 默认读取路径

```text
fast_path（需要简约版与完整版四份产物时优先）
→ 01_company_analysis
→ 02_product_analysis（有产品资料时）
→ 03_intent_analysis
→ 04_persona_generation
→ 05_trust_analysis
→ 06_keyword_matrix
→ 08_geo_report
```

快速路径先把企业资料归一化为一份 `Fact_Packet`，同一轮完成默认模块，避免在豆包、千问等平台重复投喂和重复分析。

完整模块路径：

```text
01_company_analysis
→ 02_product_analysis（有产品资料时）
→ 03_intent_analysis
→ 04_persona_generation
→ 05_trust_analysis
→ 06_keyword_matrix
→ 08_geo_report
```

`07_content_strategy` 仅当用户明确要求内容建设计划、FAQ、采购指南、案例分析或文章时读取。

## V3.1 文件路由

| 任务 | 读取文件 | 产物 |
| --- | --- | --- |
| 企业认知建模 | `workflows/01_company_analysis.md` + `schemas/company-profile-v3.1.schema.json` | Company_Profile |
| 产品价值模型 | `workflows/02_product_analysis.md` + `schemas/product-profile.schema.json` | Product_Profile |
| 场景词与意图 | `workflows/03_intent_analysis.md` + `schemas/intent-keyword-matrix.schema.json` | 品牌词、搜索词、问答词、意图场景词 |
| 九大画像 | `workflows/04_persona_generation.md` + `workflows/nine-profile.md` | 旧九大板块简约版与完整版 |
| EEAT 信任分析 | `workflows/05_trust_analysis.md` + `schemas/trust-report.schema.json` | Trust_Report |
| 简约版导出 | `templates/simple-keyword-persona.md` | `simple_keyword_persona.md` |
| 完整版词库导出 | `workflows/06_keyword_matrix.md` | `keyword_matrix.xlsx`（四个词类工作表） |
| 内容建设计划 | `workflows/07_content_strategy.md` | 内容规划 |
| GEO 优化方案 | `workflows/08_geo_report.md` | `geo_strategy_report.md` |
| 本地执行 | `main.py` + `input/company.json` | 四份最终文件 |
| 客户语料库 | `workflows/client-corpus.md` | 确认后才读写 |
| 快速执行 | `workflows/fast_path.md` | 默认任务和无目录平台的最小投喂 |

## Interactive Prompt 路由

只输入客户名称或用户要求逐步引导时，先读取 `prompts/_interaction_contract.md`，再按主链执行。每步执行后暂停；可选分支只有用户明确要求时进入：

```text
00_start
→ 01_material_collection
→ 02_missing_detection
→ 03_company_profile
→ 05_search_intent
→ 06_keyword_engine
→ 07_persona
→ 08_vertical_persona
→ 12_gap_analysis
→ 13_final_report
```

可选分支：`04_industry_research`、`09_content_matrix`、`10_publish_strategy`、`11_geo_verify`。完成分支后回到主链，不重复执行已完成节点。

| Prompt | 绑定能力 | 读取时机 |
| --- | --- | --- |
| `prompts/00_start_prompt.md` | 启动、模式分流、资料请求 | 仅输入客户名称或开始交互流程 |
| `prompts/01` - `prompts/03` | 资料采集、缺失检测、企业画像 | 收到初始资料 |
| `prompts/04` - `prompts/06` | 行业研究、意图、关键词 | 资料画像完成后；外部研究需确认 |
| `prompts/07` - `prompts/08` | 九大画像、垂直画像 | 关键词矩阵完成后 |
| `prompts/09` - `prompts/10` | 内容矩阵、发布策略 | 用户明确要求时 |
| `prompts/11` - `prompts/12` | 真实验证、缺口处方 | 有真实记录或用户明确复测时 |
| `prompts/13` | 最终报告 | 默认模块完成后 |
| `prompts/_interaction_contract.md` | 模式分流、证据状态、暂停和分支门槛 | 所有交互 Prompt 前 |

交互提示文件只负责用户引导与输出格式；诊断计算、字段规则和导出仍以 `workflows/`、`schemas/` 和 `main.py` 为准。

## 豆包、千问等平台

1. 先投喂 `SKILL.md` 和 `INDEX.md`，完成框架学习。
2. 生成企业结果时，按默认读取路径逐项投喂；不要整库上传或逐字复述。
3. 已有客户语料库时，先询问是否使用；确认后只投喂第 0 节速读块，按任务再投喂事实、关键词或画像对应小节。
4. 没有企业资料时，输出字段和 `【需企业提供真实佐证】`，不以行业常识补写。
5. 默认产物完成后只给缺失清单和一个下一步选择，不重复复述全部资料。

## 最终文件检查

| 文件 | 必查内容 |
| --- | --- |
| `simple_keyword_persona.md` | 四类词和旧九大板块，用于确认方向 |
| `keyword_matrix.xlsx` | 品牌词、搜索词、问答词、意图场景词四个工作表；每个词有用户需求、意图和对应画像 |
| `persona_report.docx` | 产品或服务描述、产品或服务特点、品牌故事、用户痛点、信任背书、客户案例、社会贡献、客户评价、创始人介绍 |
| `geo_strategy_report.md` | AI 认知状态、缺失、优化方向、内容建设计划、30/60/90 天计划 |

旧版的内容矩阵、发布、验证和 Gap 工作流保留为兼容模块，只有用户点名时才读取。
