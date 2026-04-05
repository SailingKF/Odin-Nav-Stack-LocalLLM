import unittest

from services.deployment_profile import (
    build_canonical_endpoint_config,
    build_deployment_command_manifest,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
    build_deployment_verification_manifest,
)


class DeploymentEndpointContractTests(unittest.TestCase):
    def test_dev_endpoint_contract_uses_llm_gateway_url_and_default_api_server_target(self) -> None:
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

        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)

        gateway = next(item for item in endpoint_contract["services"] if item["service_id"] == "llm_gateway")
        self.assertEqual(gateway["base_url"], "http://192.168.0.20:9900")
        self.assertEqual(gateway["port"], 9900)
        self.assertEqual(gateway["connect_host_source"], "legacy_compatibility")
        self.assertEqual(gateway["port_source"], "legacy_compatibility")
        api_server = next(item for item in endpoint_contract["services"] if item["service_id"] == "api_server")
        self.assertEqual(api_server["base_url"], "http://127.0.0.1:8000")
        self.assertEqual(api_server["bind_host_source"], "default")
        self.assertEqual(api_server["port_source"], "default")

    def test_sim_endpoint_contract_honors_service_endpoint_overrides(self) -> None:
        config = {
            "env_name": "sim",
            "pose_provider_type": "sim_ingress",
            "session_log_dir": "session_logs/sim",
            "current_route_file": "content/routes/demo_route.yaml",
            "current_poi_file": "content/poi/demo_pois.yaml",
            "service_endpoints": {
                "sim_pose_ingress_server": {
                    "bind_host": "0.0.0.0",
                    "connect_host": "127.0.0.1",
                    "port": 8200,
                }
            },
        }

        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        ingress = next(item for item in endpoint_contract["services"] if item["service_id"] == "sim_pose_ingress_server")

        self.assertEqual(ingress["bind_host"], "0.0.0.0")
        self.assertEqual(ingress["base_url"], "http://127.0.0.1:8200")
        self.assertEqual(ingress["bind_host_source"], "canonical_endpoint_config")
        self.assertEqual(ingress["port_source"], "canonical_endpoint_config")

    def test_verification_targets_align_with_endpoint_contract(self) -> None:
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
                "api_server": {
                    "bind_host": "0.0.0.0",
                    "connect_host": "127.0.0.1",
                    "port": 8088,
                }
            },
        }

        launch_plan = build_deployment_launch_plan(config)
        endpoint_contract = build_deployment_endpoint_contract(config, launch_plan)
        command_manifest = build_deployment_command_manifest(config, launch_plan, endpoint_contract)
        verification_manifest = build_deployment_verification_manifest(command_manifest, endpoint_contract)

        gateway_verification = next(item for item in verification_manifest["verifications"] if item["step_id"] == "llm_gateway")
        self.assertEqual(gateway_verification["target_url"], "http://127.0.0.1:9555/health")
        api_verification = next(item for item in verification_manifest["verifications"] if item["step_id"] == "api_server")
        self.assertEqual(api_verification["target_url"], "http://127.0.0.1:8088/health")

    def test_canonical_endpoint_config_prefers_service_endpoints_over_legacy_url(self) -> None:
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
                    "connect_host": "127.0.0.1",
                    "port": 9777,
                    "scheme": "http",
                }
            },
        }

        launch_plan = build_deployment_launch_plan(config)
        canonical = build_canonical_endpoint_config(config, launch_plan)
        self.assertEqual(canonical["preferred_config_shape"], "service_endpoints.<service_id>")
        gateway = next(item for item in canonical["services"] if item["service_id"] == "llm_gateway")

        self.assertEqual(gateway["base_url"], "http://127.0.0.1:9777")
        self.assertEqual(gateway["connect_host_source"], "canonical_endpoint_config")
        self.assertEqual(gateway["port_source"], "canonical_endpoint_config")


if __name__ == "__main__":
    unittest.main()
