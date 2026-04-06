import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from fastapi.testclient import TestClient

from services.mvsim_validation_harness.app import create_app
from services.sim_publisher_bridge.mvsim_live import describe_mvsim_runtime_mode, probe_mvsim_live_runtime
from services.mvsim_validation_harness.runtime import (
    MVSimValidationHarnessRuntime,
    build_operator_service_check,
    summarize_validation_snapshot,
)


class _FakeHarnessRuntime:
    debug_url = "http://127.0.0.1:8000/debug"

    def __init__(self) -> None:
        self._latest_report = {
            "report_id": "20260406T120000Z-live_runtime",
            "status": "passed",
            "validation_mode": "live_runtime",
            "route_completed": True,
            "report_path": "session_logs/mvsim_validation_harness/reports/20260406T120000Z-live_runtime.json",
        }
        self._status = {
            "status": "ok",
            "service": "mvsim-validation-harness",
            "harness_url": "http://127.0.0.1:8300",
            "config_path": "configs/sim.yaml",
            "debug_url": self.debug_url,
            "supports_attach_existing": True,
            "supports_local_launch": True,
            "validation_modes": {
                "available": ["compatibility_shim", "live_runtime"],
                "default_validation_mode": "live_runtime",
                "selected_validation_mode": "live_runtime",
            },
            "mvsim_mode_summary": {
                "configured_mode": "live_runtime",
                "effective_mode": "live_runtime",
                "live_runtime": {
                    "runtime_available": True,
                    "world_file_exists": True,
                    "live_pose_surface": {"topic_name": "/tour_bot/pose", "bridge_mode": "wsl_topic_echo_to_http_ingress"},
                    "live_validation_alignment": {
                        "strategy": "isolated_live_validation_world_with_forward_motion",
                        "target_spot_name": "East Gate",
                        "second_target_spot_name": "Central Plaza",
                    },
                },
                "compatibility_source": {
                    "source_kind": "mvsim_compatibility_shim",
                    "observation_file_exists": True,
                },
                "wsl_enablement": {
                    "wsl_installed": True,
                    "current_shell_elevated": False,
                },
            },
            "service_checks": {
                "sim_pose_ingress": build_operator_service_check(
                    "sim_pose_ingress_server",
                    "Sim Pose Ingress",
                    "http://127.0.0.1:8100/health",
                    True,
                    "attach_existing",
                    "health endpoint reachable",
                ),
                "api_server": build_operator_service_check(
                    "api_server",
                    "Sim API Proxy",
                    "http://127.0.0.1:8000/health",
                    True,
                    "attach_existing",
                    "health endpoint reachable",
                ),
                "debug_page": build_operator_service_check(
                    "debug_page",
                    "Debug Page",
                    self.debug_url,
                    True,
                    "attach_existing",
                    "debug page reachable",
                ),
            },
            "validation_snapshot": {
                "overall_status": "idle",
                "validation_mode": "live_runtime",
                "mvsim_mode": "live_runtime",
                "live_runtime_available": True,
                "live_first_poi_hit": False,
                "live_second_poi_hit": False,
                "route_completed": False,
                "latest_spot_name": None,
                "latest_narration_text": None,
                "latest_session_id": None,
                "followup_question_ok": False,
                "debug_available": True,
            },
            "last_validation_result": None,
            "latest_report": self._latest_report,
            "recent_reports": [self._latest_report],
        }

    def status(self) -> dict:
        return self._status

    def latest_report(self) -> dict:
        return self._latest_report

    def recent_reports(self, limit: int = 5) -> list:
        return [self._latest_report][:limit]

    def start_local_stack(self, validation_mode: str = "live_runtime") -> dict:
        self._status["validation_modes"]["selected_validation_mode"] = validation_mode
        return {
            "ok": True,
            "action": "start_local_stack",
            "validation_mode": validation_mode,
            "service_checks": self._status["service_checks"],
            "debug_url": self.debug_url,
        }

    def stop_local_stack(self) -> dict:
        return {"ok": True, "action": "stop_local_stack", "stopped_services": ["sim_pose_ingress_server", "api_server"]}

    def run_validation(self, question: str, validation_mode: str = "live_runtime") -> dict:
        result = {
            "status": "passed",
            "validation_mode": validation_mode,
            "mvsim_source": {"source_kind": "mvsim_live_topic_echo" if validation_mode == "live_runtime" else "mvsim_compatibility_shim"},
            "sim_ingress_state": {"route_completed": True},
            "api_latest_session": {
                "session_id": "mock_tour_123",
                "latest_spot_name": "History Gallery",
                "latest_narration_text": "Final stop narration.",
            },
            "question_result": {
                "ok": True,
                "answer_text": f"Answered: {question}",
            },
        }
        if validation_mode == "live_runtime":
            result["live_validation_summary"] = {
                "live_first_poi_hit_occurred": True,
                "live_second_poi_hit_occurred": True,
            }
        result["validation_report"] = dict(self._latest_report)
        self._status["last_validation_result"] = result
        self._status["validation_snapshot"] = summarize_validation_snapshot(
            self._status["service_checks"]["sim_pose_ingress"],
            self._status["service_checks"]["api_server"],
            self._status["service_checks"]["debug_page"],
            self._status["mvsim_mode_summary"],
            result,
        )
        return result


