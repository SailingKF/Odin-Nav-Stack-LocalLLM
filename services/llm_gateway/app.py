from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.poi.models import POI
from services.llm_gateway.backends import GatewayBackend, MockGatewayBackend, build_gateway_backend

REPO_ROOT = Path(__file__).resolve().parents[2]


class GenerateNarrationRequest(BaseModel):
    spot: dict
    mode: str = "standard"


class AnswerQuestionRequest(BaseModel):
    spot: dict
    question: str


class LocalLLMGateway:
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._primary_backend = build_gateway_backend(config)
        self._fallback_enabled = bool(config.get("llm_enable_fallback", True))
        self._fallback_backend: Optional[GatewayBackend] = None
        if self._fallback_enabled and self._primary_backend.backend_type != "mock":
            self._fallback_backend = MockGatewayBackend()

    @classmethod
    def from_config_path(cls, config_path: Path) -> "LocalLLMGateway":
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        return cls(config=config)

    def _select_backend(self) -> Dict[str, Any]:
        primary_health = self._primary_backend.health()
        fallback_health = self._fallback_backend.health() if self._fallback_backend is not None else None
        fallback_active = bool(self._fallback_backend is not None and not primary_health["available"] and fallback_health and fallback_health["available"])
        active_backend = self._fallback_backend if fallback_active else self._primary_backend
        return {
            "active_backend": active_backend,
            "primary_health": primary_health,
            "fallback_health": fallback_health,
            "fallback_active": fallback_active,
        }

    def health(self) -> Dict[str, Any]:
        selection = self._select_backend()
        primary_health = selection["primary_health"]
        fallback_health = selection["fallback_health"]
        fallback_active = selection["fallback_active"]
        status = "ok" if primary_health["available"] else "degraded" if fallback_active else "error"
        active_backend = selection["active_backend"]

        return {
            "status": status,
            "service": "llm-gateway",
            "configured_backend_type": self._primary_backend.backend_type,
            "active_backend_type": active_backend.backend_type,
            "model_name": active_backend.model_name,
            "fallback_enabled": self._fallback_enabled,
            "fallback_active": fallback_active,
            "primary_backend": primary_health,
            "fallback_backend": fallback_health,
        }

    def _run_with_fallback(self, operation: str, fn_name: str, *args: Any) -> Dict[str, Any]:
        selection = self._select_backend()
        active_backend = selection["active_backend"]
        try:
            text = getattr(active_backend, fn_name)(*args)
            return {
                "status": "ok" if not selection["fallback_active"] else "degraded",
                "backend_type": active_backend.backend_type,
                "model_name": active_backend.model_name,
                "fallback_used": selection["fallback_active"],
                "text": text,
            }
        except Exception as exc:
            if self._fallback_backend is not None and active_backend is self._primary_backend:
                fallback_text = getattr(self._fallback_backend, fn_name)(*args)
                return {
                    "status": "degraded",
                    "backend_type": self._fallback_backend.backend_type,
                    "model_name": self._fallback_backend.model_name,
                    "fallback_used": True,
                    "text": fallback_text,
                    "warning": f"{operation} fell back after primary backend error: {exc}",
                }
            raise HTTPException(status_code=503, detail=f"{operation} failed and no fallback backend was available: {exc}")

    def generate_narration(self, payload: GenerateNarrationRequest) -> Dict[str, Any]:
        spot = POI.from_dict(payload.spot)
        result = self._run_with_fallback("generate_narration", "generate_narration", spot, payload.mode)
        return {
            "status": result["status"],
            "backend_type": result["backend_type"],
            "model_name": result["model_name"],
            "fallback_used": result["fallback_used"],
            "mode": payload.mode,
            "narration_text": result["text"],
            "warning": result.get("warning"),
        }

    def answer_question(self, payload: AnswerQuestionRequest) -> Dict[str, Any]:
        spot = POI.from_dict(payload.spot)
        result = self._run_with_fallback("answer_question", "answer_question", spot, payload.question)
        return {
            "status": result["status"],
            "backend_type": result["backend_type"],
            "model_name": result["model_name"],
            "fallback_used": result["fallback_used"],
            "answer_text": result["text"],
            "warning": result.get("warning"),
        }


def create_app(
    gateway: Optional[LocalLLMGateway] = None,
    config: Optional[Dict[str, Any]] = None,
    config_path: Optional[Path] = None,
) -> FastAPI:
    app = FastAPI(title="Odin Local LLM Gateway", version="0.2.0")
    if gateway is not None:
        active_gateway = gateway
    elif config is not None:
        active_gateway = LocalLLMGateway(config)
    else:
        active_gateway = LocalLLMGateway.from_config_path(config_path or REPO_ROOT / "configs" / "dev.yaml")
    app.state.gateway = active_gateway

    @app.get("/health")
    def health() -> dict:
        return active_gateway.health()

    @app.post("/generate_narration")
    def generate_narration(payload: GenerateNarrationRequest) -> dict:
        return active_gateway.generate_narration(payload)

    @app.post("/answer_question")
    def answer_question(payload: AnswerQuestionRequest) -> dict:
        return active_gateway.answer_question(payload)

    return app
