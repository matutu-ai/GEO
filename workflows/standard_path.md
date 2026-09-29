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
→ user_persona_strategy
→ guidance_projection
→ execution_projection
```

Prescription Intake 只读保存 `diagnostic_id`、`company_id` 和 Prescription。Strategy 只能说明“如何执行 Prescription”，不能重新判断处方是否正确。Company / Product 仅提供执行背景。

每个 Intent 必须引用 Strategy 和 Prescription；每个 Keyword 必须引用 `intent_ids`、`strategy_ids`、`prescription_ids`、`fact_ids`；每个 Persona Unit 必须引用 `strategy_ids`、`prescription_ids`、`fact_ids`。无效引用直接 Fail Closed。

Standard Path 对外主输出：

```text
GEO训练与运营词画像.md
```

关键词按品牌词、搜索词、问答词、意图场景词四类输出，并直接说明各类词的训练用途。`keyword_origin` 与 `decision_status` 区分客户提出、系统推荐和已确认状态。九大画像按固定顺序输出已有资料及其运营价值；未知内容标记待补。文件末尾只保留一条下一步 GEO 运营方向。内容、信源、发布和复测不属于当前主交付。

主交付只保留一份人类可读结果。结构化产物完成校验和引用检查后，不再默认导出 JSON、Excel 或 `audit/`。

默认交互采用快速模式：一次收集企业、产品/服务、目标客户、想做的词和业务目标；直接生成一份训练运营建议稿。未确认的词和资料保留状态提示，不用选择表阻塞结果。

可选输入放在企业 JSON 的 `geo_preferences` 中：

```json
{
  "geo_preferences": {
    "delivery_mode": "完整版",
    "primary_objective": "业务获客",
    "requested_keywords": [],
    "excluded_keywords": [],
    "approved_keywords": [],
    "user_personas": []
  }
}
```

当 `user_personas` 未提供时，系统只根据已确认目标客户生成待确认草案，不把行业推断当作已确认画像。
