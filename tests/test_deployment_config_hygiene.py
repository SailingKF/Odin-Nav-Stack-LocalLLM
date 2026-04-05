import unittest

from services.deployment_profile import (
    build_deployment_config_hygiene,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
)


class DeploymentConfigHygieneTests(unittest.TestCase):
    @staticmethod
    def _build_hygiene(config):
        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        return build_deployment_config_hygiene(config, endpoint_contract)

    def test_fully_canonicalized_config_reports_clean_status(self) -> None:
        config = {
            "env_name": "edge",
            "pose_provider_type": "odin_ros",
            "narrator_type": "local_llm",
            "llm_backend_type": "ollama",
            "session_log_dir": "session_logs/edge",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
            "service_endpoints": {
                "llm_gateway": {
                    "bind_host": "0.0.0.0",
                    "connect_host": "127.0.0.1",
                    "port": 9000,
                    "scheme": "http",
                },
                "api_server": {
                    "bind_host": "0.0.0.0",
                    "connect_host": "127.0.0.1",
                    "port": 8000,
                    "scheme": "http",
                },
            },
        }

        hygiene = self._build_hygiene(config)

        self.assertEqual(hygiene["overall_hygiene_status"], "fully_canonicalized")
        self.assertFalse(hygiene["legacy_compatibility_in_use"])
        self.assertFalse(hygiene["legacy_compatibility_present"])
        self.assertEqual(hygiene["fully_canonicalized_service_count"], 2)
        self.assertEqual(hygiene["recommended_actions"], [])

    def test_legacy_only_config_reports_legacy_dependency(self) -> None:
        config = {
            "env_name": "dev",
            "pose_provider_type": "mock",
            "narrator_type": "local_llm",
            "llm_backend_type": "ollama",
            "llm_gateway_url": "http://192.168.0.20:9900",
            "session_log_dir": "session_logs/dev",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }

        hygiene = self._build_hygiene(config)

        self.assertEqual(hygiene["overall_hygiene_status"], "legacy_dependent")
        self.assertTrue(hygiene["legacy_compatibility_present"])
        self.assertTrue(hygiene["legacy_compatibility_in_use"])
        self.assertIn("llm_gateway_url", hygiene["legacy_compatibility_fields_present"])
        gateway = next(item for item in hygiene["services"] if item["service_id"] == "llm_gateway")
        self.assertEqual(gateway["hygiene_status"], "legacy_dependent")
        self.assertIn("service_endpoints.llm_gateway", " ".join(gateway["recommended_actions"]))

    def test_mixed_canonical_plus_legacy_config_is_reported_explicitly(self) -> None:
        config = {
            "env_name": "edge",
            "pose_provider_type": "odin_ros",
            "narrator_type": "local_llm",
            "llm_backend_type": "ollama",
            "llm_gateway_url": "http://127.0.0.1:9555",
            "session_log_dir": "session_logs/edge",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
            "service_endpoints": {
                "llm_gateway": {
                    "bind_host": "0.0.0.0",
                }
            },
        }

        hygiene = self._build_hygiene(config)

        self.assertEqual(hygiene["overall_hygiene_status"], "mixed_canonical_and_legacy")
        gateway = next(item for item in hygiene["services"] if item["service_id"] == "llm_gateway")
        self.assertEqual(gateway["hygiene_status"], "mixed_canonical_and_legacy")
        self.assertEqual(gateway["canonical_fields_in_use"], ["bind_host"])
        self.assertIn("connect_host", gateway["legacy_fields_in_use"])
        self.assertIn("llm_gateway_url", gateway["legacy_compatibility_fields_present"])

    def test_default_heavy_and_partially_canonicalized_actions_are_generated(self) -> None:
        default_heavy_config = {
            "env_name": "sim",
            "pose_provider_type": "sim_ingress",
            "narrator_type": "mock",
            "llm_backend_type": "mock",
            "session_log_dir": "session_logs/sim",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
        }
        partially_canonicalized_config = {
            "env_name": "sim",
            "pose_provider_type": "sim_ingress",
            "narrator_type": "mock",
            "llm_backend_type": "mock",
            "session_log_dir": "session_logs/sim",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
            "service_endpoints": {
                "sim_pose_ingress_server": {
                    "port": 8200,
                }
            },
        }

        default_heavy = self._build_hygiene(default_heavy_config)
        partially_canonicalized = self._build_hygiene(partially_canonicalized_config)

        self.assertEqual(default_heavy["overall_hygiene_status"], "default_heavy")
        self.assertGreater(default_heavy["default_heavy_service_count"], 0)
        self.assertTrue(
            any("service_endpoints.sim_pose_ingress_server" in action for action in default_heavy["recommended_actions"])
        )

        ingress = next(
            item
            for item in partially_canonicalized["services"]
            if item["service_id"] == "sim_pose_ingress_server"
        )
        self.assertEqual(ingress["hygiene_status"], "partially_canonicalized")
        self.assertIn("connect_host", ingress["default_fields_in_use"])
        self.assertTrue(
            any("Fill in the remaining explicit fields" in action for action in ingress["recommended_actions"])
        )


if __name__ == "__main__":
    unittest.main()
