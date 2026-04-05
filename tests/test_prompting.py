import unittest

from core.poi.loader import load_pois
from services.llm_gateway.prompting import (
    UNSUPPORTED_DETAIL_REPLY,
    build_answer_prompt,
    build_narration_prompt,
)


class PromptingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.poi = load_pois("content/poi/demo_pois.yaml")[0]

    def test_short_mode_prompt_has_tight_shape_and_grounding(self) -> None:
        prompt = build_narration_prompt(self.poi, "short")

        self.assertIn("SHORT MODE", prompt)
        self.assertIn("exactly 1 sentence", prompt)
        self.assertIn("Use `short_text` first", prompt)
        self.assertIn("only source of truth", prompt)
        self.assertIn(self.poi.short_text, prompt)

    def test_standard_mode_prompt_uses_standard_text_as_backbone(self) -> None:
        prompt = build_narration_prompt(self.poi, "standard")

        self.assertIn("STANDARD MODE", prompt)
        self.assertIn("Use `standard_text` as the backbone", prompt)
        self.assertIn("2 sentences", prompt)
        self.assertIn(self.poi.standard_text, prompt)

    def test_extended_mode_prompt_allows_more_detail_but_stays_grounded(self) -> None:
        prompt = build_narration_prompt(self.poi, "extended")

        self.assertIn("EXTENDED MODE", prompt)
        self.assertIn("3 or 4 sentences", prompt)
        self.assertIn("Use `extended_text` as the backbone", prompt)
        self.assertIn("up to two supporting facts", prompt)
        self.assertIn(self.poi.extended_text, prompt)

    def test_unknown_mode_falls_back_to_standard_contract(self) -> None:
        prompt = build_narration_prompt(self.poi, "unexpected_mode")

        self.assertIn("Requested mode: standard", prompt)
        self.assertIn("STANDARD MODE", prompt)
        self.assertNotIn("Requested mode: unexpected_mode", prompt)

    def test_answer_prompt_prioritizes_faq_and_declines_unsupported_details(self) -> None:
        prompt = build_answer_prompt(self.poi, "Who designed this gate?")

        self.assertIn("Prefer an FAQ answer", prompt)
        self.assertIn("Otherwise answer from the listed facts", prompt)
        self.assertIn(UNSUPPORTED_DETAIL_REPLY, prompt)
        self.assertIn("Do not answer with a nearby or partially related fact", prompt)
        self.assertIn("If the question asks for a year, date, builder, measurement, cause, or other detail that is not explicitly supported", prompt)
        self.assertIn("If unsupported, output only the required fallback sentence.", prompt)
        self.assertIn("Visitor question: Who designed this gate?", prompt)


if __name__ == "__main__":
    unittest.main()
