"""Phase-1 acceptance tests for the Prescription-driven Standard Path."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.standard_pipeline import PERSONA_UNITS, STANDARD_STAGES, StandardPathBlocked, StandardPathPipeline
from validators.contract_validator import (
    ContractValidationError,
    validate_geo_bd_handoff,
    validate_geo_strategy,
    validate_intent_strategy,
    validate_keyword_strategy,
    validate_manual_prescription_input,
    validate_persona_plan,
)


STANDARD_OUTPUTS = {
    "01_简约版-词与画像.md",
    "02_完整版-词与画像.md",
    "03_垂直业务画像.md",
    "audit",
}


def load_json(name):
    return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))


def run_pipeline(handoff_name="geo-bd-handoff-v1.json"):
    return StandardPathPipeline().run(
        load_json(handoff_name), load_json("complete-v4-company.json")
    )


def recursive_keys(value):
    keys = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(recursive_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(recursive_keys(item))
    return keys


class StandardPathTests(unittest.TestCase):
    def test_01_standard_reads_geo_bd_handoff(self):
        artifacts, trace = run_pipeline()
        self.assertEqual(artifacts["execution"]["source_system"], "GEO-BD")
        self.assertEqual(trace["pipeline_id"], "geo-standard-path-v1")

    def test_02_standard_reads_manual_prescription(self):
        artifacts, _ = run_pipeline("manual-prescription-v1.json")
        self.assertEqual(artifacts["execution"]["source_system"], "MANUAL")

    def test_03_standard_without_prescription_fails_closed(self):
        handoff = load_json("geo-bd-handoff-v1.json")
        handoff["prescriptions"] = []
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(handoff, load_json("complete-v4-company.json"))

    def test_04_strategy_must_reference_prescription(self):
        artifacts, _ = run_pipeline()
        strategy = copy.deepcopy(artifacts["geo_strategy"])
        strategy["strategies"][0]["prescription_ids"] = []
        with self.assertRaises(ContractValidationError):
            validate_geo_strategy(strategy, load_json("geo-bd-handoff-v1.json"))

    def test_05_intent_must_reference_strategy(self):
        artifacts, _ = run_pipeline()
        intents = copy.deepcopy(artifacts["intent_strategy"])
        intents["intents"][0]["strategy_ids"] = []
        with self.assertRaises(ContractValidationError):
            validate_intent_strategy(
                intents, artifacts["geo_strategy"], load_json("geo-bd-handoff-v1.json")
            )

    def test_06_keyword_requires_strategy_and_prescription(self):
        artifacts, _ = run_pipeline()
        for field in ("strategy_ids", "prescription_ids"):
            keywords = copy.deepcopy(artifacts["keyword_matrix"])
            keywords["keywords"][0][field] = []
            with self.subTest(field=field), self.assertRaises(ContractValidationError):
                validate_keyword_strategy(
                    keywords,
                    artifacts["geo_strategy"],
                    artifacts["intent_strategy"],
                    load_json("geo-bd-handoff-v1.json"),
                )

    def test_07_persona_requires_strategy_and_prescription(self):
        artifacts, _ = run_pipeline()
        for field in ("strategy_ids", "prescription_ids"):
            personas = copy.deepcopy(artifacts["persona_plan"])
            personas["personas"][0][field] = []
            with self.subTest(field=field), self.assertRaises(ContractValidationError):
                validate_persona_plan(
                    personas, artifacts["geo_strategy"], load_json("geo-bd-handoff-v1.json")
                )

    def test_08_standard_does_not_modify_prescription_priority(self):
        handoff = load_json("geo-bd-handoff-v1.json")
        original = copy.deepcopy(handoff["prescriptions"])
        artifacts, _ = StandardPathPipeline().run(handoff, load_json("complete-v4-company.json"))
        self.assertEqual(handoff["prescriptions"], original)
        self.assertEqual(artifacts["execution"]["prescriptions"], original)

    def test_09_standard_does_not_generate_root_cause_object(self):
        artifacts, _ = run_pipeline()
        keys = recursive_keys(artifacts)
        self.assertNotIn("root_cause", keys)
        self.assertNotIn("root_causes", keys)

    def test_10_standard_does_not_generate_judgment(self):
        artifacts, _ = run_pipeline()
        self.assertNotIn("judgment", recursive_keys(artifacts))

    def test_11_standard_does_not_generate_diagnostic_score(self):
        artifacts, _ = run_pipeline()
        keys = recursive_keys(artifacts)
        self.assertNotIn("diagnostic_score", keys)
        self.assertNotIn("geo_score", keys)

    def test_12_retest_request_has_no_success_conclusion(self):
        artifacts, _ = run_pipeline()
        retest = artifacts["retest_request"]
        self.assertNotIn("success", retest)
        self.assertNotIn("optimized", retest)

    def test_13_invalid_standard_does_not_fallback_to_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handoff = load_json("geo-bd-handoff-v1.json")
            handoff["prescriptions"] = []
            handoff_path = root / "invalid-handoff.json"
            handoff_path.write_text(json.dumps(handoff, ensure_ascii=False), encoding="utf-8")
            output = root / "output"
            result = subprocess.run([
                sys.executable, str(ROOT / "main.py"), "--mode", "standard",
                "--handoff", str(handoff_path), "--input",
                str(ROOT / "tests" / "fixtures" / "complete-v4-company.json"),
                "--output", str(output),
            ], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())
            self.assertNotIn("generated validated GEO V4 assets", result.stdout)

    def test_14_standard_outputs_keyword_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with zipfile.ZipFile(output / "audit" / "keyword_matrix.xlsx") as archive:
                workbook = ET.fromstring(archive.read("xl/workbook.xml"))
            namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
            self.assertEqual(
                [node.get("name") for node in workbook.findall(f".//{namespace}sheet")],
                ["品牌词", "搜索词", "问答词", "意图场景词"],
            )

    def test_15_standard_outputs_persona_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            content = (output / "audit" / "persona_report.md").read_text(encoding="utf-8")
            for name in PERSONA_UNITS:
                self.assertIn(f"## {name}", content)

    def test_16_standard_outputs_traceable_keyword_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            matrix = json.loads((output / "audit" / "keyword_matrix.json").read_text(encoding="utf-8"))
            required = {
                "keyword", "keyword_type", "product_or_service", "user_scenario",
                "search_intent", "persona_unit", "fact_ids", "prescription_ids",
                "strategy_ids", "intent_ids", "evidence_status", "risk_level",
                "needs_confirmation", "keyword_origin", "decision_status",
            }
            self.assertTrue(matrix["keywords"])
            self.assertTrue(required.issubset(matrix["keywords"][0]))

    def test_17_standard_outputs_user_personas_and_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            user_plan = json.loads((output / "audit" / "user_persona_plan.json").read_text(encoding="utf-8"))
            self.assertTrue(user_plan["personas"])
            self.assertIn("decision_stage", user_plan["personas"][0])
            guidance = (output / "audit" / "guided_next_steps.md").read_text(encoding="utf-8")
            self.assertIn("相关技能建议", guidance)
            self.assertIn("推荐下一阶段", guidance)
            summary = (output / "audit" / "delivery_summary.md").read_text(encoding="utf-8")
            self.assertIn("GEO 核心交付摘要", summary)

    def test_18_standard_accepts_guided_preferences(self):
        handoff = load_json("geo-bd-handoff-v1.json")
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {
            "delivery_mode": "完整版",
            "primary_objective": "招商代理获客",
            "requested_keywords": [{"keyword": "测试企业代理加盟", "keyword_type": "品牌词"}],
            "user_personas": [{
                "name": "渠道服务商",
                "audience": "有企业客户资源的网络营销服务商",
                "scenario": "寻找 AI 营销代理项目",
                "decision_stage": "考虑期→决策期",
                "pain_points": ["缺少新的产品线"],
                "decision_criteria": ["总部支持", "交付边界"],
                "query_patterns": ["AI 营销代理怎么选"],
            }],
        }
        artifacts, _ = StandardPathPipeline().run(handoff, company)
        self.assertEqual(artifacts["user_persona_plan"]["personas"][0]["status"], "CONFIRMED")
        requested = [item for item in artifacts["keyword_matrix"]["keywords"] if item["keyword"] == "测试企业代理加盟"]
        self.assertTrue(requested)
        self.assertEqual(requested[0]["keyword_origin"], "CLIENT_REQUESTED")
        self.assertEqual(artifacts["guided_next_steps"]["recommended_next_stage"], "keyword_review")

        company["geo_preferences"]["approved_keywords"] = ["测试企业代理加盟"]
        approved_artifacts, _ = StandardPathPipeline().run(handoff, company)
        self.assertEqual(approved_artifacts["guided_next_steps"]["recommended_next_stage"], "enterprise_persona_review")
        approved = [item for item in approved_artifacts["keyword_matrix"]["keywords"] if item["keyword"] == "测试企业代理加盟"]
        self.assertEqual(approved[0]["decision_status"], "CONFIRMED")

    def test_19_legacy_interactive_still_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "interactive"
            result = subprocess.run([
                sys.executable, str(ROOT / "main.py"), "--mode", "interactive", "--output", str(output)
            ], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual({path.name for path in output.iterdir()}, {"fact_packet.json", "interactive_state.json", "execution_trace.json"})

    def test_20_legacy_fast_path_still_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fast"
            result = subprocess.run([
                sys.executable, str(ROOT / "main.py"), "--mode", "fast_path", "--input",
                str(ROOT / "tests" / "fixtures" / "complete-v4-company.json"), "--output", str(output)
            ], text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(list(output.iterdir())), 10)

    def test_21_phase_0_contracts_still_validate(self):
        validate_geo_bd_handoff(load_json("geo-bd-handoff-v1.json"))
        validate_manual_prescription_input(load_json("manual-prescription-v1.json"))

    def test_22_standard_uses_fixed_stage_order(self):
        _, trace = run_pipeline()
        self.assertEqual([item["stage"] for item in trace["stages"]], list(STANDARD_STAGES))
        self.assertEqual(trace["status"], "VALIDATED")

    @staticmethod
    def _run_standard_cli(output):
        return subprocess.run([
            sys.executable, str(ROOT / "main.py"), "--mode", "standard", "--handoff",
            str(ROOT / "tests" / "fixtures" / "geo-bd-handoff-v1.json"), "--input",
            str(ROOT / "tests" / "fixtures" / "complete-v4-company.json"), "--output", str(output),
        ], text=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
