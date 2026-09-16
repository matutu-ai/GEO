# GEO Skill V3.2 架构

## 定位

`GEO-BD` 是诊断医生：发现企业 AI 可见度问题并给出处方。

`GEO Skill` 是执行系统：将企业已确认资料转化为企业 AI 认知资产和可执行 GEO 优化方案。

## 执行链路

```text
企业资料
→ Company_Profile
→ Product_Profile
→ Intent_Keyword_Matrix
→ Nine_Personas
→ Trust_Report
→ GEO 场景词库
→ 内容建设计划
→ GEO 优化执行方案
```

## 快速路径

默认任务使用 `workflows/fast_path.md`：一份 `Fact_Packet` 在同一次上下文中派生全部默认资产，避免平台反复读取同一资料。快速路径不自动外部检索，不生成文章正文，不读取客户语料库。

## 模块

| 编号 | 模块 ID | 工作流 | 作用 |
| --- | --- | --- | --- |
| 01 | company-intelligence | `01_company_analysis.md` | 定义企业是谁、做什么、服务谁、边界是什么 |
| 02 | product-model | `02_product_analysis.md` | 定义产品价值、场景、能力与交付边界 |
| 03 | user-intent-engine | `03_intent_analysis.md` | 生成问题、采购、信任与场景词 |
| 04 | persona-engine | `04_persona_generation.md` | 生成九大画像 |
| 05 | trust-engine | `05_trust_analysis.md` | 评估 EEAT 资料完整度 |
| 06 | keyword-matrix | `06_keyword_matrix.md` | 导出 GEO 场景词库 |
| 07 | content-strategy | `07_content_strategy.md` | 按需规划 AI 知识资产 |
| 08 | geo-report | `08_geo_report.md` | 输出 30/60/90 天优化方案 |

## 可运行交付

`python main.py` 从 `input/company.json` 生成：

```text
output/
├── simple_keyword_persona.md
├── keyword_matrix.xlsx
├── persona_report.docx
└── geo_strategy_report.md
```

简约版和完整版均严格采用旧九大板块。完整版关键词矩阵固定拆为品牌词、搜索词、问答词、意图场景词四个工作表。默认样例只提供“德州拓晟通风设备有限公司”名称，用于证明系统能在资料不足时保留完整结构、标记缺失，而不会虚构产品、资质、案例和客户。

## 质量边界

- 所有缺失事实使用 `【需企业提供真实佐证】`。
- 场景词必须具有用户需求、搜索意图和对应画像。
- EEAT 分数是资料完整度。
- 文章生成不属于默认交付；必须由用户明确要求且绑定画像、场景词、用户意图与真实证据。
- 默认产物完成后只输出缺失清单和一个下一步问题；补充资料是否回写客户语料库必须单独确认。
