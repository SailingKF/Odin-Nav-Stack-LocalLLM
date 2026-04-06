import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.api_server.app import create_app as create_api_app
from services.api_server.runtime import SimIngressProxyApiRuntime
from services.sim_pose_ingress.app import create_app as create_sim_app
from services.sim_pose_ingress.runtime import SimPoseIngressRuntime
from services.sim_publisher_bridge.mvsim_source import (
    YamlFileMVSimPoseSource,
    describe_mvsim_compat_source,
    mvsim_observation_to_richer_payload,
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

    def pause_tour(self) -> dict:
        return self._client.post("/tour/pause", json={}).json()

    def resume_tour(self) -> dict:
        return self._client.post("/tour/resume", json={}).json()

    def next_poi(self) -> dict:
        return self._client.post("/tour/next", json={}).json()

    def ask_question(self, question: str) -> dict:
        return self._client.post("/tour/question", json={"question": question}).json()


class MVSimIntegrationTests(unittest.TestCase):
    def test_mvsim_observation_conversion_is_planar_and_explicit(self) -> None:
        payload = mvsim_observation_to_richer_payload(
            {
                "world_name": "demo_world",
                "vehicle": "tour_bot",
                "sim_time_sec": 1.25,
                "frame_id": "map",
                "note": "gate_inside",
                "pose2d": {"x_m": 1.5, "y_m": -0.25, "yaw_rad": 0.2},
                "velocity2d": {"vx_mps": 0.4, "vy_mps": 0.0, "yaw_rate_radps": 0.1},
            }
        )

        self.assertEqual(payload["label"], "gate_inside")
        self.assertEqual(payload["position"]["x"], 1.5)
        self.assertEqual(payload["position"]["y"], -0.25)
        self.assertEqual(payload["orientation"]["yaw_rad"], 0.2)
        self.assertEqual(payload["mvsim"]["vehicle_name"], "tour_bot")

    def test_yaml_mvsim_source_reads_demo_observations(self) -> None:
        source = YamlFileMVSimPoseSource(Path("content/sim/demo_mvsim_pose_stream.yaml"))
        payloads = list(source.iter_payloads())
        descriptor = describe_mvsim_compat_source(Path("content/sim/demo_mvsim_pose_stream.yaml"))

        self.assertGreaterEqual(len(payloads), 4)
        self.assertEqual(payloads[0]["mvsim"]["world_name"], "odin_demo_world")
        self.assertEqual(descriptor["source_kind"], "mvsim_compatibility_shim")

    def test_mvsim_bridge_and_api_proxy_run_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path.cwd()
            sim_config = {
                "env_name": "sim",
                "pose_provider_type": "sim_ingress",
                "narrator_type": "mock",
                "audio_output_type": "mock",
                "tts_backend_type": "mock",
                "artifact_player_backend_type": "mock",
                "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts" / "sim"),
                "narration_mode_default": "standard",
                "llm_gateway_url": "http://127.0.0.1:9000",
                "llm_backend_type": "mock",
                "llm_model_name": "mock-curated-content",
                "llm_base_url": "http://127.0.0.1:11434",
                "llm_timeout_sec": 8.0,
                "llm_enable_fallback": True,
                "session_log_dir": str(Path(temp_dir) / "session_logs" / "sim_mvsim"),
                "recording_enabled": False,
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
                "service_endpoints": {
                    "sim_pose_ingress_server": {
                        "bind_host": "127.0.0.1",
                        "connect_host": "127.0.0.1",
                        "port": 8100,
                        "scheme": "http",
                    },
                    "api_server": {
                        "bind_host": "127.0.0.1",
                        "connect_host": "127.0.0.1",
                        "port": 8000,
                        "scheme": "http",
                    },
                },
            }
            sim_runtime = SimPoseIngressRuntime(config=sim_config, repo_root=repo_root)
            sim_client = TestClient(create_sim_app(runtime=sim_runtime))
            ingress_client = _TestClientSimIngressHttpClient(sim_client)

            api_runtime = SimIngressProxyApiRuntime(
                config=sim_config,
                repo_root=repo_root,
                ingress_client=ingress_client,
            )
            api_client = TestClient(create_api_app(runtime=api_runtime))

            bridge_runtime = SimulatorPublisherBridgeRuntime(
                source=YamlFileMVSimPoseSource(Path("content/sim/demo_mvsim_pose_stream.yaml")),
                projection_config=SimPoseProjectionConfig(),
                transform_config=SimFrameTransformConfig(
                    raw_x_field="sim_x",
                    raw_y_field="sim_y",
                    swap_axes=False,
                    flip_x=False,
                    flip_y=False,
                    scale=1.0,
                    offset_x=0.0,
                    offset_y=0.0,
                ),
                ingress_client=ingress_client,
            )

            result = bridge_runtime.run()

            proxied_state = api_client.get("/state").json()
            proxied_session = api_client.get("/session/latest").json()
            answer_response = api_client.post(
                "/tour/question",
                json={"question": "What does this final stop prove?"},
            ).json()
            debug_page = api_client.get("/debug")

        self.assertEqual(result["batch_response"]["accepted_count"], 4)
        self.assertTrue(result["final_state"]["route_completed"])
        self.assertEqual(proxied_state["api_mode"], "sim_ingress_proxy")
        self.assertEqual(debug_page.status_code, 200)
        self.assertIn("History Gallery", proxied_session["latest_narration_text"])
        self.assertTrue(answer_response["ok"])
        self.assertIn("finish cleanly", answer_response["answer_text"])


if __name__ == "__main__":
    unittest.main()
