"""Repository-level acceptance checks for Standard Path and Legacy-compatible V4."""

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md", "INDEX.md", "QUICK_ROUTER.md", "main.py", "requirements.txt", "config/pipeline_policy.json",
    "core/execution_protocol.py", "core/agent_contracts.py", "core/artifact_store.py",
    "core/fixed_pipeline.py", "core/output_renderer.py", "core/standard_pipeline.py",
    "core/standard_renderer.py", "validators/v4_validator.py",
    "schemas/execution-protocol.schema.json", "schemas/fact-packet-v4.schema.json",
    "schemas/company-profile-v4.schema.json", "schemas/product-profile-v4.schema.json",
    "schemas/intent-keyword-matrix-v4.schema.json", "schemas/nine-personas-v4.schema.json",
    "schemas/trust-report-v4.schema.json", "schemas/keyword-matrix-v4.schema.json",
    "schemas/final-report-v4.schema.json", "schemas/final-summary-v4.schema.json", "workflows/fixed_pipeline.md",
    "schemas/geo-bd-handoff-v1.schema.json", "schemas/geo-strategy-v1.schema.json",
    "schemas/geo-retest-request-v1.schema.json", "schemas/intent-strategy-v1.schema.json",
    "schemas/keyword-strategy-v1.schema.json", "schemas/persona-plan-v1.schema.json",
    "schemas/execution-v1.schema.json", "validators/contract_validator.py",
    "workflows/content_strategy.md", "workflows/legacy/fast_path.md",
    "prompts/_interaction_contract.md", "prompts/00_start_prompt.md",
    "prompts/legacy/13_final_report_prompt.md", "tests/test_protocol_compliance.py",
    "tests/test_contract_boundaries.py", "tests/test_standard_path.py",
    "tests/fixtures/geo-bd-handoff-v1.json", "tests/fixtures/manual-prescription-v1.json",
]
V4_OUTPUTS = [
    "fact_packet.json", "company_profile.json", "product_profile.json", "intent_keyword_matrix.json",
    "persona_report.docx", "trust_report.json", "keyword_matrix.xlsx", "geo_strategy_report.md",
    "final_summary.json", "execution_trace.json",
]
STANDARD_OUTPUTS = [
    "01_简约版-词与画像.md", "02_完整版-词与画像.md", "03_垂直业务画像.md", "audit",
]
failures = []

for path in REQUIRED:
    if not (ROOT / path).is_file():
        failures.append(f"missing required V4 file: {path}")

for path in (ROOT / "schemas").glob("*.json"):
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON schema {path.name}: {exc}")

for source in [ROOT / "main.py", *sorted((ROOT / "core").glob("*.py")), *sorted((ROOT / "validators").glob("*.py"))]:
    content = source.read_text(encoding="utf-8")
    for reference in sorted(set(re.findall(r"schemas/[A-Za-z0-9_.-]+\.json", content))):
        if not (ROOT / reference).is_file():
            failures.append(f"missing runtime schema reference: {source.name} -> {reference}")

