"""The only component allowed to render GEO V4 final files."""

import html
import json
import zipfile
from pathlib import Path

from validators.v4_validator import KEYWORD_TYPES, PERSONA_UNITS


MISSING = "【需企业提供真实佐证】"
INFERRED = "【基于现有资料推断，未经企业确认】"
CONFLICTED = "【资料存在冲突，需人工确认】"
KEYWORD_HEADERS = [
    "关键词", "关键词类型", "产品或服务", "用户场景", "搜索意图", "对应画像",
    "事实来源", "证据状态", "风险等级", "需确认",
]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        cells = "".join(_xlsx_cell(f"{_column_name(index)}{row_number}", value) for index, value in enumerate(values, start=1))
        xml_rows.append(f'<row r="{row_number}">{cells}</row>')
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + "".join(xml_rows) + "</sheetData></worksheet>"


def write_keyword_xlsx(path, matrix):
    grouped = {kind: [] for kind in KEYWORD_TYPES}
    for item in matrix["keywords"]:
        grouped[item["keyword_type"]].append([
            item["keyword"], item["keyword_type"], item["product_or_service"], item["user_scenario"],
            item["search_intent"], item["persona_unit"], "；".join(item["fact_ids"]),
            item["evidence_status"], item["risk_level"], "是" if item["needs_confirmation"] else "否",
        ])
    overrides = "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, 5))
    sheets = "".join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>' for i, name in enumerate(KEYWORD_TYPES, start=1))
    relations = "".join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1, 5))
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>' + overrides + "</Types>",
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>' + sheets + "</sheets></workbook>",
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + relations + "</Relationships>",
    }
    for index, kind in enumerate(KEYWORD_TYPES, start=1):
        files[f"xl/worksheets/sheet{index}.xml"] = _keyword_sheet_xml(grouped[kind])
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"))


def _paragraph(text, heading=False):
    properties = "<w:pPr><w:spacing w:after=\"160\"/></w:pPr>"
    if heading:
        properties = "<w:pPr><w:spacing w:before=\"240\" w:after=\"120\"/></w:pPr>"
    bold = "<w:b/>" if heading else ""
    size = "32" if heading else "22"
    return f"<w:p>{properties}<w:r><w:rPr>{bold}<w:sz w:val=\"{size}\"/></w:rPr><w:t>{html.escape(str(text))}</w:t></w:r></w:p>"


def write_persona_docx(path, company_profile, personas):
    company_name = company_profile["company_name"]["display"]
    paragraphs = [_paragraph("企业 GEO 九大画像", True), _paragraph(f"企业名称：{company_name}"), _paragraph("本报告由已校验的 Fact_Packet 汇总生成；未知、推断和冲突内容保持原状态。")]
    for unit in personas["units"]:
        paragraphs.append(_paragraph(unit["name"], True))
        paragraphs.append(_paragraph("已确认内容：" + ("；".join(unit["confirmed_content"]) or "【暂无企业真实资料】")))
        paragraphs.append(_paragraph("推断内容：" + ("；".join(unit["inferred_content"]) or "无")))
        paragraphs.append(_paragraph("未知内容：" + ("；".join(unit["unknown_content"]) or "无")))
        paragraphs.append(_paragraph("事实来源：" + ("；".join(unit["evidence_ids"]) or "无")))
        paragraphs.append(_paragraph("待补资料：" + ("；".join(unit["missing_materials"]) or "无")))
    document = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' + "".join(paragraphs) + "<w:sectPr/></w:body></w:document>"
    files = {
        "[Content_Types].xml": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
        "word/document.xml": document,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"))


def write_geo_report(path, report):
    text = "\n".join([
        "# 企业 GEO 优化报告", "", "## 当前 AI 认知状态", *[f"- {value}" for value in report["current_state"]],
        "", "## 当前缺失", *[f"- {value}" for value in report["gaps"]],
        "", "## 优化方向", *[f"- {value}" for value in report["directions"]],
        "", "## 内容建设计划", *[f"- {value}" for value in report["plan"]],
        "", "## 30/60/90 天执行计划", "- 0-30 天：补齐 Fact_Packet 中的 UNKNOWN 与 CONFLICTED 资料。", "- 31-60 天：仅基于 CONFIRMED 事实建设知识资产。", "- 61-90 天：补充真实验证记录后复核并重新运行固定 Pipeline。", "",
    ])
    path.write_text(text, encoding="utf-8")


def render_final(output_dir, artifacts, execution_trace):
    """Render only already validated artifacts; callers cannot supply free-form reports."""
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = {"fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report", "keyword_matrix", "geo_report", "final_summary"}
    actual = {artifact.get("artifact_type") for artifact in artifacts}
    if actual != expected or any(artifact.get("status") != "VALIDATED" for artifact in artifacts):
        raise ValueError("RENDER-001: renderer requires the complete validated V4 artifact set")
    if execution_trace.get("protocol", {}).get("pipeline_id") != "geo-v4-fixed-pipeline":
        raise ValueError("RENDER-002: renderer requires a GEO V4 execution trace")
    payloads = {artifact["artifact_type"]: artifact["payload"] for artifact in artifacts}
    write_json(output_dir / "fact_packet.json", payloads["fact_packet"])
    write_json(output_dir / "company_profile.json", payloads["company_profile"])
    write_json(output_dir / "product_profile.json", payloads["product_profile"])
    write_json(output_dir / "intent_keyword_matrix.json", payloads["intent_keyword_matrix"])
    write_json(output_dir / "trust_report.json", payloads["trust_report"])
    write_keyword_xlsx(output_dir / "keyword_matrix.xlsx", payloads["keyword_matrix"])
    write_persona_docx(output_dir / "persona_report.docx", payloads["company_profile"], payloads["nine_personas"])
    write_geo_report(output_dir / "geo_strategy_report.md", payloads["geo_report"])
    write_json(output_dir / "final_summary.json", payloads["final_summary"])
    write_json(output_dir / "execution_trace.json", execution_trace)
