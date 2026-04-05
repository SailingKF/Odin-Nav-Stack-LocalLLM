import tempfile
import unittest
from pathlib import Path

from core.session.logger import JsonlSessionStore


class AudioObservabilityTests(unittest.TestCase):
    def test_session_summary_includes_audio_summary_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = JsonlSessionStore(str(Path(temp_dir) / "session_logs"))
            store.start_session({"env_name": "test"})
            store.append_event(
                event_type="audio_playback_requested",
                state="PLAYING_NARRATION",
                narration_text="hello",
                extra={
                    "output_type": "tts_service",
                    "playback_kind": "narration",
                    "status": "failed",
                    "metadata": {
                        "lifecycle_action": "failed_start_continued",
                        "playback_failure_source": "start_failed",
                        "failure_status": "artifact_player_start_failed",
                        "failure_message": "simulated failure",
                        "degraded_continuation_applied": True,
                        "latest_playback_handle_status": None,
                    },
                },
            )

            summary = store.get_current_session_summary()

        audio = summary["audio_summary"]
        self.assertEqual(audio["latest_failure_source"], "start_failed")
        self.assertEqual(audio["latest_failure_status"], "artifact_player_start_failed")
        self.assertTrue(audio["degraded_continuation_applied"])
        self.assertEqual(audio["latest_lifecycle_action"], "failed_start_continued")
        self.assertIn("active_output_type", audio)


if __name__ == "__main__":
    unittest.main()
