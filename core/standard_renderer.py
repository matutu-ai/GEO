"""Render the focused Standard Path deliverables: keywords and nine personas."""

import html
import json
import zipfile


KEYWORD_TYPES = ("品牌词", "搜索词", "问答词", "意图场景词")
KEYWORD_HEADERS = [
    "关键词", "关键词类型", "产品或服务", "用户场景", "搜索意图", "对应画像",
    "事实来源", "证据状态", "风险等级", "需确认",
]
STANDARD_OUTPUTS = (
    "keyword_matrix.json",
    "persona_plan.json",
    "keyword_matrix.xlsx",
    "persona_report.md",
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
        f"# {company_name} 九大画像",
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


def render_standard(output_dir, artifacts):
    required = {
        "geo_strategy", "keyword_matrix", "persona_plan", "execution", "retest_request",
        "company_context", "product_context", "intent_strategy",
    }
    if set(artifacts) != required:
        raise ValueError("STANDARD_RENDER-001: complete validated Standard artifacts are required")
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "keyword_matrix.json", artifacts["keyword_matrix"])
    _write_json(output_dir / "persona_plan.json", artifacts["persona_plan"])
    write_keyword_xlsx(output_dir / "keyword_matrix.xlsx", artifacts["keyword_matrix"])
    write_persona_markdown(output_dir / "persona_report.md", artifacts)
