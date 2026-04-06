from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from services.sim_pose_ingress.runtime import SimPoseIngressRuntime

REPO_ROOT = Path(__file__).resolve().parents[2]


class PosePayload(BaseModel):
    x: float
    y: float
    label: Optional[str] = None


class PoseBatchRequest(BaseModel):
    poses: List[PosePayload]


class TourQuestionRequest(BaseModel):
    question: str


def _payload_to_dict(model: BaseModel) -> dict:
    dump = getattr(model, "model_dump", None)
    if callable(dump):
        return dump()
    return model.dict()


def create_app(
    runtime: Optional[SimPoseIngressRuntime] = None,
    config_path: Optional[Path] = None,
) -> FastAPI:
    app = FastAPI(title="Odin Nav Stack Sim Pose Ingress HTTP Bridge", version="0.1.0")
    active_runtime = runtime or SimPoseIngressRuntime.from_config_path(
        config_path=config_path or REPO_ROOT / "configs" / "sim.yaml",
        repo_root=REPO_ROOT,
    )
    app.state.runtime = active_runtime

    @app.get("/health")
    def health() -> dict:
        return active_runtime.health()

    @app.post("/runtime/start")
    def start_runtime() -> dict:
        return {
            "ok": True,
            "action": "start",
            "state": active_runtime.start(),
        }

    @app.post("/tour/pause")
    def pause_tour() -> dict:
        return {
            "ok": True,
            "action": "pause",
            "message": "tour paused",
            "state": active_runtime.pause(),
        }

    @app.post("/tour/resume")
    def resume_tour() -> dict:
        return {
            "ok": True,
            "action": "resume",
            "message": "tour resumed",
            "state": active_runtime.resume(),
        }

    @app.post("/tour/next")
    def next_poi() -> dict:
        return {
            "ok": True,
            "action": "next",
            "message": "advanced to next poi",
            "state": active_runtime.next_poi(),
        }

    @app.post("/poses")
    def ingest_pose(payload: PosePayload) -> dict:
        pose = active_runtime.ingest_pose_payload(_payload_to_dict(payload))
        return {
            "ok": True,
            "action": "ingest_pose",
            "pose": {"x": pose.x, "y": pose.y, "label": pose.label},
            "state": active_runtime.state(),
        }

    @app.post("/poses/batch")
    def ingest_pose_batch(payload: PoseBatchRequest) -> dict:
        count = active_runtime.ingest_pose_payloads([_payload_to_dict(item) for item in payload.poses])
        return {
            "ok": True,
            "action": "ingest_pose_batch",
            "accepted_count": count,
            "state": active_runtime.state(),
        }

    @app.post("/stream/finish")
    def finish_stream() -> dict:
        return {
            "ok": True,
            "action": "finish_stream",
            "state": active_runtime.finish_stream(),
        }

    @app.get("/state")
    def state() -> dict:
        return active_runtime.state()

    @app.get("/session/latest")
    def latest_session() -> dict:
        return active_runtime.latest_session()

    @app.post("/tour/question")
    def ask_question(payload: TourQuestionRequest) -> dict:
        return active_runtime.ask_question(payload.question)

    return app
