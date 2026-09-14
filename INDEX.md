# GEO Skill V3.1 文件索引

用途：以最小读取量完成企业 AI 可见度资产生成。学习阶段只读 `SKILL.md` 和本文件；不加载无关工作流、旧模板、测试或示例。

## 默认读取路径

```text
fast_path（只要默认三份产物时优先）
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
| 场景词与意图 | `workflows/03_intent_analysis.md` + `schemas/intent-keyword-matrix.schema.json` | Intent_Keyword_Matrix |
| 九大画像 | `workflows/04_persona_generation.md` | Nine_Personas |
| EEAT 信任分析 | `workflows/05_trust_analysis.md` + `schemas/trust-report.schema.json` | Trust_Report |
| 场景词库导出 | `workflows/06_keyword_matrix.md` | `keyword_matrix.xlsx` |
| 内容建设计划 | `workflows/07_content_strategy.md` | 内容规划 |
| GEO 优化方案 | `workflows/08_geo_report.md` | `geo_strategy_report.md` |
| 本地执行 | `main.py` + `input/company.json` | 三份最终文件 |
| 客户语料库 | `workflows/client-corpus.md` | 确认后才读写 |
| 快速执行 | `workflows/fast_path.md` | 默认任务和无目录平台的最小投喂 |

## 豆包、千问等平台

1. 先投喂 `SKILL.md` 和 `INDEX.md`，完成框架学习。
2. 生成企业结果时，按默认读取路径逐项投喂；不要整库上传或逐字复述。
3. 已有客户语料库时，先询问是否使用；确认后只投喂第 0 节速读块，按任务再投喂事实、关键词或画像对应小节。
4. 没有企业资料时，输出字段和 `【需企业提供真实佐证】`，不以行业常识补写。
5. 默认产物完成后只给缺失清单和一个下一步选择，不重复复述全部资料。

## 最终文件检查

| 文件 | 必查内容 |
| --- | --- |
| `keyword_matrix.xlsx` | 固定七列表头；每个词有用户需求、意图和对应画像 |
| `persona_report.docx` | 九个固定画像标题；缺失事实有待佐证标记 |
| `geo_strategy_report.md` | AI 认知状态、缺失、优化方向、内容建设计划、30/60/90 天计划 |

旧版的内容矩阵、发布、验证和 Gap 工作流保留为兼容模块，只有用户点名时才读取。
