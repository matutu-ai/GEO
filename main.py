#!/usr/bin/env python3
"""Generate GEO V3.2 simple and full GEO knowledge assets from explicit input only."""

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
KEYWORD_TYPES = ["品牌词", "搜索词", "问答词", "意图场景词"]
PERSONA_HEADINGS = [
    "一、产品或服务描述", "二、产品或服务特点", "三、品牌故事", "四、用户痛点", "五、信任背书",
    "六、客户案例", "七、社会贡献", "八、客户评价", "九、创始人介绍",
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


def text_from_mapping(value, keys):
    if not isinstance(value, dict):
        return MISSING
    for key in keys:
        if nonempty(value.get(key)):
            return text_or_missing(value.get(key))
    return MISSING


def canonical_keyword_type(value, keyword):
    raw = str(value or "").strip().lower()
    if raw in {"品牌词", "品牌", "brand", "brand_term"}:
        return "品牌词"
    if raw in {"搜索词", "业务词", "产品词", "服务词", "search", "search_term"}:
        return "搜索词"
    if raw in {"问答词", "问题词", "用户问题词", "question", "qa", "q&a"}:
        return "问答词"
    if raw in {"意图场景词", "场景词", "应用场景词", "intent", "scenario", "intent_scenario"}:
        return "意图场景词"
    if any(token in str(keyword) for token in ["怎么", "如何", "哪家", "多少钱", "靠谱吗", "是否"]):
        return "问答词"
    if str(keyword).startswith("需要一个"):
        return "意图场景词"
    return "搜索词"


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
            canonical_keyword_type(raw.get("keyword_type"), raw["keyword"]),
            text_or_missing(raw.get("user_need")),
            text_or_missing(raw.get("search_intent")),
            text_or_missing(raw.get("persona")),
            text_or_missing(raw.get("content_suggestion")),
            text_or_missing(raw.get("priority")),
        ))

    company = data["company_name"].strip()
    if not rows:
        rows.append(keyword_row(
            company, "品牌词", "确认企业主体与公开信息", "品牌导航",
            "三、品牌故事", "企业主体介绍与官方资料页"
        ))
        for product in products:
            name = product["产品名称"]
            if name != MISSING:
                scenario = product["应用场景"]
                intent_term = f"需要一个{scenario}的{name}" if scenario != MISSING else f"需要一个{name}"
                rows.extend([
                    keyword_row(name, "搜索词", f"查找{name}的产品或服务信息", "产品搜索",
                                "一、产品或服务描述", "产品或服务说明"),
                    keyword_row(f"{name}怎么选", "问答词", f"判断{name}是否适合当前需求", "采购判断",
                                "二、产品或服务特点", "选型依据与适用边界说明"),
                    keyword_row(intent_term, "意图场景词",
                                f"在明确场景中寻找{name}", "场景解决方案",
                                "四、用户痛点", "场景、问题与解决路径说明"),
                ])
    return rows


