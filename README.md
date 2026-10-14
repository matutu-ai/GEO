# GEO：企业 GEO 优化执行系统

GEO 的当前主交付是：基于已确认事实和上游处方，生成四类关键词和固定九大画像；默认一份交付，不要求客户逐阶段参与校验。

GEO-BD 决定：
“为什么要优化、优先优化什么”

GEO 决定：
“具体怎么优化、生成什么、如何执行”

## 当前主线：四类关键词与九大画像

GEO-BD 是企业 GEO 诊断与处方系统，负责“事实 → 证据 → 指标 → 判断 → 根因 → 处方”。GEO 当前负责“处方 / 已确认事实 → 关键词 → 九大画像”。内容、信源、发布和复测暂不作为主交付。

两个仓库必须独立运行和交付，不共享业务模块、Pipeline 或内部领域对象，不直接调用对方 Engine，也不允许隐式跨仓库依赖。唯一协作方式是版本化 JSON 数据交换：

| 方向 | Contract | Schema |
| --- | --- | --- |
| GEO-BD → GEO | Prescription Handoff V1 | `schemas/geo-bd-handoff-v1.schema.json` |
| GEO 内部 | Execution Strategy V1 | `schemas/geo-strategy-v1.schema.json` |
| GEO → GEO-BD | Retest Request V1 | `schemas/geo-retest-request-v1.schema.json` |

Prescription 是上游只读对象。GEO 可以读取处方并生成 Strategy，但不能修改处方原文、Root Cause、Priority、Judgment 或 Diagnostic Score。每个 Strategy 必须引用至少一个已存在的 `prescription_id`。

GEO 支持两种标准输入：GEO-BD Prescription Handoff + Confirmed Company Facts，或 Manual Prescription + Confirmed Company Facts。Manual Prescription 使用与 GEO-BD Handoff 完全相同的 Prescription 对象结构、`source_system: "MANUAL"`，且同样不能跳过 Strategy 层。

完整边界、引用链和禁用字段见 [阶段 0 系统边界](docs/phase-0-system-boundaries.md)；运行时流程见 [关键词与九大画像路径](workflows/standard_path.md)。

## 当前 V4 状态

当前八阶段实现是 **Legacy-compatible V4 execution path**：

```text
fact_normalization
→ company_intelligence
→ product_intelligence
→ intent_intelligence
→ persona_intelligence
→ trust_intelligence
→ keyword_intelligence
→ geo_report
```

它仍保留为 Legacy-compatible V4，不替换现有 10 个 V4 输出，也不重构 `core/fixed_pipeline.py`。新的 `standard` 模式是关键词与九大画像主路径，不会静默回退到 Legacy。

当前 Trust Score 只表示资料完整度 / Evidence Readiness，不是 GEO 总分、AI 推荐概率、企业真实权威度或最终 EEAT 分数。当前 GEO Report 只汇总执行结果，不得重新诊断或覆盖 GEO-BD 结论。

## 运行 Legacy-compatible V4

资料不足时默认进入交互暂停状态：

```bash
python3 main.py
```

用户明确要求一次完成且资料满足现有 V4 契约时：

```bash
python3 main.py --mode fast_path --input tests/fixtures/complete-v4-company.json --output output
```

## 运行关键词与九大画像主路径

```bash
python3 main.py --mode standard \
  --handoff tests/fixtures/geo-bd-handoff-v1.json \
  --input tests/fixtures/complete-v4-company.json \
  --output output-standard
```

Standard Path CLI 只输出一份用于 GEO 训练与运营的文件：

- `GEO 业务词根与画像.md`：输入摘要与事实状态、六类词根及来源、四类关键词及词根关联、核心业务词根画像卡、固定九大画像、集中确认问题及一条下一步建议。

结构化关键词、画像和事实引用仍在运行时校验；默认不另行导出 JSON、Excel 和审计目录。文档供 GEO 语料与内容运营使用，不代表直接微调模型或保证推荐结果。

默认一次收集企业/品牌与主营业务、产品/服务、定位、目标客户、使用场景。缺失核心事实时一次合并追问。输出模式为完整模式（默认）、仅词模式或仅画像模式；垂直业务是完整模式内的业务范围选择。

可选的 `geo_preferences` 记录输出模式、地区许可与客户词，不改变固定 Pipeline。每类最多 12 词；业务/场景/需求根不带地区，搜索词和问答词默认不带地区，只有明确许可时意图场景词可带已确认地区：

```json
{
  "geo_preferences": {
    "output_mode": "完整模式",
    "primary_objective": "业务获客",
    "vertical_business": "",
    "include_region_in_intent": false,
    "requested_keywords": [],
    "excluded_keywords": [],
    "approved_keywords": [],
    "user_personas": []
  }
}
```

选词逻辑：客户确认事实限定业务边界；搜索词覆盖场景中找服务，问答词覆盖比较/判断/选择，意图场景词覆盖明确任务/需求。首轮训练优先品牌词和搜索词。系统推荐词是候选表达而非平台实测热词；默认不抓取外部平台。外部研究须经用户明确要求，并记录原句、来源和日期；当前 Standard 合同不承载平台来源字段，不得将外部观察伪装成 CLI 已采集数据。

导出规则：完整模式包含词根、四类词、核心词根画像卡和九大画像；仅词模式完全不输出画像；仅画像模式完全不输出词。客户原词与系统建议分开，推荐不等于客户批准。交付结尾只给一条下一步建议。

## 验证

```bash
python3 -m pip install -r requirements.txt
python3 tests/run_tests.py
```

该命令验证 Standard Path、现有 V4、Fail Closed、Traceability、原 25 项协议测试、阶段 0 Contract 测试和阶段 1 测试。
