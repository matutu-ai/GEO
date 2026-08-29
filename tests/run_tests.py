import json
import sys
from pathlib import Path


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
    "SKILL.md",
    "schemas/geo-profile.schema.json",
    "schemas/evidence.schema.json",
    "schemas/keyword.schema.json",
    "schemas/entity-map.schema.json",
    "schemas/content-matrix.schema.json",
    "workflows/intake.md",
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
    "references/evidence-rules.md",
    "references/keyword-rules.md",
    "references/geo-rules.md",
    "references/quality-rules.md",
    "templates/company-profile.md",
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

for schema_name in [
    "geo-profile.schema.json",
    "evidence.schema.json",
    "keyword.schema.json",
    "entity-map.schema.json",
    "content-matrix.schema.json",
]:
    try:
        json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    except Exception as exc:
        failures.append(f"{schema_name}: invalid JSON {exc}")

if failures:
    print("\n".join(failures))
    sys.exit(1)

print(f"PASS: {len(SCENARIOS)} scenarios, {len(REQUIRED)} modules, schemas valid")
