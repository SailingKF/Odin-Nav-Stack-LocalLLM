from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AudioPlaybackRequest:
    text: str
    playback_kind: str
    spot_id: Optional[str] = None
    spot_name: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AudioPlaybackResult:
    output_type: str
    playback_kind: str
    status: str
    text: str
    spot_id: Optional[str] = None
    spot_name: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AudioOutput(ABC):
    @abstractmethod
    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        """Request playback of a narration or answer text segment."""

    @abstractmethod
    def get_playback_state(self) -> Dict[str, Any]:
        """Return observable playback lifecycle state for runtime inspection."""
