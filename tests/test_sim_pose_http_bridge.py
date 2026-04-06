import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.sim_pose_ingress.app import create_app
from services.sim_pose_ingress.runtime import SimPoseIngressRuntime


class SimPoseHttpBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        repo_root = Path.cwd()
        self._config = {
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
            "session_log_dir": str(Path(self._temp_dir.name) / "session_logs" / "sim_http"),
            "recording_enabled": False,
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        self.runtime = SimPoseIngressRuntime(config=self._config, repo_root=repo_root)
        self.client = TestClient(create_app(runtime=self.runtime))

    def tearDown(self) -> None:
        deadline = time.time() + 3.0
        while time.time() < deadline:
            state = self.runtime.state()
            if not state.get("is_running"):
                break
            time.sleep(0.05)
        self._temp_dir.cleanup()

    def test_health_and_start_endpoint(self) -> None:
        health = self.client.get("/health")
        start = self.client.post("/runtime/start", json={})

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["service"], "sim-pose-ingress-runtime")
        self.assertEqual(start.status_code, 200)
        self.assertTrue(start.json()["ok"])
        self.assertEqual(start.json()["state"]["state"], "NAVIGATING")

    def test_batch_ingestion_triggers_narration_and_session(self) -> None:
        self.client.post("/runtime/start", json={})

        batch = {
            "poses": [
                {"x": -0.6, "y": 0.0, "label": "gate_trigger_edge"},
                {"x": 0.0, "y": 0.0, "label": "gate_inside"},
            ]
        }
        batch_response = self.client.post("/poses/batch", json=batch)
        finish_response = self.client.post("/stream/finish", json={})

        deadline = time.time() + 3.0
        state_payload = {}
        while time.time() < deadline:
            state_payload = self.client.get("/state").json()
            if not state_payload["is_running"]:
                break
            time.sleep(0.05)

        session_payload = self.client.get("/session/latest").json()

        self.assertEqual(batch_response.status_code, 200)
        self.assertEqual(batch_response.json()["accepted_count"], 2)
        self.assertEqual(finish_response.status_code, 200)
        self.assertIn("East Gate", state_payload["last_narration_text"])
        self.assertGreater(session_payload["event_count"], 0)
        self.assertIn("East Gate", session_payload["latest_narration_text"])

    def test_single_pose_endpoint_accepts_contract_shape(self) -> None:
        self.client.post("/runtime/start", json={})

        response = self.client.post("/poses", json={"x": -0.6, "y": 0.0, "label": "gate_trigger_edge"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["pose"]["label"], "gate_trigger_edge")

    def test_question_endpoint_is_available_after_pose_ingress(self) -> None:
        self.client.post("/runtime/start", json={})
        self.client.post(
            "/poses/batch",
            json={"poses": [{"x": 0.0, "y": 0.0, "label": "gate_inside"}]},
        )

        response = self.client.post("/tour/question", json={"question": "Why start here?"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertIn("East Gate", payload["spot_name"])


if __name__ == "__main__":
    unittest.main()
