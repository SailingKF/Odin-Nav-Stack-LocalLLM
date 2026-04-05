import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from adapters.mock.artifact_player import ArtifactPlaybackHandle, ArtifactPlaybackRequest, build_artifact_player_backend
from core.interfaces.audio_output import AudioOutput, AudioPlaybackRequest, AudioPlaybackResult
from services.tts_service.service import TTSService, TTSRequest, TTSResponse, build_tts_service


def _default_duration_ms(text: str) -> int:
    return max(400, len(text) * 45)


@dataclass
class _PreparedPlayback:
    request: AudioPlaybackRequest
    output_type: str
    duration_ms: int
    metadata: Dict[str, Any]


class _PreparedAudioDelegate:
    output_type = "delegate"

    def prepare_playback(self, request: AudioPlaybackRequest) -> _PreparedPlayback:
        raise NotImplementedError

    def start_prepared(self, prepared: _PreparedPlayback) -> AudioPlaybackResult:
        raise NotImplementedError

    def interrupt_prepared(self, prepared: _PreparedPlayback) -> Dict[str, Any]:
        raise NotImplementedError


class MockAudioOutput(AudioOutput, _PreparedAudioDelegate):
    output_type = "mock"

    def __init__(self, event_callback: Optional[Callable[[str], None]] = None) -> None:
        self._event_callback = event_callback
        self.history: List[AudioPlaybackResult] = []
        self.interrupt_history: List[Dict[str, Any]] = []

    def prepare_playback(self, request: AudioPlaybackRequest) -> _PreparedPlayback:
        return _PreparedPlayback(
            request=request,
            output_type="mock",
            duration_ms=_default_duration_ms(request.text),
            metadata={
                **dict(request.metadata),
                "estimated_duration_ms": _default_duration_ms(request.text),
            },
        )

    def start_prepared(self, prepared: _PreparedPlayback) -> AudioPlaybackResult:
        result = AudioPlaybackResult(
            output_type="mock",
            playback_kind=prepared.request.playback_kind,
            status="played",
            text=prepared.request.text,
            spot_id=prepared.request.spot_id,
            spot_name=prepared.request.spot_name,
            session_id=prepared.request.session_id,
            metadata={
                **dict(prepared.metadata),
                "start_hook_invoked": True,
            },
        )
        self.history.append(result)
        if self._event_callback is not None:
            label = prepared.request.spot_name or prepared.request.spot_id or "tour"
            self._event_callback(f"[AUDIO] {prepared.request.playback_kind} via mock: {label}")
        return result

    def interrupt_prepared(self, prepared: _PreparedPlayback) -> Dict[str, Any]:
        payload = {
            "interrupt_hook_invoked": True,
            "interrupt_status": "mock_interrupted",
            "playback_kind": prepared.request.playback_kind,
            "spot_id": prepared.request.spot_id,
        }
        self.interrupt_history.append(payload)
        return payload

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        prepared = self.prepare_playback(request)
        return self.start_prepared(prepared)

    def get_playback_state(self) -> Dict[str, Any]:
        return {
            "policy_name": "direct_immediate",
            "active_playback": None,
            "queued_playbacks": [],
            "recent_events": [],
        }


class SilentAudioOutput(AudioOutput, _PreparedAudioDelegate):
    output_type = "silent"

    def prepare_playback(self, request: AudioPlaybackRequest) -> _PreparedPlayback:
        return _PreparedPlayback(
            request=request,
            output_type="silent",
            duration_ms=0,
            metadata={
                **dict(request.metadata),
                "estimated_duration_ms": 0,
            },
        )

    def start_prepared(self, prepared: _PreparedPlayback) -> AudioPlaybackResult:
        return AudioPlaybackResult(
            output_type="silent",
            playback_kind=prepared.request.playback_kind,
            status="skipped",
            text=prepared.request.text,
            spot_id=prepared.request.spot_id,
            spot_name=prepared.request.spot_name,
            session_id=prepared.request.session_id,
            metadata={
                **dict(prepared.metadata),
                "start_hook_invoked": False,
            },
        )

    def interrupt_prepared(self, prepared: _PreparedPlayback) -> Dict[str, Any]:
        return {
            "interrupt_hook_invoked": False,
            "interrupt_status": "silent_noop",
            "playback_kind": prepared.request.playback_kind,
        }

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        prepared = self.prepare_playback(request)
        return self.start_prepared(prepared)

    def get_playback_state(self) -> Dict[str, Any]:
        return {
            "policy_name": "silent_no_playback",
            "active_playback": None,
            "queued_playbacks": [],
            "recent_events": [],
        }


