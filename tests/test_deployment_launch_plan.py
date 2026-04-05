import unittest

from services.deployment_profile import build_deployment_launch_plan


class DeploymentLaunchPlanTests(unittest.TestCase):
    def test_dev_launch_plan_orders_runtime_before_api(self) -> None:
        plan = build_deployment_launch_plan(
            {
                "env_name": "dev",
                "narrator_type": "local_llm",
                "llm_backend_type": "ollama",
            }
        )

        self.assertEqual(plan["profile_name"], "dev")
        self.assertEqual(plan["automation_level"], "manual_guided")
        self.assertIn("internal_service", plan["categories"])
        ordered_ids = [item["step_id"] for item in plan["steps"]]
        self.assertEqual(ordered_ids, ["ollama_runtime", "llm_gateway", "api_server", "debug_browser"])

    def test_sim_launch_plan_distinguishes_internal_and_optional_services(self) -> None:
        plan = build_deployment_launch_plan(
            {
                "env_name": "sim",
                "isaac_source": {"mode": "stub"},
            }
        )

        ordered_ids = [item["step_id"] for item in plan["steps"]]
        self.assertEqual(ordered_ids[0], "isaac_stub_source")
        self.assertIn("sim_pose_ingress_server", ordered_ids)
        self.assertIn("optional_service", plan["categories"])

    def test_edge_launch_plan_marks_external_and_manual_steps(self) -> None:
        plan = build_deployment_launch_plan(
            {
                "env_name": "edge",
                "llm_backend_type": "ollama",
                "audio_output_type": "mock",
            }
        )

        ordered_ids = [item["step_id"] for item in plan["steps"]]
        self.assertEqual(ordered_ids[0], "hardware_pose_dependency")
        self.assertIn("llm_gateway", ordered_ids)
        self.assertIn("api_server", ordered_ids)
        self.assertIn("external_dependency", plan["categories"])
        audio_step = next(item for item in plan["steps"] if item["step_id"] == "audio_device_dependency")
        self.assertEqual(audio_step["category"], "optional_service")
        self.assertFalse(audio_step["required"])


if __name__ == "__main__":
    unittest.main()
