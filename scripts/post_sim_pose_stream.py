import argparse
import json
from pathlib import Path
import sys
import time
from urllib.request import Request, urlopen

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def post_json(base_url: str, path: str, payload: dict) -> dict:
    request = Request(
        url=f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(base_url: str, path: str) -> dict:
    request = Request(url=f"{base_url}{path}", method="GET")
    with urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Post the demo pose stream to the sim ingress HTTP bridge.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100", help="HTTP bridge base URL.")
    parser.add_argument(
        "--payload",
        default=str(REPO_ROOT / "content" / "sim" / "demo_pose_stream.yaml"),
        help="Pose payload file to post.",
    )
    args = parser.parse_args()

    payload = load_yaml(Path(args.payload))
    poses = payload.get("poses", [])

    print(json.dumps(get_json(args.base_url, "/health"), indent=2))
    print(json.dumps(post_json(args.base_url, "/runtime/start", {}), indent=2))
    print(json.dumps(post_json(args.base_url, "/poses/batch", {"poses": poses}), indent=2))
    print(json.dumps(post_json(args.base_url, "/stream/finish", {}), indent=2))

    deadline = time.time() + 3.0
    latest_state = {}
    while time.time() < deadline:
        latest_state = get_json(args.base_url, "/state")
        if not latest_state.get("is_running"):
            break
        time.sleep(0.05)

    print(json.dumps(latest_state, indent=2))
    print(json.dumps(get_json(args.base_url, "/session/latest"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
