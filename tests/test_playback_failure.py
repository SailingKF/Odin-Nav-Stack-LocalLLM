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


class PlaybackFailureTests(unittest.TestCase):
    def test_service_backed_start_failure_marks_item_failed(self) -> None:
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

            result = output.play_text(
                AudioPlaybackRequest(
                    text="this playback should fail at start",
                    playback_kind="narration",
                    session_id="failure-session",
                    spot_id="gate",
                    spot_name="East Gate",
                    metadata={"simulate_playback_start_failure": True},
                )
            )
            playback_state = output.get_playback_state()

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.metadata["lifecycle_action"], "failed_start_continued")
        self.assertEqual(result.metadata["failure_status"], "artifact_player_start_failed")
        self.assertEqual(result.metadata["playback_failure_source"], "start_failed")
        self.assertTrue(result.metadata["degraded_continuation_applied"])
        self.assertIsNone(playback_state["active_playback"])
        failed_events = [item for item in playback_state["recent_events"] if item["event_type"] == "playback_failed"]
        self.assertEqual(len(failed_events), 1)
        self.assertEqual(failed_events[0]["extra"]["failure_source"], "start_failed")
        self.assertFalse(failed_events[0]["extra"]["queue_advanced"])

    def test_service_backed_active_failure_continues_queue(self) -> None:
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
                    text="active playback should fail after start",
                    playback_kind="narration",
                    session_id="failure-session",
                    spot_id="gate",
                    spot_name="East Gate",
                    metadata={"simulate_active_playback_failure_after_ms": 500},
                )
            )
            queued = output.play_text(
                AudioPlaybackRequest(
                    text="queued playback should continue after failure",
                    playback_kind="narration",
                    session_id="failure-session",
                    spot_id="plaza",
                    spot_name="Central Plaza",
                )
            )
            self.assertEqual(queued.status, "prepared")

            clock.advance(1.0)
            playback_state = output.get_playback_state()

        failed_events = [item for item in playback_state["recent_events"] if item["event_type"] == "playback_failed"]
        self.assertEqual(len(failed_events), 1)
        self.assertEqual(failed_events[0]["extra"]["failure_source"], "backend_reported")
        self.assertEqual(failed_events[0]["extra"]["failure_status"], "artifact_player_active_failed")
        self.assertTrue(failed_events[0]["extra"]["queue_advanced"])
        self.assertEqual(
            failed_events[0]["extra"]["degraded_continuation_policy"],
            "mark_failed_and_continue_queue",
        )
        self.assertEqual(playback_state["active_playback"]["spot_id"], "plaza")
        self.assertEqual(playback_state["active_playback"]["status"], "playing")
        self.assertEqual(playback_state["active_playback"]["metadata"]["latest_playback_handle_status"], "active")


if __name__ == "__main__":
    unittest.main()
