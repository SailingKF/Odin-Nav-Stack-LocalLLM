from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.mvsim_validation_harness.runtime import MVSimValidationHarnessRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_DIR = Path(__file__).resolve().parent / "static"


class ValidationRequest(BaseModel):
    question: str = "What does this final stop prove?"


def create_app(
    runtime: Optional[MVSimValidationHarnessRuntime] = None,
    config_path: Optional[Path] = None,
    harness_url: str = "http://127.0.0.1:8300",
) -> FastAPI:
    app = FastAPI(title="MVSim Validation Harness", version="0.1.0")
    active_runtime = runtime or MVSimValidationHarnessRuntime(
        config_path=config_path or REPO_ROOT / "configs" / "sim.yaml",
        repo_root=REPO_ROOT,
        harness_url=harness_url,
    )
    app.state.runtime = active_runtime
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR)), name="assets")

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/harness", status_code=307)

    @app.get("/harness", include_in_schema=False)
    def harness_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict:
        return active_runtime.status()

    @app.get("/status")
    def status() -> dict:
        return active_runtime.status()

    @app.post("/services/start")
    def start_services() -> dict:
        return active_runtime.start_local_stack()

    @app.post("/services/stop")
    def stop_services() -> dict:
        return active_runtime.stop_local_stack()

    @app.post("/validation/run")
    def run_validation(payload: ValidationRequest) -> dict:
        return active_runtime.run_validation(question=payload.question)

    @app.get("/debug-link")
    def debug_link() -> dict:
        return {"debug_url": active_runtime.debug_url}

    return app
