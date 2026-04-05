import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.sim_pose_ingress.app import create_app
from services.sim_pose_ingress.runtime import SimPoseIngressRuntime
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime
from services.sim_publisher_bridge.source import IterableSimulatorPoseSource, YamlFileRicherPoseSource


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


class SimPublisherBridgeTests(unittest.TestCase):
    def test_iterable_pose_source_yields_payloads(self) -> None:
        source = IterableSimulatorPoseSource(
            [
                {"label": "one", "position": {"x": 0.1, "y": 0.2, "z": 0.0}},
                {"label": "two", "position": {"x": 0.3, "y": 0.4, "z": 0.0}},
            ]
        )

        payloads = list(source.iter_payloads())

        self.assertEqual(len(payloads), 2)
        self.assertEqual(payloads[0]["label"], "one")
        self.assertEqual(payloads[1]["position"]["y"], 0.4)

    def test_yaml_file_source_reads_richer_payloads(self) -> None:
        source = YamlFileRicherPoseSource(Path("content/sim/demo_richer_pose_stream.yaml"))

        payloads = list(source.iter_payloads())

        self.assertGreaterEqual(len(payloads), 2)
        self.assertIn("position", payloads[0])
        self.assertIn("orientation", payloads[0])

    def test_bridge_runtime_runs_end_to_end_against_http_bridge(self) -> None:
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
                    "session_log_dir": str(Path(temp_dir) / "session_logs" / "sim_publisher_bridge"),
                    "recording_enabled": False,
                    "current_route_file": "content/routes/demo_route.yaml",
                    "current_poi_file": "content/poi/demo_pois.yaml",
                },
                repo_root=Path.cwd(),
            )
            client = TestClient(create_app(runtime=runtime))
            bridge_runtime = SimulatorPublisherBridgeRuntime(
                source=IterableSimulatorPoseSource(
                    [
                        {
                            "label": "gate_approach_richer",
                            "position": {"x": 0.7, "y": 1.8, "z": 0.0},
                            "orientation": {"yaw_rad": 0.0},
                        },
                        {
                            "label": "gate_trigger_edge_richer",
                            "position": {"x": 0.0, "y": 0.6, "z": 0.0},
                            "orientation": {"yaw_rad": 0.1},
                        },
                        {
                            "label": "gate_inside_richer",
                            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                            "orientation": {"yaw_rad": 0.1},
                        },
                    ]
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
