"""Render one traceable GEO root, keyword and persona report."""

from core.keyword_terms import compact_keyword_root, confirmed_region_terms


STANDARD_OUTPUTS = ("GEO 业务词根与画像.md",)
KEYWORD_PURPOSES = {
    "品牌词": "训练品牌识别及品牌—业务—主体关联",
    "搜索词": "训练使用场景＋业务＋定位的检索匹配",
    "问答词": "训练业务需求的对比、判断与选择回答",
    "意图场景词": "训练明确需求＋场景＋产品业务的方案匹配",
}
KEYWORD_SHORT_PURPOSES = {
    "品牌词": "品牌关联", "搜索词": "场景检索", "问答词": "对比决策", "意图场景词": "需求匹配",
}
ROOT_FIELDS = {
    "company_name": "品牌根", "main_businesses": "业务根", "positioning": "定位根",
    "target_customers": "人群根", "use_cases": "场景根", "user_pain_points": "需求根",
}
PERSONA_ADVANTAGES = {
    "产品或服务描述": "识别提供什么、服务谁、解决什么",
    "产品或服务特点": "呈现可核实的差异点与适用场景",
    "品牌故事": "关联品牌、企业主体与定位",
    "用户痛点": "把需求映射到对应业务方案",
    "信任背书": "以可核验证据支撑可信度",
    "客户案例": "以真实过程和结果辅助判断",
    "社会贡献": "补充可核实的社会价值信息",
    "客户评价": "呈现真实体验，辅助决策",
    "创始人介绍": "关联人物身份、专业背景与品牌",
}
MAPPED_PERSONAS = ("产品或服务描述", "产品或服务特点", "品牌故事", "用户痛点")


def _text(value):
    if isinstance(value, list):
        return "；".join(_text(item) for item in value if item not in (None, ""))
    if isinstance(value, dict):
        for key in ("name", "title", "keyword"):
            if value.get(key):
                return str(value[key])
    return str(value)


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _short_root(value):
    text = str(value).strip()
    return text if 2 <= len(text) <= 8 else "—"


def _keyword_root(item, business):
    """Compatibility helper for a short query cue; never truncates a client term."""
    if item.get("keyword_origin") == "CLIENT_REQUESTED":
        for value in (item["keyword"], item["user_scenario"], item["search_intent"]):
            root = _short_root(value)
            if root != "—":
                return root
        return "—"
    if item["keyword_type"] == "搜索词":
        return _short_root(business)
    if item["keyword_type"] == "问答词":
        combined = _short_root(f"{business}怎么选")
        return combined if combined != "—" else "怎么选"
    return _short_root(item["user_scenario"])


def _keyword_status(item):
    if item.get("decision_status") == "CONFIRMED":
        return "已确认"
    if item.get("keyword_origin") == "CLIENT_REQUESTED":
        return "客户提出，待确认"
    return "系统推荐，待确认"


def _fact_status(status):
    return {"CONFIRMED": "已确认", "INFERRED": "【基于现有资料推断，未经企业确认】",
            "UNKNOWN": "【需企业提供真实佐证】", "CONFLICTED": "【资料存在冲突，需人工确认】"}.get(status, "待核验")


def _persona_summary(persona, full=False):
    if persona["status"] != "READY":
        return "【需企业提供真实佐证】"
    fragments = [
        part.strip() for value in persona["confirmed_content"]
        for part in value.split("；") if part.strip()
    ]
    return "；".join(fragments if full else fragments[:2]) or "【需企业提供真实佐证】"


def _items(value):
    return value if isinstance(value, list) else [value]


def _root_cue(value, region_terms=()):
    return compact_keyword_root(_text(value).strip(), region_terms)


def _brand_cue(source_facts):
    businesses = _items(source_facts["main_businesses"]["value"])
    if len(businesses) > 1:
        common = str(businesses[0])
        for business in businesses[1:]:
            while common and not str(business).startswith(common):
                common = common[:-1]
        if 2 <= len(common) <= 10:
            return common, source_facts["main_businesses"]
    fact = source_facts["company_name"]
    return _root_cue(fact["value"]) or _text(fact["value"]), fact


