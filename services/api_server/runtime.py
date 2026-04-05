from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from adapters.mock.audio_output import build_audio_output
from adapters.mock.mock_pose_provider import MockPoseProvider
from core.narrator.factory import build_narrator
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import JsonlSessionStore
from core.tour_orchestrator.orchestrator import TourOrchestrator


class MockTourApiRuntime:
    def __init__(
        self,
        config: Dict[str, Any],
        repo_root: Path,
        step_interval_seconds: float = 0.05,
    ) -> None:
        self._config = config
        self._repo_root = repo_root
        self._step_interval_seconds = step_interval_seconds
        self._orchestrator: Optional[TourOrchestrator] = None
        self._session_log_dir = repo_root / config["session_log_dir"]

    @classmethod
    def from_config_path(
        cls,
        config_path: Path,
        repo_root: Path,
        step_interval_seconds: float = 0.05,
    ) -> "MockTourApiRuntime":
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
        return cls(config=config, repo_root=repo_root, step_interval_seconds=step_interval_seconds)

    def _build_orchestrator(self) -> TourOrchestrator:
        poi_file = self._repo_root / self._config["current_poi_file"]
        route_file = self._repo_root / self._config["current_route_file"]

        pois = load_pois(str(poi_file))
        route = load_route(str(route_file))
        poi_store = InMemoryPoiStore(pois)
        route_pois = poi_store.route_pois(route)
        pose_provider = MockPoseProvider.from_route_pois(route_pois)
        session_store = JsonlSessionStore(str(self._session_log_dir))
        narrator = build_narrator(self._config)
        audio_output = build_audio_output(self._config, event_callback=print, repo_root=self._repo_root)

        return TourOrchestrator(
            route_pois=route_pois,
            narrator=narrator,
            session_store=session_store,
            audio_output=audio_output,
            pose_provider=pose_provider,
            session_metadata={
                "env_name": self._config["env_name"],
                "pose_provider_type": self._config["pose_provider_type"],
                "route_id": route.route_id,
                "recording_enabled": bool(self._config["recording_enabled"]),
                "control_mode": "api",
                "narrator_type": self._config.get("narrator_type", "mock"),
                "audio_output_type": self._config.get("audio_output_type", "mock"),
            },
            event_callback=print,
            narration_mode_default=str(self._config.get("narration_mode_default", "standard")),
            step_interval_seconds=self._step_interval_seconds,
        )

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "service": "mock-tour-api",
            "env_name": self._config["env_name"],
            "pose_provider_type": self._config["pose_provider_type"],
            "narrator_type": self._config.get("narrator_type", "mock"),
            "audio_output_type": self._config.get("audio_output_type", "mock"),
        }

    def state(self) -> Dict[str, Any]:
        if self._orchestrator is None:
            return {
                "session_id": None,
                "state": "IDLE",
                "is_running": False,
                "is_paused": False,
                "route_completed": False,
                "current_index": 0,
                "route_length": 0,
                "active_spot_id": None,
                "active_spot_name": None,
                "narrator_type": self._config.get("narrator_type", "mock"),
                "narration_mode_default": self._config.get("narration_mode_default", "standard"),
                "last_pose": None,
                "last_event_type": None,
                "last_narration_text": None,
                "last_answer_text": None,
                "audio_output_type": self._config.get("audio_output_type", "mock"),
                "last_audio_playback": None,
                "session_log_path": None,
            }
        return self._orchestrator.get_state()

    def start_tour(self) -> Dict[str, Any]:
        if self._config["pose_provider_type"] != "mock":
            raise ValueError("This API bundle only supports the mock pose provider in dev mode.")

        state = self.state()
        if self._orchestrator is not None and state["is_running"]:
            return {"ok": True, "action": "start", "message": "tour already running", "state": state}

        self._orchestrator = self._build_orchestrator()
        return {"ok": True, "action": "start", "message": "tour started", "state": self._orchestrator.start()}

    def pause_tour(self) -> Dict[str, Any]:
        if self._orchestrator is None:
            return {"ok": True, "action": "pause", "message": "no active tour", "state": self.state()}
        return {"ok": True, "action": "pause", "message": "tour paused", "state": self._orchestrator.pause()}

    def resume_tour(self) -> Dict[str, Any]:
        if self._orchestrator is None:
            return {"ok": True, "action": "resume", "message": "no active tour", "state": self.state()}
        return {"ok": True, "action": "resume", "message": "tour resumed", "state": self._orchestrator.resume()}

    def next_poi(self) -> Dict[str, Any]:
        if self._orchestrator is None:
            return {"ok": True, "action": "next", "message": "no active tour", "state": self.state()}
        return {"ok": True, "action": "next", "message": "advanced to next poi", "state": self._orchestrator.next_poi()}

    def latest_session(self) -> Dict[str, Any]:
        if self._orchestrator is not None:
            return self._orchestrator.get_latest_session_summary()
        return JsonlSessionStore.read_latest_session_summary(self._session_log_dir)

    def ask_question(self, question: str) -> Dict[str, Any]:
        if self._orchestrator is None:
            return {
                "ok": False,
                "action": "question",
                "message": "no active tour",
                "question": question,
                "answer_text": "Start a tour before asking follow-up questions.",
                "state": self.state(),
            }
        response = self._orchestrator.answer_question(question)
        return {
            "ok": True,
            "action": "question",
            "message": "question answered",
            **response,
        }
