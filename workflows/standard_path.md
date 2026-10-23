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

报告只使用 `templates/delivery.md`，与独立 Skill 的模板相同。四类词固定两列：推荐词、短词根；训练用途放在每类标题下面。角色、业务线、来源和确认状态保留在内部合同。选定后的九大画像固定九项，默认完整版每项800–1000字。结尾只有待补资料和一条下一步建议。程序导出前自动调用一次 `scripts/check_delivery.py` 检查结构和字数，不重复要求用户确认。

选词含义与边界统一见 `references/keyword-rules.md`。系统建议不是平台实测词；客户原词保持原文，不适合本轮业务或含地区的原词保留在内部并说明未纳入推荐。自然词句随客户资料变化，表头与章节顺序不变。内容、信源、发布和复测不属于当前主交付。

主交付只保留一份人类可读结果。结构化产物完成校验和引用检查后，不再默认导出 JSON、Excel 或 `audit/`。

默认交互先选词再画像：一次收集企业/品牌、产品或服务、定位、目标客户与场景，首轮只给候选词。用户一次回复所选词与品牌/业务画像范围，再生成画像；已有明确选择则直接进入第二阶段。关键事实缺口集中追问，不逐词、逐画像反复确认。

输出模式只有三种：仅词模式（初次默认）、仅画像模式（选定后使用）、完整模式（选定后明确要求合并导出）。画像默认完整版，简约版只显式选择时使用。仅词模式不输出九大画像，内部只作事实映射；仅画像模式不输出词表但记录已选词；完整模式只列已选词。品牌画像与指定业务画像固定九项，每项800–1000字。

五项输入为企业/品牌及主营业务、产品/服务、定位、目标客户、主要使用场景；缺失时一次合并追问。短词根通常 3–10 字；每条词内部同时记录搜索角色、业务线、场景、地区、来源、确认状态和关联画像。多业务按已确认核心度排列，按资料明确关联后分别生成四类候选；词数动态决定，不设条数上限或最低数，资料少时少给并标缺口，不用相似句凑数。搜索词不得带地区，问答词默认不带地区；明确允许时才可在意图场景词使用已确认地区。

可选输入放在企业 JSON 的 `geo_preferences` 中：

```json
{
  "geo_preferences": {
    "output_mode": "仅词模式",
    "delivery_mode": "完整版",
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

用户选定后，`approved_keywords` 填写推荐词原文，`output_mode` 改为仅画像模式；`vertical_business` 为空表示品牌画像，非空必须是一条确认业务。跨轮用 `requested_keywords` 保存所选条目的原文、类型、短词根和业务线。程序拒绝未知、已排除、禁用地区或业务不符的已选词；用户仅提供候选词不是批准。

推荐表外的客户词通过`requested_keywords`加入，不要求首轮系统推荐过。先由Skill核对语义与事实适配，补齐类型、词根、意向及业务线，再由程序校验；明确选择后写`approved_keywords`。未知词提示先接入补词，不自动批准；原词和优化候选分别记录。

当 `user_personas` 未提供时，系统只根据已确认目标客户生成内部搜索角色草案，不把行业推断当作已确认画像。第二阶段完整版要求 `complete_personas` 提供固定九项的已确认正文，或九项事实映射本身均满足800–1000字；CLI不调用模型展开长文，缺少资料停止交付，不凑字数。
