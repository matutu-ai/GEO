"""Repository-level acceptance checks for GEO V4."""

import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md", "INDEX.md", "QUICK_ROUTER.md", "main.py", "config/pipeline_policy.json",
    "core/execution_protocol.py", "core/agent_contracts.py", "core/artifact_store.py",
    "core/fixed_pipeline.py", "core/output_renderer.py", "validators/v4_validator.py",
    "schemas/execution-protocol.schema.json", "schemas/fact-packet-v4.schema.json",
    "schemas/company-profile-v4.schema.json", "schemas/product-profile-v4.schema.json",
    "schemas/intent-keyword-matrix-v4.schema.json", "schemas/nine-personas-v4.schema.json",
    "schemas/trust-report-v4.schema.json", "schemas/keyword-matrix-v4.schema.json",
    "schemas/final-summary-v4.schema.json", "workflows/fixed_pipeline.md",
    "workflows/content_strategy.md", "workflows/legacy/fast_path.md",
    "prompts/_interaction_contract.md", "prompts/00_start_prompt.md",
    "prompts/legacy/13_final_report_prompt.md", "tests/test_protocol_compliance.py",
]
V4_OUTPUTS = [
    "fact_packet.json", "company_profile.json", "product_profile.json", "intent_keyword_matrix.json",
    "persona_report.docx", "trust_report.json", "keyword_matrix.xlsx", "geo_strategy_report.md",
    "final_summary.json", "execution_trace.json",
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

protocol_result = subprocess.run([sys.executable, "-m", "unittest", "tests/test_protocol_compliance.py"], cwd=ROOT, text=True, capture_output=True)
if protocol_result.returncode:
    failures.append(f"protocol compliance failed: {protocol_result.stdout}{protocol_result.stderr}")

if failures:
    print("\n".join(failures))
    raise SystemExit(1)

print("PASS: GEO V4 fixed pipeline, artifacts, fail-closed validation, and 25 protocol compliance checks")
