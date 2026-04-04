import re
from typing import Iterable

from core.interfaces.narrator import Narrator
from core.poi.models import POI


def _normalized_keywords(text: str) -> Iterable[str]:
    for token in re.findall(r"[a-zA-Z0-9_]+", text.lower()):
        if len(token) >= 4:
            yield token


class MockNarrator(Narrator):
    def generate_narration(self, spot: POI, mode: str = "standard") -> str:
        base_text = spot.text_for_mode(mode)
        if mode == "extended" and spot.facts:
            return f"{base_text} Key facts: {' '.join(spot.facts)}"
        return base_text

    def answer_question(self, spot: POI, question: str) -> str:
        lowered_question = question.strip().lower()
        if not lowered_question:
            return "Please provide a follow-up question for this POI."

        for faq_entry in spot.faq:
            faq_keywords = set(_normalized_keywords(faq_entry.question))
            question_keywords = set(_normalized_keywords(lowered_question))
            if faq_keywords and faq_keywords.intersection(question_keywords):
                return faq_entry.answer
            if faq_entry.question.lower() in lowered_question:
                return faq_entry.answer

        if spot.facts:
            return f"Based on the curated content for {spot.name}, {spot.facts[0]}"

        return f"The mock narrator does not have a more specific answer for {spot.name} yet."
