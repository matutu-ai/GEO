"""Render the focused Standard Path deliverables: keywords and nine personas."""

import html
import json
import zipfile


KEYWORD_TYPES = ("品牌词", "搜索词", "问答词", "意图场景词")
KEYWORD_HEADERS = [
    "关键词", "关键词类型", "产品或服务", "用户场景", "搜索意图", "对应画像",
    "事实来源", "证据状态", "风险等级", "需确认", "关键词来源", "决策状态",
]
STANDARD_OUTPUTS = (
    "01_简约版-词与画像.md",
    "02_完整版-词与画像.md",
    "03_垂直业务画像.md",
    "audit",
)


def _write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _text(value):
    if isinstance(value, list):
        return "；".join(_text(item) for item in value if item is not None and item != "")
    if isinstance(value, dict):
        for key in ("name", "title", "keyword"):
            if value.get(key):
                return str(value[key])
        return "；".join(f"{key}：{_text(item)}" for key, item in value.items() if item not in (None, "", [], {}))
    return str(value)


def _column_name(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def _xlsx_cell(reference, value):
    return f'<c r="{reference}" t="inlineStr"><is><t>{html.escape(str(value))}</t></is></c>'


def _keyword_sheet_xml(rows):
    all_rows = [KEYWORD_HEADERS] + rows
    xml_rows = []
    for row_number, values in enumerate(all_rows, start=1):
        cells = "".join(
            _xlsx_cell(f"{_column_name(index)}{row_number}", value)
            for index, value in enumerate(values, start=1)
        )
        xml_rows.append(f'<row r="{row_number}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>'
    )


def _keyword_rows(matrix):
    grouped = {kind: [] for kind in KEYWORD_TYPES}
    for item in matrix["keywords"]:
        grouped[item["keyword_type"]].append([
            item["keyword"], item["keyword_type"], item["product_or_service"],
            item["user_scenario"], item["search_intent"], item["persona_unit"],
            "；".join(item["fact_ids"]), item["evidence_status"],
            item["risk_level"], "是" if item["needs_confirmation"] else "否",
            item.get("keyword_origin", "SYSTEM_RECOMMENDED"),
            item.get("decision_status", "RECOMMENDED"),
        ])
    return grouped


def write_keyword_xlsx(path, matrix):
    grouped = _keyword_rows(matrix)
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for i in range(1, 5)
    )
    sheets = "".join(
        f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>'
        for i, name in enumerate(KEYWORD_TYPES, start=1)
    )
    relations = "".join(
        f'<Relationship Id="rId{i}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, 5)
    )
    files = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            f"{overrides}</Types>"
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="xl/workbook.xml"/></Relationships>'
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{sheets}</sheets></workbook>"
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{relations}</Relationships>"
        ),
    }
    for index, kind in enumerate(KEYWORD_TYPES, start=1):
        files[f"xl/worksheets/sheet{index}.xml"] = _keyword_sheet_xml(grouped[kind])
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"))