class ServiceBackedTTSAudioOutput(AudioOutput, _PreparedAudioDelegate):
    output_type = "tts_service"

    def __init__(
        self,
        tts_service: TTSService,
        artifact_player_backend: Any,
    ) -> None:
        self._tts_service = tts_service
        self._artifact_player_backend = artifact_player_backend
        self.history: List[AudioPlaybackResult] = []
        self.interrupt_history: List[Dict[str, Any]] = []

    def prepare_playback(self, request: AudioPlaybackRequest) -> _PreparedPlayback:
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
        return _PreparedPlayback(
            request=request,
            output_type="tts_service",
            duration_ms=int(synthesis.estimated_duration_ms),
            metadata=synthesis.to_metadata_dict(),
        )

    def start_prepared(self, prepared: _PreparedPlayback) -> AudioPlaybackResult:
        artifact_metadata = dict(prepared.metadata.get("artifact") or {})
        if not artifact_metadata:
            raise ValueError("Service-backed playback requires synthesized artifact metadata before start.")
        playback_handle = self._artifact_player_backend.start_artifact(
            ArtifactPlaybackRequest(
                artifact_uri=str(artifact_metadata.get("artifact_uri")),
                artifact_kind=str(artifact_metadata.get("artifact_kind")),
                mime_type=str(artifact_metadata.get("mime_type")),
                content_hash=artifact_metadata.get("content_hash"),
                text=prepared.request.text,
                playback_kind=prepared.request.playback_kind,
                session_id=prepared.request.session_id,
                spot_id=prepared.request.spot_id,
                spot_name=prepared.request.spot_name,
                metadata={
                    "tts_backend_type": prepared.metadata.get("tts_backend_type", prepared.metadata.get("backend_type")),
                    "tts_status": prepared.metadata.get("tts_status", prepared.metadata.get("status")),
                },
            )
        )
        prepared.metadata = {
            **dict(prepared.metadata),
            "playback_backend_type": playback_handle.backend_type,
            "playback_handle": playback_handle.to_metadata_dict(),
            "player_start_hook_invoked": True,
            "player_status": playback_handle.status,
        }
        result = AudioPlaybackResult(
            output_type="tts_service",
            playback_kind=prepared.request.playback_kind,
            status="played",
            text=prepared.request.text,
            spot_id=prepared.request.spot_id,
            spot_name=prepared.request.spot_name,
            session_id=prepared.request.session_id,
            metadata={
                **dict(prepared.metadata),
                "start_hook_invoked": True,
            },
        )
        self.history.append(result)
        return result

    def interrupt_prepared(self, prepared: _PreparedPlayback) -> Dict[str, Any]:
        handle_metadata = dict(prepared.metadata.get("playback_handle") or {})
        if not handle_metadata:
            payload = {
                "interrupt_hook_invoked": True,
                "interrupt_status": "service_tts_missing_playback_handle",
                "backend_type": prepared.metadata.get("backend_type"),
                "tts_backend_type": prepared.metadata.get("tts_backend_type", prepared.metadata.get("backend_type")),
                "playback_backend_type": prepared.metadata.get("playback_backend_type"),
                "player_interrupt_hook_invoked": False,
                "playback_kind": prepared.request.playback_kind,
                "spot_id": prepared.request.spot_id,
            }
            self.interrupt_history.append(payload)
            return payload
        interrupt_payload = self._artifact_player_backend.interrupt_handle(
            ArtifactPlaybackHandle(
                backend_type=str(handle_metadata.get("backend_type")),
                handle_id=str(handle_metadata.get("handle_id")),
                status=str(handle_metadata.get("status")),
                artifact_uri=str(handle_metadata.get("artifact_uri")),
                artifact_kind=str(handle_metadata.get("artifact_kind")),
                mime_type=str(handle_metadata.get("mime_type")),
                content_hash=handle_metadata.get("content_hash"),
                playback_kind=str(handle_metadata.get("playback_kind")),
                session_id=handle_metadata.get("session_id"),
                spot_id=handle_metadata.get("spot_id"),
                spot_name=handle_metadata.get("spot_name"),
                metadata=dict(handle_metadata.get("metadata") or {}),
            )
        )
        payload = {
            "interrupt_hook_invoked": True,
            "interrupt_status": "service_tts_interrupted",
            "backend_type": prepared.metadata.get("backend_type"),
            "tts_backend_type": prepared.metadata.get("tts_backend_type", prepared.metadata.get("backend_type")),
            "playback_backend_type": prepared.metadata.get("playback_backend_type"),
            "playback_kind": prepared.request.playback_kind,
            "spot_id": prepared.request.spot_id,
            **interrupt_payload,
        }
        self.interrupt_history.append(payload)
        return payload

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        prepared = self.prepare_playback(request)
        return self.start_prepared(prepared)

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
        delegate: _PreparedAudioDelegate,
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
            "prepared_at_monotonic": item["prepared_at_monotonic"],
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
        delegate_result = self._delegate.start_prepared(item["prepared"])
        item["metadata"] = dict(delegate_result.metadata)
        item["status"] = "playing"
        item["started_at_monotonic"] = now
        item["finish_at"] = now + (item["duration_ms"] / 1000.0)
        self._active_playback = item
        self._record_event(
            "playback_started",
            item,
            now,
            extra={"start_status": delegate_result.status},
        )

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

    def _item_from_prepared(self, prepared: _PreparedPlayback, now: float) -> Dict[str, Any]:
        playback_id = f"audio-{self._next_playback_id}"
        self._next_playback_id += 1
        metadata = dict(prepared.metadata)
        duration_ms = int(metadata.get("estimated_duration_ms", prepared.duration_ms or _default_duration_ms(prepared.request.text)))
        return {
            "playback_id": playback_id,
            "prepared": prepared,
            "output_type": prepared.output_type,
            "playback_kind": prepared.request.playback_kind,
            "status": "prepared",
            "text": prepared.request.text,
            "spot_id": prepared.request.spot_id,
            "spot_name": prepared.request.spot_name,
            "session_id": prepared.request.session_id,
            "requested_at_monotonic": now,
            "prepared_at_monotonic": now,
            "started_at_monotonic": None,
            "finish_at": None,
            "duration_ms": duration_ms,
            "metadata": metadata,
        }

    def _interrupt_active(self, replacement_item: Dict[str, Any], now: float) -> Optional[str]:
        if self._active_playback is None:
            return None
        interrupted = self._active_playback
        interrupt_payload = self._delegate.interrupt_prepared(interrupted["prepared"])
        interrupted["status"] = "interrupted"
        self._record_event(
            "playback_interrupted",
            interrupted,
            now,
            extra={
                "replaced_by_playback_id": replacement_item["playback_id"],
                **interrupt_payload,
            },
        )
        self._active_playback = None
        return interrupted["playback_id"]

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        self._refresh_state()
        now = self._clock()
        prepared = self._delegate.prepare_playback(request)
        item = self._item_from_prepared(prepared, now)
        self._record_event("playback_prepared", item, now)

        lifecycle_action = "started"
        replaced_playback_id = None
        returned_status = "started"

        if self._active_playback is None:
            self._start_item(item, now)
        elif request.playback_kind == "answer":
            replaced_playback_id = self._interrupt_active(item, now)
            self._start_item(item, now)
            lifecycle_action = "replaced_active"
        else:
            item["status"] = "queued"
            self._queued_playbacks.append(item)
            self._record_event("playback_queued", item, now)
            lifecycle_action = "queued"
            returned_status = "prepared"

        merged_metadata = {
            **dict(item["metadata"]),
            "estimated_duration_ms": item["duration_ms"],
            "lifecycle_action": lifecycle_action,
            "playback_id": item["playback_id"],
            "replaced_playback_id": replaced_playback_id,
            "prepared_at_monotonic": item["prepared_at_monotonic"],
            "started_at_monotonic": item["started_at_monotonic"],
            "start_hook_invoked": item["started_at_monotonic"] is not None,
        }
        return AudioPlaybackResult(
            output_type=item["output_type"],
            playback_kind=item["playback_kind"],
            status=returned_status,
            text=item["text"],
            spot_id=item["spot_id"],
            spot_name=item["spot_name"],
            session_id=item["session_id"],
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
            artifact_player_backend=build_artifact_player_backend(config, event_callback=event_callback),
        )
        return ManagedAudioOutput(delegate)

    delegate = MockAudioOutput(event_callback=event_callback)
    return ManagedAudioOutput(delegate)
