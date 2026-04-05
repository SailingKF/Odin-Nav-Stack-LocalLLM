import unittest

from services.deployment_profile import (
    build_bringup_verification_sheet,
    build_deployment_command_manifest,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
    build_deployment_verification_manifest,
)


class DeploymentVerificationManifestTests(unittest.TestCase):
    def test_dev_verification_manifest_maps_gateway_and_api(self) -> None:
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
        verification_manifest = build_deployment_verification_manifest(command_manifest, endpoint_contract)

        self.assertEqual(verification_manifest["profile_name"], "dev")
        gateway_verification = next(item for item in verification_manifest["verifications"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_verification["target_url"], "http://127.0.0.1:9000/health")
        self.assertIn("fallback_active", gateway_verification["expected_fields"])
        api_verification = next(item for item in verification_manifest["verifications"] if item["step_id"] == "api_server")
        self.assertEqual(api_verification["target_url"], "http://127.0.0.1:8000/health")
        debug_step = next(item for item in verification_manifest["steps"] if item["step_id"] == "debug_browser")
        self.assertFalse(debug_step["verification_available"])
        self.assertEqual(debug_step["verification_type"], "manual_optional")

    def test_sim_verification_manifest_distinguishes_repo_checks_from_external_steps(self) -> None:
        config = {
            "env_name": "sim",
            "pose_provider_type": "sim_ingress",
            "isaac_source": {"mode": "live"},
            "session_log_dir": "session_logs/sim",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }

        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        command_manifest = build_deployment_command_manifest(config, launch_plan, endpoint_contract)
        verification_manifest = build_deployment_verification_manifest(command_manifest, endpoint_contract)

        ingress_verification = next(
            item for item in verification_manifest["verifications"] if item["step_id"] == "sim_pose_ingress_server"
        )
        self.assertEqual(ingress_verification["target_url"], "http://127.0.0.1:8100/health")
        self.assertIn("ingress_contract", ingress_verification["expected_fields"])
        live_step = next(item for item in verification_manifest["steps"] if item["step_id"] == "isaac_live_dependency")
        self.assertFalse(live_step["verification_available"])
        self.assertEqual(live_step["verification_type"], "manual_external")

    def test_edge_bringup_verification_sheet_combines_commands_readiness_and_checks(self) -> None:
        config = {
            "env_name": "edge",
            "pose_provider_type": "odin_ros",
            "narrator_type": "local_llm",
            "audio_output_type": "mock",
            "llm_backend_type": "ollama",
            "llm_gateway_url": "http://127.0.0.1:65500",
            "llm_base_url": "http://127.0.0.1:11434",
            "session_log_dir": "session_logs/edge",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        repo_root = "C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs"

        profile = build_deployment_profile(config)
        preflight = build_deployment_preflight(config, repo_root=repo_root)
        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        readiness = build_deployment_readiness(profile, preflight, launch_plan)
        command_manifest = build_deployment_command_manifest(config, launch_plan, endpoint_contract)
        verification_manifest = build_deployment_verification_manifest(command_manifest, endpoint_contract)
        verification_sheet = build_bringup_verification_sheet(
            readiness,
            command_manifest,
            verification_manifest,
        )

        self.assertEqual(verification_sheet["overall_status"], "blocked")
        gateway_step = next(item for item in verification_sheet["steps"] if item["step_id"] == "llm_gateway")
        self.assertEqual(
            gateway_step["display_command"],
            "python scripts/run_llm_gateway.py --config configs/edge.yaml --host 0.0.0.0 --port 65500",
        )
        self.assertEqual(gateway_step["verification_target"], "http://127.0.0.1:65500/health")
        self.assertIn("ok", gateway_step["expected_statuses"])
        hardware_step = next(item for item in verification_sheet["steps"] if item["step_id"] == "hardware_pose_dependency")
        self.assertFalse(hardware_step["verification_available"])
        self.assertIsNone(hardware_step["verification_target"])


if __name__ == "__main__":
    unittest.main()
