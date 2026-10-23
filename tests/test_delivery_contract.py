"""Regression checks for client/CLI format drift and keyword identity errors."""

import copy
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

from core.standard_pipeline import PERSONA_UNITS, StandardPathBlocked, StandardPathPipeline
from core.standard_renderer import render_standard
from scripts.check_delivery import validate_delivery
from scripts.package_skill import package_skill
from tests.test_standard_path import load_json


class DeliveryContractTests(unittest.TestCase):
    def report(self, mode="完整模式", company=None):
        company = copy.deepcopy(company or load_json("complete-v4-company.json"))
        preferences = company.setdefault("geo_preferences", {})
        preferences["output_mode"] = mode
        preferences.setdefault("delivery_mode", "简约版")
        if mode != "仅词模式":
            preferences.setdefault("approved_keywords", [company["company_name"]])
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        with tempfile.TemporaryDirectory() as directory:
            render_standard(Path(directory), artifacts)
            report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        return report, artifacts

    def test_modes_keep_fixed_order_and_repeatable_structure(self):
        for mode in ("完整模式", "仅词模式", "仅画像模式"):
            with self.subTest(mode=mode):
                first, _ = self.report(mode)
                second, _ = self.report(mode)
                self.assertEqual(first, second)
                validate_delivery(first, mode, "简约版")
                headings = re.findall(r"^## .+", first, re.M)
                self.assertEqual(headings[0], "## 客户资料摘要")
                self.assertEqual(headings[-2:], ["## 待补资料", "## 下一步建议"])
                if mode != "仅画像模式":
                    self.assertEqual(first.count("| 推荐词 | 短词根 |"), 4)
                if mode != "仅词模式":
                    section = first.split("## 九大画像", 1)[1].split("## 待补资料", 1)[0]
                    self.assertEqual(len(re.findall(r"^### .+", section, re.M)), 9)

    def test_structure_drift_is_rejected(self):
        report, _ = self.report()
        invalid_reports = [
            report.replace("| 推荐词 | 短词根 |", "| 推荐词 | 短词根 | 意向程度 |", 1),
            report.replace("### 品牌故事", "### 搜索用户画像", 1),
            report.replace("### 客户评价", "### 创始人介绍", 1),
            report.replace("## 待补资料", "## 额外报告\n\n## 待补资料", 1),
            "```markdown\n" + report + "```",
        ]
        for invalid in invalid_reports:
            with self.assertRaises(ValueError):
                validate_delivery(invalid, "完整模式", "简约版")
        with self.assertRaises(ValueError):
            validate_delivery(report, "完整模式", "完整版")

    def test_profile_contents_follow_names_even_if_payload_order_changes(self):
        _, artifacts = self.report()
        artifacts["persona_plan"]["personas"].reverse()
        with tempfile.TemporaryDirectory() as directory:
            render_standard(Path(directory), artifacts)
            report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        product = report.split("### 产品或服务描述\n", 1)[1].split("### 产品或服务特点", 1)[0]
        self.assertIn("工业设备方案", product)
        artifacts["persona_plan"]["personas"][0]["name"] = "错误板块"
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            render_standard(Path(directory), artifacts)

    def test_customer_brand_and_query_roots_are_not_replaced_by_product_brand(self):
        company = load_json("complete-v4-company.json")
        company.update({
            "company_name": "大作美居",
            "main_businesses": ["丝涟床垫零售", "丝涟床垫工程供货"],
            "products": [{"name": "丝涟床垫"}],
            "positioning": "京北本地床垫体验服务商",
            "service_regions": ["北京市朝阳区", "京北"],
            "use_cases": ["新房装修选床垫"],
            "user_intents": [],
        })
        report, artifacts = self.report("仅词模式", company=company)
        keywords = artifacts["keyword_matrix"]["keywords"]
        for item in keywords:
            if item["keyword_type"] == "品牌词":
                self.assertTrue(item["keyword"].startswith("大作美居"))
            if item["keyword_type"] in ("搜索词", "问答词"):
                self.assertFalse(any(region in item["keyword"] for region in ("北京", "朝阳", "京北", "本地")))
            if item["keyword_type"] in ("问答词", "意图场景词"):
                self.assertNotIn("零售", item["keyword"])
        questions = [item for item in keywords if item["keyword_type"] == "问答词"]
        self.assertGreater(len({item["root_phrase"] for item in questions}), 1)
        intents = [item for item in keywords if item["keyword_type"] == "意图场景词"]
        self.assertTrue(all(item["intent_level"] == "中意向" for item in intents))
        self.assertNotIn("我想用", report)

    def test_regional_client_words_survive_in_records_not_recommendation_rows(self):
        company = load_json("complete-v4-company.json")
        company["service_regions"] = ["深圳市"]
        company["geo_preferences"] = {"requested_keywords": ["深圳工业设备服务商"]}
        report, artifacts = self.report("仅词模式", company=company)
        self.assertTrue(any(item["keyword"] == "深圳工业设备服务商" for item in artifacts["keyword_matrix"]["keywords"]))
        self.assertNotIn("| 深圳工业设备服务商 |", report)
        self.assertIn("未纳入推荐：深圳工业设备服务商", report)

    def test_standalone_bundle_can_validate_without_repository(self):
        report, _ = self.report()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "geo-keyword-persona"
            archive = root / "skill.zip"
            package_skill(target, archive)
            case = root / "case.md"
            case.write_text(report, encoding="utf-8")
            result = subprocess.run([sys.executable, str(target / "scripts/check_delivery.py"), str(case),
                                     "--output-mode", "完整模式", "--delivery-mode", "简约版"],
                                    cwd=root, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(bundle.read("geo-keyword-persona/templates/delivery.md"),
                                 (target / "templates/delivery.md").read_bytes())
            self.assertFalse((target / "core").exists())

    def test_first_round_is_keywords_only_without_long_profile_requirements(self):
        company = load_json("complete-v4-company.json")
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        self.assertEqual(artifacts["company_context"]["output_mode"], "仅词模式")
        self.assertEqual(artifacts["guided_next_steps"]["delivery_mode"], "完整版")
        self.assertTrue(artifacts["guided_next_steps"]["decision_required"])
        self.assertEqual(artifacts["guided_next_steps"]["current_stage"], "keyword_selection")
        with tempfile.TemporaryDirectory() as directory:
            render_standard(Path(directory), artifacts)
            report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
        validate_delivery(report)
        self.assertNotIn("## 九大画像", report)
        self.assertNotIn("意向程度", report)
        self.assertIn("补充你想做的词", report)

    def test_profile_gate_rejects_missing_unknown_excluded_and_cross_business_selection(self):
        for mode in ("仅画像模式", "完整模式"):
            for approved, extra in (
                ([], {}),
                (["未出现的词"], {}),
                (["测试企业（仅验收数据）"], {"excluded_keywords": ["测试企业（仅验收数据）"]}),
                (["其他业务词"], {"requested_keywords": [{"keyword": "其他业务词", "business_line": "其他业务"}]}),
                (["全国设备采购"], {"requested_keywords": ["全国设备采购"]}),
                ([{"keyword": "不是字符串"}], {}),
            ):
                with self.subTest(mode=mode, approved=approved):
                    company = load_json("complete-v4-company.json")
                    company["geo_preferences"] = {
                        "output_mode": mode, "approved_keywords": approved, "delivery_mode": "简约版", **extra,
                    }
                    with self.assertRaises(StandardPathBlocked):
                        StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)

    def test_selected_words_and_profile_scope_are_carried_into_second_round(self):
        for vertical in ("", "工业设备服务"):
            company = load_json("complete-v4-company.json")
            word = "车间设备采购方案"
            company["geo_preferences"] = {
                "output_mode": "仅画像模式", "vertical_business": vertical,
                "approved_keywords": [word],
                "requested_keywords": [{"keyword": word, "keyword_type": "搜索词", "root_phrase": "设备采购",
                                        "business_line": "工业设备服务"}],
                # Length-only synthetic fixture, never a customer deliverable.
                "complete_personas": {name: "仅用于字数验收的合成文本。" * 70 for name in PERSONA_UNITS},
            }
            artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
            self.assertFalse(artifacts["guided_next_steps"]["decision_required"])
            chosen = next(item for item in artifacts["keyword_matrix"]["keywords"] if item["keyword"] == word)
            self.assertEqual(chosen["decision_status"], "CONFIRMED")
            self.assertFalse(chosen["needs_confirmation"])
            with tempfile.TemporaryDirectory() as directory:
                render_standard(Path(directory), artifacts)
                report = (Path(directory) / "GEO 关键词与画像.md").read_text(encoding="utf-8")
            validate_delivery(report, "仅画像模式", "完整版")
            self.assertNotIn("## 四类关键词", report)
            self.assertIn(f"本轮已选词：{word}。", report)
            self.assertIn("业务画像｜工业设备服务" if vertical else "画像范围：品牌画像", report)

    def test_combined_export_does_not_recommend_unselected_words(self):
        report, artifacts = self.report()
        approved = artifacts["guided_next_steps"]["keyword_review"]["approved"]
        section = report.split("## 四类关键词", 1)[1].split("## 九大画像", 1)[0]
        for item in artifacts["keyword_matrix"]["keywords"]:
            if item["keyword"] not in approved:
                self.assertNotIn(f"| {item['keyword']} |", section)
        with self.assertRaises(ValueError):
            validate_delivery(report.replace("本轮已选词：", "未确认词："), "完整模式", "简约版")

    def test_selection_without_profile_request_only_asks_for_scope(self):
        company = load_json("complete-v4-company.json")
        company["geo_preferences"] = {"approved_keywords": [company["company_name"]]}
        artifacts, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        self.assertEqual(artifacts["company_context"]["output_mode"], "仅词模式")
        self.assertEqual(artifacts["guided_next_steps"]["current_stage"], "profile_choice")
        self.assertIn("已记录所选词", artifacts["guided_next_steps"]["next_prompt"])

    def test_customer_can_add_unlisted_keyword_without_automatic_approval(self):
        company = load_json("complete-v4-company.json")
        word = "车间改造设备采购报价"
        before, _ = StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        self.assertNotIn(word, [item["keyword"] for item in before["keyword_matrix"]["keywords"]])
        company["geo_preferences"] = {"requested_keywords": [{
            "keyword": word, "keyword_type": "搜索词", "root_phrase": "设备采购报价",
            "business_line": "工业设备服务", "intent_level": "高意向",
        }]}
        report, artifacts = self.report("仅词模式", company)
        added = next(item for item in artifacts["keyword_matrix"]["keywords"] if item["keyword"] == word)
        self.assertEqual(added["keyword_origin"], "CLIENT_REQUESTED")
        self.assertEqual(added["decision_status"], "PENDING_CONFIRMATION")
        self.assertTrue(added["needs_confirmation"])
        self.assertIn(f"| {word} | 设备采购报价 |", report)
        self.assertEqual(added["intent_level"], "高意向")
        self.assertNotIn("高意向", report)
        company["geo_preferences"].update({"output_mode": "仅画像模式", "delivery_mode": "简约版"})
        with self.assertRaises(StandardPathBlocked):
            StandardPathPipeline().run(load_json("geo-bd-handoff-v1.json"), company)
        company["geo_preferences"]["approved_keywords"] = [word]
        report, artifacts = self.report("仅画像模式", company)
        self.assertIn(f"本轮已选词：{word}。", report)
        chosen = next(item for item in artifacts["keyword_matrix"]["keywords"] if item["keyword"] == word)
        self.assertEqual(chosen["decision_status"], "CONFIRMED")


if __name__ == "__main__":
    unittest.main()
