import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class ArtifactPlaybackRequest:
    artifact_uri: str
    artifact_kind: str
    mime_type: str
    content_hash: Optional[str]
    text: str
    playback_kind: str
    session_id: Optional[str] = None
    spot_id: Optional[str] = None
    spot_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ArtifactPlaybackHandle:
    backend_type: str
    handle_id: str
    status: str
    artifact_uri: str
    artifact_kind: str
    mime_type: str
    content_hash: Optional[str]
    playback_kind: str
    session_id: Optional[str] = None
    spot_id: Optional[str] = None
    spot_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_metadata_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ArtifactPlaybackObservation:
    backend_type: str
    handle_id: str
    status: str
    completion_supported: bool
    observed_at_monotonic: Optional[float] = None
    completed_at_monotonic: Optional[float] = None
    failed_at_monotonic: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_metadata_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ArtifactPlayerBackend(ABC):
    @abstractmethod
    def start_artifact(self, request: ArtifactPlaybackRequest) -> ArtifactPlaybackHandle:
        """Start playback for a synthesized artifact."""

    @abstractmethod
    def interrupt_handle(self, handle: ArtifactPlaybackHandle) -> Dict[str, Any]:
        """Interrupt a previously started artifact playback handle."""

    @abstractmethod
    def get_handle_state(self, handle: ArtifactPlaybackHandle) -> ArtifactPlaybackObservation:
        """Return the latest observable playback state for a started handle."""


class ArtifactPlaybackStartError(RuntimeError):
    def __init__(self, backend_type: str, failure_status: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.backend_type = backend_type
        self.failure_status = failure_status
        self.message = message
        self.metadata = metadata or {}

    def to_metadata_dict(self) -> Dict[str, Any]:
        return {
            "playback_backend_type": self.backend_type,
            "failure_status": self.failure_status,
            "failure_message": self.message,
            "failure_metadata": dict(self.metadata),
        }


class MockArtifactPlayerBackend(ArtifactPlayerBackend):
    backend_type = "mock_artifact_player"

    def __init__(
        self,
        event_callback: Optional[Callable[[str], None]] = None,
        clock: Optional[Callable[[], float]] = None,
    ) -> None:
        self._event_callback = event_callback
        self._clock = clock or time.monotonic
        self.start_history: List[ArtifactPlaybackHandle] = []
        self.interrupt_history: List[Dict[str, Any]] = []
        self._next_handle_id = 1
        self._handle_runtime_state: Dict[str, Dict[str, Any]] = {}

    def start_artifact(self, request: ArtifactPlaybackRequest) -> ArtifactPlaybackHandle:
        if bool(request.metadata.get("simulate_playback_start_failure")):
            raise ArtifactPlaybackStartError(
                backend_type=self.backend_type,
                failure_status="artifact_player_start_failed",
                message="Mock artifact player simulated a playback start failure.",
                metadata={"failure_mode": "start_failure"},
            )
        handle = ArtifactPlaybackHandle(
            backend_type=self.backend_type,
            handle_id=f"artifact-playback-{self._next_handle_id}",
            status="started",
            artifact_uri=request.artifact_uri,
            artifact_kind=request.artifact_kind,
            mime_type=request.mime_type,
            content_hash=request.content_hash,
            playback_kind=request.playback_kind,
            session_id=request.session_id,
            spot_id=request.spot_id,
            spot_name=request.spot_name,
            metadata=dict(request.metadata),
        )
        self._next_handle_id += 1
        self.start_history.append(handle)
        self._handle_runtime_state[handle.handle_id] = {
            "handle": handle,
            "status": "active",
            "started_at_monotonic": self._clock(),
            "completed_at_monotonic": None,
            "failed_at_monotonic": None,
            "interrupted_at_monotonic": None,
            "expected_duration_ms": int(request.metadata.get("estimated_duration_ms", 0)),
            "fail_after_ms": request.metadata.get("simulate_active_playback_failure_after_ms"),
        }
        if self._event_callback is not None:
            label = request.spot_name or request.spot_id or "tour"
            self._event_callback(f"[AUDIO] {request.playback_kind} via artifact_player/mock: {label}")
        return handle

    def interrupt_handle(self, handle: ArtifactPlaybackHandle) -> Dict[str, Any]:
        state = self._handle_runtime_state.get(handle.handle_id)
        if state is not None:
            state["status"] = "interrupted"
            state["interrupted_at_monotonic"] = self._clock()
        payload = {
            "playback_backend_type": handle.backend_type,
            "playback_handle_id": handle.handle_id,
            "player_interrupt_hook_invoked": True,
            "player_interrupt_status": "artifact_player_interrupted",
        }
        self.interrupt_history.append(payload)
        return payload

    def get_handle_state(self, handle: ArtifactPlaybackHandle) -> ArtifactPlaybackObservation:
        state = self._handle_runtime_state.get(handle.handle_id)
        now = self._clock()
        if state is None:
            return ArtifactPlaybackObservation(
                backend_type=handle.backend_type,
                handle_id=handle.handle_id,
                status="unknown",
                completion_supported=True,
                observed_at_monotonic=now,
                metadata={"reason": "missing_handle_state"},
            )

        if state["status"] == "active":
            expected_duration_ms = int(state.get("expected_duration_ms", 0))
            started_at = state.get("started_at_monotonic")
            fail_after_ms = state.get("fail_after_ms")
            if fail_after_ms is not None and started_at is not None:
                elapsed_ms = int((now - started_at) * 1000)
                if elapsed_ms >= int(fail_after_ms):
                    state["status"] = "failed"
                    state["failed_at_monotonic"] = now
            if expected_duration_ms > 0 and started_at is not None:
                elapsed_ms = int((now - started_at) * 1000)
                if state["status"] == "active" and elapsed_ms >= expected_duration_ms:
                    state["status"] = "completed"
                    state["completed_at_monotonic"] = now

        return ArtifactPlaybackObservation(
            backend_type=handle.backend_type,
            handle_id=handle.handle_id,
            status=str(state["status"]),
            completion_supported=True,
            observed_at_monotonic=now,
            completed_at_monotonic=state.get("completed_at_monotonic"),
            failed_at_monotonic=state.get("failed_at_monotonic"),
            metadata={
                "expected_duration_ms": state.get("expected_duration_ms"),
                "failure_status": "artifact_player_active_failed" if state["status"] == "failed" else None,
                "failure_reason": "simulated_active_playback_failure" if state["status"] == "failed" else None,
                "started_at_monotonic": state.get("started_at_monotonic"),
                "interrupted_at_monotonic": state.get("interrupted_at_monotonic"),
            },
        )


def build_artifact_player_backend(
    config: Dict[str, Any],
    event_callback: Optional[Callable[[str], None]] = None,
) -> ArtifactPlayerBackend:
    backend_type = str(config.get("artifact_player_backend_type", "mock"))
    if backend_type == "mock":
        return MockArtifactPlayerBackend(event_callback=event_callback)
    raise ValueError(f"Unsupported artifact player backend type: {backend_type}")
