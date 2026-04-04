import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api_server.app import REPO_ROOT, create_app
from services.api_server.runtime import MockTourApiRuntime


class ApiServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        session_dir = Path(self._temp_dir.name) / "session_logs" / "dev_api_test"
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "session_log_dir": str(session_dir),
            "recording_enabled": False,
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        runtime = MockTourApiRuntime(config=config, repo_root=REPO_ROOT, step_interval_seconds=0.02)
        self.client = TestClient(create_app(runtime=runtime))

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def test_health_and_state(self) -> None:
        health = self.client.get("/health")
        state = self.client.get("/state")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")
        self.assertEqual(state.status_code, 200)
        payload = state.json()
        self.assertIn("state", payload)
        self.assertIn("is_running", payload)
        self.assertIn("session_log_path", payload)

    def test_control_endpoints_and_latest_session(self) -> None:
        start_response = self.client.post("/tour/start")
        self.assertEqual(start_response.status_code, 200)
        self.assertTrue(start_response.json()["ok"])

        pause_response = self.client.post("/tour/pause")
        self.assertEqual(pause_response.status_code, 200)

        resume_response = self.client.post("/tour/resume")
        self.assertEqual(resume_response.status_code, 200)

        deadline = time.time() + 3.0
        latest_state = {}
        while time.time() < deadline:
            latest_state = self.client.get("/state").json()
            if latest_state["route_completed"]:
                break
            time.sleep(0.05)

        self.assertTrue(latest_state["route_completed"])

        latest_session = self.client.get("/session/latest")
        self.assertEqual(latest_session.status_code, 200)
        session_payload = latest_session.json()
        self.assertIsNotNone(session_payload["session_id"])
        self.assertGreater(session_payload["event_count"], 0)
        self.assertIn("latest_state", session_payload)


if __name__ == "__main__":
    unittest.main()