def _roots(source_facts, vertical_business):
    roots, seen = [], set()
    regions = confirmed_region_terms(source_facts.get("service_regions", {}).get("value", []))
    for field, kind in ROOT_FIELDS.items():
        fact = source_facts[field]
        if vertical_business and field not in ("company_name", "main_businesses", "positioning"):
            continue
        if fact["status"] != "CONFIRMED":
            continue
        values = [_brand_cue(source_facts)[0]] if field == "company_name" else _items(fact["value"])
        if field == "use_cases":
            values = [value for value in values if not _text(value).strip().startswith(
                ("考察", "申请", "寻找", "准备", "核验", "评估", "判断", "选择", "了解", "对比")
            )]
        if field == "company_name":
            fact = _brand_cue(source_facts)[1]
        for value in values:
            if field in ("main_businesses", "use_cases", "user_pain_points"):
                root = _text(value).strip() if field == "main_businesses" else _root_cue(value, regions)
            else:
                root = _root_cue(value)
            if not root or (field == "main_businesses" and vertical_business and root != vertical_business):
                continue
            key = (kind, root.replace(" ", "").lower())
            if key in seen:
                continue
            seen.add(key)
            roots.append({"name": root, "type": kind, "fact_id": fact["fact_id"],
                          "field": fact["field"], "core": kind == "业务根"})
    return roots


def _matched_user(business, user_personas):
    for token in ("招商加盟", "区域代理", "渠道合作", "加盟", "代理", "渠道"):
        if token not in business:
            continue
        for persona in user_personas:
            context = "；".join([persona["name"], persona["scenario"], *persona["query_patterns"]])
            if token in context:
                return persona
    return None


def _linked_roots(item, roots):
    linked = []
    linked_names = set()
    for root in roots:
        if root["name"] in item["keyword"] and root["name"] not in linked_names:
            linked.append(root)
            linked_names.add(root["name"])
    core = next((root for root in linked if root["core"]), None)
    if core:
        return linked, core, False
    for token in ("区域代理", "招商加盟", "渠道合作", "加盟", "代理", "渠道"):
        if token in item["keyword"]:
            candidates = [root for root in roots if root["core"] and token in root["name"]]
            if len(candidates) == 1:
                return linked, candidates[0], True
    return linked, None, False


def _questions(business):
    return (f"{business}适合哪些客户？", f"{business}怎么选？", f"{business}与其他方案如何比较？")


