"""Phase-1 acceptance tests for the Prescription-driven Standard Path."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
    "GEO 关键词与画像.md",
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
    def test_00_cli_defaults_to_standard_and_requires_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = subprocess.run([
                sys.executable, str(ROOT / "main.py"), "--output", str(output)
            ], text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("--handoff is required in standard mode", result.stdout)
            self.assertFalse(output.exists())

    def test_01_standard_reads_geo_bd_handoff(self):
        artifacts, trace = run_pipeline()
        self.assertEqual(artifacts["execution"]["source_system"], "GEO-BD")
        self.assertEqual(trace["pipeline_id"], "geo-standard-path-v1")
        guidance = artifacts["guided_next_steps"]
        self.assertEqual(guidance["delivery_mode"], "简约版")
        self.assertFalse(guidance["decision_required"])
        self.assertEqual(guidance["recommended_next_stage"], "geo_training_operations")
        self.assertEqual(len(guidance["stages"]), 1)
        self.assertFalse(guidance["stages"][0]["requires_user_confirmation"])
        self.assertEqual(len(guidance["skill_recommendations"]), 1)
        self.assertEqual(len(guidance["optimization_directions"]), 1)

    def test_02_standard_reads_manual_prescription(self):
        artifacts, _ = run_pipeline("manual-prescription-v1.json")
        self.assertEqual(artifacts["execution"]["source_system"], "MANUAL")

    def test_03_standard_without_prescription_fails_closed(self):
        handoff = load_json("geo-bd-handoff-v1.json")
        handoff["prescriptions"] = []
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(handoff, load_json("complete-v4-company.json"))

    def test_03a_standard_requires_use_scenario(self):
        company = load_json("complete-v4-company.json")
        company["use_cases"] = []
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)

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

    def test_14_standard_outputs_one_training_and_operations_brief(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual({path.name for path in output.iterdir()}, STANDARD_OUTPUTS)
            content = (output / "GEO 关键词与画像.md").read_text(encoding="utf-8")
            for kind in ("品牌词", "搜索词", "问答词", "意图场景词"):
                self.assertIn(f"### {kind}｜", content)
            for purpose in ("训练品牌识别", "训练使用场景", "训练业务需求", "训练明确需求"):
                self.assertIn(purpose, content)
            self.assertIn("## 九大画像", content)
            self.assertIn("系统推荐，待确认", content)
            self.assertNotIn("你的选择", content)

    def test_15_standard_outputs_persona_markdown(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            content = (output / "GEO 关键词与画像.md").read_text(encoding="utf-8")
            for name in PERSONA_UNITS:
                self.assertIn(f"### {name}", content)

    def test_16_standard_outputs_traceable_keyword_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            artifacts, _ = run_pipeline()
            matrix = artifacts["keyword_matrix"]
            self.assertEqual(matrix["keyword_version"], "1.1.0")
            required = {
                "keyword", "keyword_type", "root_phrase", "intent_level", "search_role",
                "business_line", "region", "product_or_service", "user_scenario",
                "search_intent", "persona_unit", "fact_ids", "prescription_ids",
                "strategy_ids", "intent_ids", "evidence_status", "risk_level",
                "needs_confirmation", "keyword_origin", "decision_status",
            }
            self.assertTrue(matrix["keywords"])
            self.assertTrue(required.issubset(matrix["keywords"][0]))
            generated = {item["keyword"] for item in matrix["keywords"] if item["keyword_origin"] == "SYSTEM_RECOMMENDED"}
            self.assertIn("测试企业（仅验收数据） 工业设备服务", generated)
            self.assertIn("车间设备改造 工业设备服务商", generated)
            self.assertIn("工业设备服务怎么选？", generated)
            self.assertIn("我需要车间设备改造，请推荐工业设备服务", generated)
            content = (output / "GEO 关键词与画像.md").read_text(encoding="utf-8")
            self.assertIn("| 推荐词 | 短词根 | 意向 | 搜索角色 | 训练用途 | 状态 |", content)
            self.assertIn("| 我需要车间设备改造，请推荐工业设备服务 |", content)
            self.assertIn("不是平台实测热搜词", content)
            self.assertNotIn("## 六类词根", content)
            self.assertNotIn("## 核心词根画像卡", content)

    def test_17_standard_outputs_user_personas_and_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            result = self._run_standard_cli(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            artifacts, _ = run_pipeline()
            user_plan = artifacts["user_persona_plan"]
            self.assertEqual(user_plan["user_persona_version"], "1.1.0")
            self.assertTrue(user_plan["personas"])
            for field in (
                "business_line", "region", "organization_scale", "purchase_authority",
                "decision_stage", "content_preferences", "exclusions",
            ):
                self.assertIn(field, user_plan["personas"][0])
            self.assertIn("next_prompt", artifacts["guided_next_steps"])
            content = (output / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        self.assertIn("## 下一步建议", content)

    def test_18_standard_accepts_guided_preferences(self):
        handoff = load_json("geo-bd-handoff-v1.json")
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {
            "delivery_mode": "简约版",
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
        self.assertEqual(artifacts["guided_next_steps"]["recommended_next_stage"], "geo_training_operations")
        self.assertFalse(artifacts["guided_next_steps"]["decision_required"])

        company["geo_preferences"]["approved_keywords"] = ["测试企业代理加盟"]
        approved_artifacts, _ = StandardPathPipeline().run(handoff, company)
        self.assertEqual(approved_artifacts["guided_next_steps"]["recommended_next_stage"], "geo_training_operations")
        approved = [item for item in approved_artifacts["keyword_matrix"]["keywords"] if item["keyword"] == "测试企业代理加盟"]
        self.assertEqual(approved[0]["decision_status"], "CONFIRMED")

    def test_18a_report_uses_all_confirmed_business_roots_and_three_priority_terms(self):
        from core.standard_renderer import render_standard
        company = load_json("complete-v4-company.json")
        company["main_businesses"].append("设备运维服务")
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_standard(output, artifacts)
            report = (output / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        self.assertIn("工业设备服务", report)
        self.assertIn("设备运维服务", report)
        for kind in ("品牌词", "搜索词", "问答词", "意图场景词"):
            self.assertGreaterEqual(sum(item["keyword_type"] == kind for item in artifacts["keyword_matrix"]["keywords"]), 3)
        self.assertIn("## 九大画像", report)

    def test_18b_vertical_report_does_not_mix_other_business_facts(self):
        from core.standard_renderer import render_standard
        company = load_json("complete-v4-company.json")
        company["main_businesses"].append("设备运维服务")
        company["geo_preferences"] = {"delivery_mode": "简约版", "vertical_business": "设备运维服务"}
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            render_standard(output, artifacts)
            report = (output / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        self.assertIn("设备运维服务", report)
        self.assertNotIn("工业设备服务怎么选", report)
        self.assertIn("【需确认本板块资料与指定业务的关联】", report)
        self.assertIn("待核对指定业务产品", report)

    def test_18c_unknown_vertical_business_fails_closed(self):
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {"vertical_business": "未确认业务"}
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)

    def test_18d_output_modes_do_not_leak_other_sections(self):
        from core.standard_renderer import render_standard
        for mode, included, excluded in (
            ("仅词模式", "## 四类关键词", ("## 九大画像",)),
            ("仅画像模式", "## 九大画像", ("## 四类关键词",)),
            ("完整模式", "## 四类关键词", ()),
        ):
            company = load_json("complete-v4-company.json")
            company["geo_preferences"] = {"output_mode": mode}
            artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
            with tempfile.TemporaryDirectory() as directory:
                render_standard(Path(directory), artifacts)
                report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
            self.assertIn(included, report)
            self.assertNotIn("## 六类词根", report)
            self.assertNotIn("## 核心词根画像卡", report)
            if mode == "完整模式":
                self.assertIn("## 九大画像", report)
            for section in excluded:
                self.assertNotIn(section, report)

    def test_18da_complete_persona_requires_each_section_to_be_800_to_1000_chars(self):
        from core.standard_renderer import render_standard
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {"output_mode": "仅画像模式", "delivery_mode": "完整版"}
        with self.assertRaises(StandardPathBlocked) as context:
            StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        self.assertIn("每项必须为800-1000字", str(context.exception))

        complete_text = "完整画像内容" * 140
        self.assertTrue(800 <= len(complete_text) <= 1000)
        company["geo_preferences"]["complete_personas"] = {
            name: complete_text for name in PERSONA_UNITS
        }
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        with tempfile.TemporaryDirectory() as directory:
            render_standard(Path(directory), artifacts)
            report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        self.assertIn("## 九大画像｜品牌画像", report)
        self.assertIn(complete_text, report)

    def test_18db_complete_persona_rejects_content_over_1000_chars(self):
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {
            "output_mode": "仅画像模式",
            "delivery_mode": "完整版",
            "complete_personas": {name: "超长画像内容" * 180 for name in PERSONA_UNITS},
        }
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)

    def test_18e_scenario_roots_and_search_terms_drop_regions(self):
        from core.standard_renderer import render_standard
        company = load_json("complete-v4-company.json")
        company["service_regions"] = ["中国广东省深圳市"]
        company["use_cases"] = ["申请深圳市本地渠道项目", "为本地企业承接AI搜索获客需求"]
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        search_and_answers = [
            item["keyword"] for item in artifacts["keyword_matrix"]["keywords"]
            if item["keyword_type"] in ("搜索词", "问答词")
        ]
        self.assertTrue(search_and_answers)
        self.assertTrue(all("深圳" not in term and "本地" not in term for term in search_and_answers))
        self.assertEqual(artifacts["intent_strategy"]["intents"][0]["scenario"], "为本地企业承接AI搜索获客需求")
        with tempfile.TemporaryDirectory() as directory:
            render_standard(Path(directory), artifacts)
            report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        self.assertIn("AI搜索获客需求", report)
        self.assertNotIn("深圳", "\n".join(search_and_answers))

    def test_18f_each_keyword_type_is_limited_to_twelve(self):
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {"requested_keywords": [
            {"keyword": f"客户词{i}", "keyword_type": "品牌词"} for i in range(13)
        ]}
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)

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
