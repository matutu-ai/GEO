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
GEO 业务词根与画像.md
```

报告先列品牌、业务、定位、人群、场景、需求六类词根及来源事实，再按品牌词、搜索词、问答词、意图场景词四类输出推荐词、词根关联、训练用途和对应的核心业务词根画像卡。搜索词表达“在场景中找服务”，问答词表达“比较、判断或选择”，意图场景词表达“明确任务/需求”；首轮训练优先品牌词和搜索词。`keyword_origin` 与 `decision_status` 区分客户提出、系统推荐和已确认状态。系统推荐是按确认资料生成的候选，不是平台实测词。默认不调用外部搜索；明确授权外部研究时须保留原句、平台/页面来源和采集日期，但当前 JSON 合同不承载平台来源，不能在默认 CLI 中声称已完成平台抓词。每个核心业务根一张卡；九大画像按固定顺序汇总已有资料、词根关联和运营价值；未知内容标记待补。最后集中列出待确认问题，只保留一条下一步 GEO 运营方向。内容、信源、发布和复测不属于当前主交付。

主交付只保留一份人类可读结果。结构化产物完成校验和引用检查后，不再默认导出 JSON、Excel 或 `audit/`。

默认交互采用快速模式：一次收集企业/品牌、产品或服务、定位、目标客户与场景、可选关键词、业务目标和交付版本。资料完整时直接生成；只有关键事实缺失或冲突会改变结论时，才合并追问一次。不得逐阶段、逐词或逐画像反复要求确认。

输出模式只有三种：完整模式（默认）、仅词模式、仅画像模式。仅词模式不得输出画像卡或画像正文；仅画像模式不得输出词根、关键词和组合说明。垂直业务只是在完整模式内限定到已确认的一个主营业务，业务关联不足时标待补。完整画像据已确认事实呈现，资料不足不凑字数。

五项输入为企业/品牌及主营业务、产品/服务、定位、目标客户、主要使用场景；缺失时一次合并追问。词根类型固定为品牌、业务、定位、人群、场景、需求；通常 2–8 字，业务/场景/需求词根不带地区。每类关键词不超过 12 条。搜索词和问答词默认不带地区；明确允许时才可在意图场景词使用已确认地区。

可选输入放在企业 JSON 的 `geo_preferences` 中：

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

当 `user_personas` 未提供时，系统只根据已确认目标客户生成待确认草案，不把行业推断当作已确认画像。
