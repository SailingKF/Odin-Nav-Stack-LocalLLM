import tempfile
import unittest
from pathlib import Path

from adapters.mock.artifact_player import MockArtifactPlayerBackend
from adapters.mock.audio_output import ManagedAudioOutput, ServiceBackedTTSAudioOutput
from core.interfaces.audio_output import AudioPlaybackRequest
from services.tts_service.service import build_tts_service


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class PlaybackCompletionTests(unittest.TestCase):
    def test_service_backed_active_state_exposes_backend_handle_status(self) -> None:
        clock = _FakeClock()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "audio_output_type": "tts_service",
                "tts_backend_type": "mock",
                "artifact_player_backend_type": "mock",
                "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
            }
            output = ManagedAudioOutput(
                ServiceBackedTTSAudioOutput(
                    tts_service=build_tts_service(config, repo_root=Path.cwd()),
                    artifact_player_backend=MockArtifactPlayerBackend(clock=clock),
                ),
                clock=clock,
            )

            output.play_text(
                AudioPlaybackRequest(
                    text="service-backed narration for completion state",
                    playback_kind="narration",
                    session_id="completion-session",
                    spot_id="gate",
                    spot_name="East Gate",
                )
            )
            playback_state = output.get_playback_state()

        self.assertEqual(playback_state["active_playback"]["metadata"]["latest_playback_handle_status"], "active")
        self.assertTrue(playback_state["active_playback"]["metadata"]["playback_completion_supported"])
        self.assertIsNone(playback_state["active_playback"]["metadata"]["playback_completion_source"])

    def test_service_backed_completion_is_reported_by_backend(self) -> None:
        clock = _FakeClock()
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "audio_output_type": "tts_service",
                "tts_backend_type": "mock",
                "artifact_player_backend_type": "mock",
                "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
            }
            output = ManagedAudioOutput(
                ServiceBackedTTSAudioOutput(
                    tts_service=build_tts_service(config, repo_root=Path.cwd()),
                    artifact_player_backend=MockArtifactPlayerBackend(clock=clock),
                ),
                clock=clock,
            )

            output.play_text(
                AudioPlaybackRequest(
                    text="service-backed narration that should complete by backend signal",
                    playback_kind="narration",
                    session_id="completion-session",
                    spot_id="gate",
                    spot_name="East Gate",
                )
            )
            clock.advance(5.0)
            playback_state = output.get_playback_state()

        self.assertIsNone(playback_state["active_playback"])
        completed_events = [item for item in playback_state["recent_events"] if item["event_type"] == "playback_completed"]
        self.assertEqual(len(completed_events), 1)
        self.assertEqual(completed_events[0]["extra"]["completion_source"], "backend_reported")
        self.assertEqual(completed_events[0]["extra"]["latest_playback_handle_status"], "completed")
        self.assertTrue(completed_events[0]["extra"]["player_completion_hook_invoked"])
