import json
from urllib.request import Request, urlopen


class SimIngressHttpClient:
    def __init__(self, base_url: str):
        self._base_url = base_url.rstrip("/")

    def _post_json(self, path: str, payload: dict) -> dict:
        request = Request(
            url=f"{self._base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get_json(self, path: str) -> dict:
        request = Request(url=f"{self._base_url}{path}", method="GET")
        with urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))

    def health(self) -> dict:
        return self._get_json("/health")

    def start_runtime(self) -> dict:
        return self._post_json("/runtime/start", {})

    def ingest_pose_batch(self, poses: list) -> dict:
        return self._post_json("/poses/batch", {"poses": poses})

    def finish_stream(self) -> dict:
        return self._post_json("/stream/finish", {})

    def state(self) -> dict:
        return self._get_json("/state")

    def latest_session(self) -> dict:
        return self._get_json("/session/latest")

    def pause_tour(self) -> dict:
        return self._post_json("/tour/pause", {})

    def resume_tour(self) -> dict:
        return self._post_json("/tour/resume", {})

    def next_poi(self) -> dict:
        return self._post_json("/tour/next", {})

    def ask_question(self, question: str) -> dict:
        return self._post_json("/tour/question", {"question": question})
