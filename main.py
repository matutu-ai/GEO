#!/usr/bin/env python3
"""Generate GEO V3.1 knowledge assets from explicit enterprise input only."""

import argparse
import html
import json
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
MISSING = "【需企业提供真实佐证】"
KEYWORD_HEADERS = [
    "关键词", "关键词类型", "用户需求", "搜索意图", "对应画像", "内容建议", "优先级"
]
PERSONA_HEADINGS = [
    "一、品牌画像", "二、产品画像", "三、用户痛点画像", "四、场景画像", "五、行业画像",
    "六、信任画像", "七、案例画像", "八、客户评价画像", "九、专家画像",
]


def nonempty(value):
    return value is not None and str(value).strip() != ""


def as_list(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if nonempty(item)]
    return [str(value).strip()] if nonempty(value) else []


def list_or_missing(value):
    items = as_list(value)
    return "；".join(items) if items else MISSING


def text_or_missing(value):
    return str(value).strip() if nonempty(value) else MISSING


def load_input(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not nonempty(data.get("company_name")):
        raise ValueError("input JSON must contain a non-empty company_name")
    data.setdefault("evidence", {})
    return data


def company_profile(data):
    return {
        "企业名称": text_or_missing(data.get("company_name")),
        "企业定位": text_or_missing(data.get("positioning")),
        "主营业务": list_or_missing(data.get("main_businesses")),
        "目标客户": list_or_missing(data.get("target_customers")),
        "服务区域": list_or_missing(data.get("service_regions")),
        "核心能力": list_or_missing(data.get("core_capabilities")),
        "应用场景": list_or_missing(data.get("use_cases")),
        "竞争优势": list_or_missing(data.get("competitive_advantages")),
        "业务边界": list_or_missing(data.get("business_boundaries")),
    }


def product_profiles(data):
    rows = []
    for raw in data.get("products", []):
        if not isinstance(raw, dict):
            continue
        rows.append({
            "产品名称": text_or_missing(raw.get("name")),
            "产品类别": text_or_missing(raw.get("category")),
            "目标客户": list_or_missing(raw.get("target_customers")),
            "应用场景": list_or_missing(raw.get("use_cases")),
            "解决问题": list_or_missing(raw.get("problems_solved")),
            "核心优势": list_or_missing(raw.get("advantages")),
            "技术特点": list_or_missing(raw.get("technical_features")),
            "交付方式": list_or_missing(raw.get("delivery_methods")),
            "限制边界": list_or_missing(raw.get("boundaries")),
        })
    if not rows:
        rows.append({field: MISSING for field in [
            "产品名称", "产品类别", "目标客户", "应用场景", "解决问题", "核心优势", "技术特点", "交付方式", "限制边界"
        ]})
    return rows


def keyword_row(keyword, kind, need, intent, persona, content, priority="高"):
    return {
        "关键词": keyword,
        "关键词类型": kind,
        "用户需求": need,
        "搜索意图": intent,
        "对应画像": persona,
        "内容建议": content,
        "优先级": priority,
    }


def intent_keywords(data, products):
    rows = []
    for raw in data.get("user_intents", []):
        if not isinstance(raw, dict) or not nonempty(raw.get("keyword")):
            continue
        rows.append(keyword_row(
            str(raw["keyword"]).strip(),
            text_or_missing(raw.get("keyword_type")),
            text_or_missing(raw.get("user_need")),
            text_or_missing(raw.get("search_intent")),
            text_or_missing(raw.get("persona")),
            text_or_missing(raw.get("content_suggestion")),
            text_or_missing(raw.get("priority")),
        ))

    company = data["company_name"].strip()
    if not rows:
        rows.extend([
            keyword_row(company, "品牌词", "确认企业主体与公开信息", "品牌导航", "品牌画像", "企业主体介绍与官方资料页"),
            keyword_row(f"{company}靠谱吗", "信任验证词", "核验企业主体、官网、资质与案例", "信任验证", "信任画像", "资质、案例与业务边界说明"),
        ])
        for product in products:
            name = product["产品名称"]
            if name != MISSING:
                rows.append(keyword_row(
                    f"{name}是什么", "用户问题词", f"了解{name}的用途与适用条件", "问题了解",
                    "产品画像", "产品解释与适用场景说明"
                ))
    return rows


def trust_report(data):
    evidence = data.get("evidence", {})
    products = [item for item in data.get("products", []) if isinstance(item, dict)]
    expertise = min(25, (10 if products else 0) + (10 if as_list(data.get("core_capabilities")) else 0) + (5 if nonempty(data.get("positioning")) else 0))
    experience = min(25, 20 if as_list(evidence.get("cases")) else 0)
    authority = min(25, 5 * sum(bool(as_list(evidence.get(key))) for key in ["qualifications", "certifications", "patents", "media", "team"]))
    trust = min(25, (5 if nonempty(data.get("company_name")) else 0) + (10 if nonempty(data.get("official_website")) else 0) + (5 if as_list(data.get("business_boundaries")) else 0) + (5 if as_list(evidence.get("reviews")) else 0))
    missing = []
    checks = [
        ("官网或官方主体链接", data.get("official_website")),
        ("产品资料与技术说明", products),
        ("业务边界说明", data.get("business_boundaries")),
        ("真实客户案例与证明材料", evidence.get("cases")),
        ("资质、认证或专利材料", as_list(evidence.get("qualifications")) + as_list(evidence.get("certifications")) + as_list(evidence.get("patents"))),
        ("客户评价授权材料", evidence.get("reviews")),
        ("团队或专家公开资料", evidence.get("team")),
    ]
    for label, value in checks:
        if not as_list(value):
            missing.append(label)
    return {
        "总分": expertise + experience + authority + trust,
        "Expertise": expertise,
        "Experience": experience,
        "Authority": authority,
        "Trustworthiness": trust,
        "缺失": missing,
        "优化建议": [f"补充{item}，并保留可追溯来源。" for item in missing],
    }


def persona_sections(profile, products, data, trust):
    evidence = data.get("evidence", {})
    return [
        (PERSONA_HEADINGS[0], [
            ("企业介绍", profile["企业名称"]), ("定位", profile["企业定位"]),
            ("发展历程", MISSING), ("主营方向", profile["主营业务"]),
            ("品牌价值", profile["竞争优势"]), ("业务边界", profile["业务边界"]),
        ]),
        (PERSONA_HEADINGS[1], [
            ("产品名称", "；".join(product["产品名称"] for product in products)),
            ("产品能力", "；".join(product["核心优势"] for product in products)),
            ("适用场景", "；".join(product["应用场景"] for product in products)),
            ("客户对象", "；".join(product["目标客户"] for product in products)),
            ("解决问题", "；".join(product["解决问题"] for product in products)),
        ]),
        (PERSONA_HEADINGS[2], [
            ("用户类型", profile["目标客户"]), ("痛点问题", list_or_missing(data.get("user_pain_points"))),
            ("产生原因", MISSING), ("业务影响", MISSING), ("解决方案", MISSING),
        ]),
        (PERSONA_HEADINGS[3], [
            ("场景", profile["应用场景"]), ("触发条件", MISSING),
            ("需求描述", MISSING), ("解决路径", MISSING),
        ]),
        (PERSONA_HEADINGS[4], [
            ("行业趋势", MISSING), ("行业问题", MISSING),
            ("专业解释", MISSING), ("行业建议", MISSING),
        ]),
        (PERSONA_HEADINGS[5], [
            ("资质", list_or_missing(evidence.get("qualifications"))),
            ("认证", list_or_missing(evidence.get("certifications"))),
            ("专利", list_or_missing(evidence.get("patents"))),
            ("团队", list_or_missing(evidence.get("team"))),
            ("案例", list_or_missing(evidence.get("cases"))),
            ("媒体证明", list_or_missing(evidence.get("media"))),
            ("EEAT 资料完整度", f"{trust['总分']}/100（不代表企业实际评级）"),
        ]),
        (PERSONA_HEADINGS[6], [
            ("客户类型", MISSING), ("项目背景", MISSING), ("问题", MISSING),
            ("方案", MISSING), ("结果", MISSING), ("证明材料", list_or_missing(evidence.get("cases"))),
        ]),
        (PERSONA_HEADINGS[7], [
            ("客户身份", MISSING), ("使用过程", MISSING), ("体验反馈", MISSING),
            ("结果", list_or_missing(evidence.get("reviews"))),
        ]),
        (PERSONA_HEADINGS[8], [
            ("人物背景", MISSING), ("行业经验", MISSING), ("专业能力", MISSING),
            ("行业观点", MISSING), ("团队资料", list_or_missing(evidence.get("team"))),
        ]),
    ]


def column_name(index):
    result = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result


def xlsx_cell(reference, value):
    safe = html.escape(str(value))
    return f'<c r="{reference}" t="inlineStr"><is><t>{safe}</t></is></c>'


def write_keyword_xlsx(path, keywords):
    rows = [KEYWORD_HEADERS] + [[row[header] for header in KEYWORD_HEADERS] for row in keywords]
    sheet_rows = []
    for row_number, values in enumerate(rows, start=1):
        cells = "".join(xlsx_cell(f"{column_name(index)}{row_number}", value) for index, value in enumerate(values, start=1))
        sheet_rows.append(f'<row r="{row_number}">{cells}</row>')
    sheet_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>""" + "".join(sheet_rows) + "</sheetData></worksheet>"
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="GEO场景词库" sheetId="1" r:id="rId1"/></sheets></workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>""",
        "xl/worksheets/sheet1.xml": sheet_xml,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"))


def docx_paragraph(text, heading=False):
    safe = html.escape(str(text))
    properties = "<w:pPr><w:spacing w:after=\"160\"/></w:pPr>"
    if heading:
        properties = "<w:pPr><w:spacing w:before=\"240\" w:after=\"120\"/></w:pPr>"
    size = "36" if heading else "22"
    bold = "<w:b/>" if heading else ""
    return f"<w:p>{properties}<w:r><w:rPr>{bold}<w:sz w:val=\"{size}\"/></w:rPr><w:t>{safe}</w:t></w:r></w:p>"


def write_persona_docx(path, profile, personas):
    paragraphs = [
        docx_paragraph("企业AI认知画像", heading=True),
        docx_paragraph("本报告仅基于企业提供的资料生成；未获佐证的信息统一标记为“【需企业提供真实佐证】”。"),
        docx_paragraph("企业认知建模", heading=True),
    ]
    paragraphs.extend(docx_paragraph(f"{key}：{value}") for key, value in profile.items())
    for heading, fields in personas:
        paragraphs.append(docx_paragraph(heading, heading=True))
        paragraphs.extend(docx_paragraph(f"{label}：{value}") for label, value in fields)
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>""" + "".join(paragraphs) + "<w:sectPr/></w:body></w:document>"
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>""",
        "word/document.xml": document_xml,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content.encode("utf-8"))