policy = json.loads((ROOT / "config" / "pipeline_policy.json").read_text(encoding="utf-8"))
for key, expected in {
    "default_pipeline": "geo-v4-fixed-pipeline", "legacy_enabled": False,
    "allow_dynamic_routing": False, "allow_agent_override": False,
    "allow_unapproved_tools": False, "require_schema_validation": True,
    "require_traceability": True, "fail_closed": True,
}.items():
    if policy.get(key) != expected:
        failures.append(f"pipeline policy: {key} must be {expected!r}")

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    interactive = root / "interactive"
    result = subprocess.run([sys.executable, str(ROOT / "main.py"), "--output", str(interactive)], text=True, capture_output=True)
    if result.returncode:
        failures.append(f"interactive mode failed: {result.stdout}{result.stderr}")
    elif {path.name for path in interactive.iterdir()} != {"fact_packet.json", "interactive_state.json", "execution_trace.json"}:
        failures.append("interactive mode: unexpected output; final reports must not be rendered")

    complete = root / "complete"
    result = subprocess.run([
        sys.executable, str(ROOT / "main.py"), "--mode", "fast_path",
        "--input", str(ROOT / "tests" / "fixtures" / "complete-v4-company.json"), "--output", str(complete),
    ], text=True, capture_output=True)
    if result.returncode:
        failures.append(f"fast path failed: {result.stdout}{result.stderr}")
    else:
        actual = {path.name for path in complete.iterdir()}
        if actual != set(V4_OUTPUTS):
            failures.append(f"fast path: output mismatch {sorted(actual)}")
        for name in ["fact_packet.json", "company_profile.json", "product_profile.json", "intent_keyword_matrix.json", "trust_report.json", "final_summary.json", "execution_trace.json"]:
            try:
                json.loads((complete / name).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"fast path: invalid {name}: {exc}")
        with zipfile.ZipFile(complete / "keyword_matrix.xlsx") as archive:
            workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        spreadsheet_ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        header_row = sheet.find(".//x:row", spreadsheet_ns)
        headers = ["".join(cell.itertext()) for cell in header_row.findall("x:c", spreadsheet_ns)]
        if headers != ["关键词", "关键词类型", "产品或服务", "用户场景", "搜索意图", "对应画像", "事实来源", "证据状态", "风险等级", "需确认"]:
            failures.append("fast path: keyword columns are not traceable")
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        names = [node.get("name") for node in workbook.findall(".//x:sheet", ns)]
        if names != ["品牌词", "搜索词", "问答词", "意图场景词"]:
            failures.append("fast path: keyword sheets are not fixed")
        with zipfile.ZipFile(complete / "persona_report.docx") as archive:
            document = ET.fromstring(archive.read("word/document.xml"))
        word_ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        document_text = "\n".join("".join(node.itertext()) for node in document.findall(".//w:p", word_ns))
        for heading in ["产品或服务描述", "产品或服务特点", "品牌故事", "用户痛点", "信任背书", "客户案例", "社会贡献", "客户评价", "创始人介绍"]:
            if heading not in document_text:
                failures.append(f"fast path: missing fixed persona unit {heading}")
        fact_packet = json.loads((complete / "fact_packet.json").read_text(encoding="utf-8"))
        if any(not fact.get("fact_id") or not fact.get("source") for fact in fact_packet["facts"]):
            failures.append("fast path: fact packet lacks traceability")

    blocked = root / "blocked"
    result = subprocess.run([sys.executable, str(ROOT / "main.py"), "--mode", "fast_path", "--output", str(blocked)], text=True, capture_output=True)
    if result.returncode != 2 or any(blocked.iterdir()):
        failures.append("fail closed: incomplete Fast Path must block final export")

    standard = root / "standard"
    result = subprocess.run([
        sys.executable, str(ROOT / "main.py"), "--mode", "standard",
        "--handoff", str(ROOT / "tests" / "fixtures" / "geo-bd-handoff-v1.json"),
        "--input", str(ROOT / "tests" / "fixtures" / "complete-v4-company.json"),
        "--output", str(standard),
    ], text=True, capture_output=True)
    if result.returncode:
        failures.append(f"standard path failed: {result.stdout}{result.stderr}")
    elif {path.name for path in standard.iterdir()} != set(STANDARD_OUTPUTS):
        failures.append("standard path: output set does not match the four-file keyword/persona contract")
    else:
        audit = standard / "audit"
        for name in ["keyword_matrix.json", "persona_plan.json", "user_persona_plan.json"]:
            try:
                json.loads((audit / name).read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                failures.append(f"standard path: invalid {name}: {exc}")
        try:
            with zipfile.ZipFile(audit / "keyword_matrix.xlsx") as archive:
                workbook = ET.fromstring(archive.read("xl/workbook.xml"))
                sheet_names = [node.get("name") for node in workbook.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet")]
                if sheet_names != ["品牌词", "搜索词", "问答词", "意图场景词"]:
                    failures.append("standard path: keyword workbook sheets are not fixed")
        except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
            failures.append(f"standard path: invalid keyword_matrix.xlsx: {exc}")
        try:
            report = (audit / "persona_report.md").read_text(encoding="utf-8")
            for heading in ["产品或服务描述", "产品或服务特点", "品牌故事", "用户痛点", "信任背书", "客户案例", "社会贡献", "客户评价", "创始人介绍"]:
                if f"## {heading}" not in report:
                    failures.append(f"standard path: persona report missing {heading}")
        except OSError as exc:
            failures.append(f"standard path: invalid persona_report.md: {exc}")
        try:
            user_report = (audit / "user_persona_report.md").read_text(encoding="utf-8")
            if "用户决策画像" not in user_report:
                failures.append("standard path: user persona report marker missing")
            guidance = (audit / "guided_next_steps.md").read_text(encoding="utf-8")
            for marker in ["每阶段提示建议", "相关技能建议", "推荐下一阶段"]:
                if marker not in guidance:
                    failures.append(f"standard path: guidance report missing {marker}")
            summary = (audit / "delivery_summary.md").read_text(encoding="utf-8")
            for marker in ["GEO 核心交付摘要", "关键词速览", "用户决策画像速览", "下一步方向"]:
                if marker not in summary:
                    failures.append(f"standard path: summary missing {marker}")
        except OSError as exc:
            failures.append(f"standard path: missing guided output: {exc}")

    standard_blocked = root / "standard-blocked"
    result = subprocess.run([
        sys.executable, str(ROOT / "main.py"), "--mode", "standard",
        "--input", str(ROOT / "tests" / "fixtures" / "complete-v4-company.json"),
        "--output", str(standard_blocked),
    ], text=True, capture_output=True)
    if result.returncode != 2 or standard_blocked.exists():
        failures.append("standard path: missing handoff must fail closed without legacy fallback")

protocol_result = subprocess.run([
    sys.executable, "-m", "unittest",
    "tests/test_protocol_compliance.py", "tests/test_contract_boundaries.py",
    "tests/test_standard_path.py",
], cwd=ROOT, text=True, capture_output=True)
if protocol_result.returncode:
    failures.append(f"protocol compliance failed: {protocol_result.stdout}{protocol_result.stderr}")

if failures:
    print("\n".join(failures))
    raise SystemExit(1)

print("PASS: GEO Standard Path, Legacy V4, 25 protocol checks, 20 phase-0 checks, and 20 phase-1 checks")
