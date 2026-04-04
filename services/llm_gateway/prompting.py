from typing import List

from core.poi.models import FAQEntry, POI


def _format_list(items: List[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _format_faq(items: List[FAQEntry]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- Q: {item.question}\n  A: {item.answer}" for item in items)


def _shared_context(spot: POI) -> str:
    return (
        f"Spot name: {spot.name}\n"
        f"Persona: {spot.persona or 'default guide'}\n"
        f"Theme: {spot.theme or 'general'}\n"
        f"Tags:\n{_format_list(spot.tags)}\n"
        f"Short text:\n{spot.short_text}\n"
        f"Standard text:\n{spot.standard_text}\n"
        f"Extended text:\n{spot.extended_text}\n"
        f"Facts:\n{_format_list(spot.facts)}\n"
        f"FAQ:\n{_format_faq(spot.faq)}"
    )


def build_narration_prompt(spot: POI, mode: str) -> str:
    return (
        "You are a local museum-style guide.\n"
        "Use only the supplied POI content as the source of truth.\n"
        "Do not invent facts. Keep the answer concise, natural, and faithful to the content.\n"
        f"Requested mode: {mode}\n"
        "If the mode is short, produce a brief intro.\n"
        "If the mode is standard, produce a balanced explanation.\n"
        "If the mode is extended, give a richer explanation but stay within the provided facts.\n\n"
        f"{_shared_context(spot)}\n\n"
        "Return only the final narration text."
    )


def build_answer_prompt(spot: POI, question: str) -> str:
    return (
        "You are a local tour guide answering a follow-up question about a single POI.\n"
        "Use only the supplied POI content, facts, and FAQ as the source of truth.\n"
        "If the answer is not supported, say that the current POI content does not include that detail.\n"
        "Keep the answer short and specific.\n\n"
        f"Visitor question: {question}\n\n"
        f"{_shared_context(spot)}\n\n"
        "Return only the final answer text."
    )
