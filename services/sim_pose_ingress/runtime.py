from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from adapters.mock.audio_output import build_audio_output
from adapters.sim.external_pose_provider import ExternalPoseProvider
from core.interfaces.pose_provider import Pose2D
from core.narrator.factory import build_narrator
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import JsonlSessionStore, build_audio_lifecycle_session_persister
from core.tour_orchestrator.orchestrator import TourOrchestrator
from services.deployment_profile import (
    build_deployment_command_manifest,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
    build_deployment_verification_manifest,
)


class SimPoseIngressRuntime:
    def __init__(
        self,
        config: Dict[str, Any],
        repo_root: Path,
        step_interval_seconds: float = 0.0,
    ) -> None:
        self._config = config
        self._repo_root = repo_root
        self._step_interval_seconds = step_interval_seconds
        self._orchestrator: Optional[TourOrchestrator] = None
        self._pose_provider: Optional[ExternalPoseProvider] = None
        self._session_log_dir = repo_root / config["session_log_dir"]
        self._deployment_profile = build_deployment_profile(config)
        self._deployment_preflight = build_deployment_preflight(config, repo_root)
        self._deployment_launch_plan = build_deployment_launch_plan(config)
        self._deployment_endpoint_contract = build_deployment_endpoint_contract(
            config,
            self._deployment_launch_plan,
        )
        self._deployment_readiness = build_deployment_readiness(
            self._deployment_profile,
            self._deployment_preflight,
            self._deployment_launch_plan,
        )
        self._deployment_command_manifest = build_deployment_command_manifest(
            config,
            self._deployment_launch_plan,
            self._deployment_endpoint_contract,
        )
        self._deployment_verification_manifest = build_deployment_verification_manifest(
            self._deployment_command_manifest,
            self._deployment_endpoint_contract,
        )

    @classmethod
    def from_config_path(
        cls,
        config_path: Path,
        repo_root: Path,
        step_interval_seconds: float = 0.0,
    ) -> "SimPoseIngressRuntime":
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
        pose_provider = ExternalPoseProvider()
        session_store = JsonlSessionStore(str(self._session_log_dir))
        narrator = build_narrator(self._config)
        audio_output = build_audio_output(
            self._config,
            event_callback=print,
            repo_root=self._repo_root,
            lifecycle_event_callback=build_audio_lifecycle_session_persister(session_store, route_pois),
        )

        self._pose_provider = pose_provider
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
                "control_mode": "sim_pose_ingress",
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
            "service": "sim-pose-ingress-runtime",
            "env_name": self._config["env_name"],
            "pose_provider_type": self._config["pose_provider_type"],
            "narrator_type": self._config.get("narrator_type", "mock"),
            "audio_output_type": self._config.get("audio_output_type", "mock"),
            "ingress_contract": {"required_fields": ["x", "y"], "optional_fields": ["label"]},
            "deployment_profile": self._deployment_profile,
            "deployment_preflight": self._deployment_preflight,
            "deployment_launch_plan": self._deployment_launch_plan,
            "deployment_endpoint_contract": self._deployment_endpoint_contract,
            "deployment_readiness": self._deployment_readiness,
            "deployment_command_manifest": self._deployment_command_manifest,
            "deployment_verification_manifest": self._deployment_verification_manifest,
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
                "session_log_path": None,
                "deployment_profile": self._deployment_profile,
                "deployment_preflight": self._deployment_preflight,
                "deployment_launch_plan": self._deployment_launch_plan,
                "deployment_endpoint_contract": self._deployment_endpoint_contract,
                "deployment_readiness": self._deployment_readiness,
                "deployment_command_manifest": self._deployment_command_manifest,
                "deployment_verification_manifest": self._deployment_verification_manifest,
            }
        state = self._orchestrator.get_state()
        state["deployment_profile"] = self._deployment_profile
        state["deployment_preflight"] = self._deployment_preflight
        state["deployment_launch_plan"] = self._deployment_launch_plan
        state["deployment_endpoint_contract"] = self._deployment_endpoint_contract
        state["deployment_readiness"] = self._deployment_readiness
        state["deployment_command_manifest"] = self._deployment_command_manifest
        state["deployment_verification_manifest"] = self._deployment_verification_manifest
        return state

    def start(self) -> Dict[str, Any]:
        if self._config["pose_provider_type"] != "sim_ingress":
            raise ValueError("sim.yaml must use pose_provider_type=sim_ingress for this baseline.")
        if self._orchestrator is not None and self.state().get("is_running"):
            return self.state()

        self._orchestrator = self._build_orchestrator()
        return self._orchestrator.start()

    def ingest_pose(self, pose: Pose2D) -> Pose2D:
        if self._pose_provider is None:
            raise RuntimeError("Start the sim runtime before pushing poses.")
        self._pose_provider.push_pose(pose)
        return pose

    def ingest_pose_payload(self, payload: Dict[str, Any]) -> Pose2D:
        if self._pose_provider is None:
            raise RuntimeError("Start the sim runtime before pushing poses.")
        return self._pose_provider.push_payload(payload)

    def ingest_pose_payloads(self, payloads: List[Dict[str, Any]]) -> int:
        for payload in payloads:
            self.ingest_pose_payload(payload)
        return len(payloads)

    def finish_stream(self) -> Dict[str, Any]:
        if self._pose_provider is None:
            return self.state()
        self._pose_provider.close_stream()
        return self.state()

    def latest_session(self) -> Dict[str, Any]:
        if self._orchestrator is not None:
            return self._orchestrator.get_latest_session_summary()
        return JsonlSessionStore.read_latest_session_summary(self._session_log_dir)
