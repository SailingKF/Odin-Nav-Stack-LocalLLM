import unittest

from services.deployment_profile import (
    build_bringup_verification_sheet,
    build_deployment_command_manifest,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
    build_deployment_verification_manifest,
    build_verification_result_summary,
    run_deployment_verification_once,
)


class DeploymentVerificationRunnerTests(unittest.TestCase):
    @staticmethod
    def _dev_verification_manifest() -> dict:
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "narrator_type": "local_llm",
            "llm_backend_type": "ollama",
            "audio_output_type": "mock",
            "session_log_dir": "session_logs/dev",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        command_manifest = build_deployment_command_manifest(config, launch_plan, endpoint_contract)
        return build_deployment_verification_manifest(command_manifest, endpoint_contract)

    def test_runner_reports_passed_result_when_expected_status_and_fields_are_present(self) -> None:
        verification_manifest = self._dev_verification_manifest()

        def fetch_json(url: str, timeout_sec: float) -> dict:
            self.assertGreater(timeout_sec, 0.0)
            if url.endswith(":9000/health"):
                return {
                    "status": "ok",
                    "service": "llm-gateway",
                    "active_backend_type": "mock",
                    "fallback_active": False,
                }
            if url.endswith(":8000/health"):
                return {
                    "status": "ok",
                    "service": "mock-tour-api",
                    "env_name": "dev",
                    "deployment_profile": {"profile_name": "dev"},
                }
            raise AssertionError(f"unexpected url: {url}")

        result = run_deployment_verification_once(verification_manifest, fetch_json=fetch_json)

        self.assertEqual(result["overall_result_status"], "passed")
        self.assertEqual(result["passed_verification_count"], 2)
        self.assertEqual(result["failed_verification_count"], 0)
        gateway_result = next(item for item in result["results"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_result["result_status"], "passed")

    def test_runner_reports_unreachable_failure(self) -> None:
        verification_manifest = self._dev_verification_manifest()

        def fetch_json(url: str, timeout_sec: float) -> dict:
            raise OSError("connection refused")

        result = run_deployment_verification_once(verification_manifest, fetch_json=fetch_json)

        self.assertEqual(result["overall_result_status"], "failed")
        self.assertEqual(result["passed_verification_count"], 0)
        self.assertEqual(result["failed_verification_count"], 2)
        gateway_result = next(item for item in result["results"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_result["result_status"], "failed_unreachable")
        self.assertIn("connection refused", gateway_result["error_detail"])

    def test_runner_reports_missing_expected_fields(self) -> None:
        verification_manifest = self._dev_verification_manifest()

        def fetch_json(url: str, timeout_sec: float) -> dict:
            return {
                "status": "ok",
                "service": "incomplete",
            }

        result = run_deployment_verification_once(verification_manifest, fetch_json=fetch_json)

        self.assertEqual(result["overall_result_status"], "failed")
        gateway_result = next(item for item in result["results"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_result["result_status"], "failed_missing_fields")
        self.assertIn("active_backend_type", gateway_result["missing_fields"])

    def test_result_summary_combines_step_contracts_with_runner_results(self) -> None:
        config = {
            "env_name": "edge",
            "pose_provider_type": "odin_ros",
            "narrator_type": "local_llm",
            "audio_output_type": "mock",
            "llm_backend_type": "ollama",
            "session_log_dir": "session_logs/edge",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        command_manifest = build_deployment_command_manifest(config, launch_plan, endpoint_contract)
        verification_manifest = build_deployment_verification_manifest(command_manifest, endpoint_contract)
        bringup_verification_sheet = build_bringup_verification_sheet(
            {"overall_status": "blocked", "blocking_reasons": ["llm gateway down"], "steps": [
                {
                    "step_id": item["step_id"],
                    "order": item["order"],
                    "name": item["name"],
                    "status": "blocked" if item["step_id"] == "llm_gateway" else "ready",
                    "required": True,
                    "category": "internal_service" if item["step_id"] in {"llm_gateway", "api_server"} else "external_dependency",
                    "action_type": item["action_type"],
                    "display_command": None,
                    "verification_available": item["verification_available"],
                    "verification_target": item["verification_target"],
                    "verification_kind": "http_json_health" if item["verification_available"] else None,
                    "expected_statuses": ["ok"],
                    "blocking_reasons": ["llm gateway down"] if item["step_id"] == "llm_gateway" else [],
                }
                for item in verification_manifest["steps"]
            ]},
            command_manifest,
            verification_manifest,
        )

        run_result = {
            "profile_name": "edge",
            "config_path": "configs/edge.yaml",
            "overall_result_status": "failed",
            "verification_result_count": 2,
            "passed_verification_count": 1,
            "failed_verification_count": 1,
            "skipped_manual_step_count": 3,
            "results": [],
            "steps": [
                {
                    "step_id": "hardware_pose_dependency",
                    "name": "Ensure hardware pose source is available",
                    "result_status": "manual_external",
                    "verification_available": False,
                    "verification_target": None,
                    "observed_status": None,
                    "missing_fields": [],
                    "error_detail": None,
                },
                {
                    "step_id": "ollama_runtime",
                    "name": "Ensure local Ollama runtime is available",
                    "result_status": "manual_external",
                    "verification_available": False,
                    "verification_target": None,
                    "observed_status": None,
                    "missing_fields": [],
                    "error_detail": None,
                },
                {
                    "step_id": "llm_gateway",
                    "name": "Start llm gateway",
                    "result_status": "failed_unreachable",
                    "verification_available": True,
                    "verification_target": "http://127.0.0.1:9000/health",
                    "observed_status": None,
                    "missing_fields": [],
                    "error_detail": "url error: timed out",
                },
                {
                    "step_id": "api_server",
                    "name": "Start backend API server",
                    "result_status": "passed",
                    "verification_available": True,
                    "verification_target": "http://127.0.0.1:8000/health",
                    "observed_status": "ok",
                    "missing_fields": [],
                    "error_detail": None,
                },
                {
                    "step_id": "audio_device_dependency",
                    "name": "Verify audio output path",
                    "result_status": "manual_optional",
                    "verification_available": False,
                    "verification_target": None,
                    "observed_status": None,
                    "missing_fields": [],
                    "error_detail": None,
                },
            ],
        }

        summary = build_verification_result_summary(bringup_verification_sheet, run_result)

        self.assertEqual(summary["overall_result_status"], "failed")
        self.assertEqual(summary["failed_verification_count"], 1)
        gateway_step = next(item for item in summary["steps"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_step["result_status"], "failed_unreachable")
        self.assertEqual(gateway_step["verification_target"], "http://127.0.0.1:9000/health")
        hardware_step = next(item for item in summary["steps"] if item["step_id"] == "hardware_pose_dependency")
        self.assertEqual(hardware_step["result_status"], "manual_external")


if __name__ == "__main__":
    unittest.main()
