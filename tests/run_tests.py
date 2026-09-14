import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent

SCENARIOS = [
    "完整制造企业资料",
    "资料严重缺失企业",
    "本地服务企业",
    "B2B工业企业",
    "多个产品企业",
    "多个业务垂直企业",
    "存在虚假/未经验证信息的资料",
    "批量企业输入",
]

REQUIRED = [
    "INDEX.md",
    "SKILL.md",
    "main.py",
    "input/company.json",
    "schemas/geo-profile.schema.json",
    "schemas/evidence.schema.json",
    "schemas/keyword.schema.json",
    "schemas/entity-map.schema.json",
    "schemas/content-matrix.schema.json",
    "schemas/company-profile-v3.1.schema.json",
    "schemas/product-profile.schema.json",
    "schemas/intent-keyword-matrix.schema.json",
    "schemas/trust-report.schema.json",
    "workflows/intake.md",
    "workflows/client-corpus.md",
    "workflows/data-gap-detection.md",
    "workflows/company-profile.md",
    "workflows/industry-research.md",
    "workflows/competitor-research.md",
    "workflows/search-intent.md",
    "workflows/keyword-engine.md",
    "workflows/nine-profile.md",
    "workflows/vertical-profile.md",
    "workflows/content-matrix.md",
    "workflows/publishing-strategy.md",
    "workflows/geo-validation.md",
    "workflows/gap-analysis.md",
    "workflows/01_company_analysis.md",
    "workflows/02_product_analysis.md",
    "workflows/03_intent_analysis.md",
    "workflows/04_persona_generation.md",
    "workflows/05_trust_analysis.md",
    "workflows/06_keyword_matrix.md",
    "workflows/07_content_strategy.md",
    "workflows/08_geo_report.md",
    "workflows/fast_path.md",
    "prompts/00_start_prompt.md",
    "prompts/01_material_collection_prompt.md",
    "prompts/02_missing_detection_prompt.md",
    "prompts/03_company_profile_prompt.md",
    "prompts/04_industry_research_prompt.md",
    "prompts/05_search_intent_prompt.md",
    "prompts/06_keyword_engine_prompt.md",
    "prompts/07_persona_prompt.md",
    "prompts/08_vertical_persona_prompt.md",
    "prompts/09_content_matrix_prompt.md",
    "prompts/10_publish_strategy_prompt.md",
    "prompts/11_geo_verify_prompt.md",
    "prompts/12_gap_analysis_prompt.md",
    "prompts/13_final_report_prompt.md",
    "prompts/_interaction_contract.md",
    "references/evidence-rules.md",
    "references/keyword-rules.md",
    "references/geo-rules.md",
    "references/quality-rules.md",
    "templates/company-profile.md",
    "templates/client-intake-table.md",
    "templates/client-corpus-single-file.md",
    "templates/client-corpus/README.md",
    "templates/client-corpus/00-当前进度.md",
    "templates/client-corpus/01-事实与证据.md",
    "templates/client-corpus/02-定稿关键词.md",
    "templates/client-corpus/03-画像正文.md",
    "templates/client-corpus/04-缺失清单.md",
    "templates/client-corpus/05-更新日志.md",
    "templates/nine-profile.md",
    "templates/vertical-profile.md",
    "templates/keyword-matrix.md",
    "templates/content-matrix.md",
    "templates/final-report.md",
]

failures = []

for scenario in SCENARIOS:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    if missing:
        failures.append(f"{scenario}: missing {missing}")

single_file = (ROOT / "templates/client-corpus-single-file.md").read_text(encoding="utf-8")
if "## 0 当前进度与任务队列（速读块）" not in single_file:
    failures.append("client corpus single-file template: missing quick-resume section 0")
if "## 9 当前进度与任务队列" in single_file:
    failures.append("client corpus single-file template: duplicate progress section remains")

fast_path = (ROOT / "workflows" / "fast_path.md").read_text(encoding="utf-8")
for marker in ["Fact_Packet", "不生成文章", "先询问是否更新客户语料库"]:
    if marker not in fast_path:
        failures.append(f"fast path: missing {marker}")

