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

from adapters.sim.frame_transform import SimFrameTransformConfig, normalize_raw_pose_payloads
from adapters.sim.projection import SimPoseProjectionConfig, project_richer_pose_payloads


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
    parser = argparse.ArgumentParser(description="Project richer simulator poses, normalize them, and post them to the sim ingress HTTP bridge.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100", help="HTTP bridge base URL.")
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim.yaml"), help="Simulation config file.")
    parser.add_argument(
        "--richer-payload",
        default=str(REPO_ROOT / "content" / "sim" / "demo_richer_pose_stream.yaml"),
        help="Richer simulator-style pose payload file.",
    )
    args = parser.parse_args()

    config = load_yaml(Path(args.config))
    payload = load_yaml(Path(args.richer_payload))
    projection_config = SimPoseProjectionConfig.from_dict(config.get("publisher_pose_projection", {}))
    transform_config = SimFrameTransformConfig.from_dict(config.get("publisher_frame_transform", {}))
    richer_poses = payload.get("poses", [])
    projected_poses = project_richer_pose_payloads(richer_poses, projection_config)
    normalized_poses = normalize_raw_pose_payloads(projected_poses, transform_config)

    print(json.dumps({"projection_config": projection_config.__dict__}, indent=2))
    print(json.dumps({"transform_config": transform_config.__dict__}, indent=2))
    print(json.dumps({"richer_payload_sample": richer_poses[:2]}, indent=2))
    print(json.dumps({"projected_payload_sample": projected_poses[:2]}, indent=2))
    print(json.dumps({"normalized_payload_sample": normalized_poses[:2]}, indent=2))
    print(json.dumps(get_json(args.base_url, "/health"), indent=2))
    print(json.dumps(post_json(args.base_url, "/runtime/start", {}), indent=2))
    print(json.dumps(post_json(args.base_url, "/poses/batch", {"poses": normalized_poses}), indent=2))
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
