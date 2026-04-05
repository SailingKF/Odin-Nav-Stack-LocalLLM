import tempfile
import unittest
from pathlib import Path

from adapters.mock.artifact_player import MockArtifactPlayerBackend
from adapters.mock.audio_output import ManagedAudioOutput, MockAudioOutput, ServiceBackedTTSAudioOutput
from core.interfaces.audio_output import AudioPlaybackRequest
from core.interfaces.pose_provider import Pose2D
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import JsonlSessionStore, build_audio_lifecycle_session_persister
from services.tts_service.service import build_tts_service


class _FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class AudioSessionPersistenceTests(unittest.TestCase):
    @staticmethod
    def _load_route_pois():
        pois = load_pois("content/poi/demo_pois.yaml")
        route = load_route("content/routes/demo_route.yaml")
        return InMemoryPoiStore(pois).route_pois(route)

    @staticmethod
    def _append_request_event(
        store: JsonlSessionStore,
        pose: Pose2D,
        spot,
        request: AudioPlaybackRequest,
        result,
    ) -> None:
        store.append_event(
            event_type="audio_playback_requested",
            pose=pose,
            poi=spot,
            state="PLAYING_NARRATION",
            narration_text=request.text,
            extra={
                "output_type": result.output_type,
                "playback_kind": result.playback_kind,
                "status": result.status,
                "metadata": dict(result.metadata),
            },
        )

    def test_service_backed_completion_is_persisted_into_session_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            route_pois = self._load_route_pois()
            spot = route_pois[0]
            pose = Pose2D(x=spot.x, y=spot.y, label="gate_inside")
            store = JsonlSessionStore(str(Path(temp_dir) / "session_logs"))
            store.start_session({"env_name": "test"})
            store.append_event("pose_update", pose=pose, poi=spot, state="PLAYING_NARRATION")

            clock = _FakeClock()
            delegate = ServiceBackedTTSAudioOutput(
                tts_service=build_tts_service(
                    {
                        "tts_backend_type": "mock",
                        "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
                    },
                    repo_root=Path.cwd(),
                ),
                artifact_player_backend=MockArtifactPlayerBackend(clock=clock),
            )
            output = ManagedAudioOutput(
                delegate,
                clock=clock,
                lifecycle_event_callback=build_audio_lifecycle_session_persister(store, route_pois),
            )

            request = AudioPlaybackRequest(
                text=spot.standard_text,
                playback_kind="narration",
                spot_id=spot.spot_id,
                spot_name=spot.name,
                session_id=store.session_id,
            )
            result = output.play_text(request)
            self._append_request_event(store, pose, spot, request, result)

            clock.advance(10.0)
            output.get_playback_state()
            store.close()

            events = JsonlSessionStore._load_events(store.output_path)
            persisted_event_types = [item["event_type"] for item in events]
            summary = JsonlSessionStore.read_latest_session_summary(store.output_path.parent)

        self.assertIn("playback_started", persisted_event_types)
        self.assertIn("playback_completed", persisted_event_types)
        self.assertNotIn("playback_prepared", persisted_event_types)
        self.assertNotIn("playback_queued", persisted_event_types)
        self.assertEqual(summary["audio_summary"]["latest_completion_source"], "backend_reported")
        self.assertEqual(summary["audio_summary"]["latest_lifecycle_event"], "playback_completed")
        self.assertEqual(summary["audio_summary"]["active_playback_status"], "completed")
        self.assertEqual(summary["audio_summary"]["summary_status"], "idle")
        self.assertEqual(summary["recent_audio_events"][-1]["event_type"], "playback_completed")

    def test_interruption_is_persisted_without_raw_lifecycle_spam(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            route_pois = self._load_route_pois()
            spot = route_pois[0]
            pose = Pose2D(x=spot.x, y=spot.y, label="gate_inside")
            store = JsonlSessionStore(str(Path(temp_dir) / "session_logs"))
            store.start_session({"env_name": "test"})
            store.append_event("pose_update", pose=pose, poi=spot, state="PLAYING_NARRATION")

            output = ManagedAudioOutput(
                MockAudioOutput(),
                clock=_FakeClock(),
                lifecycle_event_callback=build_audio_lifecycle_session_persister(store, route_pois),
            )

            narration_request = AudioPlaybackRequest(
                text=spot.standard_text,
                playback_kind="narration",
                spot_id=spot.spot_id,
                spot_name=spot.name,
                session_id=store.session_id,
            )
            narration_result = output.play_text(narration_request)
            self._append_request_event(store, pose, spot, narration_request, narration_result)

            answer_request = AudioPlaybackRequest(
                text="The East Gate is the first stop in this demo route.",
                playback_kind="answer",
                spot_id=spot.spot_id,
                spot_name=spot.name,
                session_id=store.session_id,
            )
            answer_result = output.play_text(answer_request)
            self._append_request_event(store, pose, spot, answer_request, answer_result)
            store.close()

            events = JsonlSessionStore._load_events(store.output_path)
            persisted_event_types = [item["event_type"] for item in events]
            summary = JsonlSessionStore.read_latest_session_summary(store.output_path.parent)

        self.assertIn("playback_interrupted", persisted_event_types)
        self.assertEqual(persisted_event_types.count("playback_started"), 2)
        self.assertNotIn("playback_prepared", persisted_event_types)
        self.assertNotIn("playback_queued", persisted_event_types)
        self.assertTrue(any(item["event_type"] == "playback_interrupted" for item in summary["recent_audio_events"]))

    def test_failure_is_persisted_and_marked_as_degraded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            route_pois = self._load_route_pois()
            spot = route_pois[0]
            pose = Pose2D(x=spot.x, y=spot.y, label="gate_inside")
            store = JsonlSessionStore(str(Path(temp_dir) / "session_logs"))
            store.start_session({"env_name": "test"})
            store.append_event("pose_update", pose=pose, poi=spot, state="PLAYING_NARRATION")

            clock = _FakeClock()
            delegate = ServiceBackedTTSAudioOutput(
                tts_service=build_tts_service(
                    {
                        "tts_backend_type": "mock",
                        "tts_artifact_dir": str(Path(temp_dir) / "tts_artifacts"),
                    },
                    repo_root=Path.cwd(),
                ),
                artifact_player_backend=MockArtifactPlayerBackend(clock=clock),
            )
            output = ManagedAudioOutput(
                delegate,
                clock=clock,
                lifecycle_event_callback=build_audio_lifecycle_session_persister(store, route_pois),
            )

            request = AudioPlaybackRequest(
                text=spot.standard_text,
                playback_kind="narration",
                spot_id=spot.spot_id,
                spot_name=spot.name,
                session_id=store.session_id,
                metadata={"simulate_playback_start_failure": True},
            )
            result = output.play_text(request)
            self._append_request_event(store, pose, spot, request, result)
            store.close()

            events = JsonlSessionStore._load_events(store.output_path)
            persisted_event_types = [item["event_type"] for item in events]
            summary = JsonlSessionStore.read_latest_session_summary(store.output_path.parent)

        self.assertIn("playback_failed", persisted_event_types)
        self.assertEqual(summary["audio_summary"]["latest_failure_source"], "start_failed")
        self.assertEqual(summary["audio_summary"]["latest_lifecycle_event"], "playback_failed")
        self.assertEqual(summary["audio_summary"]["summary_status"], "degraded")
        self.assertTrue(summary["audio_summary"]["degraded_continuation_applied"])
        self.assertEqual(summary["recent_audio_events"][-1]["event_type"], "playback_failed")


if __name__ == "__main__":
    unittest.main()
