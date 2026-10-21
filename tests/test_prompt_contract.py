"""Guard the current GEO user-facing flow against stale multi-step prompts."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class PromptContractTests(unittest.TestCase):
    def test_standard_intake_offers_only_three_output_modes(self):
        prompt = (ROOT / "prompts/standard/00_quick_start.md").read_text(encoding="utf-8")
        for mode in ("完整模式", "仅词模式", "仅画像模式"):
            self.assertIn(mode, prompt)
        self.assertIn("默认完整模式", prompt)
        self.assertIn("不输出画像", prompt)
        self.assertIn("仅画像模式不输出关键词", prompt)
        self.assertIn("默认简约版", prompt)
        self.assertIn("每项 800–1000 字", prompt)

    def test_standard_flow_avoids_repeated_confirmation(self):
        prompt = (ROOT / "prompts/standard/00_quick_start.md").read_text(encoding="utf-8")
        confirmation = (ROOT / "prompts/standard/01_evidence_confirmation.md").read_text(encoding="utf-8")
        self.assertIn("不逐阶段、逐词或逐画像", prompt)
        self.assertIn("合并所有必要问题", prompt)
        self.assertIn("一次", confirmation)
        self.assertIn("不要求逐字段反复确认", confirmation)

    def test_four_keyword_types_are_canonical(self):
        rules = (ROOT / "references/keyword-rules.md").read_text(encoding="utf-8")
        for keyword_type in ("品牌词", "搜索词", "问答词", "意图场景词"):
            self.assertIn(keyword_type, rules)
        self.assertIn("使用场景 + 业务 + 定位", rules)
        self.assertIn("业务/需求 + 对比、判断、选择或适配问题", rules)
        self.assertIn("搜索词回答", rules)
        self.assertIn("问答词回答", rules)
        self.assertIn("意图场景词表达", rules)
        self.assertIn("不是搜索平台实测词", rules)
        self.assertIn("短词根通常 3–10 个字", rules)
        self.assertIn("高意向 60%、中意向 30%、低意向 10%", rules)

    def test_complete_persona_and_article_rules_are_strict(self):
        profile = (ROOT / "references/template-guide.md").read_text(encoding="utf-8")
        article = (ROOT / "references/article-training.md").read_text(encoding="utf-8")
        self.assertIn("每项 800–1000 字", profile)
        self.assertIn("Fail Closed", profile)
        self.assertIn("一个业务线、一个搜索角色、一个意向阶段", article)
        self.assertIn("1–2 个主词", article)

    def test_legacy_prompt_is_explicitly_out_of_standard_scope(self):
        start = (ROOT / "prompts/00_start_prompt.md").read_text(encoding="utf-8")
        contract = (ROOT / "prompts/_interaction_contract.md").read_text(encoding="utf-8")
        self.assertIn("仅在用户明确指定旧版 V4 时使用", start)
        self.assertIn("Standard Path 不加载本文件", contract)


if __name__ == "__main__":
    unittest.main()
