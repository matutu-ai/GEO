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

- `GEO训练与运营词画像.md`：四类关键词及其训练用途、九大画像及其运营价值，并保留确认状态和待补资料。

结构化关键词、画像和事实引用仍在运行时校验；默认不另行导出 JSON、Excel 和审计目录。文档供 GEO 语料与内容运营使用，不代表直接微调模型或保证推荐结果。

默认采用快速交互：一次收集企业/品牌、产品或服务、定位、目标客户与场景、业务目标和画像版本；关键词可选填。资料完整时直接生成，只在关键事实缺失或冲突会改变结论时合并追问一次，不做逐阶段、逐词或逐画像确认。

画像版本为简约版、完整版或指定单一业务的垂直完整版。简约版每项画像写核心事实；完整版与垂直完整版每项画像目标为 800–1000 个中文字，资料不足时标记待补，不凑字数、不编造。**当前 CLI 渲染器只输出精简画像表**；长版由 Skill 基于确认资料与校验后的事实组织，不能将 CLI 结果误称为长版。

可选的 `geo_preferences` 用于记录客户选择，不改变固定 Pipeline。垂直完整版以 `delivery_mode: "完整版"` 加 `vertical_business` 表示；当前 CLI 仍固定渲染精简画像表：

```json
{
  "geo_preferences": {
    "delivery_mode": "简约版",
    "primary_objective": "业务获客",
    "vertical_business": "",
    "requested_keywords": [],
    "excluded_keywords": [],
    "approved_keywords": [],
    "user_personas": []
  }
}
```

导出规则：四类词分开呈现，区分客户提出、系统推荐和待确认状态；推荐不等于客户批准。交付结尾只给一条下一步 GEO 运营建议。内容发布和平台验证不进入默认主交付。

## 验证

```bash
python3 -m pip install -r requirements.txt
python3 tests/run_tests.py
```

该命令验证 Standard Path、现有 V4、Fail Closed、Traceability、原 25 项协议测试、阶段 0 Contract 测试和阶段 1 测试。
