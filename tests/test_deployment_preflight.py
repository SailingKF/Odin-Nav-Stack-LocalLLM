import tempfile
import unittest
from pathlib import Path

from services.deployment_profile import build_deployment_preflight


class DeploymentPreflightTests(unittest.TestCase):
    def test_local_files_and_mock_mode_probe_as_ok_or_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "content" / "routes").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "poi").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "routes" / "demo.yaml").write_text("route_id: demo\nspots: []\n", encoding="utf-8")
            (repo_root / "content" / "poi" / "demo.yaml").write_text("pois: []\n", encoding="utf-8")

            preflight = build_deployment_preflight(
                {
                    "env_name": "dev",
                    "pose_provider_type": "mock",
                    "narrator_type": "mock",
                    "audio_output_type": "mock",
                    "llm_backend_type": "mock",
                    "session_log_dir": "session_logs/dev",
                    "current_route_file": "content/routes/demo.yaml",
                    "current_poi_file": "content/poi/demo.yaml",
                },
                repo_root=repo_root,
            )

        self.assertEqual(preflight["summary_status"], "ok")
        checks = {item["name"]: item for item in preflight["checks"]}
        self.assertEqual(checks["route_file"]["status"], "ok")
        self.assertEqual(checks["poi_file"]["status"], "ok")
        self.assertEqual(checks["session_log_dir"]["status"], "ok")
        self.assertEqual(checks["llm_gateway"]["status"], "not_applicable")
        self.assertEqual(checks["ollama_runtime"]["status"], "not_applicable")

    def test_missing_route_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "content" / "poi").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "poi" / "demo.yaml").write_text("pois: []\n", encoding="utf-8")

            preflight = build_deployment_preflight(
                {
                    "env_name": "dev",
                    "pose_provider_type": "mock",
                    "narrator_type": "mock",
                    "audio_output_type": "mock",
                    "llm_backend_type": "mock",
                    "session_log_dir": "session_logs/dev",
                    "current_route_file": "content/routes/missing.yaml",
                    "current_poi_file": "content/poi/demo.yaml",
                },
                repo_root=repo_root,
            )

        self.assertEqual(preflight["summary_status"], "missing")
        route_check = next(item for item in preflight["checks"] if item["name"] == "route_file")
        self.assertEqual(route_check["status"], "missing")

    def test_http_probe_outcomes_are_surfaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "content" / "routes").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "poi").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "routes" / "demo.yaml").write_text("route_id: demo\nspots: []\n", encoding="utf-8")
            (repo_root / "content" / "poi" / "demo.yaml").write_text("pois: []\n", encoding="utf-8")

            def fake_probe(url: str, timeout_sec: float):
                if url.endswith("/health"):
                    return {"status": "ok", "http_status": 200, "detail": "gateway reachable"}
                return {"status": "unreachable", "detail": "connection refused"}

            preflight = build_deployment_preflight(
                {
                    "env_name": "edge",
                    "pose_provider_type": "odin_ros",
                    "narrator_type": "local_llm",
                    "audio_output_type": "mock",
                    "llm_backend_type": "ollama",
                    "llm_gateway_url": "http://127.0.0.1:9000",
                    "llm_base_url": "http://127.0.0.1:11434",
                    "session_log_dir": "session_logs/edge",
                    "current_route_file": "content/routes/demo.yaml",
                    "current_poi_file": "content/poi/demo.yaml",
                },
                repo_root=repo_root,
                url_probe=fake_probe,
            )

        checks = {item["name"]: item for item in preflight["checks"]}
        self.assertEqual(checks["llm_gateway"]["status"], "ok")
        self.assertEqual(checks["ollama_runtime"]["status"], "unreachable")
        self.assertEqual(checks["hardware_pose_dependency"]["status"], "unverified_external")
        self.assertEqual(checks["audio_device_dependency"]["status"], "not_applicable")
        self.assertEqual(preflight["summary_status"], "unreachable")

    def test_live_sim_and_real_audio_dependencies_are_marked_external(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            (repo_root / "content" / "routes").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "poi").mkdir(parents=True, exist_ok=True)
            (repo_root / "content" / "routes" / "demo.yaml").write_text("route_id: demo\nspots: []\n", encoding="utf-8")
            (repo_root / "content" / "poi" / "demo.yaml").write_text("pois: []\n", encoding="utf-8")

            preflight = build_deployment_preflight(
                {
                    "env_name": "sim",
                    "pose_provider_type": "sim_ingress",
                    "narrator_type": "mock",
                    "audio_output_type": "tts_service",
                    "llm_backend_type": "mock",
                    "tts_backend_type": "mock",
                    "artifact_player_backend_type": "mock",
                    "isaac_source": {"mode": "live"},
                    "session_log_dir": "session_logs/sim",
                    "current_route_file": "content/routes/demo.yaml",
                    "current_poi_file": "content/poi/demo.yaml",
                },
                repo_root=repo_root,
            )

        checks = {item["name"]: item for item in preflight["checks"]}
        self.assertEqual(checks["isaac_live_dependency"]["status"], "unverified_external")
        self.assertEqual(checks["audio_device_dependency"]["status"], "unverified_external")
        self.assertEqual(preflight["summary_status"], "needs_external_verification")


if __name__ == "__main__":
    unittest.main()