def write_persona_markdown(path, artifacts):
    company = artifacts["company_context"]["values"]
    company_name = _text(company.get("company_name", artifacts["persona_plan"]["company_id"]))
    lines = [
        f"# {company_name} 企业九大画像",
        "",
        f"- 企业定位：{_text(company.get('positioning', '待补充'))}",
        f"- 主营业务：{_text(company.get('main_businesses', '待补充'))}",
        f"- 目标客户：{_text(company.get('target_customers', '待补充'))}",
    ]
    for persona in artifacts["persona_plan"]["personas"]:
        lines.extend([
            "",
            f"## {persona['name']}",
            f"- 状态：{persona['status']}",
            f"- 重点内容：{'；'.join(persona['confirmed_content']) or '暂无已确认内容'}",
            f"- 未知内容：{'；'.join(persona['unknown_content']) or '无'}",
            f"- 待补材料：{'；'.join(persona['missing_materials']) or '无'}",
            f"- 禁止声明：{'；'.join(persona['forbidden_claims'])}",
            f"- 事实来源：{'；'.join(persona['fact_ids'])}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_user_persona_markdown(path, artifacts):
    company = artifacts["company_context"]["values"]
    company_name = _text(company.get("company_name", artifacts["user_persona_plan"]["company_id"]))
    plan = artifacts["user_persona_plan"]
    lines = [
        f"# {company_name} 用户决策画像",
        "",
        "本报告回答谁会搜索、为什么搜索、处于什么决策阶段，以及应覆盖哪些问题词。",
    ]
    for persona in plan["personas"]:
        lines.extend([
            "",
            f"## {persona['name']}",
            f"- 状态：{persona['status']}",
            f"- 人群：{persona['audience']}",
            f"- 场景：{persona['scenario']}",
            f"- 决策阶段：{persona['decision_stage']}",
            f"- 核心痛点：{'；'.join(persona['pain_points']) or '待补充'}",
            f"- 决策标准：{'；'.join(persona['decision_criteria']) or '待补充'}",
            f"- 典型问题：{'；'.join(persona['query_patterns'])}",
            f"- 问题词来源：{persona['query_pattern_status']}",
            f"- 对应关键词：{'；'.join(persona['keyword_ids']) or '待关键词复核'}",
            f"- 事实来源：{'；'.join(persona['fact_ids'])}",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_guidance_markdown(path, artifacts):
    guidance = artifacts["guided_next_steps"]
    lines = [
        "# GEO 下一步引导",
        "",
        f"- 交付版本：{guidance['delivery_mode']}",
        f"- 当前阶段：{guidance['current_stage']}",
        f"- 推荐下一阶段：{guidance['recommended_next_stage']}",
        f"- 下一步提示：{guidance['next_prompt']}",
        "",
        "## 每阶段提示建议",
    ]
    for stage in guidance["stages"]:
        lines.extend([
            "",
            f"### {stage['name']}",
            f"- 状态：{stage['status']}",
            f"- 提示词：{stage['prompt']}",
            f"- 建议：{stage['recommendation']}",
            f"- 是否需要用户确认：{'是' if stage['requires_user_confirmation'] else '否'}",
        ])
    lines.extend(["", "## 相关技能建议"])
    for item in guidance["skill_recommendations"]:
        lines.extend([
            "",
            f"### {item['skill']}",
            f"- 适用时机：{item['when']}",
            f"- 使用理由：{item['reason']}",
            f"- 下一步决策：{item['next_decision']}",
        ])
    lines.extend(["", "## 优化方向"])
    for item in guidance["optimization_directions"]:
        lines.extend([
            "",
            f"### {item['priority']}｜{item['title']}",
            f"- 状态：{item['status']}",
            f"- 原因：{item['reason']}",
            f"- 下一动作：{item['next_action']}",
        ])
    review = guidance["keyword_review"]
    lines.extend([
        "",
        "## 关键词复核分层",
        "",
        f"- 客户指定词：{'；'.join(review['client_requested']) or '暂无'}",
        f"- 已批准词：{'；'.join(review['approved']) or '暂无，需确认'}",
        f"- 暂不使用词：{'；'.join(review['excluded']) or '暂无'}",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_delivery_summary(path, artifacts):
    company = artifacts["company_context"]["values"]
    company_name = _text(company.get("company_name", artifacts["user_persona_plan"]["company_id"]))
    user_plan = artifacts["user_persona_plan"]
    matrix = artifacts["keyword_matrix"]["keywords"]
    guidance = artifacts["guided_next_steps"]
    grouped = {kind: [] for kind in KEYWORD_TYPES}
    for item in matrix:
        grouped[item["keyword_type"]].append(item)
    lines = [
        f"# {company_name} GEO 核心交付摘要",
        "",
        "本页是快速审阅版；完整追溯、企业九大画像和阶段提示见同目录其他文件。",
        "",
        "## 当前结果",
        "",
        f"- 用户决策画像：{len(user_plan['personas'])} 个（状态：{user_plan['personas'][0]['status']}）",
        f"- 关键词：{len(matrix)} 条",
        f"- 推荐下一步：{guidance['recommended_next_stage']}",
        f"- 下一步提示：{guidance['next_prompt']}",
        "",
        "## 关键词速览",
        "",
        "| 类型 | 数量 | 示例 |",
        "| --- | ---: | --- |",
    ]
    for kind in KEYWORD_TYPES:
        examples = "；".join(item["keyword"] for item in grouped[kind][:3]) or "待补充"
        lines.append(f"| {kind} | {len(grouped[kind])} | {examples} |")
    lines.extend(["", "## 用户决策画像速览", "", "| 画像 | 场景 | 阶段 | 典型问题 |", "| --- | --- | --- | --- |"])
    for persona in user_plan["personas"]:
        lines.append(
            f"| {persona['name']} | {persona['scenario']} | {persona['decision_stage']} | {persona['query_patterns'][0]} |"
        )
    lines.extend(["", "## 下一步方向", "", "| 优先级 | 方向 | 状态 | 下一动作 |", "| --- | --- | --- | --- |"])
    for item in guidance["optimization_directions"]:
        lines.append(f"| {item['priority']} | {item['title']} | {item['status']} | {item['next_action']} |")
    lines.extend([
        "",
        "## 决策结论",
        "",
        "先确认用户决策画像和关键词分层，再决定是否进入企业九大画像补全或相关技能。内容、信源、发布和平台验证不自动执行。",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _company_basics(artifacts):
    values = artifacts["company_context"]["values"]
    return (
        _text(values.get("company_name", artifacts["user_persona_plan"]["company_id"])),
        _text(values.get("positioning", "待补充")),
        _text(values.get("main_businesses", "待补充")),
        _text(values.get("target_customers", "待补充")),
    )


def _next_step_lines(artifacts):
    guidance = artifacts["guided_next_steps"]
    return [
        "",
        "## 下一步",
        f"- 建议：{guidance['next_prompt']}",
        "- 当前不进入：内容、信源、发布和平台验证。",
        "- 相关技能：先用 `geo-keyword-persona` 完成词和画像确认；确认后再考虑 `ai-promotion-summary`。",
    ]


def write_simple_delivery(path, artifacts):
    company_name, positioning, business, target = _company_basics(artifacts)
    matrix = artifacts["keyword_matrix"]["keywords"]
    grouped = {kind: [] for kind in KEYWORD_TYPES}
    for item in matrix:
        grouped[item["keyword_type"]].append(item)
    lines = [
        f"# {company_name} 简约版词与画像",
        "",
        f"- 企业定位：{positioning}",
        f"- 主营业务：{business}",
        f"- 目标客户：{target}",
        "",
        "## 核心词",
        "",
        "| 类型 | 关键词 | 对应场景 |",
        "| --- | --- | --- |",
    ]
    for kind in KEYWORD_TYPES:
        for item in grouped[kind][:3]:
            lines.append(f"| {kind} | {item['keyword']} | {item['user_scenario']} |")
    lines.extend(["", "## 核心用户画像", "", "| 画像 | 场景 | 阶段 | 典型问题 |", "| --- | --- | --- | --- |"])
    for persona in artifacts["user_persona_plan"]["personas"][:3]:
        lines.append(f"| {persona['name']} | {persona['scenario']} | {persona['decision_stage']} | {persona['query_patterns'][0]} |")
    lines.extend(_next_step_lines(artifacts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_full_delivery(path, artifacts):
    company_name, positioning, business, target = _company_basics(artifacts)
    lines = [
        f"# {company_name} 完整版词与画像",
        "",
        f"- 企业定位：{positioning}",
        f"- 主营业务：{business}",
        f"- 目标客户：{target}",
        "",
        "## 完整关键词矩阵",
        "",
        "| 关键词 | 类型 | 用户场景 | 搜索意图 | 来源 | 状态 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in artifacts["keyword_matrix"]["keywords"]:
        lines.append(
            f"| {item['keyword']} | {item['keyword_type']} | {item['user_scenario']} | "
            f"{item['search_intent']} | {item.get('keyword_origin', 'SYSTEM_RECOMMENDED')} | "
            f"{item.get('decision_status', 'RECOMMENDED')} |"
        )
    lines.extend(["", "## 用户决策画像", "", "| 画像 | 场景 | 痛点 | 决策标准 | 阶段 |", "| --- | --- | --- | --- | --- |"])
    for persona in artifacts["user_persona_plan"]["personas"]:
        lines.append(
            f"| {persona['name']} | {persona['scenario']} | {'；'.join(persona['pain_points']) or '待补充'} | "
            f"{'；'.join(persona['decision_criteria']) or '待补充'} | {persona['decision_stage']} |"
        )
    lines.extend(["", "## 企业九大画像状态", "", "| 画像 | 状态 | 已确认内容 | 待补材料 |", "| --- | --- | --- | --- |"])
    for persona in artifacts["persona_plan"]["personas"]:
        lines.append(
            f"| {persona['name']} | {persona['status']} | "
            f"{'；'.join(persona['confirmed_content']) or '暂无'} | "
            f"{'；'.join(persona['missing_materials']) or '无'} |"
        )
    lines.extend(["", "## 优化方向", "", "| 优先级 | 方向 | 状态 |", "| --- | --- | --- |"])
    for item in artifacts["guided_next_steps"]["optimization_directions"]:
        lines.append(f"| {item['priority']} | {item['title']} | {item['status']} |")
    lines.extend(_next_step_lines(artifacts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_vertical_delivery(path, artifacts):
    company_name, _positioning, _business, _target = _company_basics(artifacts)
    guidance = artifacts["guided_next_steps"]
    vertical = guidance["vertical_business"]
    lines = [
        f"# {company_name} 垂直业务画像",
        "",
        f"- 垂直业务：{vertical}",
        "- 说明：只整理该业务线的人群、场景、问题词和企业画像，不与其他业务线混合。",
        "",
        "## 目标人群与决策场景",
        "",
        "| 画像 | 场景 | 痛点 | 决策标准 |",
        "| --- | --- | --- | --- |",
    ]
    for persona in artifacts["user_persona_plan"]["personas"]:
        lines.append(
            f"| {persona['name']} | {persona['scenario']} | {'；'.join(persona['pain_points']) or '待确认'} | "
            f"{'；'.join(persona['decision_criteria']) or '待确认'} |"
        )
    lines.extend(["", "## 垂直业务关键词", "", "| 类型 | 关键词 | 搜索意图 | 状态 |", "| --- | --- | --- | --- |"])
    for item in artifacts["keyword_matrix"]["keywords"]:
        lines.append(
            f"| {item['keyword_type']} | {item['keyword']} | {item['search_intent']} | "
            f"{item.get('decision_status', 'RECOMMENDED')} |"
        )
    lines.extend(["", "## 垂直业务画像建议", ""])
    lines.append("先确认该垂直业务的目标客户和核心问题词，再扩展企业九大画像；其他业务线暂不并入本版本。")
    lines.extend(_next_step_lines(artifacts))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_standard(output_dir, artifacts):
    required = {
        "geo_strategy", "keyword_matrix", "persona_plan", "execution", "retest_request",
        "company_context", "product_context", "intent_strategy", "user_persona_plan",
        "guided_next_steps",
    }
    if set(artifacts) != required:
        raise ValueError("STANDARD_RENDER-001: complete validated Standard artifacts are required")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_simple_delivery(output_dir / "01_简约版-词与画像.md", artifacts)
    write_full_delivery(output_dir / "02_完整版-词与画像.md", artifacts)
    write_vertical_delivery(output_dir / "03_垂直业务画像.md", artifacts)
    audit_dir = output_dir / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    _write_json(audit_dir / "keyword_matrix.json", artifacts["keyword_matrix"])
    _write_json(audit_dir / "persona_plan.json", artifacts["persona_plan"])
    _write_json(audit_dir / "user_persona_plan.json", artifacts["user_persona_plan"])
    write_keyword_xlsx(audit_dir / "keyword_matrix.xlsx", artifacts["keyword_matrix"])
    write_persona_markdown(audit_dir / "persona_report.md", artifacts)
    write_user_persona_markdown(audit_dir / "user_persona_report.md", artifacts)
    write_guidance_markdown(audit_dir / "guided_next_steps.md", artifacts)
    write_delivery_summary(audit_dir / "delivery_summary.md", artifacts)
