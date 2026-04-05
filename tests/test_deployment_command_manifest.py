import unittest

from services.deployment_profile import (
    build_deployment_command_manifest,
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
    build_guided_bringup_sheet,
)


class DeploymentCommandManifestTests(unittest.TestCase):
    def test_dev_manifest_maps_internal_services_to_repo_commands(self) -> None:
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
        manifest = build_deployment_command_manifest(config, launch_plan)

        self.assertEqual(manifest["profile_name"], "dev")
        self.assertEqual(manifest["config_path"], "configs/dev.yaml")
        llm_gateway_command = next(item for item in manifest["commands"] if item["step_id"] == "llm_gateway")
        self.assertEqual(llm_gateway_command["entrypoint_path"], "scripts/run_llm_gateway.py")
        self.assertIn("--config", llm_gateway_command["argv"])
        api_server_command = next(item for item in manifest["commands"] if item["step_id"] == "api_server")
        self.assertEqual(api_server_command["entrypoint_path"], "scripts/run_api_server.py")
        debug_browser_step = next(item for item in manifest["steps"] if item["step_id"] == "debug_browser")
        self.assertFalse(debug_browser_step["command_available"])
        self.assertEqual(debug_browser_step["action_type"], "manual_optional")

    def test_sim_manifest_leaves_external_and_unmapped_steps_without_repo_commands(self) -> None:
        config = {
            "env_name": "sim",
            "pose_provider_type": "sim_ingress",
            "isaac_source": {"mode": "live"},
            "session_log_dir": "session_logs/sim",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }

        launch_plan = build_deployment_launch_plan(config)
        manifest = build_deployment_command_manifest(config, launch_plan)

        ingress_command = next(item for item in manifest["commands"] if item["step_id"] == "sim_pose_ingress_server")
        self.assertEqual(ingress_command["display_command"], "python scripts/run_sim_pose_ingress_server.py --config configs/sim.yaml")
        live_step = next(item for item in manifest["steps"] if item["step_id"] == "isaac_live_dependency")
        self.assertFalse(live_step["command_available"])
        self.assertEqual(live_step["action_type"], "manual_external")
        bridge_step = next(item for item in manifest["steps"] if item["step_id"] == "sim_publisher_bridge")
        self.assertFalse(bridge_step["command_available"])
        self.assertEqual(bridge_step["action_type"], "manual_optional")

    def test_edge_bringup_sheet_combines_readiness_with_repo_commands(self) -> None:
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
        readiness = build_deployment_readiness(profile, preflight, launch_plan)
        manifest = build_deployment_command_manifest(config, launch_plan)
        bringup_sheet = build_guided_bringup_sheet(launch_plan, readiness, manifest)

        self.assertEqual(bringup_sheet["overall_status"], "blocked")
        gateway_step = next(item for item in bringup_sheet["steps"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_step["action_type"], "repo_command")
        self.assertIn("scripts/run_llm_gateway.py", gateway_step["display_command"])
        hardware_step = next(item for item in bringup_sheet["steps"] if item["step_id"] == "hardware_pose_dependency")
        self.assertEqual(hardware_step["action_type"], "manual_external")
        self.assertIsNone(hardware_step["display_command"])
        self.assertGreaterEqual(len(bringup_sheet["blocking_reasons"]), 1)


if __name__ == "__main__":
    unittest.main()
