import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.interfaces.audio_output import AudioOutput, AudioPlaybackRequest, AudioPlaybackResult
from services.tts_service.service import TTSService, TTSRequest, build_tts_service


def _default_duration_ms(text: str) -> int:
    return max(400, len(text) * 45)


class MockAudioOutput(AudioOutput):
    output_type = "mock"

    def __init__(self, event_callback: Optional[Callable[[str], None]] = None) -> None:
        self._event_callback = event_callback
        self.history: List[AudioPlaybackResult] = []

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        result = AudioPlaybackResult(
            output_type="mock",
            playback_kind=request.playback_kind,
            status="played",
            text=request.text,
            spot_id=request.spot_id,
            spot_name=request.spot_name,
            session_id=request.session_id,
            metadata={
                **dict(request.metadata),
                "estimated_duration_ms": _default_duration_ms(request.text),
            },
        )
        self.history.append(result)
        if self._event_callback is not None:
            label = request.spot_name or request.spot_id or "tour"
            self._event_callback(f"[AUDIO] {request.playback_kind} via mock: {label}")
        return result

    def get_playback_state(self) -> Dict[str, Any]:
        return {
            "policy_name": "direct_immediate",
            "active_playback": None,
            "queued_playbacks": [],
            "recent_events": [],
        }


class SilentAudioOutput(AudioOutput):
    output_type = "silent"

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        return AudioPlaybackResult(
            output_type="silent",
            playback_kind=request.playback_kind,
            status="skipped",
            text=request.text,
            spot_id=request.spot_id,
            spot_name=request.spot_name,
            session_id=request.session_id,
            metadata={
                **dict(request.metadata),
                "estimated_duration_ms": 0,
            },
        )

    def get_playback_state(self) -> Dict[str, Any]:
        return {
            "policy_name": "silent_no_playback",
            "active_playback": None,
            "queued_playbacks": [],
            "recent_events": [],
        }


class ServiceBackedTTSAudioOutput(AudioOutput):
    output_type = "tts_service"

    def __init__(self, tts_service: TTSService, event_callback: Optional[Callable[[str], None]] = None) -> None:
        self._tts_service = tts_service
        self._event_callback = event_callback
        self.history: List[AudioPlaybackResult] = []

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        synthesis = self._tts_service.synthesize(
            TTSRequest(
                text=request.text,
                playback_kind=request.playback_kind,
                session_id=request.session_id,
                spot_id=request.spot_id,
                spot_name=request.spot_name,
                metadata=dict(request.metadata),
            )
        )
        result = AudioPlaybackResult(
            output_type="tts_service",
            playback_kind=request.playback_kind,
            status="played",
            text=request.text,
            spot_id=request.spot_id,
            spot_name=request.spot_name,
            session_id=request.session_id,
            metadata=synthesis.to_metadata_dict(),
        )
        self.history.append(result)
        if self._event_callback is not None:
            label = request.spot_name or request.spot_id or "tour"
            backend_type = synthesis.backend_type
            self._event_callback(f"[AUDIO] {request.playback_kind} via tts_service/{backend_type}: {label}")
        return result

    def get_playback_state(self) -> Dict[str, Any]:
        return {
            "policy_name": "direct_immediate",
            "active_playback": None,
            "queued_playbacks": [],
            "recent_events": [],
        }