class MVSimValidationHarnessTests(unittest.TestCase):
    def test_probe_marks_live_runtime_missing_when_mvsim_not_installed(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = {
            "mvsim_integration": {
                "mode": "live_runtime",
                "executable": "definitely_missing_mvsim_binary",
                "world_file": "content/sim/mvsim/worlds/odin_minimal_tour.world.xml",
                "vehicle_name": "tour_bot",
            }
        }

        probe = probe_mvsim_live_runtime(config, repo_root)

        self.assertEqual(probe["configured_mode"], "live_runtime")
        self.assertFalse(probe["runtime_available"])
        self.assertTrue(probe["world_file_exists"])
        self.assertEqual(probe["blocker"]["code"], "mvsim_executable_not_found")

    def test_live_mode_validation_stops_at_real_runtime_blocker(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sim_live.yaml"
            payload = {
                "env_name": "sim",
                "service_endpoints": {
                    "sim_pose_ingress_server": {"bind_host": "127.0.0.1", "connect_host": "127.0.0.1", "port": 8100, "scheme": "http"},
                    "api_server": {"bind_host": "127.0.0.1", "connect_host": "127.0.0.1", "port": 8000, "scheme": "http"},
                },
                "mvsim_integration": {
                    "mode": "live_runtime",
                    "executable": "definitely_missing_mvsim_binary",
                    "world_file": "content/sim/mvsim/worlds/odin_minimal_tour.world.xml",
                    "vehicle_name": "tour_bot",
                },
            }
            config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")

            runtime = MVSimValidationHarnessRuntime(config_path=config_path, repo_root=repo_root)
            result = runtime.run_validation()

        self.assertEqual(result["status"], "blocked_live_runtime_unavailable")
        self.assertEqual(result["mvsim_mode"], "blocked_live_runtime")
        self.assertIn("not found", result["detail"])

    def test_runtime_normalizes_relative_config_path_for_cli_startup(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        runtime = MVSimValidationHarnessRuntime(
            config_path=Path("configs/sim.yaml"),
            repo_root=repo_root,
        )

        self.assertTrue(runtime._config_path.is_absolute())
        self.assertEqual(runtime._config_path, repo_root / "configs" / "sim.yaml")

    def test_snapshot_summary_marks_passed_when_core_checks_pass(self) -> None:
        sim_check = build_operator_service_check("sim", "Sim", "http://127.0.0.1:8100/health", True, "attach_existing", "ok")
        api_check = build_operator_service_check("api", "API", "http://127.0.0.1:8000/health", True, "attach_existing", "ok")
        debug_check = build_operator_service_check("debug", "Debug", "http://127.0.0.1:8000/debug", True, "attach_existing", "ok")
        validation = {
            "validation_mode": "compatibility_shim",
            "mvsim_mode": "compatibility_shim",
            "sim_ingress_state": {"route_completed": True},
            "api_latest_session": {"session_id": "mock_tour_1", "latest_spot_name": "History Gallery", "latest_narration_text": "Done"},
            "question_result": {"ok": True},
        }
        mvsim_mode_summary = {
            "effective_mode": "compatibility_shim",
            "live_runtime": {"runtime_available": False},
        }

        snapshot = summarize_validation_snapshot(sim_check, api_check, debug_check, mvsim_mode_summary, validation)

        self.assertEqual(snapshot["overall_status"], "passed")
        self.assertEqual(snapshot["validation_mode"], "compatibility_shim")
        self.assertEqual(snapshot["mvsim_mode"], "compatibility_shim")
        self.assertTrue(snapshot["route_completed"])
        self.assertEqual(snapshot["latest_session_id"], "mock_tour_1")

    def test_snapshot_summary_stays_idle_before_validation(self) -> None:
        sim_check = build_operator_service_check("sim", "Sim", "url", False, "attach_existing", "not running")
        api_check = build_operator_service_check("api", "API", "url", False, "attach_existing", "not running")
        debug_check = build_operator_service_check("debug", "Debug", "url", False, "attach_existing", "not running")
        mvsim_mode_summary = {
            "effective_mode": "blocked_live_runtime",
            "live_runtime": {"runtime_available": False},
        }

        snapshot = summarize_validation_snapshot(sim_check, api_check, debug_check, mvsim_mode_summary, None)

        self.assertEqual(snapshot["overall_status"], "idle")
        self.assertEqual(snapshot["validation_mode"], "blocked_live_runtime")
        self.assertEqual(snapshot["mvsim_mode"], "blocked_live_runtime")
        self.assertFalse(snapshot["debug_available"])

    def test_runtime_uses_harness_default_mode_and_isolated_ports(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        runtime = MVSimValidationHarnessRuntime(
            config_path=repo_root / "configs" / "sim_harness.yaml",
            repo_root=repo_root,
        )

        status = runtime.status()

        self.assertEqual(status["validation_modes"]["default_validation_mode"], "live_runtime")
        self.assertEqual(status["validation_modes"]["selected_validation_mode"], "live_runtime")
        self.assertIn("compatibility_shim", status["validation_modes"]["available"])
        self.assertIn("live_runtime", status["validation_modes"]["available"])
        self.assertEqual(
            status["service_checks"]["api_server"]["target_url"],
            "http://127.0.0.1:8001/health",
        )
        self.assertEqual(
            status["service_checks"]["sim_pose_ingress"]["target_url"],
            "http://127.0.0.1:8110/health",
        )

    def test_harness_page_and_actions_are_served(self) -> None:
        client = TestClient(create_app(runtime=_FakeHarnessRuntime()))

        page = client.get("/harness")
        status = client.get("/status")
        start = client.post("/services/start", json={"validation_mode": "live_runtime"})
        validation = client.post(
            "/validation/run",
            json={"validation_mode": "live_runtime", "question": "What does this final stop prove?"},
        )
        debug_link = client.get("/debug-link")
        latest_report = client.get("/reports/latest")
        recent_reports = client.get("/reports/recent")

        self.assertEqual(page.status_code, 200)
        self.assertIn("MVSim Validation Harness", page.text)
        self.assertIn("Run MVSim Validation", page.text)
        self.assertIn("Configured MVSim Mode", page.text)
        self.assertIn("Validation Mode", page.text)
        self.assertIn("Latest Report", page.text)
        self.assertIn("Recent Runs", page.text)
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["service"], "mvsim-validation-harness")
        self.assertTrue(start.json()["ok"])
        self.assertEqual(start.json()["validation_mode"], "live_runtime")
        self.assertEqual(validation.json()["status"], "passed")
        self.assertEqual(validation.json()["validation_mode"], "live_runtime")
        self.assertEqual(debug_link.json()["debug_url"], "http://127.0.0.1:8000/debug")
        self.assertEqual(latest_report.json()["latest_report"]["report_id"], "20260406T120000Z-live_runtime")
        self.assertEqual(recent_reports.json()["recent_reports"][0]["validation_mode"], "live_runtime")

    def test_harness_can_run_compatibility_mode_request(self) -> None:
        client = TestClient(create_app(runtime=_FakeHarnessRuntime()))

        validation = client.post(
            "/validation/run",
            json={"validation_mode": "compatibility_shim", "question": "What does this final stop prove?"},
        )

        self.assertEqual(validation.status_code, 200)
        self.assertEqual(validation.json()["status"], "passed")
        self.assertEqual(validation.json()["validation_mode"], "compatibility_shim")
        self.assertEqual(validation.json()["mvsim_source"]["source_kind"], "mvsim_compatibility_shim")


if __name__ == "__main__":
    unittest.main()
