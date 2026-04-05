import unittest

from services.deployment_profile import (
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
)


class DeploymentReadinessTests(unittest.TestCase):
    def test_dev_mock_path_reports_ready_for_guided_bringup(self) -> None:
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "narrator_type": "mock",
            "audio_output_type": "mock",
            "llm_backend_type": "mock",
            "session_log_dir": "session_logs/dev",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        profile = build_deployment_profile(config)
        preflight = build_deployment_preflight(config, repo_root="C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs")
        launch_plan = build_deployment_launch_plan(config)

        readiness = build_deployment_readiness(profile, preflight, launch_plan)

        self.assertEqual(readiness["overall_status"], "ready_for_guided_bringup")
        self.assertEqual(readiness["required_blocked_count"], 0)
        self.assertEqual(readiness["required_external_unverified_count"], 0)
        api_step = next(item for item in readiness["steps"] if item["step_id"] == "api_server")
        self.assertEqual(api_step["status"], "ready")
        debug_step = next(item for item in readiness["steps"] if item["step_id"] == "debug_browser")
        self.assertEqual(debug_step["status"], "optional")

    def test_edge_path_surfaces_blocked_and_external_unverified_steps(self) -> None:
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
        profile = build_deployment_profile(config)
        preflight = build_deployment_preflight(config, repo_root="C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs")
        launch_plan = build_deployment_launch_plan(config)

        readiness = build_deployment_readiness(profile, preflight, launch_plan)

        self.assertEqual(readiness["overall_status"], "blocked")
        self.assertGreaterEqual(readiness["required_blocked_count"], 1)
        self.assertGreaterEqual(readiness["required_external_unverified_count"], 1)
        gateway_step = next(item for item in readiness["steps"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_step["status"], "blocked")
        hardware_step = next(item for item in readiness["steps"] if item["step_id"] == "hardware_pose_dependency")
        self.assertEqual(hardware_step["status"], "external_unverified")
        audio_step = next(item for item in readiness["steps"] if item["step_id"] == "audio_device_dependency")
        self.assertEqual(audio_step["status"], "not_applicable")

    def test_sim_live_path_reports_external_verification_needed_without_blocker(self) -> None:
        config = {
            "env_name": "sim",
            "pose_provider_type": "sim_ingress",
            "narrator_type": "mock",
            "audio_output_type": "mock",
            "llm_backend_type": "mock",
            "isaac_source": {"mode": "live"},
            "session_log_dir": "session_logs/sim",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        profile = build_deployment_profile(config)
        preflight = build_deployment_preflight(config, repo_root="C:\\Users\\saili\\Desktop\\odin_nav_stack_local_llm_docs")
        launch_plan = build_deployment_launch_plan(config)

        readiness = build_deployment_readiness(profile, preflight, launch_plan)

        self.assertEqual(readiness["overall_status"], "external_verification_needed")
        self.assertEqual(readiness["required_blocked_count"], 0)
        self.assertGreaterEqual(readiness["required_external_unverified_count"], 1)
        live_step = next(item for item in readiness["steps"] if item["step_id"] == "isaac_live_dependency")
        self.assertEqual(live_step["status"], "external_unverified")


if __name__ == "__main__":
    unittest.main()
