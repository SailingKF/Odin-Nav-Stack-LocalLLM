from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.interfaces.pose_provider import Pose2D
from core.poi.models import POI


class SessionStore(ABC):
    @abstractmethod
    def start_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session and return its identifier."""

    @abstractmethod
    def append_event(
        self,
        event_type: str,
        pose: Optional[Pose2D] = None,
        poi: Optional[POI] = None,
        state: Optional[str] = None,
        narration_text: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a structured runtime event."""

    @abstractmethod
    def close(self) -> None:
        """Close any open session resources."""
