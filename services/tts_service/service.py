from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from hashlib import sha1
import json
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TTSArtifact:
    artifact_uri: str
    artifact_kind: str
    mime_type: str
    content_hash: str


@dataclass(frozen=True)
class TTSRequest:
    text: str
    playback_kind: str
    session_id: Optional[str] = None
    spot_id: Optional[str] = None
    spot_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TTSResponse:
    backend_type: str
    status: str
    text: str
    playback_kind: str
    session_id: Optional[str] = None
    spot_id: Optional[str] = None
    spot_name: Optional[str] = None
    estimated_duration_ms: int = 0
    artifact: Optional[TTSArtifact] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_metadata_dict(self) -> Dict[str, Any]:
        payload = {
            "backend_type": self.backend_type,
            "status": self.status,
            "tts_backend_type": self.backend_type,
            "tts_status": self.status,
            "estimated_duration_ms": self.estimated_duration_ms,
            "metadata": dict(self.metadata),
        }
        if self.artifact is not None:
            payload["artifact"] = asdict(self.artifact)
        return payload


class TTSBackend(ABC):
    @abstractmethod
    def synthesize(self, request: TTSRequest) -> TTSResponse:
        """Synthesize a playback artifact for the requested text."""


class MockTTSBackend(TTSBackend):
    def __init__(self, artifact_dir: Path) -> None:
        self._artifact_dir = Path(artifact_dir)

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        self._artifact_dir.mkdir(parents=True, exist_ok=True)
        stable_seed = "|".join(
            [
                request.session_id or "no-session",
                request.playback_kind,
                request.spot_id or "no-spot",
                request.text,
            ]
        )
        content_hash = sha1(stable_seed.encode("utf-8")).hexdigest()
        artifact_name = f"{content_hash[:16]}.mock_tts.json"
        artifact_path = self._artifact_dir / artifact_name
        artifact_payload = {
            "backend_type": "mock",
            "playback_kind": request.playback_kind,
            "session_id": request.session_id,
            "spot_id": request.spot_id,
            "spot_name": request.spot_name,
            "text": request.text,
            "metadata": dict(request.metadata),
        }
        artifact_path.write_text(json.dumps(artifact_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        estimated_duration_ms = max(400, len(request.text) * 45)
        return TTSResponse(
            backend_type="mock",
            status="synthesized",
            text=request.text,
            playback_kind=request.playback_kind,
            session_id=request.session_id,
            spot_id=request.spot_id,
            spot_name=request.spot_name,
            estimated_duration_ms=estimated_duration_ms,
            artifact=TTSArtifact(
                artifact_uri=str(artifact_path),
                artifact_kind="mock_json",
                mime_type="application/json",
                content_hash=content_hash,
            ),
            metadata={"artifact_file_name": artifact_name},
        )


class TTSService:
    def __init__(self, backend: TTSBackend) -> None:
        self._backend = backend

    def synthesize(self, request: TTSRequest) -> TTSResponse:
        return self._backend.synthesize(request)


def build_tts_service(config: Dict[str, Any], repo_root: Path) -> TTSService:
    backend_type = str(config.get("tts_backend_type", "mock"))
    artifact_dir = repo_root / config.get("tts_artifact_dir", "session_logs/tts_artifacts")
    if backend_type == "mock":
        return TTSService(backend=MockTTSBackend(artifact_dir=artifact_dir))
    raise ValueError(f"Unsupported tts backend type: {backend_type}")
