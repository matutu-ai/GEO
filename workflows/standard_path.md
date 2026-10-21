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

关键词、内部搜索角色卡和执行投影合同版本为 `1.1.0`；新增字段属于显式合同变更，旧消费者必须按版本适配，不能静默忽略。

Standard Path 对外主输出：

```text
GEO 关键词与画像.md
```

报告按品牌词、搜索词、问答词、意图场景词四类输出推荐词、短词根、意向等级、搜索角色、训练用途和确认状态，再输出固定九大画像。搜索词表达“在场景中找服务”，问答词表达“比较、判断或选择”，意图场景词表达“明确动作/任务＋场景＋业务”；首轮训练优先品牌词和搜索词。`keyword_origin` 与 `decision_status` 区分客户提出、系统推荐和已确认状态。系统推荐是按确认资料生成的候选，不是平台实测词。默认不调用外部搜索；明确授权外部研究时须保留原句、平台/页面来源和采集日期。短词根和搜索角色卡仅作内部生成依据，不独立输出。九大画像简约版缺项标待补；完整版九项每项 800–1000 字，不合规则阻止导出。最后只保留一条下一步 GEO 运营方向。内容、信源、发布和复测不属于当前主交付。

主交付只保留一份人类可读结果。结构化产物完成校验和引用检查后，不再默认导出 JSON、Excel 或 `audit/`。

默认交互采用快速模式：一次收集企业/品牌、产品或服务、定位、目标客户与场景、可选关键词、业务目标和交付版本。资料完整时直接生成；只有关键事实缺失或冲突会改变结论时，才合并追问一次。不得逐阶段、逐词或逐画像反复要求确认。

输出模式只有三种：完整模式（默认）、仅词模式、仅画像模式。仅词模式不得输出九大画像；仅画像模式不得输出四类关键词。画像详略为简约版（默认）或完整版；垂直业务限定到已确认的一个主营业务。品牌画像与业务画像都固定九项；完整版据已确认事实呈现并严格执行每项 800–1000 字。

五项输入为企业/品牌及主营业务、产品/服务、定位、目标客户、主要使用场景；缺失时一次合并追问。内部短词根通常 3–10 字；每条词同时记录意向等级、搜索角色、业务线、场景、地区、来源、确认状态和关联画像。默认每类推荐 3–5 条，最多 12 条。搜索词和问答词默认不带地区；明确允许时才可在意图场景词使用已确认地区。

可选输入放在企业 JSON 的 `geo_preferences` 中：

```json
{
  "geo_preferences": {
    "output_mode": "完整模式",
    "delivery_mode": "简约版",
    "primary_objective": "业务获客",
    "vertical_business": "",
    "include_region_in_intent": false,
    "requested_keywords": [],
    "excluded_keywords": [],
    "approved_keywords": [],
    "user_personas": [],
    "complete_personas": {}
  }
}
```

当 `user_personas` 未提供时，系统只根据已确认目标客户生成内部搜索角色草案，不把行业推断当作已确认画像。选择完整版时，`complete_personas` 必须提供固定九项的已确认正文，或九项事实映射本身均满足 800–1000 字。