def write_strategy_report(path, profile, keywords, trust):
    company = profile["企业名称"]
    gap_lines = "\n".join(f"- {item}" for item in trust["缺失"]) or "- 暂无"
    plan_rows = "\n".join(
        f"| {row['关键词']} | {row['对应画像']} | {row['用户需求']} | {row['内容建议']} |"
        for row in keywords
    )
    text = f"""# 企业GEO优化报告

企业：{company}

## 当前AI认知状态

- 企业主体：已收到企业名称，证据等级为 B（企业输入，尚未外部验证）。
- 企业定位：{profile['企业定位']}
- 主营业务：{profile['主营业务']}
- 产品能力：{profile['核心能力']}
- 业务边界：{profile['业务边界']}
- EEAT 资料完整度：{trust['总分']}/100。该分数仅反映当前资料完整度，不代表企业实际实力、信用或搜索排名。

| 维度 | 分数 | 当前依据 |
| --- | ---: | --- |
| Expertise | {trust['Expertise']}/25 | 产品、能力、技术资料 |
| Experience | {trust['Experience']}/25 | 可公开项目与案例资料 |
| Authority | {trust['Authority']}/25 | 资质、认证、专利、媒体资料 |
| Trustworthiness | {trust['Trustworthiness']}/25 | 主体、官网、边界与来源一致性 |

## 当前缺失

{gap_lines}

## 优化方向

1. 建立企业主体、官网、业务定位和业务边界的一致公开资料。
2. 补齐产品 Profile：产品名称、适用场景、解决问题、技术特点、交付方式和限制边界。
3. 只以可公开核验的资质、案例、评价和团队资料构建信任画像。
4. 按场景词、用户意图和对应画像建设 AI 知识资产；没有佐证的内容先补资料，不写成事实。

## 内容建设计划

| 场景词 | 绑定画像 | 用户需求 | 建议知识资产 |
| --- | --- | --- | --- |
{plan_rows}

## 30/60/90天执行计划

### 0-30天：建立企业认知底座

- 核验企业主体、官网、品牌名和业务边界。
- 完成 Company_Profile、Product_Profile 与九大画像中缺失资料收集。
- 输出并审核首版 GEO 场景词库。

### 31-60天：建设可信知识资产

- 根据已确认场景词建立产品解释、用户问题回答、FAQ、采购指南或案例分析计划。
- 每项内容绑定一个画像、一个用户场景和一项真实证据。
- 补充资质、案例、评价、团队与媒体证明，更新 Trust_Report。

### 61-90天：持续优化与复核

- 根据已发布且可验证的内容，复核品牌、产品和场景的 AI 认知一致性。
- 仅在具备真实验证记录时补充验证结论；没有记录时标记 NOT_AVAILABLE。
- 更新场景词库、九大画像和下一轮缺失资料清单。
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def validate_output(output_dir):
    paths = {
        "xlsx": output_dir / "keyword_matrix.xlsx",
        "docx": output_dir / "persona_report.docx",
        "md": output_dir / "geo_strategy_report.md",
    }
    if not all(path.is_file() for path in paths.values()):
        raise RuntimeError("missing required output files")
    spreadsheet_ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(paths["xlsx"]) as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    first_row = sheet.find(".//x:row", spreadsheet_ns)
    headers = ["".join(cell.itertext()) for cell in first_row.findall("x:c", spreadsheet_ns)]
    if headers != KEYWORD_HEADERS:
        raise RuntimeError("keyword matrix headers are invalid")
    word_ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(paths["docx"]) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    document_text = "\n".join("".join(paragraph.itertext()) for paragraph in document.findall(".//w:p", word_ns))
    if not all(heading in document_text for heading in PERSONA_HEADINGS):
        raise RuntimeError("nine persona report is incomplete")
    report = paths["md"].read_text(encoding="utf-8")
    required = ["## 当前AI认知状态", "## 当前缺失", "## 优化方向", "## 内容建设计划", "## 30/60/90天执行计划"]
    if not all(heading in report for heading in required):
        raise RuntimeError("strategy report format is incomplete")


def main():
    parser = argparse.ArgumentParser(description="Generate GEO V3.1 enterprise AI cognition assets.")
    parser.add_argument("--input", type=Path, default=ROOT / "input" / "company.json")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()

    data = load_input(args.input)
    profile = company_profile(data)
    products = product_profiles(data)
    keywords = intent_keywords(data, products)
    trust = trust_report(data)
    personas = persona_sections(profile, products, data, trust)

    resolved_output = args.output.resolve()
    if resolved_output in {ROOT, ROOT.parent}:
        raise ValueError("output directory must not be the repository or its parent")
    if args.output.exists():
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True)
    write_keyword_xlsx(args.output / "keyword_matrix.xlsx", keywords)
    write_persona_docx(args.output / "persona_report.docx", profile, personas)
    write_strategy_report(args.output / "geo_strategy_report.md", profile, keywords, trust)
    validate_output(args.output)
    print(f"PASS: generated GEO V3.1 assets for {data['company_name']}")
    for path in sorted(args.output.iterdir()):
        print(path.name)


if __name__ == "__main__":
    main()
