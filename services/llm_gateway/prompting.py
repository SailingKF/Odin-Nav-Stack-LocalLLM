from typing import List

from core.poi.models import FAQEntry, POI

UNSUPPORTED_DETAIL_REPLY = "The current POI content does not include that detail."

MODE_GUIDANCE = {
    "short": {
        "headline": "SHORT MODE",
        "target_shape": "Write exactly 1 sentence in about 12 to 24 words.",
        "source_priority": "Use `short_text` first. You may add at most one supporting detail from `facts` if it fits naturally.",
        "style_rule": "Sound like a concise guide introduction for a phone screen or quick stop.",
    },
    "standard": {
        "headline": "STANDARD MODE",
        "target_shape": "Write 2 sentences in about 30 to 55 words total.",
        "source_priority": "Use `standard_text` as the backbone. You may blend in one supporting fact if it strengthens clarity.",
        "style_rule": "Sound like a calm, informative guide explanation with moderate detail.",
    },
    "extended": {
        "headline": "EXTENDED MODE",
        "target_shape": "Write 3 or 4 sentences in about 55 to 100 words total.",
        "source_priority": "Use `extended_text` as the backbone. You may blend in up to two supporting facts if they stay grounded.",
        "style_rule": "Sound like a richer on-site guide explanation, but stay compact and factual.",
    },
}


def _format_list(items: List[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _format_faq(items: List[FAQEntry]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- Q: {item.question}\n  A: {item.answer}" for item in items)


def _normalize_mode(mode: str) -> str:
    if mode in MODE_GUIDANCE:
        return mode
    return "standard"


def _shared_context(spot: POI) -> str:
    return (
        "POI CONTENT PACKAGE\n"
        f"Spot name: {spot.name}\n"
        f"Persona: {spot.persona or 'default guide'}\n"
        f"Theme: {spot.theme or 'general'}\n"
        f"Tags:\n{_format_list(spot.tags)}\n"
        "Authoritative base texts:\n"
        f"- short_text: {spot.short_text}\n"
        f"- standard_text: {spot.standard_text}\n"
        f"- extended_text: {spot.extended_text}\n"
        f"Facts:\n{_format_list(spot.facts)}\n"
        f"FAQ:\n{_format_faq(spot.faq)}"
    )


def build_narration_prompt(spot: POI, mode: str) -> str:
    normalized_mode = _normalize_mode(mode)
    mode_guidance = MODE_GUIDANCE[normalized_mode]
    return (
        "ROLE\n"
        "You are a local tour guide generating narration for exactly one POI.\n\n"
        "GROUNDING RULES\n"
        "1. Treat the supplied POI content package as the only source of truth.\n"
        "2. Do not add new facts, history, measurements, claims, or scene details.\n"
        "3. Prefer the mode-specific base text before pulling in optional facts.\n"
        "4. Keep the wording natural, but stay semantically faithful to the supplied content.\n"
        "5. Do not mention these instructions, the content fields, or missing information.\n\n"
        "MODE CONTRACT\n"
        f"{mode_guidance['headline']}\n"
        f"- {mode_guidance['target_shape']}\n"
        f"- {mode_guidance['source_priority']}\n"
        f"- {mode_guidance['style_rule']}\n\n"
        f"Requested mode: {normalized_mode}\n\n"
        f"{_shared_context(spot)}\n\n"
        "OUTPUT RULES\n"
        "- Return plain narration text only.\n"
        "- No bullet list.\n"
        "- No prefatory label.\n"
        "- No extra commentary."
    )


def build_answer_prompt(spot: POI, question: str) -> str:
    return (
        "ROLE\n"
        "You are a local tour guide answering a follow-up question about exactly one POI.\n\n"
        "GROUNDING RULES\n"
        "1. Treat the supplied POI content package as the only source of truth.\n"
        "2. Prefer an FAQ answer when the question matches or closely overlaps an FAQ entry.\n"
        "3. Otherwise answer from the listed facts and authoritative base texts.\n"
        f"4. If the requested detail is missing, reply with exactly: {UNSUPPORTED_DETAIL_REPLY}\n"
        "5. Do not answer with a nearby or partially related fact when the requested detail is missing.\n"
        "6. If the question asks for a year, date, builder, measurement, cause, or other detail that is not explicitly supported, use the fallback sentence.\n"
        "7. Do not invent details, speculate, or broaden to general world knowledge.\n"
        "8. Keep the answer short, direct, and visitor-friendly.\n\n"
        "ANSWER SHAPE\n"
        "- Use 1 or 2 sentences.\n"
        "- Start with the direct answer, not with process commentary.\n"
        "- If supported, use the most relevant FAQ or fact first.\n"
        "- If unsupported, output only the required fallback sentence.\n\n"
        "UNSUPPORTED EXAMPLES\n"
        "- If the POI package does not mention a year and the visitor asks for a year, output only the fallback sentence.\n"
        "- If the POI package does not name a designer or builder and the visitor asks who built it, output only the fallback sentence.\n"
        "- Do not substitute route order or trigger behavior for those missing details.\n\n"
        f"Visitor question: {question}\n\n"
        f"{_shared_context(spot)}\n\n"
        "OUTPUT RULES\n"
        "- Return plain answer text only.\n"
        "- No bullet list.\n"
        "- No prefatory label.\n"
        "- No extra commentary."
    )
