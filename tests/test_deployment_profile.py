import unittest

from services.deployment_profile import build_deployment_profile


class DeploymentProfileTests(unittest.TestCase):
    def test_dev_profile_derives_dev_only_ready_summary(self) -> None:
        profile = build_deployment_profile(
            {
                "env_name": "dev",
                "pose_provider_type": "mock",
                "narrator_type": "local_llm",
                "audio_output_type": "tts_service",
                "llm_backend_type": "ollama",
                "recording_enabled": False,
                "tts_backend_type": "mock",
                "artifact_player_backend_type": "mock",
            }
        )

        self.assertEqual(profile["deployment_class"], "dev_only")
        self.assertEqual(profile["readiness_status"], "ready_for_profile")
        self.assertEqual(profile["capabilities"]["pose_source_expectation"], "mock")
        self.assertEqual(profile["errors"], [])

    def test_sim_profile_surfaces_stub_placeholder_warning(self) -> None:
        profile = build_deployment_profile(
            {
                "env_name": "sim",
                "pose_provider_type": "sim_ingress",
                "narrator_type": "mock",
                "audio_output_type": "mock",
                "llm_backend_type": "mock",
                "recording_enabled": False,
                "isaac_source": {"mode": "stub"},
            }
        )

        self.assertEqual(profile["deployment_class"], "sim_only")
        self.assertEqual(profile["readiness_status"], "ready_for_profile")
        self.assertIn("isaac_stub_source", profile["placeholder_components"])
        self.assertTrue(any("stub source" in warning for warning in profile["warnings"]))

    def test_edge_profile_marks_mock_backends_as_placeholder(self) -> None:
        profile = build_deployment_profile(
            {
                "env_name": "edge",
                "pose_provider_type": "odin_ros",
                "narrator_type": "local_llm",
                "audio_output_type": "mock",
                "llm_backend_type": "ollama",
                "recording_enabled": False,
                "tts_backend_type": "mock",
                "artifact_player_backend_type": "mock",
            }
        )

        self.assertEqual(profile["deployment_class"], "edge_candidate")
        self.assertEqual(profile["readiness_status"], "placeholder")
        self.assertFalse(profile["is_edge_ready"])
        self.assertIn("mock_audio_output", profile["placeholder_components"])
        self.assertIn("mock_tts_backend", profile["placeholder_components"])
        self.assertIn("mock_artifact_player", profile["placeholder_components"])

    def test_invalid_pose_provider_is_reported_as_error(self) -> None:
        profile = build_deployment_profile(
            {
                "env_name": "edge",
                "pose_provider_type": "mock",
                "narrator_type": "local_llm",
                "audio_output_type": "tts_service",
                "llm_backend_type": "ollama",
                "recording_enabled": False,
                "tts_backend_type": "mock",
                "artifact_player_backend_type": "mock",
            }
        )

        self.assertEqual(profile["readiness_status"], "invalid")
        self.assertTrue(any("expects pose_provider_type=odin_ros" in error for error in profile["errors"]))


if __name__ == "__main__":
    unittest.main()
