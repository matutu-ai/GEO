"""Rule-consistency tests for the non-overridable GEO V4 protocol."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.agent_contracts import AGENT_CONTRACTS
from core.artifact_store import ArtifactStore
from core.execution_protocol import ExecutionProtocol, ProtocolViolation
from core.fixed_pipeline import FixedPipeline, PipelineBlocked
from core.output_renderer import render_final
from validators.v4_validator import (
    INFERRED_MARKER, PERSONA_UNITS, UNKNOWN_MARKER, validate_fact_packet,
    validate_keyword_matrix, validate_personas,
)


def load_complete():
    return json.loads((ROOT / "tests" / "fixtures" / "complete-v4-company.json").read_text(encoding="utf-8"))


class ProtocolComplianceTests(unittest.TestCase):
    def test_01_only_company_name_enters_collection(self):
        pipeline = FixedPipeline()
        state = pipeline.interactive_state({"company_name": "仅名称企业"})
        facts = pipeline.store.get("fact_packet")["payload"]["facts"]
        self.assertEqual(state["current_stage"], "fact_normalization")
        self.assertEqual(next(item for item in facts if item["field"] == "company_name")["status"], "CONFIRMED")
        self.assertIn("positioning", state["missing_materials"])

    def test_02_partial_data_cannot_run_fast_path(self):
        with self.assertRaises(PipelineBlocked):
            FixedPipeline("fast_path").run({"company_name": "部分资料企业"})

    def test_03_complete_data_uses_fixed_order(self):
        pipeline = FixedPipeline("fast_path")
        artifacts, trace = pipeline.run(load_complete())
        self.assertEqual([item["stage"] for item in trace["stages"][:8]], list(pipeline.protocol.required_stages))
        self.assertEqual({item["artifact_type"] for item in artifacts}, {"fact_packet", "company_profile", "product_profile", "intent_keyword_matrix", "nine_personas", "trust_report", "keyword_matrix", "geo_report", "final_summary"})

    def test_04_conflicting_data_is_retained(self):
        pipeline = FixedPipeline()
        state = pipeline.interactive_state({"company_name": "冲突企业", "conflicts": {"positioning": ["定位 A", "定位 B"]}})
        fact = next(item for item in pipeline.store.get("fact_packet")["payload"]["facts"] if item["field"] == "positioning")
        self.assertEqual(fact["status"], "CONFLICTED")
        self.assertEqual(state["conflicts"], ["positioning"])

    def test_05_missing_product_is_not_invented(self):
        pipeline = FixedPipeline()
        pipeline.interactive_state({"company_name": "无产品企业"})
        product = next(item for item in pipeline.store.get("fact_packet")["payload"]["facts"] if item["field"] == "products")
        self.assertEqual(product["status"], "UNKNOWN")

    def test_06_missing_case_is_a_trust_gap(self):
        data = load_complete()
        data["evidence"] = {"qualifications": ["验收资料"]}
        artifacts, _ = FixedPipeline("fast_path").run(data)
        trust = next(item["payload"] for item in artifacts if item["artifact_type"] == "trust_report")
        self.assertIn("evidence.cases", trust["gaps"])

    def test_07_missing_qualification_is_a_trust_gap(self):
        data = load_complete()
        data["evidence"] = {"cases": ["验收资料"]}
        artifacts, _ = FixedPipeline("fast_path").run(data)
        trust = next(item["payload"] for item in artifacts if item["artifact_type"] == "trust_report")
        self.assertIn("evidence.qualifications", trust["gaps"])

    def test_08_missing_review_is_a_trust_gap(self):
        artifacts, _ = FixedPipeline("fast_path").run(load_complete())
        trust = next(item["payload"] for item in artifacts if item["artifact_type"] == "trust_report")
        self.assertIn("evidence.reviews", trust["gaps"])

    def test_09_non_owner_cannot_modify_positioning(self):
        with self.assertRaises(ProtocolViolation):
            AGENT_CONTRACTS["keyword_intelligence"].assert_write("keyword_matrix", ["positioning"])

    def test_10_stage_cannot_be_skipped(self):
        with self.assertRaises(ProtocolViolation):
            ExecutionProtocol().check_stage("keyword_intelligence", [])

    def test_11_keyword_agent_cannot_execute_early(self):
        with self.assertRaises(ProtocolViolation):
            FixedPipeline("fast_path")._run_keywords({})

    def test_12_legacy_pipeline_is_forbidden(self):
        with self.assertRaises(ProtocolViolation):
            ExecutionProtocol().check_stage("legacy_pipeline", [])

    def test_13_schema_bypass_is_detected(self):
        issues = validate_fact_packet({"protocol_version": "4.0.0", "facts": [], "conflicts": []})
        self.assertFalse([item for item in issues if item.level == "ERROR"])
        issues = validate_fact_packet({"facts": [], "conflicts": []})
        self.assertTrue([item for item in issues if item.level == "ERROR"])

    def test_14_renderer_rejects_direct_final_write(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                render_final(Path(directory), [], {"protocol": {}})

    def test_15_fact_without_id_is_illegal(self):
        issues = validate_fact_packet({"protocol_version": "4.0.0", "facts": [{"field": "company_name", "value": "x", "status": "CONFIRMED", "source": "input", "evidence": [], "confidence": "high", "created_by": "fact_normalization"}], "conflicts": []})
        self.assertTrue([item for item in issues if item.code == "SCHEMA-001"])

    def test_16_keyword_without_scenario_is_illegal(self):
        issues = validate_keyword_matrix({"keywords": [{"keyword": "x", "keyword_type": "品牌词", "product_or_service": "x", "user_scenario": "", "search_intent": "导航", "persona_unit": "品牌故事", "fact_ids": ["fact-001"], "evidence_status": "CONFIRMED", "risk_level": "低", "needs_confirmation": False}], "fact_ids": ["fact-001"]}, {"fact-001"})
        self.assertTrue([item for item in issues if item.code == "KEYWORD-003"])

    def test_17_keyword_without_persona_is_illegal(self):
        issues = validate_keyword_matrix({"keywords": [{"keyword": "x", "keyword_type": "品牌词", "product_or_service": "x", "user_scenario": "导航", "search_intent": "导航", "persona_unit": "", "fact_ids": ["fact-001"], "evidence_status": "CONFIRMED", "risk_level": "低", "needs_confirmation": False}], "fact_ids": ["fact-001"]}, {"fact-001"})
        self.assertTrue([item for item in issues if item.code == "KEYWORD-004"])

    def test_18_unmarked_inferred_content_is_illegal(self):
        units = [{"name": name, "confirmed_content": ["已确认"], "inferred_content": [], "unknown_content": [], "evidence_ids": ["fact-001"], "missing_materials": [], "forbidden_claims": []} for name in PERSONA_UNITS]
        units[0]["inferred_content"] = ["未标记推断"]
        issues = validate_personas({"units": units, "fact_ids": ["fact-001"]}, {"fact-001"})
        self.assertTrue([item for item in issues if item.code == "PERSONA-003"])

    def test_19_unmarked_unknown_content_is_illegal(self):
        units = [{"name": name, "confirmed_content": [], "inferred_content": [], "unknown_content": [], "evidence_ids": [], "missing_materials": [], "forbidden_claims": []} for name in PERSONA_UNITS]
        issues = validate_personas({"units": units, "fact_ids": []}, set())
        self.assertTrue([item for item in issues if item.code == "PERSONA-002"])

    def test_20_case_is_not_fabricated(self):
        pipeline = FixedPipeline()
        pipeline.interactive_state({"company_name": "无案例企业"})
        self.assertEqual(next(item for item in pipeline.store.get("fact_packet")["payload"]["facts"] if item["field"] == "evidence")["status"], "UNKNOWN")

    def test_21_review_is_not_fabricated(self):
        artifacts, _ = FixedPipeline("fast_path").run(load_complete())
        trust = next(item["payload"] for item in artifacts if item["artifact_type"] == "trust_report")
        self.assertIn("evidence.reviews", trust["gaps"])

    def test_22_qualification_is_not_fabricated(self):
        data = load_complete()
        data["evidence"] = {"cases": ["验收资料"], "reviews": ["验收资料"]}
        artifacts, _ = FixedPipeline("fast_path").run(data)
        trust = next(item["payload"] for item in artifacts if item["artifact_type"] == "trust_report")
        self.assertIn("evidence.qualifications", trust["gaps"])

    def test_23_upstream_artifact_is_immutable(self):
        store = ArtifactStore()
        store.put("fact_packet", "fact_normalization", "schema", {"fact_ids": []}, [], [])
        with self.assertRaises(ProtocolViolation):
            store.put("fact_packet", "fact_normalization", "schema", {"fact_ids": []}, [], [])

    def test_24_pipeline_order_cannot_change(self):
        protocol = ExecutionProtocol()
        with self.assertRaises(ProtocolViolation):
            protocol.check_stage("product_intelligence", ["fact_normalization"])

    def test_25_final_export_exists_only_after_validation(self):
        pipeline = FixedPipeline("fast_path")
        artifacts, trace = pipeline.run(load_complete())
        with tempfile.TemporaryDirectory() as directory:
            render_final(Path(directory), artifacts, trace)
            self.assertEqual(len(list(Path(directory).iterdir())), 10)


if __name__ == "__main__":
    unittest.main()
