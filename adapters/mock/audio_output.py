from pathlib import Path
from typing import Any, Callable, Dict, Optional

from core.interfaces.audio_output import AudioOutput, AudioPlaybackRequest, AudioPlaybackResult
from services.tts_service.service import TTSService, TTSRequest, build_tts_service


class MockAudioOutput(AudioOutput):
    output_type = "mock"

    def __init__(self, event_callback: Optional[Callable[[str], None]] = None) -> None:
        self._event_callback = event_callback
        self.history = []

    def play_text(self, request: AudioPlaybackRequest) -> AudioPlaybackResult:
        result = AudioPlaybackResult(
            output_type="mock",
            playback_kind=request.playback_kind,
            status="played",
            text=request.text,
            spot_id=request.spot_id,
            spot_name=request.spot_name,
            session_id=request.session_id,
            metadata=dict(request.metadata),
        )
        self.history.append(result)
        if self._event_callback is not None:
            label = request.spot_name or request.spot_id or "tour"
            self._event_callback(f"[AUDIO] {request.playback_kind} via mock: {label}")
        return result


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
            metadata=dict(request.metadata),
        )


class ServiceBackedTTSAudioOutput(AudioOutput):
    output_type = "tts_service"

    def __init__(self, tts_service: TTSService, event_callback: Optional[Callable[[str], None]] = None) -> None:
        self._tts_service = tts_service
        self._event_callback = event_callback
        self.history = []

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
        return ServiceBackedTTSAudioOutput(
            tts_service=build_tts_service(config, repo_root=resolved_repo_root),
            event_callback=event_callback,
        )
    return MockAudioOutput(event_callback=event_callback)
