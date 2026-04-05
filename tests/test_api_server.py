import tempfile
import time
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from services.api_server.app import REPO_ROOT, create_app
from services.api_server.runtime import MockTourApiRuntime


class ApiServerTests(unittest.TestCase):
    @staticmethod
    def _wait_until_runtime_stops(runtime: MockTourApiRuntime, timeout_seconds: float = 3.0) -> None:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            state = runtime.state()
            if not state.get("is_running"):
                break
            time.sleep(0.05)

    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        session_dir = Path(self._temp_dir.name) / "session_logs" / "dev_api_test"
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "narrator_type": "mock",
            "audio_output_type": "mock",
            "tts_backend_type": "mock",
            "tts_artifact_dir": str(Path(self._temp_dir.name) / "tts_artifacts" / "mock"),
            "narration_mode_default": "standard",
            "llm_gateway_url": "http://127.0.0.1:9000",
            "llm_backend_type": "mock",
            "llm_model_name": "mock-curated-content",
            "llm_base_url": "http://127.0.0.1:11434",
            "llm_timeout_sec": 8.0,
            "llm_enable_fallback": True,
            "session_log_dir": str(session_dir),
            "recording_enabled": False,
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        self.runtime = MockTourApiRuntime(config=config, repo_root=REPO_ROOT, step_interval_seconds=0.02)
        self.client = TestClient(create_app(runtime=self.runtime))

    def tearDown(self) -> None:
        self._wait_until_runtime_stops(self.runtime)
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
        self.assertIn("audio_output_type", payload)
        self.assertIn("audio_playback_state", payload)
        self.assertIn("last_audio_playback", payload)
        self.assertIn("audio_summary", payload)
        self.assertIn("deployment_profile", payload)
        self.assertIn("deployment_preflight", payload)
        self.assertIn("deployment_launch_plan", payload)
        self.assertIn("deployment_endpoint_contract", payload)
        self.assertIn("deployment_readiness", payload)
        self.assertIn("deployment_command_manifest", payload)
        self.assertIn("deployment_verification_manifest", payload)
        self.assertEqual(payload["deployment_profile"]["profile_name"], "dev")
        self.assertEqual(payload["deployment_profile"]["deployment_class"], "dev_only")
        self.assertEqual(payload["deployment_profile"]["readiness_status"], "ready_for_profile")
        self.assertIn("deployment_profile", health.json())
        self.assertIn("deployment_preflight", health.json())
        self.assertIn("deployment_launch_plan", health.json())
        self.assertIn("deployment_endpoint_contract", health.json())
        self.assertIn("deployment_readiness", health.json())
        self.assertIn("deployment_command_manifest", health.json())
        self.assertIn("deployment_verification_manifest", health.json())
        self.assertIn("summary_status", payload["deployment_preflight"])
        self.assertIn("checks", payload["deployment_preflight"])
        self.assertIn("steps", payload["deployment_launch_plan"])
        self.assertIn("services", payload["deployment_endpoint_contract"])
        self.assertGreater(payload["deployment_launch_plan"]["step_count"], 0)
        self.assertIn("overall_status", payload["deployment_readiness"])
        self.assertIn("steps", payload["deployment_readiness"])
        self.assertIn("commands", payload["deployment_command_manifest"])
        self.assertIn("steps", payload["deployment_command_manifest"])
        self.assertIn("verifications", payload["deployment_verification_manifest"])
        self.assertIn("steps", payload["deployment_verification_manifest"])

    def test_debug_page_is_served_for_mobile_use(self) -> None:
        response = self.client.get("/debug")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Mock Tour Debug Panel", response.text)
        self.assertIn('name="viewport"', response.text)
        self.assertIn("Start Tour", response.text)
        self.assertIn("Refresh Status", response.text)
        self.assertIn("http://127.0.0.1:8000", response.text)
        self.assertIn("Ask Question", response.text)
        self.assertIn("Audio Summary", response.text)
        self.assertIn("Latest Failure", response.text)

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
        self.assertIn("latest_narration_text", session_payload)
        self.assertIn("latest_audio_playback", session_payload)
        self.assertIn("audio_summary", session_payload)
        self.assertIn("recent_audio_events", session_payload)
        self.assertTrue(
            any(
                item["event_type"] in {"playback_started", "playback_completed"}
                for item in session_payload["recent_audio_events"]
            )
        )

    def test_question_endpoint_returns_answer(self) -> None:
        self.client.post("/tour/start")
        time.sleep(0.25)

        question_response = self.client.post("/tour/question", json={"question": "Why does the tour start here?"})

        self.assertEqual(question_response.status_code, 200)
        payload = question_response.json()
        self.assertTrue(payload["ok"])
        self.assertIn("answer_text", payload)
        self.assertIn("state", payload)

    def test_question_endpoint_in_local_llm_mode_falls_back_cleanly(self) -> None:
        session_dir = Path(self._temp_dir.name) / "session_logs" / "dev_api_local_llm_test"
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "narrator_type": "local_llm",
            "audio_output_type": "mock",
            "tts_backend_type": "mock",
            "tts_artifact_dir": str(Path(self._temp_dir.name) / "tts_artifacts" / "local_llm"),
            "narration_mode_default": "standard",
            "llm_gateway_url": "http://127.0.0.1:65500",
            "llm_backend_type": "ollama",
            "llm_model_name": "gemma-local",
            "llm_base_url": "http://127.0.0.1:11434",
            "llm_timeout_sec": 0.2,
            "llm_enable_fallback": True,
            "session_log_dir": str(session_dir),
            "recording_enabled": False,
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        runtime = MockTourApiRuntime(config=config, repo_root=REPO_ROOT, step_interval_seconds=0.02)
        client = TestClient(create_app(runtime=runtime))

        try:
            client.post("/tour/start")
            time.sleep(0.25)
            response = client.post("/tour/question", json={"question": "Why does the tour start here?"})

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertTrue(payload["ok"])
            self.assertIn("answer_text", payload)
            self.assertIn("first stop", payload["answer_text"])
        finally:
            self._wait_until_runtime_stops(runtime)

    def test_service_backed_audio_output_exposes_tts_metadata(self) -> None:
        session_dir = Path(self._temp_dir.name) / "session_logs" / "dev_api_tts_service_test"
        artifact_dir = Path(self._temp_dir.name) / "tts_artifacts" / "service_api"
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "narrator_type": "mock",
            "audio_output_type": "tts_service",
            "tts_backend_type": "mock",
            "tts_artifact_dir": str(artifact_dir),
            "narration_mode_default": "standard",
            "llm_gateway_url": "http://127.0.0.1:9000",
            "llm_backend_type": "mock",
            "llm_model_name": "mock-curated-content",
            "llm_base_url": "http://127.0.0.1:11434",
            "llm_timeout_sec": 8.0,
            "llm_enable_fallback": True,
            "session_log_dir": str(session_dir),
            "recording_enabled": False,
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        runtime = MockTourApiRuntime(config=config, repo_root=REPO_ROOT, step_interval_seconds=0.02)
        client = TestClient(create_app(runtime=runtime))

        try:
            client.post("/tour/start")
            time.sleep(0.25)
            client.post("/tour/question", json={"question": "Why does the tour start here?"})
            payload = client.get("/session/latest").json()

            self.assertEqual(payload["latest_audio_playback"]["extra"]["output_type"], "tts_service")
            self.assertEqual(payload["latest_audio_playback"]["extra"]["metadata"]["backend_type"], "mock")
            artifact_uri = payload["latest_audio_playback"]["extra"]["metadata"]["artifact"]["artifact_uri"]
            self.assertTrue(Path(artifact_uri).exists())
            state_payload = client.get("/state").json()
            self.assertEqual(
                state_payload["audio_playback_state"]["policy_name"],
                "answers_interrupt_active_playback__narration_queues_fifo",
            )
            self.assertIn("audio_summary", state_payload)
            self.assertIn("queued_count", state_payload["audio_summary"])
            self.assertIn("audio_summary", payload)
            self.assertEqual(payload["audio_summary"]["active_output_type"], "tts_service")
        finally:
            self._wait_until_runtime_stops(runtime)


if __name__ == "__main__":
    unittest.main()
