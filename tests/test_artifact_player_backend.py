import tempfile
import unittest
from pathlib import Path

from adapters.mock.audio_output import ManagedAudioOutput, build_audio_output
from core.interfaces.audio_output import AudioPlaybackRequest


class ArtifactPlayerBackendTests(unittest.TestCase):
    def test_service_backed_start_routes_through_artifact_player_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = build_audio_output(
                {
                    "audio_output_type": "tts_service",
                    "tts_backend_type": "mock",
                    "artifact_player_backend_type": "mock",
                    "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
                },
                repo_root=Path.cwd(),
            )

            self.assertIsInstance(output, ManagedAudioOutput)
            result = output.play_text(
                AudioPlaybackRequest(
                    text="hello from tts service",
                    playback_kind="narration",
                    session_id="session-1",
                    spot_id="gate",
                    spot_name="East Gate",
                )
            )
            self.assertEqual(result.output_type, "tts_service")
            self.assertEqual(result.status, "started")
            self.assertEqual(result.metadata["tts_backend_type"], "mock")
            self.assertEqual(result.metadata["playback_backend_type"], "mock_artifact_player")
            self.assertTrue(result.metadata["player_start_hook_invoked"])
            self.assertEqual(result.metadata["player_status"], "started")
            self.assertIn("playback_handle", result.metadata)
            self.assertEqual(result.metadata["playback_handle"]["backend_type"], "mock_artifact_player")
            self.assertTrue(Path(result.metadata["artifact"]["artifact_uri"]).exists())

    def test_service_backed_interrupt_routes_through_artifact_player_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = build_audio_output(
                {
                    "audio_output_type": "tts_service",
                    "tts_backend_type": "mock",
                    "artifact_player_backend_type": "mock",
                    "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
                },
                repo_root=Path.cwd(),
            )

            output.play_text(
                AudioPlaybackRequest(
                    text="long narration for interruption",
                    playback_kind="narration",
                    session_id="session-2",
                    spot_id="gate",
                    spot_name="East Gate",
                )
            )
            answer = output.play_text(
                AudioPlaybackRequest(
                    text="answer now",
                    playback_kind="answer",
                    session_id="session-2",
                    spot_id="gate",
                    spot_name="East Gate",
                )
            )
            playback_state = output.get_playback_state()

        self.assertEqual(answer.metadata["playback_backend_type"], "mock_artifact_player")
        interrupted_events = [
            item for item in playback_state["recent_events"] if item["event_type"] == "playback_interrupted"
        ]
        self.assertEqual(len(interrupted_events), 1)
        interruption = interrupted_events[0]
        self.assertEqual(interruption["extra"]["playback_backend_type"], "mock_artifact_player")
        self.assertTrue(interruption["extra"]["player_interrupt_hook_invoked"])
        self.assertEqual(interruption["extra"]["player_interrupt_status"], "artifact_player_interrupted")
        self.assertIsNotNone(interruption["extra"]["playback_handle_id"])


if __name__ == "__main__":
    unittest.main()
