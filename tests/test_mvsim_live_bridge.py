import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.sim_pose_ingress.app import create_app as create_sim_app
from services.sim_pose_ingress.runtime import SimPoseIngressRuntime
from services.sim_publisher_bridge.http_client import SimIngressHttpClient
from services.sim_publisher_bridge.mvsim_live_source import (
    describe_mvsim_live_pose_source,
    parse_time_stamped_pose_blocks,
)
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime
from services.sim_publisher_bridge.source import IterableSimulatorPoseSource


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


class MVSimLiveBridgeTests(unittest.TestCase):
    def test_parse_time_stamped_pose_blocks_extracts_pose_samples(self) -> None:
        sample_text = """
        [2026/04/06,18:08:41.564584] Received data :
         - typeName: mvsim_msgs.TimeStampedPose
         - data: 75 bytes
        unixTimestamp: 1775470121.5642531
        objectId: "tour_bot"
        pose {
          x: -3
          y: -1.5
          z: 0
          yaw: 0
          pitch: 0
          roll: 0
        }
        """

        samples = parse_time_stamped_pose_blocks(sample_text)

        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["label"], "tour_bot")
        self.assertEqual(samples[0]["position"]["x"], -3.0)
        self.assertEqual(samples[0]["position"]["y"], -1.5)
        self.assertEqual(samples[0]["orientation"]["yaw_rad"], 0.0)
        self.assertEqual(samples[0]["mvsim"]["message_type"], "mvsim_msgs.TimeStampedPose")

    def test_live_bridge_runtime_relays_live_pose_shape_into_ingress(self) -> None:
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
                "session_log_dir": str(Path(temp_dir) / "session_logs" / "sim_live_bridge"),
                "recording_enabled": False,
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
                "service_endpoints": {
                    "sim_pose_ingress_server": {
                        "bind_host": "127.0.0.1",
                        "connect_host": "127.0.0.1",
                        "port": 8100,
                        "scheme": "http",
                    }
                },
            }
            sim_runtime = SimPoseIngressRuntime(config=sim_config, repo_root=repo_root)
            sim_client = TestClient(create_sim_app(runtime=sim_runtime))
            ingress_client = _TestClientSimIngressHttpClient(sim_client)

            live_samples = [
                {
                    "label": "tour_bot",
                    "position": {"x": -3.0, "y": -1.5, "z": 0.0},
                    "orientation": {"yaw_rad": 0.0},
                    "mvsim": {
                        "object_id": "tour_bot",
                        "topic_name": "/tour_bot/pose",
                        "message_type": "mvsim_msgs.TimeStampedPose",
                        "unix_timestamp": 1775470121.5642531,
                        "frame_id": "map",
                        "runtime_mode": "wsl_live_topic_echo",
                    },
                }
            ]

            bridge_runtime = SimulatorPublisherBridgeRuntime(
                source=IterableSimulatorPoseSource(live_samples),
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

        self.assertEqual(result["batch_response"]["accepted_count"], 1)
        self.assertEqual(result["normalized_payload_sample"][0]["x"], -3.0)
        self.assertEqual(result["normalized_payload_sample"][0]["y"], -1.5)
        self.assertEqual(result["final_state"]["last_pose"]["x"], -3.0)
        self.assertEqual(result["final_state"]["active_spot_name"], "East Gate")

    def test_live_pose_source_descriptor_is_explicit(self) -> None:
        descriptor = describe_mvsim_live_pose_source(
            distribution="Ubuntu",
            user="root",
            executable_path="/root/round033-mvsim-build/bin/mvsim",
            topic_name="/tour_bot/pose",
        )

        self.assertEqual(descriptor["source_kind"], "mvsim_live_topic_echo")
        self.assertEqual(descriptor["topic_name"], "/tour_bot/pose")
        self.assertEqual(descriptor["message_type"], "mvsim_msgs.TimeStampedPose")


if __name__ == "__main__":
    unittest.main()