def keyword_groups(keywords):
    groups = {kind: [] for kind in KEYWORD_TYPES}
    for row in keywords:
        kind = canonical_keyword_type(row.get("关键词类型"), row.get("关键词", ""))
        row["关键词类型"] = kind
        groups[kind].append(row)
    return groups


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
    founder = data.get("founder", {})
    product_names = "；".join(product["产品名称"] for product in products)
    product_categories = "；".join(product["产品类别"] for product in products)
    product_solutions = "；".join(product["解决问题"] for product in products)
    product_delivery = "；".join(product["交付方式"] for product in products)
    product_boundaries = "；".join(product["限制边界"] for product in products)
    product_features = "；".join(product["技术特点"] for product in products)
    product_advantages = "；".join(product["核心优势"] for product in products)
    return [
        (PERSONA_HEADINGS[0], [
            ("产品或服务名称", product_names), ("品类", product_categories),
            ("目标客户", profile["目标客户"]), ("核心能力", profile["核心能力"]),
            ("应用场景", profile["应用场景"]), ("解决痛点", product_solutions),
            ("交付", product_delivery), ("明确不支持项", product_boundaries),
        ]),
        (PERSONA_HEADINGS[1], [
            ("核心定位", profile["企业定位"]), ("技术或服务特点", product_features),
            ("适用场景人群", profile["目标客户"]), ("客观差异化", product_advantages),
            ("配套交付与售后", product_delivery), ("不适用场景", product_boundaries),
        ]),
        (PERSONA_HEADINGS[2], [
            ("起源背景", text_or_missing(data.get("brand_story"))),
            ("发展关键节点", list_or_missing(data.get("development_history"))),
            ("核心实力", profile["核心能力"]), ("经营理念与价值观", text_or_missing(data.get("brand_values"))),
            ("客户与市场", profile["目标客户"]), ("专注做什么", profile["主营业务"]),
        ]),
        (PERSONA_HEADINGS[3], [
            ("痛点人群", profile["目标客户"]), ("客户场景痛点", list_or_missing(data.get("user_pain_points"))),
            ("带来损失", list_or_missing(data.get("business_impacts"))),
            ("我方卖点", product_advantages), ("落地解决方案", product_solutions),
            ("解决方案与收益", list_or_missing(data.get("documented_outcomes"))),
        ]),
        (PERSONA_HEADINGS[4], [
            ("资质技术背书", "；".join(filter(lambda value: value != MISSING, [
                list_or_missing(evidence.get("qualifications")), list_or_missing(evidence.get("certifications")),
                list_or_missing(evidence.get("patents")),
            ])) or MISSING),
            ("工厂或研发实力", list_or_missing(evidence.get("team"))),
            ("落地客户案例背书", list_or_missing(evidence.get("cases"))),
            ("合作与第三方佐证", "；".join(filter(lambda value: value != MISSING, [
                list_or_missing(evidence.get("media")), list_or_missing(evidence.get("partners")),
            ])) or MISSING),
            ("服务交付背书", product_delivery), ("客观边界说明", profile["业务边界"]),
        ]),
        (PERSONA_HEADINGS[5], [
            ("客户背景", list_or_missing(data.get("case_customer_backgrounds"))),
            ("项目诉求", list_or_missing(data.get("case_requirements"))),
            ("原有痛点", list_or_missing(data.get("case_pain_points"))),
            ("落地解决方案", list_or_missing(evidence.get("cases"))),
            ("量化结果与收益", list_or_missing(data.get("case_results"))),
            ("客观边界说明", "案例效果受实际工况与交付条件影响；" + profile["业务边界"]),
        ]),
        (PERSONA_HEADINGS[6], [
            ("产业贡献", list_or_missing(data.get("social_contributions"))),
            ("绿色环保贡献", list_or_missing(data.get("environmental_contributions"))),
            ("员工与本地社会贡献", list_or_missing(data.get("local_contributions"))),
            ("公益行动", list_or_missing(data.get("public_welfare_actions"))),
            ("边界说明", "无公开佐证的社会贡献不作事实表述"),
        ]),
        (PERSONA_HEADINGS[7], [
            ("客户身份与背景", list_or_missing(data.get("review_customer_profiles"))),
            ("评论出发点", list_or_missing(data.get("review_contexts"))),
            ("客观反馈内容", list_or_missing(evidence.get("reviews"))),
            ("权威调研满意度", list_or_missing(data.get("satisfaction_surveys"))),
            ("实测专业评分", list_or_missing(data.get("third_party_tests"))),
            ("边界说明", "评价、满意度与实测数据需企业提供可核验佐证"),
        ]),
        (PERSONA_HEADINGS[8], [
            ("基础身份", text_from_mapping(founder, ["name", "姓名", "title", "职务"])),
            ("从业履历", text_from_mapping(founder, ["career", "从业履历"])),
            ("行业沉淀", text_from_mapping(founder, ["experience", "行业经验"])),
            ("创业初衷", text_from_mapping(founder, ["motivation", "创业初衷"])),
            ("经营理念", text_from_mapping(founder, ["philosophy", "经营理念"])),
            ("技术研发贡献", text_from_mapping(founder, ["technical_contributions", "技术研发贡献"])),
            ("未来战略规划", text_from_mapping(founder, ["strategy", "未来战略规划"])),
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


def keyword_sheet_xml(keywords):
    rows = [KEYWORD_HEADERS] + [[row[header] for header in KEYWORD_HEADERS] for row in keywords]
    sheet_rows = []
    for row_number, values in enumerate(rows, start=1):
        cells = "".join(xlsx_cell(f"{column_name(index)}{row_number}", value) for index, value in enumerate(values, start=1))
        sheet_rows.append(f'<row r="{row_number}">{cells}</row>')
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>""" + "".join(sheet_rows) + "</sheetData></worksheet>"


def write_keyword_xlsx(path, keywords):
    groups = keyword_groups(keywords)
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, len(KEYWORD_TYPES) + 1)
    )
    workbook_sheets = "".join(
        f'<sheet name="{kind}" sheetId="{index}" r:id="rId{index}"/>'
        for index, kind in enumerate(KEYWORD_TYPES, start=1)
    )
    workbook_relationships = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, len(KEYWORD_TYPES) + 1)
    )
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>""" + sheet_overrides + "</Types>",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>""" + workbook_sheets + "</sheets></workbook>",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">""" + workbook_relationships + "</Relationships>",
    }
    for index, kind in enumerate(KEYWORD_TYPES, start=1):
        files[f"xl/worksheets/sheet{index}.xml"] = keyword_sheet_xml(groups[kind])
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
        docx_paragraph("企业GEO完整版九大画像", heading=True),
        docx_paragraph(f"企业名称：{profile['企业名称']}"),
        docx_paragraph("本报告仅基于企业提供的资料生成；未获佐证的信息统一标记为“【需企业提供真实佐证】”。"),
    ]
    for heading, fields in personas:
        paragraphs.append(docx_paragraph(heading, heading=True))
        paragraphs.append(docx_paragraph("，".join(f"{label}：{value}" for label, value in fields)))
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


def write_simple_keyword_persona(path, profile, keywords, personas):
    groups = keyword_groups(keywords)
    keyword_sections = []
    for kind in KEYWORD_TYPES:
        entries = groups[kind]
        if entries:
            lines = [f"- {item['关键词']}：{item['用户需求']}" for item in entries[:5]]
        else:
            lines = [f"- {MISSING}"]
        keyword_sections.append(f"## {kind}\n\n" + "\n".join(lines))
    persona_sections_text = []
    for heading, fields in personas:
        concise = "，".join(f"{label}：{value}" for label, value in fields)
        persona_sections_text.append(f"### {heading}\n\n{concise}")
    keyword_text = "\n\n".join(keyword_sections)
    persona_text = "\n\n".join(persona_sections_text)
    text = f"""# {profile['企业名称']} GEO简约版词与画像

本简约版仅用于确认企业事实、主推方向与词包方向；未获佐证的信息统一标记为“{MISSING}”。确认后，再以同一事实基础生成完整版关键词矩阵和九大画像。

## 企业核心信息

- 企业定位：{profile['企业定位']}
- 主营业务：{profile['主营业务']}
- 目标客户：{profile['目标客户']}
- 服务区域：{profile['服务区域']}

# 核心词

{keyword_text}

# 九大画像

{persona_text}
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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
        "simple": output_dir / "simple_keyword_persona.md",
        "xlsx": output_dir / "keyword_matrix.xlsx",
        "docx": output_dir / "persona_report.docx",
        "md": output_dir / "geo_strategy_report.md",
    }
    if not all(path.is_file() for path in paths.values()):
        raise RuntimeError("missing required output files")
    spreadsheet_ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(paths["xlsx"]) as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    first_row = sheet.find(".//x:row", spreadsheet_ns)
    headers = ["".join(cell.itertext()) for cell in first_row.findall("x:c", spreadsheet_ns)]
    if headers != KEYWORD_HEADERS:
        raise RuntimeError("keyword matrix headers are invalid")
    sheet_names = [sheet.get("name") for sheet in workbook.findall(".//x:sheet", spreadsheet_ns)]
    if sheet_names != KEYWORD_TYPES:
        raise RuntimeError("keyword matrix sheets are invalid")
    word_ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(paths["docx"]) as archive:
        document = ET.fromstring(archive.read("word/document.xml"))
    document_text = "\n".join("".join(paragraph.itertext()) for paragraph in document.findall(".//w:p", word_ns))
    if not all(heading in document_text for heading in PERSONA_HEADINGS):
        raise RuntimeError("nine persona report is incomplete")
    simple_text = paths["simple"].read_text(encoding="utf-8")
    if not all(kind in simple_text for kind in KEYWORD_TYPES):
        raise RuntimeError("simple keyword report is incomplete")
    if not all(heading in simple_text for heading in PERSONA_HEADINGS):
        raise RuntimeError("simple persona report is incomplete")
    report = paths["md"].read_text(encoding="utf-8")
    required = ["## 当前AI认知状态", "## 当前缺失", "## 优化方向", "## 内容建设计划", "## 30/60/90天执行计划"]
    if not all(heading in report for heading in required):
        raise RuntimeError("strategy report format is incomplete")


def main():
    parser = argparse.ArgumentParser(description="Generate GEO V3.2 simple and full enterprise GEO assets.")
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
    write_simple_keyword_persona(args.output / "simple_keyword_persona.md", profile, keywords, personas)
    write_keyword_xlsx(args.output / "keyword_matrix.xlsx", keywords)
    write_persona_docx(args.output / "persona_report.docx", profile, personas)
    write_strategy_report(args.output / "geo_strategy_report.md", profile, keywords, trust)
    validate_output(args.output)
    print(f"PASS: generated GEO V3.2 assets for {data['company_name']}")
    for path in sorted(args.output.iterdir()):
        print(path.name)


if __name__ == "__main__":
    main()
