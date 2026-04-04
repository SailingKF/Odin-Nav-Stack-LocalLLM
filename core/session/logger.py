import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.interfaces.pose_provider import Pose2D
from core.interfaces.session_store import SessionStore
from core.poi.models import POI


class JsonlSessionStore(SessionStore):
    def __init__(self, session_log_dir: str) -> None:
        self._session_log_dir = Path(session_log_dir)
        self._session_id: Optional[str] = None
        self._output_path: Optional[Path] = None

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
        self.append_event("session_started", extra=metadata or {})
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
            "position": None if pose is None else {"x": pose.x, "y": pose.y, "label": pose.label},
            "poi": None
            if poi is None
            else {
                "spot_id": poi.spot_id,
                "name": poi.name,
                "x": poi.x,
                "y": poi.y,
                "trigger_radius": poi.trigger_radius,
            },
            "narration_text": narration_text,
            "extra": extra or {},
        }

        with self._output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def close(self) -> None:
        if self._output_path is None:
            return
        self.append_event("session_finished")