prompt_files = sorted((ROOT / "prompts").glob("*.md"))
numbered_prompts = sorted(path for path in prompt_files if path.name[0].isdigit())
if len(numbered_prompts) != 14:
    failures.append(f"interactive prompts: expected 14 numbered files, found {len(numbered_prompts)}")
if not (ROOT / "prompts" / "_interaction_contract.md").is_file():
    failures.append("interactive prompts: missing shared contract")
for prompt_file in numbered_prompts:
    prompt_text = prompt_file.read_text(encoding="utf-8")
    if "完成后暂停" not in prompt_text and prompt_file.name != "00_start_prompt.md":
        failures.append(f"interactive prompt: missing pause rule in {prompt_file.name}")
if "Interactive Mode" not in (ROOT / "SKILL.md").read_text(encoding="utf-8"):
    failures.append("skill: missing Interactive Mode routing")
if "00 → 01 → 02 → 03 → 05 → 06 → 07 → 08 → 12 → 13" not in (ROOT / "SKILL.md").read_text(encoding="utf-8"):
    failures.append("skill: missing interactive main route")
contract = (ROOT / "prompts" / "_interaction_contract.md").read_text(encoding="utf-8")
for marker in ["provided", "source_verified", "unknown", "完成后必须暂停", "外部网页或搜索"]:
    if marker not in contract:
        failures.append(f"interactive contract: missing {marker}")

for schema_name in [
    "geo-profile.schema.json",
    "evidence.schema.json",
    "keyword.schema.json",
    "entity-map.schema.json",
    "content-matrix.schema.json",
    "company-profile-v3.1.schema.json",
    "product-profile.schema.json",
    "intent-keyword-matrix.schema.json",
    "trust-report.schema.json",
]:
    try:
        json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"{schema_name}: invalid JSON {exc}")

with tempfile.TemporaryDirectory() as temp_dir:
    output_dir = Path(temp_dir) / "output"
    result = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--output", str(output_dir)],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        failures.append(f"main.py failed: {result.stderr or result.stdout}")
    else:
        xlsx = output_dir / "keyword_matrix.xlsx"
        docx = output_dir / "persona_report.docx"
        report = output_dir / "geo_strategy_report.md"
        if not all(path.is_file() for path in [xlsx, docx, report]):
            failures.append("main.py: required output files missing")
        else:
            spreadsheet_ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            word_ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            with zipfile.ZipFile(xlsx) as archive:
                sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
            headers = ["".join(cell.itertext()) for cell in sheet.find(".//x:row", spreadsheet_ns).findall("x:c", spreadsheet_ns)]
            if headers != ["关键词", "关键词类型", "用户需求", "搜索意图", "对应画像", "内容建议", "优先级"]:
                failures.append("keyword matrix: invalid headers")
            with zipfile.ZipFile(docx) as archive:
                document = ET.fromstring(archive.read("word/document.xml"))
            document_text = "\n".join("".join(node.itertext()) for node in document.findall(".//w:p", word_ns))
            for heading in ["一、品牌画像", "二、产品画像", "三、用户痛点画像", "四、场景画像", "五、行业画像", "六、信任画像", "七、案例画像", "八、客户评价画像", "九、专家画像"]:
                if heading not in document_text:
                    failures.append(f"persona report: missing {heading}")
            report_text = report.read_text(encoding="utf-8")
            for heading in ["## 当前AI认知状态", "## 当前缺失", "## 优化方向", "## 内容建设计划", "## 30/60/90天执行计划"]:
                if heading not in report_text:
                    failures.append(f"strategy report: missing {heading}")
            if "【需企业提供真实佐证】" not in document_text:
                failures.append("truthfulness check: missing evidence marker")

if failures:
    print("\n".join(failures))
    sys.exit(1)

print(f"PASS: {len(SCENARIOS)} scenarios, {len(REQUIRED)} modules, schemas valid")
