from typing import Callable, List, Optional

from core.interfaces.content_provider import ContentProvider
from core.interfaces.pose_provider import Pose2D
from core.interfaces.session_store import SessionStore
from core.poi.models import POI
from core.poi.trigger import PoiTriggerEngine
from core.tour_orchestrator.state import TourState


class TourOrchestrator:
    def __init__(
        self,
        route_pois: List[POI],
        content_provider: ContentProvider,
        session_store: SessionStore,
        trigger_engine: Optional[PoiTriggerEngine] = None,
        event_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._route_pois = route_pois
        self._content_provider = content_provider
        self._session_store = session_store
        self._trigger_engine = trigger_engine or PoiTriggerEngine()
        self._event_callback = event_callback
        self._current_index = 0
        self._state = TourState.IDLE

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

    def _transition(self, next_state: TourState, pose: Optional[Pose2D], poi: Optional[POI]) -> None:
        previous_state = self._state
        self._state = next_state
        self._session_store.append_event(
            event_type="state_transition",
            pose=pose,
            poi=poi,
            state=next_state.value,
            extra={"previous_state": previous_state.value},
        )
        target_text = f" target={poi.spot_id}" if poi is not None else ""
        self._emit(f"[STATE] {previous_state.value} -> {next_state.value}{target_text}")

    def handle_pose(self, pose: Pose2D) -> None:
        active_poi = self._active_poi()
        self._session_store.append_event(
            event_type="pose_update",
            pose=pose,
            poi=active_poi,
            state=self._state.value,
        )

        if active_poi is None:
            if self._state != TourState.IDLE:
                self._transition(TourState.IDLE, pose, None)
                self._session_store.append_event(
                    event_type="route_completed",
                    pose=pose,
                    state=self._state.value,
                )
            return

        if self._state == TourState.IDLE:
            self._transition(TourState.NAVIGATING, pose, active_poi)

        if not self._trigger_engine.evaluate(pose, active_poi):
            return

        self._transition(TourState.ARRIVED_POI, pose, active_poi)
        self._session_store.append_event(
            event_type="poi_triggered",
            pose=pose,
            poi=active_poi,
            state=self._state.value,
        )

        narration_text = self._content_provider.get_narration_text(active_poi.spot_id)
        self._transition(TourState.PLAYING_NARRATION, pose, active_poi)
        self._session_store.append_event(
            event_type="narration_started",
            pose=pose,
            poi=active_poi,
            state=self._state.value,
            narration_text=narration_text,
        )
        self._emit(f"[NARRATION] {active_poi.name}: {narration_text}")

        self._transition(TourState.CONTINUE_ROUTE, pose, active_poi)
        self._current_index += 1

        next_poi = self._active_poi()
        if next_poi is None:
            self._transition(TourState.IDLE, pose, None)
            self._session_store.append_event(
                event_type="route_completed",
                pose=pose,
                state=self._state.value,
            )
            self._emit("[ROUTE] Demo route completed.")
        else:
            self._transition(TourState.NAVIGATING, pose, next_poi)
