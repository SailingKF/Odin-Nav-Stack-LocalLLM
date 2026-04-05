import threading
import time
from typing import Any, Callable, Dict, List, Optional

from core.interfaces.audio_output import AudioOutput, AudioPlaybackRequest, AudioPlaybackResult
from core.interfaces.narrator import Narrator
from core.interfaces.pose_provider import Pose2D, PoseProvider
from core.interfaces.session_store import SessionStore
from core.poi.models import POI
from core.poi.trigger import PoiTriggerEngine
from core.tour_orchestrator.state import TourState


class TourOrchestrator:
    def __init__(
        self,
        route_pois: List[POI],
        narrator: Narrator,
        session_store: SessionStore,
        audio_output: Optional[AudioOutput] = None,
        trigger_engine: Optional[PoiTriggerEngine] = None,
        event_callback: Optional[Callable[[str], None]] = None,
        pose_provider: Optional[PoseProvider] = None,
        session_metadata: Optional[Dict[str, Any]] = None,
        narration_mode_default: str = "standard",
        step_interval_seconds: float = 0.0,
    ) -> None:
        self._route_pois = route_pois
        self._narrator = narrator
        self._session_store = session_store
        self._audio_output = audio_output
        self._trigger_engine = trigger_engine or PoiTriggerEngine()
        self._event_callback = event_callback
        self._pose_provider = pose_provider
        self._session_metadata = session_metadata or {}
        self._narration_mode_default = narration_mode_default
        self._step_interval_seconds = step_interval_seconds
        self._current_index = 0
        self._state = TourState.IDLE
        self._runner_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._paused = False
        self._resume_state = TourState.NAVIGATING
        self._completed = False
        self._session_started_by_orchestrator = False
        self._last_pose: Optional[Pose2D] = None
        self._last_narration_text: Optional[str] = None
        self._last_answer_text: Optional[str] = None
        self._last_event_type: Optional[str] = None
        self._last_focus_poi: Optional[POI] = None
        self._last_audio_playback: Optional[Dict[str, Any]] = None

    @property
    def state(self) -> TourState:
        return self._state

    def _emit(self, message: str) -> None:
        if self._event_callback is not None:
            self._event_callback(message)

    def _active_poi(self) -> Optional[POI]:
        if self._current_index >= len(self._route_pois):
            return None
        return self._route_pois[self._current_index]

    def _append_event(
        self,
        event_type: str,
        pose: Optional[Pose2D] = None,
        poi: Optional[POI] = None,
        state: Optional[str] = None,
        narration_text: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._session_store.append_event(
            event_type=event_type,
            pose=pose,
            poi=poi,
            state=state,
            narration_text=narration_text,
            extra=extra,
        )
        self._last_event_type = event_type
        if event_type == "narration_started" and narration_text is not None:
            self._last_narration_text = narration_text
        if event_type == "question_answered" and narration_text is not None:
            self._last_answer_text = narration_text
        if event_type == "audio_playback_requested":
            self._last_audio_playback = {
                "event_type": event_type,
                "state": state,
                "pose": None if pose is None else {"x": pose.x, "y": pose.y, "label": pose.label},
                "spot_id": None if poi is None else poi.spot_id,
                "spot_name": None if poi is None else poi.name,
                "text": narration_text,
                "extra": extra or {},
            }

    def _transition(self, next_state: TourState, pose: Optional[Pose2D], poi: Optional[POI]) -> None:
        previous_state = self._state
        self._state = next_state
        self._append_event(
            event_type="state_transition",
            pose=pose,
            poi=poi,
            state=next_state.value,
            extra={"previous_state": previous_state.value},
        )
        target_text = f" target={poi.spot_id}" if poi is not None else ""
        self._emit(f"[STATE] {previous_state.value} -> {next_state.value}{target_text}")

    def _start_session_if_needed(self) -> None:
        session_id = getattr(self._session_store, "session_id", None)
        if session_id is not None:
            return
        self._session_store.start_session(self._session_metadata)
        self._session_started_by_orchestrator = True

    def _request_audio_playback(
        self,
        text: str,
        playback_kind: str,
        pose: Optional[Pose2D],
        poi: Optional[POI],
        metadata: Optional[Dict[str, str]] = None,
    ) -> Optional[AudioPlaybackResult]:
        if self._audio_output is None:
            return None

        session_id = getattr(self._session_store, "session_id", None)
        result = self._audio_output.play_text(
            AudioPlaybackRequest(
                text=text,
                playback_kind=playback_kind,
                spot_id=None if poi is None else poi.spot_id,
                spot_name=None if poi is None else poi.name,
                session_id=session_id,
                metadata=metadata or {},
            )
        )
        result_payload = {
            "output_type": result.output_type,
            "playback_kind": result.playback_kind,
            "status": result.status,
            "session_id": result.session_id,
            "metadata": dict(result.metadata),
        }
        self._append_event(
            event_type="audio_playback_requested",
            pose=pose,
            poi=poi,
            state=self._state.value,
            narration_text=text,
            extra=result_payload,
        )
        return result

    def _complete_route(self, pose: Optional[Pose2D]) -> None:
        if self._completed:
            return
        self._completed = True
        self._transition(TourState.IDLE, pose, None)
        self._append_event(
            event_type="route_completed",
            pose=pose,
            state=self._state.value,
        )
        self._emit("[ROUTE] Demo route completed.")

    def _run_loop(self) -> None:
        if self._pose_provider is None:
            return

        for pose in self._pose_provider.iter_poses():
            while self._paused and not self._completed:
                time.sleep(0.02)
            if self._completed:
                break

            self.handle_pose(pose)
            if self._completed:
                break
            if self._step_interval_seconds > 0:
                time.sleep(self._step_interval_seconds)

        if self._session_started_by_orchestrator:
            self._session_store.close()

    def start(self) -> Dict[str, Any]:
        with self._lock:
            if self._runner_thread is not None and self._runner_thread.is_alive():
                return self.get_state()

            self._start_session_if_needed()
            self._paused = False
            self._completed = False
            self._last_narration_text = None
            self._last_answer_text = None
            self._last_event_type = "tour_started"
            self._last_focus_poi = None
            self._last_audio_playback = None
            self._current_index = 0
            self._trigger_engine.reset()
            self._state = TourState.IDLE
            if self._pose_provider is not None:
                self._pose_provider.reset()

            active_poi = self._active_poi()
            if active_poi is not None:
                self._transition(TourState.NAVIGATING, self._last_pose, active_poi)

            if self._pose_provider is not None:
                self._runner_thread = threading.Thread(target=self._run_loop, daemon=True)
                self._runner_thread.start()

            return self.get_state()

    def pause(self) -> Dict[str, Any]:
        with self._lock:
            if self._completed or self._state == TourState.PAUSED:
                return self.get_state()
            self._paused = True
            self._resume_state = self._state if self._state != TourState.IDLE else TourState.NAVIGATING
            self._transition(TourState.PAUSED, self._last_pose, self._active_poi())
            return self.get_state()

    def resume(self) -> Dict[str, Any]:
        with self._lock:
            if not self._paused:
                return self.get_state()
            self._paused = False
            target_state = self._resume_state if self._active_poi() is not None else TourState.IDLE
            self._transition(target_state, self._last_pose, self._active_poi())
            return self.get_state()

    def next_poi(self) -> Dict[str, Any]:
        with self._lock:
            current_poi = self._active_poi()
            if current_poi is None:
                return self.get_state()

            self._append_event(
                event_type="poi_skipped",
                pose=self._last_pose,
                poi=current_poi,
                state=self._state.value,
                extra={"reason": "manual_next"},
            )
            self._emit(f"[ROUTE] Skipping {current_poi.spot_id}.")
            self._current_index += 1

            next_poi = self._active_poi()
            if next_poi is None:
                self._complete_route(self._last_pose)
                return self.get_state()

            if not self._paused:
                self._transition(TourState.CONTINUE_ROUTE, self._last_pose, current_poi)
                self._transition(TourState.NAVIGATING, self._last_pose, next_poi)
            else:
                self._append_event(
                    event_type="navigation_target_updated",
                    pose=self._last_pose,
                    poi=next_poi,
                    state=self._state.value,
                    extra={"reason": "manual_next_while_paused"},
                )
            return self.get_state()

    def answer_question(self, question: str) -> Dict[str, Any]:
        with self._lock:
            focus_poi = self._last_focus_poi or self._active_poi()
            if focus_poi is None:
                answer_text = "No active or previously narrated POI is available for follow-up questions yet."
                return {
                    "question": question,
                    "answer_text": answer_text,
                    "spot_id": None,
                    "spot_name": None,
                    "state": self.get_state(),
                }

            answer_text = self._narrator.answer_question(focus_poi, question)
            self._append_event(
                event_type="question_answered",
                pose=self._last_pose,
                poi=focus_poi,
                state=self._state.value,
                narration_text=answer_text,
                extra={"question": question},
            )
            self._request_audio_playback(
                text=answer_text,
                playback_kind="answer",
                pose=self._last_pose,
                poi=focus_poi,
                metadata={"question": question},
            )
            self._emit(f"[ANSWER] {focus_poi.name}: {answer_text}")
            return {
                "question": question,
                "answer_text": answer_text,
                "spot_id": focus_poi.spot_id,
                "spot_name": focus_poi.name,
                "state": self.get_state(),
            }

    def get_state(self) -> Dict[str, Any]:
        active_poi = self._active_poi()
        session_id = getattr(self._session_store, "session_id", None)
        try:
            output_path = getattr(self._session_store, "output_path")
        except RuntimeError:
            output_path = None
        return {
            "session_id": session_id,
            "state": self._state.value,
            "is_running": self._runner_thread is not None and self._runner_thread.is_alive(),
            "is_paused": self._paused,
            "route_completed": self._completed,
            "current_index": self._current_index,
            "route_length": len(self._route_pois),
            "active_spot_id": None if active_poi is None else active_poi.spot_id,
            "active_spot_name": None if active_poi is None else active_poi.name,
            "narrator_type": type(self._narrator).__name__,
            "narration_mode_default": self._narration_mode_default,
            "last_pose": None
            if self._last_pose is None
            else {"x": self._last_pose.x, "y": self._last_pose.y, "label": self._last_pose.label},
            "last_event_type": self._last_event_type,
            "last_narration_text": self._last_narration_text,
            "last_answer_text": self._last_answer_text,
            "audio_output_type": None if self._audio_output is None else getattr(self._audio_output, "output_type", type(self._audio_output).__name__),
            "last_audio_playback": self._last_audio_playback,
            "session_log_path": None if output_path is None else str(output_path),
        }

    def get_latest_session_summary(self) -> Dict[str, Any]:
        if hasattr(self._session_store, "get_latest_session_summary"):
            return self._session_store.get_latest_session_summary()
        return {
            "session_id": getattr(self._session_store, "session_id", None),
            "session_log_path": None,
            "event_count": None,
            "latest_event_type": self._last_event_type,
            "latest_state": self._state.value,
            "latest_pose": None
            if self._last_pose is None
            else {"x": self._last_pose.x, "y": self._last_pose.y, "label": self._last_pose.label},
            "latest_spot_id": None if self._active_poi() is None else self._active_poi().spot_id,
            "latest_spot_name": None if self._active_poi() is None else self._active_poi().name,
            "latest_narration_text": self._last_narration_text,
            "latest_answer_text": self._last_answer_text,
            "latest_audio_playback": self._last_audio_playback,
        }

    def handle_pose(self, pose: Pose2D) -> None:
        with self._lock:
            self._last_pose = pose
            self._start_session_if_needed()
            active_poi = self._active_poi()
            self._append_event(
                event_type="pose_update",
                pose=pose,
                poi=active_poi,
                state=self._state.value,
            )

            if active_poi is None:
                if self._state != TourState.IDLE:
                    self._complete_route(pose)
                return

            if self._state == TourState.IDLE:
                self._transition(TourState.NAVIGATING, pose, active_poi)

            if not self._trigger_engine.evaluate(pose, active_poi):
                return

            self._transition(TourState.ARRIVED_POI, pose, active_poi)
            self._append_event(
                event_type="poi_triggered",
                pose=pose,
                poi=active_poi,
                state=self._state.value,
            )

            narration_text = self._narrator.generate_narration(active_poi, self._narration_mode_default)
            self._last_focus_poi = active_poi
            self._transition(TourState.PLAYING_NARRATION, pose, active_poi)
            self._append_event(
                event_type="narration_started",
                pose=pose,
                poi=active_poi,
                state=self._state.value,
                narration_text=narration_text,
                extra={"mode": self._narration_mode_default},
            )
            self._request_audio_playback(
                text=narration_text,
                playback_kind="narration",
                pose=pose,
                poi=active_poi,
                metadata={"mode": self._narration_mode_default},
            )
            self._emit(f"[NARRATION] {active_poi.name}: {narration_text}")

            self._transition(TourState.CONTINUE_ROUTE, pose, active_poi)
            self._current_index += 1

            next_poi = self._active_poi()
            if next_poi is None:
                self._complete_route(pose)
            else:
                self._transition(TourState.NAVIGATING, pose, next_poi)
