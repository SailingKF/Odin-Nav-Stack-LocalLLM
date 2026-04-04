import json
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.interfaces.narrator import Narrator
from core.narrator.mock_narrator import MockNarrator
from core.poi.models import POI


class LocalLLMNarrator(Narrator):
    def __init__(
        self,
        gateway_url: Optional[str] = None,
        timeout_seconds: float = 5.0,
        fallback_narrator: Optional[Narrator] = None,
    ) -> None:
        self._gateway_url = gateway_url.rstrip("/") if gateway_url else None
        self._timeout_seconds = timeout_seconds
        self._fallback_narrator = fallback_narrator or MockNarrator()

    def _post_json(self, path: str, payload: dict) -> dict:
        if not self._gateway_url:
            raise URLError("No llm_gateway_url configured")

        request = Request(
            url=f"{self._gateway_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self._timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def generate_narration(self, spot: POI, mode: str = "standard") -> str:
        try:
            payload = self._post_json(
                "/generate_narration",
                {"spot": spot.to_content_dict(), "mode": mode},
            )
            return str(payload["narration_text"])
        except Exception:
            return self._fallback_narrator.generate_narration(spot, mode)

    def answer_question(self, spot: POI, question: str) -> str:
        try:
            payload = self._post_json(
                "/answer_question",
                {"spot": spot.to_content_dict(), "question": question},
            )
            return str(payload["answer_text"])
        except Exception:
            return self._fallback_narrator.answer_question(spot, question)
