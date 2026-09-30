"""Guard the current GEO user-facing flow against stale multi-step prompts."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class PromptContractTests(unittest.TestCase):
    def test_standard_intake_offers_only_three_delivery_modes(self):
        prompt = (ROOT / "prompts/standard/00_quick_start.md").read_text(encoding="utf-8")
        for mode in ("简约版", "完整版", "垂直完整版"):
            self.assertIn(mode, prompt)
        self.assertIn("800–1000 个中文字", prompt)

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
        self.assertIn("业务需求 + 对比 / 判断 / 选择问题", rules)

    def test_legacy_prompt_is_explicitly_out_of_standard_scope(self):
        start = (ROOT / "prompts/00_start_prompt.md").read_text(encoding="utf-8")
        contract = (ROOT / "prompts/_interaction_contract.md").read_text(encoding="utf-8")
        self.assertIn("仅在用户明确指定旧版 V4 时使用", start)
        self.assertIn("Standard Path 不加载本文件", contract)


if __name__ == "__main__":
    unittest.main()
