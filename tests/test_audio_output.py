import tempfile
import unittest
from pathlib import Path

from adapters.mock.audio_output import ManagedAudioOutput, MockAudioOutput, ServiceBackedTTSAudioOutput, SilentAudioOutput, build_audio_output
from core.interfaces.audio_output import AudioPlaybackRequest
from core.interfaces.pose_provider import Pose2D
from core.narrator.mock_narrator import MockNarrator
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import JsonlSessionStore
from core.tour_orchestrator.orchestrator import TourOrchestrator


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


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

    def test_service_backed_audio_output_returns_synthesis_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = build_audio_output(
                {
                    "audio_output_type": "tts_service",
                    "tts_backend_type": "mock",
                    "tts_artifact_dir": temp_dir,
                },
                repo_root=Path.cwd(),
            )

            self.assertIsInstance(output, ManagedAudioOutput)
            result = output.play_text(
                request=AudioPlaybackRequest(
                    text="hello",
                    playback_kind="narration",
                    session_id="session-3",
                    spot_id="gate",
                    spot_name="East Gate",
                )
            )

            self.assertEqual(result.output_type, "tts_service")
            self.assertEqual(result.status, "started")
            self.assertEqual(result.metadata["backend_type"], "mock")
            self.assertEqual(result.metadata["tts_backend_type"], "mock")
            self.assertEqual(result.metadata["status"], "synthesized")
            self.assertEqual(result.metadata["playback_backend_type"], "mock_artifact_player")
            self.assertEqual(result.metadata["playback_handle"]["backend_type"], "mock_artifact_player")
            self.assertTrue(Path(result.metadata["artifact"]["artifact_uri"]).exists())
            self.assertEqual(result.metadata["lifecycle_action"], "started")
            self.assertTrue(result.metadata["start_hook_invoked"])
            self.assertTrue(result.metadata["player_start_hook_invoked"])

    def test_managed_audio_output_queues_second_narration(self) -> None:
        clock = _FakeClock()
        delegate = MockAudioOutput()
        output = ManagedAudioOutput(delegate, clock=clock)

        first = output.play_text(
            AudioPlaybackRequest(text="first narration", playback_kind="narration", spot_id="gate")
        )
        second = output.play_text(
            AudioPlaybackRequest(text="second narration", playback_kind="narration", spot_id="plaza")
        )
        playback_state = output.get_playback_state()

        self.assertEqual(first.status, "started")
        self.assertEqual(first.metadata["lifecycle_action"], "started")
        self.assertEqual(second.status, "prepared")
        self.assertEqual(second.metadata["lifecycle_action"], "queued")
        self.assertFalse(second.metadata["start_hook_invoked"])
        self.assertEqual(len(delegate.history), 1)
        self.assertEqual(playback_state["active_playback"]["spot_id"], "gate")
        self.assertEqual(len(playback_state["queued_playbacks"]), 1)
        self.assertEqual(playback_state["queued_playbacks"][0]["spot_id"], "plaza")
        self.assertEqual(playback_state["queued_playbacks"][0]["status"], "queued")

        clock.advance(5.0)
        playback_state = output.get_playback_state()
        self.assertEqual(len(delegate.history), 2)
        self.assertEqual(playback_state["active_playback"]["spot_id"], "plaza")
        self.assertEqual(playback_state["active_playback"]["status"], "playing")
        self.assertEqual(len(playback_state["queued_playbacks"]), 0)

    def test_managed_audio_output_interrupts_active_playback_for_answer(self) -> None:
        clock = _FakeClock()
        delegate = MockAudioOutput()
        output = ManagedAudioOutput(delegate, clock=clock)

        first = output.play_text(
            AudioPlaybackRequest(text="long narration", playback_kind="narration", spot_id="gallery")
        )
        answer = output.play_text(
            AudioPlaybackRequest(text="answer now", playback_kind="answer", spot_id="gallery")
        )
        playback_state = output.get_playback_state()

        self.assertEqual(answer.status, "started")
        self.assertEqual(first.metadata["lifecycle_action"], "started")
        self.assertEqual(answer.metadata["lifecycle_action"], "replaced_active")
        self.assertEqual(answer.metadata["replaced_playback_id"], first.metadata["playback_id"])
        self.assertTrue(answer.metadata["start_hook_invoked"])
        self.assertEqual(len(delegate.interrupt_history), 1)
        self.assertTrue(delegate.interrupt_history[0]["interrupt_hook_invoked"])
        self.assertEqual(playback_state["active_playback"]["playback_kind"], "answer")
        recent_event_types = [item["event_type"] for item in playback_state["recent_events"]]
        self.assertIn("playback_prepared", recent_event_types)
        self.assertIn("playback_interrupted", recent_event_types)

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

    def test_orchestrator_can_use_service_backed_audio_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pois = load_pois("content/poi/demo_pois.yaml")
            route = load_route("content/routes/demo_route.yaml")
            route_pois = InMemoryPoiStore(pois).route_pois(route)
            session_store = JsonlSessionStore(str(Path(temp_dir) / "session_logs"))
            session_store.start_session({"env_name": "test"})
            audio_output = build_audio_output(
                {
                    "audio_output_type": "tts_service",
                    "tts_backend_type": "mock",
                    "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
                },
                repo_root=Path.cwd(),
            )
            orchestrator = TourOrchestrator(
                route_pois=route_pois,
                narrator=MockNarrator(),
                session_store=session_store,
                audio_output=audio_output,
                narration_mode_default="standard",
            )

            orchestrator.handle_pose(Pose2D(x=0.0, y=0.0, label="gate_inside"))
            answer = orchestrator.answer_question("Why does the tour start here?")
            state = orchestrator.get_state()
            session_summary = session_store.get_latest_session_summary()
            artifact_path = Path(session_summary["latest_audio_playback"]["extra"]["metadata"]["artifact"]["artifact_uri"])

            self.assertTrue(artifact_path.exists())

        self.assertIn("first stop", answer["answer_text"])
        self.assertEqual(state["audio_output_type"], "tts_service")
        self.assertIsNotNone(state["audio_playback_state"])
        self.assertEqual(
            state["audio_playback_state"]["policy_name"],
            "answers_interrupt_active_playback__narration_queues_fifo",
        )
        self.assertEqual(state["last_audio_playback"]["extra"]["status"], "started")
        self.assertTrue(state["last_audio_playback"]["extra"]["metadata"]["start_hook_invoked"])
        self.assertEqual(
            state["last_audio_playback"]["extra"]["metadata"]["playback_backend_type"],
            "mock_artifact_player",
        )
        self.assertEqual(session_summary["latest_audio_playback"]["extra"]["output_type"], "tts_service")
        self.assertEqual(
            session_summary["latest_audio_playback"]["extra"]["metadata"]["backend_type"],
            "mock",
        )
        self.assertEqual(
            session_summary["latest_audio_playback"]["extra"]["metadata"]["playback_backend_type"],
            "mock_artifact_player",
        )


if __name__ == "__main__":
    unittest.main()