def render_standard(output_dir, artifacts):
    required = {
        "geo_strategy", "keyword_matrix", "persona_plan", "execution", "retest_request",
        "company_context", "product_context", "intent_strategy", "user_persona_plan",
        "guided_next_steps",
    }
    if set(artifacts) != required:
        raise ValueError("STANDARD_RENDER-001: complete validated Standard artifacts are required")

    context = artifacts["company_context"]
    values, sources = context["values"], context["source_facts"]
    guidance = artifacts["guided_next_steps"]
    company = _text(values["company_name"])
    businesses = _items(values["main_businesses"])
    selected = guidance["vertical_business"]
    if selected not in businesses:
        raise ValueError("STANDARD_RENDER-002: vertical business must match a confirmed main business")
    vertical = selected if context["vertical_business_requested"] and len(businesses) > 1 else ""
    roots = _roots(sources, vertical)
    core_roots = [root for root in roots if root["core"]]
    excluded = set(guidance["keyword_review"]["excluded"])
    keywords = [item for item in artifacts["keyword_matrix"]["keywords"] if item["keyword"] not in excluded]
    if vertical:
        keywords = [item for item in keywords if vertical in item["keyword"] or item["keyword"] == company]
    personas = artifacts["persona_plan"]["personas"]
    user_personas = artifacts["user_persona_plan"]["personas"]
    primary_user = user_personas[0] if user_personas and len(core_roots) == 1 and not vertical else None
    output_mode = context.get("output_mode", "完整模式")
    if output_mode not in ("完整模式", "仅词模式", "仅画像模式"):
        raise ValueError("STANDARD_RENDER-003: unsupported output mode")
    regions = confirmed_region_terms(sources.get("service_regions", {}).get("value", []))
    lines = [
        f"# {company}｜GEO 词与画像", "", "## 客户资料摘要", "",
        f"- 主体：{_cell(company)}；业务：{_cell(vertical or _text(businesses))}；定位：{_cell(values['positioning'])}",
        f"- 目标客户：{_cell('待核对指定业务人群' if vertical else _text(values['target_customers']))}；产品/服务：{_cell('待核对指定业务产品' if vertical else _text(artifacts['product_context']['products']))}",
        "- 事实仅取自客户已确认资料；缺失信息标注待补；推荐词为候选表达，不代表平台热度或 AI 推荐结果。", "",
    ]

    if output_mode != "仅画像模式":
        lines.extend(["## 六类词根", "", "| 词根 | 类型 | 来源事实 | 状态 |",
                      "| --- | --- | --- | --- |"])
        for root in roots:
            length_note = "；原词超 8 字，建议确认简称" if len(root["name"]) > 8 else ""
            lines.append(f"| {_cell(root['name'])} | {root['type']} | {_cell(root['field'])} / {root['fact_id']} | 来源事实已确认；词根建议待确认{length_note} |")
        missing_types = set(ROOT_FIELDS.values()) - {root["type"] for root in roots}
        for kind in ROOT_FIELDS.values():
            if kind in missing_types:
                field = next(field for field, root_type in ROOT_FIELDS.items() if root_type == kind)
                fact = sources[field]
                lines.append(f"| 待补 | {kind} | {field} / {fact['fact_id']} | {_fact_status(fact['status'])} |")
        lines.extend(["", "## 四类关键词", "",
                      "品牌词练品牌识别，搜索词练场景匹配，问答词练决策回答，意图场景词练需求匹配。系统建议不是平台实测热搜词。", ""])
        for kind, purpose in KEYWORD_PURPOSES.items():
            lines.extend([f"### {kind}｜{purpose}", "", "| 推荐词 | 组成词根 | 训练用途 | 状态 |",
                          "| --- | --- | --- | --- |"])
            candidates = [item for item in keywords if item["keyword_type"] == kind]
            for item in candidates:
                linked, core, tentative = _linked_roots(item, roots)
                root_names = "＋".join(root["name"] for root in linked) or "待核对"
                status = _keyword_status(item)
                if item["keyword_origin"] == "CLIENT_REQUESTED" and kind in ("搜索词", "问答词") and any(term in item["keyword"] for term in regions):
                    status += "；含地区，默认不纳入推荐"
                lines.append(f"| {_cell(item['keyword'])} | {_cell(root_names)} | {_cell(KEYWORD_SHORT_PURPOSES[kind])} | {_cell(status)} |")
            if not candidates:
                lines.append(f"| 待补 | — | {_cell(purpose)} | 待确认 |")
            lines.append("")

    if output_mode != "仅词模式":
        if output_mode == "完整模式":
            lines.extend(["## 核心词根画像卡", ""])
            for root in core_roots:
                name = root["name"]
                matched = primary_user or _matched_user(name, user_personas)
                audience = _text(matched["audience"]) if matched else "待确认"
                scenario = _text(matched["scenario"]) if matched else "待确认"
                pain = _text(matched["pain_points"]) if matched and matched["pain_points"] else "待补"
                criteria = _text(matched["decision_criteria"]) if matched and matched["decision_criteria"] else "待确认"
                stage = matched["decision_stage"] if matched else "待确认"
                questions = matched["query_patterns"][:5] if matched else _questions(name)
                lines.extend([f"### {name}", "", f"主体：{_cell(company)}；业务：{_cell(name)}；目标人群：{_cell(audience)}。",
                              f"场景：{_cell(scenario)}；痛点：{_cell(pain)}；决策标准：{_cell(criteria)}；阶段：{_cell(stage)}。",
                              "建议问题：" + "；".join(_cell(q) for q in questions), ""])
        lines.extend(["## 九大画像", ""])
        for persona in personas:
            name = persona["name"]
            summary = "【需确认本板块资料与指定业务的关联】" if vertical else _persona_summary(persona, full=True)
            lines.extend([f"### {name}", "", _cell(summary), ""])
        if output_mode == "完整模式":
            missing = [persona["name"] for persona in personas if persona["status"] != "READY"]
            lines.extend(["## 待补画像", "", "、".join(missing) if missing else "暂无待补画像。", ""])
    lines.extend(["## 下一步建议", "", _cell(guidance["next_prompt"])])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / STANDARD_OUTPUTS[0]).write_text("\n".join(lines) + "\n", encoding="utf-8")
