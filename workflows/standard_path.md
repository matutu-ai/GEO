# GEO 关键词与九大画像主路径 V1

Standard Path 是独立于 Legacy-compatible V4 的关键词与九大画像运行路径。入口必须同时提供 GEO-BD Handoff 或 Manual Prescription，以及 Confirmed Company Facts：

```bash
python3 main.py --mode standard \
  --handoff <handoff.json> \
  --input <company.json> \
  --output <output-dir>
```

固定顺序：

```text
handoff_validation
→ fact_normalization
→ prescription_intake
→ strategy_generation
→ company_context
→ product_context
→ intent_strategy
→ keyword_strategy
→ persona_strategy
→ execution_projection
```

Prescription Intake 只读保存 `diagnostic_id`、`company_id` 和 Prescription。Strategy 只能说明“如何执行 Prescription”，不能重新判断处方是否正确。Company / Product 仅提供执行背景。

每个 Intent 必须引用 Strategy 和 Prescription；每个 Keyword 必须引用 `intent_ids`、`strategy_ids`、`prescription_ids`、`fact_ids`；每个 Persona Unit 必须引用 `strategy_ids`、`prescription_ids`、`fact_ids`。无效引用直接 Fail Closed。

Standard Path 主输出：

```text
keyword_matrix.json
persona_plan.json
keyword_matrix.xlsx
persona_report.md
```

关键词按品牌词、搜索词、问答词、意图场景词四类输出；九大画像固定顺序并保留已确认内容、未知内容、待补材料和禁止声明。内容、信源、发布和复测不属于当前主交付。
