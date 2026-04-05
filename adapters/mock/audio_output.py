from typing import Any, Callable, Dict, Optional

from core.interfaces.audio_output import AudioOutput, AudioPlaybackRequest, AudioPlaybackResult


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


def build_audio_output(config: Dict[str, Any], event_callback: Optional[Callable[[str], None]] = None) -> AudioOutput:
    output_type = str(config.get("audio_output_type", "mock"))
    if output_type == "silent":
        return SilentAudioOutput()
    return MockAudioOutput(event_callback=event_callback)
