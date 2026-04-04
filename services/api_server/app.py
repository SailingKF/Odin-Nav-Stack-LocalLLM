from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.api_server.runtime import MockTourApiRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"


class TourQuestionRequest(BaseModel):
    question: str


def create_app(
    runtime: Optional[MockTourApiRuntime] = None,
    config_path: Optional[Path] = None,
) -> FastAPI:
    app = FastAPI(title="Odin Nav Stack Local LLM Mock Tour API", version="0.1.0")
    active_runtime = runtime or MockTourApiRuntime.from_config_path(
        config_path=config_path or REPO_ROOT / "configs" / "dev.yaml",
        repo_root=REPO_ROOT,
    )
    app.state.runtime = active_runtime
    app.mount("/debug-assets", StaticFiles(directory=str(STATIC_DIR)), name="debug-assets")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/debug", status_code=307)

    @app.get("/debug", include_in_schema=False)
    def debug_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict:
        return active_runtime.health()

    @app.get("/state")
    def state() -> dict:
        return active_runtime.state()

    @app.post("/tour/start")
    def start_tour() -> dict:
        return active_runtime.start_tour()

    @app.post("/tour/pause")
    def pause_tour() -> dict:
        return active_runtime.pause_tour()

    @app.post("/tour/resume")
    def resume_tour() -> dict:
        return active_runtime.resume_tour()

    @app.post("/tour/next")
    def next_poi() -> dict:
        return active_runtime.next_poi()

    @app.post("/tour/question")
    def ask_question(payload: TourQuestionRequest) -> dict:
        return active_runtime.ask_question(payload.question)

    @app.get("/session/latest")
    def latest_session() -> dict:
        return active_runtime.latest_session()

    return app
