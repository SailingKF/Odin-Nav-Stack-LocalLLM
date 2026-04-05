import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.sim_pose_ingress.app import create_app
from services.sim_pose_ingress.runtime import SimPoseIngressRuntime
from services.sim_publisher_bridge.isaac_source import (
    IsaacStubPoseSource,
    IterableIsaacObservationSource,
    YamlFileIsaacObservationSource,
)
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime


class _TestClientSimIngressHttpClient:
    def __init__(self, client: TestClient):
        self._client = client

    def health(self) -> dict:
        return self._client.get("/health").json()

    def start_runtime(self) -> dict:
        return self._client.post("/runtime/start", json={}).json()

    def ingest_pose_batch(self, poses: list) -> dict:
        return self._client.post("/poses/batch", json={"poses": poses}).json()

    def finish_stream(self) -> dict:
        return self._client.post("/stream/finish", json={}).json()

    def state(self) -> dict:
        return self._client.get("/state").json()

    def latest_session(self) -> dict:
        return self._client.get("/session/latest").json()


class IsaacStubSourceTests(unittest.TestCase):
    def test_iterable_isaac_source_yields_observations(self) -> None:
        source = IterableIsaacObservationSource(
            [
                {"label": "one", "translation": {"x": 0.1, "y": 0.2, "z": 0.0}},
                {"label": "two", "translation": {"x": 0.3, "y": 0.4, "z": 0.0}},
            ]
        )

        observations = list(source.iter_observations())

        self.assertEqual(len(observations), 2)
        self.assertEqual(observations[0]["label"], "one")
        self.assertEqual(observations[1]["translation"]["y"], 0.4)

    def test_yaml_isaac_source_reads_stub_observations(self) -> None:
        source = YamlFileIsaacObservationSource(Path("content/sim/demo_isaac_stub_pose_stream.yaml"))

        observations = list(source.iter_observations())

        self.assertGreaterEqual(len(observations), 2)
        self.assertIn("translation", observations[0])
        self.assertIn("orientation", observations[0])
        self.assertIn("prim_path", observations[0])

    def test_isaac_stub_pose_source_adapts_into_richer_payloads(self) -> None:
        source = IsaacStubPoseSource(
            IterableIsaacObservationSource(
                [
                    {
                        "label": "gate",
                        "prim_path": "/World/Robot/base_link",
                        "frame_id": "odin/base_link",
                        "sim_time_sec": 0.1,
                        "translation": {"x": 0.7, "y": 1.8, "z": 0.0},
                        "orientation": {"yaw_rad": 0.0},
                    }
                ]
            )
        )

        payloads = list(source.iter_payloads())

        self.assertEqual(payloads[0]["position"]["x"], 0.7)
        self.assertEqual(payloads[0]["orientation"]["yaw_rad"], 0.0)
        self.assertEqual(payloads[0]["source_metadata"]["frame_id"], "odin/base_link")

    def test_bridge_runtime_runs_end_to_end_with_isaac_stub_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime = SimPoseIngressRuntime(
                config={
                    "env_name": "sim",
                    "pose_provider_type": "sim_ingress",
                    "narrator_type": "mock",
                    "narration_mode_default": "standard",
                    "llm_gateway_url": "http://127.0.0.1:9000",
                    "llm_backend_type": "mock",
                    "llm_model_name": "mock-curated-content",
                    "llm_base_url": "http://127.0.0.1:11434",
                    "llm_timeout_sec": 8.0,
                    "llm_enable_fallback": True,
                    "session_log_dir": str(Path(temp_dir) / "session_logs" / "isaac_stub_bridge"),
                    "recording_enabled": False,
                    "current_route_file": "content/routes/demo_route.yaml",
                    "current_poi_file": "content/poi/demo_pois.yaml",
                },
                repo_root=Path.cwd(),
            )
            client = TestClient(create_app(runtime=runtime))
            bridge_runtime = SimulatorPublisherBridgeRuntime(
                source=IsaacStubPoseSource(
                    IterableIsaacObservationSource(
                        [
                            {
                                "label": "gate_approach_isaac_stub",
                                "prim_path": "/World/Robot/base_link",
                                "frame_id": "odin/base_link",
                                "sim_time_sec": 0.1,
                                "translation": {"x": 0.7, "y": 1.8, "z": 0.0},
                                "orientation": {"yaw_rad": 0.0},
                            },
                            {
                                "label": "gate_trigger_edge_isaac_stub",
                                "prim_path": "/World/Robot/base_link",
                                "frame_id": "odin/base_link",
                                "sim_time_sec": 0.2,
                                "translation": {"x": 0.0, "y": 0.6, "z": 0.0},
                                "orientation": {"yaw_rad": 0.1},
                            },
                            {
                                "label": "gate_inside_isaac_stub",
                                "prim_path": "/World/Robot/base_link",
                                "frame_id": "odin/base_link",
                                "sim_time_sec": 0.3,
                                "translation": {"x": 0.0, "y": 0.0, "z": 0.0},
                                "orientation": {"yaw_rad": 0.1},
                            },
                        ]
                    )
                ),
                projection_config=SimPoseProjectionConfig(),
                transform_config=SimFrameTransformConfig(
                    raw_x_field="sim_x",
                    raw_y_field="sim_y",
                    swap_axes=True,
                    flip_x=True,
                    flip_y=True,
                ),
                ingress_client=_TestClientSimIngressHttpClient(client),
            )

            result = bridge_runtime.run()

        self.assertEqual(result["health"]["service"], "sim-pose-ingress-runtime")
        self.assertEqual(result["batch_response"]["accepted_count"], 3)
        self.assertIn("East Gate", result["latest_session"]["latest_narration_text"])
        self.assertEqual(result["normalized_payload_sample"][0]["x"], -1.8)
        self.assertEqual(result["normalized_payload_sample"][0]["y"], -0.7)


if __name__ == "__main__":
    unittest.main()
