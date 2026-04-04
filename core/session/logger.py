import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.interfaces.pose_provider import Pose2D
from core.interfaces.session_store import SessionStore
from core.poi.models import POI


class JsonlSessionStore(SessionStore):
    def __init__(self, session_log_dir: str) -> None:
        self._session_log_dir = Path(session_log_dir)
        self._session_id: Optional[str] = None
        self._output_path: Optional[Path] = None
        self._event_count = 0
        self._latest_event: Optional[Dict[str, Any]] = None
        self._closed = True

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def output_path(self) -> Path:
        if self._output_path is None:
            raise RuntimeError("Session has not been started.")
        return self._output_path

    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        self._session_log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self._session_id = f"mock_tour_{timestamp}"
        self._output_path = self._session_log_dir / f"{self._session_id}.jsonl"
        self._event_count = 0
        self._latest_event = None
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

    def close(self) -> None:
        if self._output_path is None or self._closed:
            return
        state = "IDLE" if self._latest_event is None else self._latest_event.get("state")
        self.append_event("session_finished", state=state)
        self._closed = True

    def get_current_session_summary(self) -> Dict[str, Any]:
        latest = self._latest_event or {}
        return {
            "session_id": self._session_id,
            "session_log_path": None if self._output_path is None else str(self._output_path),
            "event_count": self._event_count,
            "latest_event_type": latest.get("event_type"),
            "latest_state": latest.get("state"),
            "latest_pose": latest.get("pose"),
            "latest_spot_id": latest.get("spot_id"),
            "latest_spot_name": latest.get("spot_name"),
            "latest_narration_text": latest.get("narration_text"),
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
            }

        latest_path = files[-1]
        events = cls._load_events(latest_path)
        latest = events[-1] if events else {}
        return {
            "session_id": latest.get("session_id"),
            "session_log_path": str(latest_path),
            "event_count": len(events),
            "latest_event_type": latest.get("event_type"),
            "latest_state": latest.get("state"),
            "latest_pose": latest.get("pose"),
            "latest_spot_id": latest.get("spot_id"),
            "latest_spot_name": latest.get("spot_name"),
            "latest_narration_text": latest.get("narration_text"),
        }
