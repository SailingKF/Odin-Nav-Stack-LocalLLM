from fastapi import FastAPI
from pydantic import BaseModel

from core.narrator.mock_narrator import MockNarrator
from core.poi.models import POI


class GenerateNarrationRequest(BaseModel):
    spot: dict
    mode: str = "standard"


class AnswerQuestionRequest(BaseModel):
    spot: dict
    question: str


def create_app() -> FastAPI:
    app = FastAPI(title="Odin Local LLM Gateway", version="0.1.0")
    fallback_narrator = MockNarrator()

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "service": "llm-gateway",
            "backend": "mock-scaffold",
            "target_model": "future-gemma4-local",
        }

    @app.post("/generate_narration")
    def generate_narration(payload: GenerateNarrationRequest) -> dict:
        spot = POI.from_dict(payload.spot)
        narration_text = fallback_narrator.generate_narration(spot, payload.mode)
        return {
            "backend": "mock-scaffold",
            "mode": payload.mode,
            "narration_text": narration_text,
        }

    @app.post("/answer_question")
    def answer_question(payload: AnswerQuestionRequest) -> dict:
        spot = POI.from_dict(payload.spot)
        answer_text = fallback_narrator.answer_question(spot, payload.question)
        return {
            "backend": "mock-scaffold",
            "answer_text": answer_text,
        }

    return app