class ManagedAudioOutput(AudioOutput):
    def __init__(
        self,
        delegate: AudioOutput,
        clock: Optional[Callable[[], float]] = None,
        recent_event_limit: int = 10,
    ) -> None:
        self._delegate = delegate
        self._clock = clock or time.monotonic
        self._recent_event_limit = recent_event_limit
        self._active_playback: Optional[Dict[str, Any]] = None
        self._queued_playbacks: List[Dict[str, Any]] = []
        self._recent_events: List[Dict[str, Any]] = []
        self._next_playback_id = 1

    @property
    def output_type(self) -> str:
        return getattr(self._delegate, "output_type", type(self._delegate).__name__)

    def _clone_item(self, item: Dict[str, Any], now: float) -> Dict[str, Any]:
        remaining_ms = max(0, int((item["finish_at"] - now) * 1000)) if item.get("finish_at") is not None else 0
        return {
            "playback_id": item["playback_id"],
            "output_type": item["output_type"],
            "playback_kind": item["playback_kind"],
            "status": item["status"],
            "text": item["text"],
            "spot_id": item["spot_id"],
            "spot_name": item["spot_name"],
            "session_id": item["session_id"],
            "requested_at_monotonic": item["requested_at_monotonic"],
            "started_at_monotonic": item.get("started_at_monotonic"),
            "duration_ms": item["duration_ms"],
            "remaining_ms": remaining_ms,
            "metadata": dict(item["metadata"]),
        }

    def _record_event(self, event_type: str, item: Dict[str, Any], now: float, extra: Optional[Dict[str, Any]] = None) -> None:
        payload = {
            "event_type": event_type,
            "playback_id": item["playback_id"],
            "playback_kind": item["playback_kind"],
            "output_type": item["output_type"],
            "spot_id": item["spot_id"],
            "spot_name": item["spot_name"],
            "timestamp_monotonic": now,
            "metadata": dict(item["metadata"]),
            "extra": extra or {},
        }
        self._recent_events.append(payload)
        self._recent_events = self._recent_events[-self._recent_event_limit :]

    def _start_item(self, item: Dict[str, Any], now: float) -> None:
        item["status"] = "playing"
        item["started_at_monotonic"] = now
        item["finish_at"] = now + (item["duration_ms"] / 1000.0)
        self._active_playback = item
        self._record_event("playback_started", item, now)

    def _complete_expired_playback(self, now: float) -> None:
        while self._active_playback is not None and self._active_playback["finish_at"] <= now:
            completed = self._active_playback
            completed["status"] = "completed"
            self._record_event("playback_completed", completed, now)
            self._active_playback = None
            if self._queued_playbacks:
                next_item = self._queued_playbacks.pop(0)
                self._start_item(next_item, now)
            else:
                break

    def _refresh_state(self) -> None:
        self._complete_expired_playback(self._clock())

    def _item_from_result(self, result: AudioPlaybackResult) -> Dict[str, Any]:
        playback_id = f"audio-{self._next_playback_id}"
        self._next_playback_id += 1
        metadata = dict(result.metadata)
        duration_ms = int(metadata.get("estimated_duration_ms", _default_duration_ms(result.text)))
        return {
            "playback_id": playback_id,
            "output_type": result.output_type,
            "playback_kind": result.playback_kind,
            "status": "pending",
            "text": result.text,
            "spot_id": result.spot_id,
            "spot_name": result.spot_name,
            "session_id": result.session_id,
            "requested_at_monotonic": self._clock(),
            "started_at_monotonic": None,
            "finish_at": None,
            "duration_ms": duration_ms,
            "metadata": metadata,
        }

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        self._refresh_state()
        delegate_result = self._delegate.play_text(request)
        item = self._item_from_result(delegate_result)
        now = self._clock()
        lifecycle_action = "started"
        replaced_playback_id = None

        if self._active_playback is None:
            self._start_item(item, now)
        elif request.playback_kind == "answer":
            replaced_playback_id = self._active_playback["playback_id"]
            interrupted = self._active_playback
            interrupted["status"] = "interrupted"
            self._record_event(
                "playback_interrupted",
                interrupted,
                now,
                extra={"replaced_by_playback_id": item["playback_id"]},
            )
            self._start_item(item, now)
            lifecycle_action = "replaced_active"
        else:
            item["status"] = "queued"
            self._queued_playbacks.append(item)
            self._record_event("playback_queued", item, now)
            lifecycle_action = "queued"

        merged_metadata = {
            **dict(delegate_result.metadata),
            "estimated_duration_ms": item["duration_ms"],
            "lifecycle_action": lifecycle_action,
            "playback_id": item["playback_id"],
            "replaced_playback_id": replaced_playback_id,
        }
        return AudioPlaybackResult(
            output_type=delegate_result.output_type,
            playback_kind=delegate_result.playback_kind,
            status=delegate_result.status,
            text=delegate_result.text,
            spot_id=delegate_result.spot_id,
            spot_name=delegate_result.spot_name,
            session_id=delegate_result.session_id,
            metadata=merged_metadata,
        )

    def get_playback_state(self) -> Dict[str, Any]:
        self._refresh_state()
        now = self._clock()
        return {
            "policy_name": "answers_interrupt_active_playback__narration_queues_fifo",
            "delegate_output_type": self.output_type,
            "active_playback": None if self._active_playback is None else self._clone_item(self._active_playback, now),
            "queued_playbacks": [self._clone_item(item, now) for item in self._queued_playbacks],
            "recent_events": list(self._recent_events),
        }


def build_audio_output(
    config: Dict[str, Any],
    event_callback: Optional[Callable[[str], None]] = None,
    repo_root: Optional[Path] = None,
) -> AudioOutput:
    output_type = str(config.get("audio_output_type", "mock"))
    if output_type == "silent":
        return SilentAudioOutput()

    if output_type == "tts_service":
        resolved_repo_root = Path.cwd() if repo_root is None else Path(repo_root)
        delegate = ServiceBackedTTSAudioOutput(
            tts_service=build_tts_service(config, repo_root=resolved_repo_root),
            event_callback=event_callback,
        )
        return ManagedAudioOutput(delegate)

    delegate = MockAudioOutput(event_callback=event_callback)
    return ManagedAudioOutput(delegate)
