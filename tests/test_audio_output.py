import tempfile
import unittest
from pathlib import Path

from adapters.mock.audio_output import MockAudioOutput, SilentAudioOutput
from core.interfaces.audio_output import AudioPlaybackRequest
from core.interfaces.pose_provider import Pose2D
from core.narrator.mock_narrator import MockNarrator
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import JsonlSessionStore
from core.tour_orchestrator.orchestrator import TourOrchestrator


class AudioOutputTests(unittest.TestCase):
    def test_mock_audio_output_records_playback(self) -> None:
        output = MockAudioOutput()
        result = output.play_text(
            request=AudioPlaybackRequest(
                text="hello",
                playback_kind="narration",
                spot_id="gate",
                spot_name="East Gate",
            )
        )

        self.assertEqual(result.status, "played")
        self.assertEqual(result.output_type, "mock")
        self.assertEqual(len(output.history), 1)

    def test_silent_audio_output_skips_playback(self) -> None:
        output = SilentAudioOutput()
        result = output.play_text(
            request=AudioPlaybackRequest(
                text="hello",
                playback_kind="answer",
            )
        )

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.output_type, "silent")

    def test_orchestrator_routes_narration_and_answer_through_audio_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pois = load_pois("content/poi/demo_pois.yaml")
            route = load_route("content/routes/demo_route.yaml")
            route_pois = InMemoryPoiStore(pois).route_pois(route)
            session_store = JsonlSessionStore(str(Path(temp_dir) / "session_logs"))
            session_store.start_session({"env_name": "test"})
            audio_output = MockAudioOutput()
            orchestrator = TourOrchestrator(
                route_pois=route_pois,
                narrator=MockNarrator(),
                session_store=session_store,
                audio_output=audio_output,
                narration_mode_default="standard",
            )

            orchestrator.handle_pose(Pose2D(x=0.0, y=0.0, label="gate_inside"))
            answer = orchestrator.answer_question("Why does the tour start here?")
            session_summary = session_store.get_latest_session_summary()

        self.assertIn("first stop", answer["answer_text"])
        self.assertEqual(len(audio_output.history), 2)
        self.assertEqual(audio_output.history[0].playback_kind, "narration")
        self.assertEqual(audio_output.history[1].playback_kind, "answer")
        self.assertEqual(session_summary["latest_audio_playback"]["extra"]["playback_kind"], "answer")
        self.assertIn("East Gate", session_summary["latest_narration_text"])


if __name__ == "__main__":
    unittest.main()
