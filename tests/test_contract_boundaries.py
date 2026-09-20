"""Phase-0 boundary tests for GEO/GEO-BD data-only collaboration."""

import copy
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.fixed_pipeline import FixedPipeline
from validators.contract_validator import (
    ContractValidationError,
    validate_geo_bd_handoff,
    validate_geo_strategy,
    validate_manual_prescription_input,
    validate_retest_request,
)


def valid_prescription():
    return {
        "id": "PRESCRIPTION-001",
        "statement": "强化核心业务场景表达",
        "priority": "P1",
        "root_cause_ids": ["ROOT-001"],
        "expected_outcome": "提升 AI 对企业核心业务场景的理解",
        "verification_method": "复测相关 AI Query",
        "handoff_to": "GEO",
    }


def valid_handoff(source_system="GEO-BD"):
    return {
        "handoff_version": "1.0.0",
        "diagnostic_id": "DIAG-001",
        "company_id": "COMPANY-001",
        "company_name": "示例公司",
        "source_system": source_system,
        "target_system": "GEO",
        "prescriptions": [valid_prescription()],
    }


def valid_strategy():
    return {
        "strategy_version": "1.0.0",
        "diagnostic_id": "DIAG-001",
        "company_id": "COMPANY-001",
        "strategies": [{
            "id": "STRATEGY-001",
            "prescription_ids": ["PRESCRIPTION-001"],
            "objective": "围绕真实业务场景建立 GEO 内容和关键词覆盖",
            "priority": "P1",
            "execution_scope": ["keyword", "persona", "content", "source", "publishing", "retest"],
            "fact_ids": [],
        }],
    }


def valid_retest_request():
    return {
        "retest_version": "1.0.0",
        "diagnostic_id": "DIAG-001",
        "company_id": "COMPANY-001",
        "source_system": "GEO",
        "target_system": "GEO-BD",
        "executed_prescription_ids": ["PRESCRIPTION-001"],
        "executed_strategy_ids": ["STRATEGY-001"],
        "retest_targets": ["AI_VISIBILITY", "QUERY_COVERAGE", "CITATION_COVERAGE"],
    }


class ContractBoundaryTests(unittest.TestCase):
    def test_01_geo_bd_handoff_schema_accepts_valid_contract(self):
        validate_geo_bd_handoff(valid_handoff())

    def test_02_standard_handoff_rejects_non_geo_bd_source(self):
        payload = valid_handoff("MANUAL")
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_03_handoff_rejects_non_geo_target(self):
        payload = valid_handoff()
        payload["target_system"] = "OTHER"
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_04_handoff_rejects_empty_prescriptions(self):
        payload = valid_handoff()
        payload["prescriptions"] = []
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_05_prescription_requires_root_cause_ids(self):
        payload = valid_handoff()
        del payload["prescriptions"][0]["root_cause_ids"]
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_06_prescription_handoff_to_must_be_geo(self):
        payload = valid_handoff()
        payload["prescriptions"][0]["handoff_to"] = "OTHER"
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_07_handoff_rejects_generated_keywords(self):
        payload = valid_handoff()
        payload["generated_keywords"] = []
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_08_handoff_rejects_generated_content(self):
        payload = valid_handoff()
        payload["generated_content"] = []
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_09_strategy_requires_prescription_ids(self):
        payload = valid_strategy()
        payload["strategies"][0]["prescription_ids"] = []
        with self.assertRaises(ContractValidationError):
            validate_geo_strategy(payload, valid_handoff())

    def test_10_strategy_rejects_unknown_prescription_reference(self):
        payload = valid_strategy()
        payload["strategies"][0]["prescription_ids"] = ["PRESCRIPTION-404"]
        with self.assertRaises(ContractValidationError):
            validate_geo_strategy(payload, valid_handoff())

    def test_11_geo_strategy_cannot_create_root_cause(self):
        payload = valid_strategy()
        payload["strategies"][0]["root_causes"] = []
        with self.assertRaises(ContractValidationError):
            validate_geo_strategy(payload, valid_handoff())

    def test_12_geo_strategy_cannot_create_judgment(self):
        payload = valid_strategy()
        payload["strategies"][0]["judgment"] = "new diagnosis"
        with self.assertRaises(ContractValidationError):
            validate_geo_strategy(payload, valid_handoff())

    def test_13_geo_strategy_cannot_override_diagnostic_score(self):
        payload = valid_strategy()
        payload["strategies"][0]["diagnostic_score"] = 100
        with self.assertRaises(ContractValidationError):
            validate_geo_strategy(payload, valid_handoff())

    def test_14_retest_target_system_must_be_geo_bd(self):
        payload = valid_retest_request()
        payload["target_system"] = "OTHER"
        with self.assertRaises(ContractValidationError):
            validate_retest_request(payload)

    def test_15_retest_rejects_success_conclusion(self):
        payload = valid_retest_request()
        payload["success"] = True
        with self.assertRaises(ContractValidationError):
            validate_retest_request(payload)

    def test_16_manual_prescription_can_enter_strategy_contract(self):
        manual = valid_handoff("MANUAL")
        validate_manual_prescription_input(manual)
        validate_geo_strategy(valid_strategy(), manual)

    def test_17_legacy_compatible_v4_pipeline_still_runs(self):
        data = json.loads(
            (ROOT / "tests" / "fixtures" / "complete-v4-company.json").read_text(encoding="utf-8")
        )
        artifacts, trace = FixedPipeline("fast_path").run(data)
        self.assertEqual(trace["protocol"]["pipeline_id"], "geo-v4-fixed-pipeline")
        self.assertEqual(len(artifacts), 9)

    def test_18_geo_has_no_geo_bd_code_import(self):
        import_pattern = re.compile(r"^\s*(?:from|import)\s+geo_bd(?:\.|\s|$)", re.MULTILINE)
        checked = [ROOT / "main.py", *(ROOT / "core").glob("*.py"), *(ROOT / "validators").glob("*.py")]
        for path in checked:
            self.assertIsNone(import_pattern.search(path.read_text(encoding="utf-8")), path)

    def test_19_prescription_ids_must_be_unique(self):
        payload = valid_handoff()
        duplicate = copy.deepcopy(payload["prescriptions"][0])
        duplicate["statement"] = "另一条处方"
        payload["prescriptions"].append(duplicate)
        with self.assertRaises(ContractValidationError):
            validate_geo_bd_handoff(payload)

    def test_20_retest_schema_accepts_request_without_diagnosis(self):
        validate_retest_request(valid_retest_request())


if __name__ == "__main__":
    unittest.main()
