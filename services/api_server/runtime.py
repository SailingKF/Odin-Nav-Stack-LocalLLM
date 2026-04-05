from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from adapters.mock.audio_output import build_audio_output
from adapters.mock.mock_pose_provider import MockPoseProvider
from core.narrator.factory import build_narrator
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import (
    JsonlSessionStore,
    build_audio_lifecycle_session_persister,
    build_audio_summary_from_latest_audio_playback,
)
from core.tour_orchestrator.orchestrator import TourOrchestrator
from services.deployment_profile import build_deployment_preflight, build_deployment_profile


def _build_audio_summary(
    playback_state: Optional[Dict[str, Any]],
    latest_audio_playback: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if playback_state is None:
        return build_audio_summary_from_latest_audio_playback(latest_audio_playback)

    active = playback_state.get("active_playback") or {}
    queued = playback_state.get("queued_playbacks") or []
    recent_events = playback_state.get("recent_events") or []
    completion_event = next((item for item in reversed(recent_events) if item.get("event_type") == "playback_completed"), None)
    failure_event = next((item for item in reversed(recent_events) if item.get("event_type") == "playback_failed"), None)
    latest_lifecycle_event = recent_events[-1].get("event_type") if recent_events else None
    summary = build_audio_summary_from_latest_audio_playback(
        latest_audio_playback=latest_audio_playback,
        completion_event=completion_event,
        failure_event=failure_event,
        recent_audio_events=recent_events,
    )
    active_metadata = dict(active.get("metadata") or {})
    summary.update(
        {
            "summary_status": "active"
            if active
            else ("queued" if queued else ("degraded" if summary.get("latest_failure_source") else "idle")),
            "active_playback_status": active.get("status") or summary.get("active_playback_status"),
            "active_playback_kind": active.get("playback_kind") or summary.get("active_playback_kind"),
            "active_output_type": active.get("output_type") or summary.get("active_output_type"),
            "queued_count": len(queued),
            "latest_lifecycle_event": latest_lifecycle_event,
            "latest_handle_status": active_metadata.get("latest_playback_handle_status")
            or summary.get("latest_handle_status"),
        }
    )
    return summary


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
        self._deployment_profile = build_deployment_profile(config)
        self._deployment_preflight = build_deployment_preflight(config, repo_root)

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
        audio_output = build_audio_output(
            self._config,
            event_callback=print,
            repo_root=self._repo_root,
            lifecycle_event_callback=build_audio_lifecycle_session_persister(session_store, route_pois),
        )

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
            "deployment_profile": self._deployment_profile,
            "deployment_preflight": self._deployment_preflight,
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
                "audio_playback_state": None,
                "last_audio_playback": None,
                "audio_summary": _build_audio_summary(None, None),
                "session_log_path": None,
                "deployment_profile": self._deployment_profile,
                "deployment_preflight": self._deployment_preflight,
            }
        state = self._orchestrator.get_state()
        state["audio_summary"] = _build_audio_summary(
            playback_state=state.get("audio_playback_state"),
            latest_audio_playback=state.get("last_audio_playback"),
        )
        state["deployment_profile"] = self._deployment_profile
        state["deployment_preflight"] = self._deployment_preflight
        return state

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
            summary = self._orchestrator.get_latest_session_summary()
            current_state = self.state()
            summary["audio_summary"] = current_state.get("audio_summary")
            return summary
        summary = JsonlSessionStore.read_latest_session_summary(self._session_log_dir)
        summary["audio_summary"] = _build_audio_summary(
            playback_state=None,
            latest_audio_playback=summary.get("latest_audio_playback"),
        )
        return summary

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
