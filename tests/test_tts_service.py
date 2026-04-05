import json
import tempfile
import unittest
from pathlib import Path

from services.tts_service.service import MockTTSBackend, TTSRequest, build_tts_service


class TTSServiceTests(unittest.TestCase):
    def test_mock_tts_backend_returns_deterministic_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            backend = MockTTSBackend(Path(temp_dir))
            request = TTSRequest(
                text="Welcome to the East Gate.",
                playback_kind="narration",
                session_id="session-1",
                spot_id="gate",
                spot_name="East Gate",
            )

            first = backend.synthesize(request)
            second = backend.synthesize(request)

            self.assertEqual(first.backend_type, "mock")
            self.assertEqual(first.status, "synthesized")
            self.assertEqual(first.artifact.content_hash, second.artifact.content_hash)
            self.assertEqual(first.artifact.artifact_uri, second.artifact.artifact_uri)
            artifact_payload = json.loads(Path(first.artifact.artifact_uri).read_text(encoding="utf-8"))
            self.assertEqual(artifact_payload["spot_id"], "gate")
            self.assertEqual(artifact_payload["playback_kind"], "narration")

    def test_build_tts_service_supports_mock_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = build_tts_service(
                {
                    "tts_backend_type": "mock",
                    "tts_artifact_dir": temp_dir,
                },
                repo_root=Path.cwd(),
            )
            response = service.synthesize(
                TTSRequest(text="hello", playback_kind="answer", session_id="session-2")
            )

            self.assertEqual(response.backend_type, "mock")
            self.assertEqual(response.status, "synthesized")
            self.assertTrue(Path(response.artifact.artifact_uri).exists())


if __name__ == "__main__":
    unittest.main()
