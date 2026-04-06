import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.interfaces.pose_provider import Pose2D
from core.interfaces.session_store import SessionStore
from core.poi.models import POI


def _latest_event_by_type(events: List[Dict[str, Any]], event_type: str) -> Optional[Dict[str, Any]]:
    return next((item for item in reversed(events) if item.get("event_type") == event_type), None)


def _build_recent_audio_events(events: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    return [
        {
            "event_type": item.get("event_type"),
            "state": item.get("state"),
            "timestamp": item.get("timestamp"),
            "spot_id": item.get("spot_id"),
            "spot_name": item.get("spot_name"),
            "text": item.get("narration_text"),
            "extra": item.get("extra") or {},
        }
        for item in events
        if item.get("event_type") in {"playback_started", "playback_interrupted", "playback_completed", "playback_failed"}
    ][-limit:]


def _build_recent_narrations(events: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": item.get("timestamp"),
            "spot_id": item.get("spot_id"),
            "spot_name": item.get("spot_name"),
            "text": item.get("narration_text"),
            "state": item.get("state"),
            "mode": dict(item.get("extra") or {}).get("mode"),
        }
        for item in events
        if item.get("event_type") == "narration_started" and item.get("narration_text")
    ][-limit:]


def _build_recent_poi_triggers(events: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    return [
        {
            "timestamp": item.get("timestamp"),
            "spot_id": item.get("spot_id"),
            "spot_name": item.get("spot_name"),
            "state": item.get("state"),
        }
        for item in events
        if item.get("event_type") == "poi_triggered" and item.get("spot_id")
    ][-limit:]


def build_audio_summary_from_latest_audio_playback(
    latest_audio_playback: Optional[Dict[str, Any]],
    completion_event: Optional[Dict[str, Any]] = None,
    failure_event: Optional[Dict[str, Any]] = None,
    recent_audio_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    extra = {} if latest_audio_playback is None else dict(latest_audio_playback.get("extra") or {})
    metadata = dict(extra.get("metadata") or {})
    recent_audio_events = list(recent_audio_events or [])
    if completion_event is None:
        completion_event = _latest_event_by_type(recent_audio_events, "playback_completed")
    if failure_event is None:
        failure_event = _latest_event_by_type(recent_audio_events, "playback_failed")
    latest_audio_event = next(
        (
            item
            for item in reversed(recent_audio_events)
            if item.get("event_type") in {"playback_started", "playback_interrupted", "playback_completed", "playback_failed"}
        ),
        None,
    )
    latest_audio_event_extra = {} if latest_audio_event is None else dict(latest_audio_event.get("extra") or {})
    completion_extra = {} if completion_event is None else dict(completion_event.get("extra") or {})
    failure_extra = {} if failure_event is None else dict(failure_event.get("extra") or {})

    latest_completion_source = completion_extra.get("completion_source") or metadata.get("playback_completion_source")
    latest_failure_source = failure_extra.get("failure_source") or metadata.get("playback_failure_source")
    latest_failure_status = failure_extra.get("failure_status") or metadata.get("failure_status")
    latest_failure_message = failure_extra.get("failure_message") or metadata.get("failure_message")
    degraded_continuation_applied = bool(
        failure_extra.get("degraded_continuation_policy") or metadata.get("degraded_continuation_applied")
    )
    active_playback_status = None if latest_audio_playback is None else extra.get("status") or metadata.get("player_status")
    latest_lifecycle_event = None if latest_audio_event is None else latest_audio_event.get("event_type")
    if latest_lifecycle_event == "playback_started":
        active_playback_status = active_playback_status or "playing"
    elif latest_lifecycle_event == "playback_interrupted":
        active_playback_status = "interrupted"
    elif latest_lifecycle_event == "playback_completed":
        active_playback_status = "completed"
    elif latest_lifecycle_event == "playback_failed":
        active_playback_status = "failed"

    if latest_lifecycle_event == "playback_started" or active_playback_status in {"started", "played", "playing"}:
        summary_status = "active"
    elif latest_lifecycle_event == "playback_interrupted":
        summary_status = "idle"
    elif latest_failure_source:
        summary_status = "degraded"
    elif latest_lifecycle_event == "playback_completed":
        summary_status = "idle"
    elif latest_lifecycle_event == "playback_queued" or active_playback_status == "prepared":
        summary_status = "queued"
    elif active_playback_status == "prepared":
        summary_status = "queued"
    else:
        summary_status = "idle"

    return {
        "summary_status": summary_status,
        "active_playback_status": active_playback_status,
        "active_playback_kind": latest_audio_event_extra.get("playback_kind") or extra.get("playback_kind"),
        "active_output_type": latest_audio_event_extra.get("output_type") or extra.get("output_type"),
        "queued_count": 1 if metadata.get("lifecycle_action") == "queued" else 0,
        "latest_lifecycle_action": metadata.get("lifecycle_action"),
        "latest_lifecycle_event": latest_lifecycle_event,
        "latest_completion_source": latest_completion_source,
        "latest_failure_source": latest_failure_source,
        "latest_failure_status": latest_failure_status,
        "latest_failure_message": latest_failure_message,
        "latest_handle_status": latest_audio_event_extra.get("latest_playback_handle_status")
        or completion_extra.get("latest_playback_handle_status")
        or failure_extra.get("latest_playback_handle_status")
        or metadata.get("latest_playback_handle_status"),
        "degraded_continuation_applied": degraded_continuation_applied,
        "degraded_continuation_policy": failure_extra.get("degraded_continuation_policy"),
    }


class JsonlSessionStore(SessionStore):
    def __init__(self, session_log_dir: str) -> None:
        self._session_log_dir = Path(session_log_dir)
        self._session_id: Optional[str] = None
        self._output_path: Optional[Path] = None
        self._event_count = 0
        self._latest_event: Optional[Dict[str, Any]] = None
        self._latest_narration_text: Optional[str] = None
        self._latest_answer_text: Optional[str] = None
        self._latest_audio_playback: Optional[Dict[str, Any]] = None
        self._recent_audio_events: List[Dict[str, Any]] = []
        self._recent_narrations: List[Dict[str, Any]] = []
        self._recent_poi_triggers: List[Dict[str, Any]] = []
        self._closed = True

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def output_path(self) -> Path:
        if self._output_path is None:
            raise RuntimeError("Session has not been started.")
        return self._output_path

    @property
    def latest_state(self) -> Optional[str]:
        if self._latest_event is None:
            return None
        return self._latest_event.get("state")

    @property
    def latest_pose(self) -> Optional[Pose2D]:
        if self._latest_event is None:
            return None
        pose = self._latest_event.get("pose")
        if not pose:
            return None
        return Pose2D(x=float(pose["x"]), y=float(pose["y"]), label=pose.get("label"))

    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        self._session_log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._session_id = f"mock_tour_{timestamp}"
        self._output_path = self._session_log_dir / f"{self._session_id}.jsonl"
        self._event_count = 0
        self._latest_event = None
        self._latest_narration_text = None
        self._latest_answer_text = None
        self._latest_audio_playback = None
        self._recent_audio_events = []
        self._recent_narrations = []
        self._recent_poi_triggers = []
        self._closed = False
        self.append_event("session_started", state="IDLE", extra=metadata or {})
        return self._session_id

    def append_event(
        self,
        event_type: str,
        pose: Optional[Pose2D] = None,
        poi: Optional[POI] = None,
        state: Optional[str] = None,
        narration_text: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._output_path is None:
            raise RuntimeError("Session has not been started.")

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self._session_id,
            "event_type": event_type,
            "state": state,
            "pose": None if pose is None else {"x": pose.x, "y": pose.y, "label": pose.label},
            "spot_id": None if poi is None else poi.spot_id,
            "spot_name": None if poi is None else poi.name,
            "narration_text": narration_text,
            "extra": extra or {},
        }

        with self._output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

        self._event_count += 1
        self._latest_event = payload
        if event_type == "narration_started" and narration_text:
            self._latest_narration_text = narration_text
            self._recent_narrations.append(
                {
                    "timestamp": payload.get("timestamp"),
                    "spot_id": payload.get("spot_id"),
                    "spot_name": payload.get("spot_name"),
                    "text": narration_text,
                    "state": payload.get("state"),
                    "mode": dict(payload.get("extra") or {}).get("mode"),
                }
            )
            self._recent_narrations = self._recent_narrations[-5:]
        if event_type == "poi_triggered" and payload.get("spot_id"):
            self._recent_poi_triggers.append(
                {
                    "timestamp": payload.get("timestamp"),
                    "spot_id": payload.get("spot_id"),
                    "spot_name": payload.get("spot_name"),
                    "state": payload.get("state"),
                }
            )
            self._recent_poi_triggers = self._recent_poi_triggers[-5:]
        if event_type == "question_answered" and narration_text:
            self._latest_answer_text = narration_text
        if event_type == "audio_playback_requested":
            self._latest_audio_playback = {
                "event_type": event_type,
                "state": payload.get("state"),
                "pose": payload.get("pose"),
                "spot_id": payload.get("spot_id"),
                "spot_name": payload.get("spot_name"),
                "text": payload.get("narration_text"),
                "extra": payload.get("extra") or {},
            }
        if event_type in {"playback_started", "playback_interrupted", "playback_completed", "playback_failed"}:
            self._recent_audio_events.append(
                {
                    "event_type": event_type,
                    "state": payload.get("state"),
                    "timestamp": payload.get("timestamp"),
                    "spot_id": payload.get("spot_id"),
                    "spot_name": payload.get("spot_name"),
                    "text": payload.get("narration_text"),
                    "extra": payload.get("extra") or {},
                }
            )
            self._recent_audio_events = self._recent_audio_events[-5:]

    def close(self) -> None:
        if self._output_path is None or self._closed:
            return
        state = "IDLE" if self._latest_event is None else self._latest_event.get("state")
        self.append_event("session_finished", state=state)
        self._closed = True

    def get_current_session_summary(self) -> Dict[str, Any]:
        latest = self._latest_event or {}
        completion_event = next(
            (item for item in reversed(self._recent_audio_events) if item.get("event_type") == "playback_completed"),
            None,
        )
        failure_event = next(
            (item for item in reversed(self._recent_audio_events) if item.get("event_type") == "playback_failed"),
            None,
        )
        audio_summary = build_audio_summary_from_latest_audio_playback(
            self._latest_audio_playback,
            completion_event=completion_event,
            failure_event=failure_event,
            recent_audio_events=self._recent_audio_events,
        )
        return {
            "session_id": self._session_id,
            "session_log_path": None if self._output_path is None else str(self._output_path),
            "event_count": self._event_count,
            "latest_event_type": latest.get("event_type"),
            "latest_state": latest.get("state"),
            "latest_pose": latest.get("pose"),
            "latest_spot_id": latest.get("spot_id"),
            "latest_spot_name": latest.get("spot_name"),
            "latest_narration_text": self._latest_narration_text,
            "latest_narrated_spot_id": None if not self._recent_narrations else self._recent_narrations[-1].get("spot_id"),
            "latest_narrated_spot_name": None if not self._recent_narrations else self._recent_narrations[-1].get("spot_name"),
            "latest_triggered_spot_id": None if not self._recent_poi_triggers else self._recent_poi_triggers[-1].get("spot_id"),
            "latest_triggered_spot_name": None if not self._recent_poi_triggers else self._recent_poi_triggers[-1].get("spot_name"),
            "latest_answer_text": self._latest_answer_text,
            "latest_audio_playback": self._latest_audio_playback,
            "audio_summary": audio_summary,
            "recent_audio_events": list(self._recent_audio_events),
            "recent_narrations": list(self._recent_narrations),
            "recent_poi_triggers": list(self._recent_poi_triggers),
        }

    def get_latest_session_summary(self) -> Dict[str, Any]:
        if self._session_id is not None:
            return self.get_current_session_summary()
        return self.read_latest_session_summary(self._session_log_dir)

    @staticmethod
    def _load_events(path: Path) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        if not path.exists():
            return events
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    events.append(json.loads(line))
        return events

    @classmethod
    def read_latest_session_summary(cls, session_log_dir: Path) -> Dict[str, Any]:
        session_dir = Path(session_log_dir)
        files = sorted(session_dir.glob("*.jsonl"))
        if not files:
            return {
                "session_id": None,
                "session_log_path": None,
                "event_count": 0,
                "latest_event_type": None,
                "latest_state": None,
                "latest_pose": None,
                "latest_spot_id": None,
                "latest_spot_name": None,
                "latest_narration_text": None,
                "latest_narrated_spot_id": None,
                "latest_narrated_spot_name": None,
                "latest_triggered_spot_id": None,
                "latest_triggered_spot_name": None,
                "latest_answer_text": None,
                "latest_audio_playback": None,
                "audio_summary": build_audio_summary_from_latest_audio_playback(None),
                "recent_audio_events": [],
                "recent_narrations": [],
                "recent_poi_triggers": [],
            }

        latest_path = files[-1]
        events = cls._load_events(latest_path)
        latest = events[-1] if events else {}
        latest_narration = next(
            (item.get("narration_text") for item in reversed(events) if item.get("event_type") == "narration_started" and item.get("narration_text")),
            None,
        )
        latest_answer = next(
            (item.get("narration_text") for item in reversed(events) if item.get("event_type") == "question_answered" and item.get("narration_text")),
            None,
        )
        latest_audio_playback = next(
            (
                {
                    "event_type": item.get("event_type"),
                    "state": item.get("state"),
                    "pose": item.get("pose"),
                    "spot_id": item.get("spot_id"),
                    "spot_name": item.get("spot_name"),
                    "text": item.get("narration_text"),
                    "extra": item.get("extra") or {},
                }
                for item in reversed(events)
                if item.get("event_type") == "audio_playback_requested"
            ),
            None,
        )
        recent_narrations = _build_recent_narrations(events)
        recent_poi_triggers = _build_recent_poi_triggers(events)
        return {
            "session_id": latest.get("session_id"),
            "session_log_path": str(latest_path),
            "event_count": len(events),
            "latest_event_type": latest.get("event_type"),
            "latest_state": latest.get("state"),
            "latest_pose": latest.get("pose"),
            "latest_spot_id": latest.get("spot_id"),
            "latest_spot_name": latest.get("spot_name"),
            "latest_narration_text": latest_narration,
            "latest_narrated_spot_id": None if not recent_narrations else recent_narrations[-1].get("spot_id"),
            "latest_narrated_spot_name": None if not recent_narrations else recent_narrations[-1].get("spot_name"),
            "latest_triggered_spot_id": None if not recent_poi_triggers else recent_poi_triggers[-1].get("spot_id"),
            "latest_triggered_spot_name": None if not recent_poi_triggers else recent_poi_triggers[-1].get("spot_name"),
            "latest_answer_text": latest_answer,
            "latest_audio_playback": latest_audio_playback,
            "audio_summary": build_audio_summary_from_latest_audio_playback(
                latest_audio_playback=latest_audio_playback,
                completion_event=_latest_event_by_type(events, "playback_completed"),
                failure_event=_latest_event_by_type(events, "playback_failed"),
                recent_audio_events=_build_recent_audio_events(events),
            ),
            "recent_audio_events": _build_recent_audio_events(events),
            "recent_narrations": recent_narrations,
            "recent_poi_triggers": recent_poi_triggers,
        }


def build_audio_lifecycle_session_persister(
    session_store: JsonlSessionStore,
    route_pois: List[POI],
) -> Callable[[Dict[str, Any]], None]:
    poi_by_id = {poi.spot_id: poi for poi in route_pois}
    persisted_event_types = {"playback_started", "playback_interrupted", "playback_completed", "playback_failed"}

    def _persist(event: Dict[str, Any]) -> None:
        event_type = event.get("event_type")
        if event_type not in persisted_event_types:
            return
        session_store.append_event(
            event_type=str(event_type),
            pose=session_store.latest_pose,
            poi=poi_by_id.get(str(event.get("spot_id"))) if event.get("spot_id") is not None else None,
            state=session_store.latest_state,
            narration_text=event.get("text"),
            extra={
                "playback_id": event.get("playback_id"),
                "playback_kind": event.get("playback_kind"),
                "output_type": event.get("output_type"),
                "metadata": dict(event.get("metadata") or {}),
                **dict(event.get("extra") or {}),
            },
        )

    return _persist
