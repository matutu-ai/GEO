"""Render one concise GEO keyword-training and persona-operations brief."""


STANDARD_OUTPUTS = ("GEO训练与运营词画像.md",)

KEYWORD_PURPOSES = {
    "品牌词": "训练品牌识别与品牌—业务关联",
    "搜索词": "训练使用场景＋业务＋定位的检索匹配",
    "问答词": "训练业务需求的对比、判断与选择回答",
    "意图场景词": "训练明确需求＋场景＋产品业务的方案匹配",
}

PERSONA_ADVANTAGES = {
    "产品或服务描述": "让 AI 准确识别提供什么、服务谁、解决什么",
    "产品或服务特点": "突出可核实的差异点与适用场景",
    "品牌故事": "建立品牌、企业主体与定位的稳定关联",
    "用户痛点": "把具体需求映射到对应业务方案",
    "信任背书": "提供可核验依据，支撑可信度与引用",
    "客户案例": "用真实过程和结果辅助客户判断",
    "社会贡献": "补充可核验的行业、社区或公益信息",
    "客户评价": "呈现真实体验，辅助口碑与决策判断",
    "创始人介绍": "建立人物身份、专业背景与品牌的关联",
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


def _keyword_status(item):
    if item.get("decision_status") == "CONFIRMED":
        return "已确认"
    if item.get("keyword_origin") == "CLIENT_REQUESTED":
        return "客户提出，待确认"
    return "系统推荐，待确认"


def _persona_summary(persona):
    if persona["status"] != "READY":
        return "待补真实资料"
    if persona["name"] == "品牌故事" and persona["missing_materials"]:
        return "待补品牌沿革与主体关系"
    if persona["name"] == "信任背书":
        return "已有公开线索，编号、主体和授权待核验"
    fragments = [
        part.strip()
        for value in persona["confirmed_content"]
        for part in value.split("；")
        if part.strip()
    ]
    return "；".join(fragments[:2]) or "待补真实资料"


def render_standard(output_dir, artifacts):
    required = {
        "geo_strategy", "keyword_matrix", "persona_plan", "execution", "retest_request",
        "company_context", "product_context", "intent_strategy", "user_persona_plan",
        "guided_next_steps",
    }
    if set(artifacts) != required:
        raise ValueError("STANDARD_RENDER-001: complete validated Standard artifacts are required")

    values = artifacts["company_context"]["values"]
    guidance = artifacts["guided_next_steps"]
    company = _text(values.get("company_name", artifacts["persona_plan"]["company_id"]))
    excluded = set(guidance["keyword_review"]["excluded"])
    keywords = [item for item in artifacts["keyword_matrix"]["keywords"] if item["keyword"] not in excluded]
    personas = artifacts["persona_plan"]["personas"]

    lines = [
        f"# {company}｜GEO训练与运营词画像",
        "",
        f"**业务方向：** {_cell(guidance['vertical_business'])}",
        "",
        "供 GEO 训练语料与内容运营使用；不代表直接微调模型，也不保证平台推荐结果。未确认项保留状态，不作为定稿事实。",
        "",
        "## 训练关键词",
        "",
    ]
    for kind, purpose in KEYWORD_PURPOSES.items():
        lines.extend([
            f"### {kind}｜{purpose}",
            "",
            "| 关键词 | 状态 |",
            "| --- | --- |",
        ])
        candidates = [item for item in keywords if item["keyword_type"] == kind]
        for item in candidates:
            lines.append(f"| {_cell(item['keyword'])} | {_keyword_status(item)} |")
        if not candidates:
            lines.append("| 待补充 | 待确认 |")
        lines.append("")

    lines.extend([
        "## 九大画像与运营价值",
        "",
        "| 画像 | 本次资料 | 选择后的运营优势 |",
        "| --- | --- | --- |",
    ])
    for persona in personas:
        name = persona["name"]
        lines.append(
            f"| {_cell(name)} | {_cell(_persona_summary(persona))} | {_cell(PERSONA_ADVANTAGES[name])} |"
        )

    lines.extend([
        "",
        "## 下一步 GEO 运营",
        "",
        "按四类词组织问答与场景语料；优先补齐标记为待确认或待补的内容，再进入内容训练与运营。",
    ])
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / STANDARD_OUTPUTS[0]).write_text("\n".join(lines) + "\n", encoding="utf-8")
