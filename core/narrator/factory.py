from typing import Any, Dict

from core.interfaces.narrator import Narrator
from core.narrator.local_llm_narrator import LocalLLMNarrator
from core.narrator.mock_narrator import MockNarrator


def build_narrator(config: Dict[str, Any]) -> Narrator:
    narrator_type = str(config.get("narrator_type", "mock"))
    if narrator_type == "local_llm":
        gateway_url = config.get("llm_gateway_url") or config.get("llm_base_url")
        return LocalLLMNarrator(
            gateway_url=gateway_url,
            timeout_seconds=float(config.get("llm_timeout_sec", 5.0)),
            fallback_enabled=bool(config.get("llm_enable_fallback", True)),
        )
    return MockNarrator()
