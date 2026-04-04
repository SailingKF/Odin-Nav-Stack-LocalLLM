import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.narrator.mock_narrator import MockNarrator
from core.poi.models import POI
from services.llm_gateway.prompting import build_answer_prompt, build_narration_prompt


class GatewayBackend(ABC):
    backend_type = "base"

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Return backend health details."""

    @abstractmethod
    def generate_narration(self, spot: POI, mode: str) -> str:
        """Generate narration text from structured content."""

    @abstractmethod
    def answer_question(self, spot: POI, question: str) -> str:
        """Answer a follow-up question from structured content."""


class MockGatewayBackend(GatewayBackend):
    backend_type = "mock"

    def __init__(self, model_name: str = "mock-curated-content") -> None:
        super().__init__(model_name=model_name)
        self._narrator = MockNarrator()

    def health(self) -> Dict[str, Any]:
        return {
            "available": True,
            "backend_type": self.backend_type,
            "model_name": self.model_name,
            "detail": "Mock backend is always available.",
        }

    def generate_narration(self, spot: POI, mode: str) -> str:
        return self._narrator.generate_narration(spot, mode)

    def answer_question(self, spot: POI, question: str) -> str:
        return self._narrator.answer_question(spot, question)


class OllamaGatewayBackend(GatewayBackend):
    backend_type = "ollama"

    def __init__(
        self,
        model_name: str,
        base_url: str,
        timeout_sec: float = 8.0,
    ) -> None:
        super().__init__(model_name=model_name)
        self.base_url = base_url.rstrip("/")
        self.timeout_sec = timeout_sec

    def _request_json(self, path: str, payload: Optional[Dict[str, Any]] = None, method: str = "GET") -> Dict[str, Any]:
        request = Request(
            url=f"{self.base_url}{path}",
            data=None if payload is None else json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urlopen(request, timeout=self.timeout_sec) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}

    def health(self) -> Dict[str, Any]:
        try:
            payload = self._request_json("/api/tags")
            models = payload.get("models", [])
            available_models = [item.get("name") for item in models if item.get("name")]
            model_available = self.model_name in available_models
            detail = "Configured model is available." if model_available else "Ollama reachable but configured model is not listed."
            return {
                "available": model_available,
                "backend_type": self.backend_type,
                "model_name": self.model_name,
                "detail": detail,
                "available_models": available_models,
            }
        except Exception as exc:
            return {
                "available": False,
                "backend_type": self.backend_type,
                "model_name": self.model_name,
                "detail": str(exc),
                "available_models": [],
            }

    def _generate(self, prompt: str) -> str:
        payload = self._request_json(
            "/api/generate",
            {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                },
            },
            method="POST",
        )
        response_text = str(payload.get("response", "")).strip()
        if not response_text:
            raise URLError("Ollama returned an empty response.")
        return response_text

    def generate_narration(self, spot: POI, mode: str) -> str:
        return self._generate(build_narration_prompt(spot, mode))

    def answer_question(self, spot: POI, question: str) -> str:
        return self._generate(build_answer_prompt(spot, question))


def build_gateway_backend(config: Dict[str, Any]) -> GatewayBackend:
    backend_type = str(config.get("llm_backend_type", "mock"))
    if backend_type == "ollama":
        return OllamaGatewayBackend(
            model_name=str(config.get("llm_model_name", "gemma-local")),
            base_url=str(config.get("llm_base_url", "http://127.0.0.1:11434")),
            timeout_sec=float(config.get("llm_timeout_sec", 8.0)),
        )
    return MockGatewayBackend(model_name=str(config.get("llm_model_name", "mock-curated-content")))
