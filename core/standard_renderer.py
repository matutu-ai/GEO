"""Render the same bundled delivery template used by the standalone Skill."""

import re

from core.keyword_terms import confirmed_region_terms
from scripts.check_delivery import delivery_template, validate_delivery


STANDARD_OUTPUTS = ("GEO 关键词与画像.md",)
KEYWORD_SLOTS = {
    "品牌词": "brand_rows", "搜索词": "search_rows",
    "问答词": "question_rows", "意图场景词": "intent_rows",
}


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


def _persona_summary(persona, full=False):
    if persona["status"] != "READY":
        return "待补：需企业提供真实佐证。"
    if full:
        return "；".join(persona["confirmed_content"])
    fragments = [
        part.strip() for value in persona["confirmed_content"]
        for part in value.split("；") if part.strip()
    ]
    return "；".join(fragments[:2]) or "待补：需企业提供真实佐证。"


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
    businesses = values["main_businesses"]
    businesses = businesses if isinstance(businesses, list) else [businesses]
    selected = guidance["vertical_business"]
    if selected not in businesses:
        raise ValueError("STANDARD_RENDER-002: vertical business must match a confirmed main business")
    vertical = selected if context["vertical_business_requested"] else ""
    output_mode = context.get("output_mode", "仅词模式")
    delivery_mode = guidance["delivery_mode"]
    template = delivery_template(output_mode)
    regions = confirmed_region_terms(sources.get("service_regions", {}).get("value", []))
    excluded = set(guidance["keyword_review"]["excluded"])
    approved = guidance["keyword_review"]["approved"]
    if output_mode != "仅词模式" and not approved:
        raise ValueError("STANDARD_RENDER-005: 生成画像前须选定关键词")
    keywords, notes = [], []
    if output_mode != "仅画像模式":
        for item in artifacts["keyword_matrix"]["keywords"]:
            if output_mode == "完整模式" and item["keyword"] not in approved:
                continue
            if item["keyword"] in excluded:
                continue
            if output_mode != "仅词模式" and vertical and item["business_line"] != selected:
                notes.append(f"另属业务线，待单独整理：{_cell(item['keyword'])}")
                continue
            if item["keyword_type"] in ("搜索词", "问答词") and any(term in item["keyword"] for term in regions):
                notes.append(f"含地区的原词保留在内部记录，未纳入推荐：{_cell(item['keyword'])}")
                continue
            keywords.append(item)

    slots = {
        "company": _cell(company),
        "summary": "\n".join([
            f"- 主体：{_cell(company)}；主营业务：{_cell(vertical or _text(businesses))}。",
            f"- 本轮选词业务：{_cell(selected)}；定位：{_cell(values['positioning'])}。",
            f"- 目标客户：{_cell('待核对指定业务人群' if vertical else _text(values['target_customers']))}；产品/服务：{_cell('待核对指定业务产品' if vertical else _text(artifacts['product_context']['products']))}。",
            f"- 输出模式：{output_mode}。",
        ]),
        "keyword_note": (
            "本轮候选词，等待选择；推荐不代表平台热度或 AI 推荐结果。"
            if output_mode == "仅词模式" else "以下仅列本轮已选词；推荐不代表平台热度或 AI 推荐结果。"
        ),
        "profile_scope": f"业务画像｜{_cell(vertical)}" if vertical else "品牌画像",
        "delivery_mode": delivery_mode,
        "selected_terms": "；".join(_cell(word) for word in approved),
        "next_step": _cell(guidance["next_prompt"]),
    }
    for kind, slot in KEYWORD_SLOTS.items():
        typed_keywords = [item for item in keywords if item["keyword_type"] == kind]
        group_count = len({item["business_line"] for item in typed_keywords})
        rows, previous_business = [], None
        for item in typed_keywords:
            if group_count > 1 and item["business_line"] != previous_business:
                rows.append(f"| **业务：{_cell(item['business_line'])}** | — |")
                previous_business = item["business_line"]
            rows.append(f"| {_cell(item['keyword'])} | {_cell(item['root_phrase'])} |")
        slots[slot] = "\n".join(rows) or ("| 本轮未选 | — |" if output_mode == "完整模式" else "| 待补 | — |")
    if output_mode == "仅词模式":
        first_by_type = {
            kind: next((item["keyword"] for item in keywords if item["keyword_type"] == kind), "")
            for kind in KEYWORD_SLOTS
        }
        combination = [
            f"{kind}：{first_by_type[kind]}" for kind in KEYWORD_SLOTS if first_by_type[kind]
        ]
        if combination:
            slots["keyword_note"] += (
                "\n\n建议训练组合（同一业务，可自行增删）："
                + "；".join(combination)
                + "。请按本轮目标选词；未明确选择的候选词不会进入画像。"
            )
    if output_mode != "仅词模式":
        profile_template = template.split("## 九大画像\n", 1)[1].split("## 待补资料", 1)[0]
        names = re.findall(r"^### (.+)$", profile_template, re.M)
        personas = artifacts["persona_plan"]["personas"]
        by_name = {item["name"]: item for item in personas}
        if len(personas) != len(names) or set(by_name) != set(names):
            raise ValueError("STANDARD_RENDER-004: persona names must match the fixed nine sections")
        for index, name in enumerate(names, start=1):
            persona = by_name[name]
            uncertain_vertical = bool(vertical) and delivery_mode == "简约版"
            summary = (
                "【需确认本板块资料与指定业务的关联】"
                if uncertain_vertical else _persona_summary(persona, delivery_mode == "完整版")
            )
            slots[f"persona_{index}"] = _cell(summary)
            if uncertain_vertical or persona["status"] != "READY":
                notes.append(f"{persona['name']}：待补对应业务的已确认资料。")
    slots["missing"] = "\n".join(f"- {note}" for note in dict.fromkeys(notes)) or "暂无待补资料。"
    report = re.sub(r"\{\{(\w+)\}\}", lambda match: slots[match[1]], template)
    validate_delivery(report, output_mode, delivery_mode)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / STANDARD_OUTPUTS[0]).write_text(report, encoding="utf-8")
