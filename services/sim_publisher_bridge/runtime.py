import time
from typing import Dict, List

from adapters.sim.frame_transform import SimFrameTransformConfig, normalize_raw_pose_payloads
from adapters.sim.projection import SimPoseProjectionConfig, project_richer_pose_payloads
from services.sim_publisher_bridge.source import SimulatorPoseSource


class SimulatorPublisherBridgeRuntime:
    def __init__(
        self,
        source: SimulatorPoseSource,
        projection_config: SimPoseProjectionConfig,
        transform_config: SimFrameTransformConfig,
        ingress_client,
        settle_timeout_seconds: float = 3.0,
        poll_interval_seconds: float = 0.05,
    ) -> None:
        self._source = source
        self._projection_config = projection_config
        self._transform_config = transform_config
        self._ingress_client = ingress_client
        self._settle_timeout_seconds = settle_timeout_seconds
        self._poll_interval_seconds = poll_interval_seconds

    def load_source_payloads(self) -> List[Dict]:
        return list(self._source.iter_payloads())

    def project_payloads(self, payloads: List[Dict]) -> List[Dict]:
        return project_richer_pose_payloads(payloads, self._projection_config)

    def normalize_payloads(self, projected_payloads: List[Dict]) -> List[Dict]:
        return normalize_raw_pose_payloads(projected_payloads, self._transform_config)

    def run(self) -> Dict:
        richer_payloads = self.load_source_payloads()
        projected_payloads = self.project_payloads(richer_payloads)
        normalized_payloads = self.normalize_payloads(projected_payloads)

        health = self._ingress_client.health()
        start_response = self._ingress_client.start_runtime()
        batch_response = self._ingress_client.ingest_pose_batch(normalized_payloads)
        finish_response = self._ingress_client.finish_stream()

        deadline = time.time() + self._settle_timeout_seconds
        latest_state = {}
        while time.time() < deadline:
            latest_state = self._ingress_client.state()
            if not latest_state.get("is_running"):
                break
            time.sleep(self._poll_interval_seconds)

        latest_session = self._ingress_client.latest_session()
        return {
            "projection_config": self._projection_config.__dict__,
            "transform_config": self._transform_config.__dict__,
            "richer_payload_sample": richer_payloads[:2],
            "projected_payload_sample": projected_payloads[:2],
            "normalized_payload_sample": normalized_payloads[:2],
            "health": health,
            "start_response": start_response,
            "batch_response": batch_response,
            "finish_response": finish_response,
            "final_state": latest_state,
            "latest_session": latest_session,
        }
