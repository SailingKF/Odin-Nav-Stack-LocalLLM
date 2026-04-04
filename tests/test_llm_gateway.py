import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi.testclient import TestClient

from core.narrator.local_llm_narrator import LocalLLMNarrator
from core.poi.loader import load_pois
from services.llm_gateway.app import create_app


class _StubGatewayHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        payload = json.loads(raw_body) if raw_body else {}

        if self.path == "/generate_narration":
            response = {"narration_text": f"stub narration for {payload['spot']['name']}"}
        elif self.path == "/answer_question":
            response = {"answer_text": f"stub answer for {payload['question']}"}
        else:
            self.send_response(404)
            self.end_headers()
            return

        body = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return None


class LLMGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.poi = load_pois("content/poi/demo_pois.yaml")[0]

    def test_gateway_mock_backend_generate_and_answer(self) -> None:
        app = create_app(
            config={
                "llm_backend_type": "mock",
                "llm_model_name": "mock-curated-content",
                "llm_enable_fallback": True,
            }
        )
        client = TestClient(app)

        health = client.get("/health")
        narration = client.post("/generate_narration", json={"spot": self.poi.to_content_dict(), "mode": "standard"})
        answer = client.post("/answer_question", json={"spot": self.poi.to_content_dict(), "question": "Why does the tour start here?"})

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["active_backend_type"], "mock")
        self.assertEqual(narration.status_code, 200)
        self.assertEqual(narration.json()["backend_type"], "mock")
        self.assertIn(self.poi.standard_text, narration.json()["narration_text"])
        self.assertEqual(answer.status_code, 200)
        self.assertIn("first stop", answer.json()["answer_text"])

    def test_gateway_ollama_falls_back_to_mock_when_unavailable(self) -> None:
        app = create_app(
            config={
                "llm_backend_type": "ollama",
                "llm_model_name": "gemma-local",
                "llm_base_url": "http://127.0.0.1:11435",
                "llm_timeout_sec": 0.2,
                "llm_enable_fallback": True,
            }
        )
        client = TestClient(app)

        health = client.get("/health")
        narration = client.post("/generate_narration", json={"spot": self.poi.to_content_dict(), "mode": "short"})

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "degraded")
        self.assertTrue(health.json()["fallback_active"])
        self.assertEqual(narration.status_code, 200)
        self.assertTrue(narration.json()["fallback_used"])
        self.assertEqual(narration.json()["backend_type"], "mock")

    def test_local_llm_narrator_calls_gateway_main_path(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _StubGatewayHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        gateway_url = f"http://127.0.0.1:{server.server_port}"

        try:
            narrator = LocalLLMNarrator(
                gateway_url=gateway_url,
                timeout_seconds=1.0,
                fallback_enabled=False,
            )

            narration_text = narrator.generate_narration(self.poi, "standard")
            answer_text = narrator.answer_question(self.poi, "What is here?")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=1.0)

        self.assertEqual(narration_text, f"stub narration for {self.poi.name}")
        self.assertEqual(answer_text, "stub answer for What is here?")


if __name__ == "__main__":
    unittest.main()
