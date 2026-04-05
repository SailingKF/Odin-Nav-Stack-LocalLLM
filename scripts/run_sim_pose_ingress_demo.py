from pathlib import Path
import sys
import time

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.sim_pose_ingress.runtime import SimPoseIngressRuntime


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    config_path = REPO_ROOT / "configs" / "sim.yaml"
    payload_path = REPO_ROOT / "content" / "sim" / "demo_pose_stream.yaml"

    runtime = SimPoseIngressRuntime.from_config_path(config_path=config_path, repo_root=REPO_ROOT)
    payload = load_yaml(payload_path)
    poses = payload.get("poses", [])

    print(f"[CONFIG] env=sim pose_provider={runtime.health()['pose_provider_type']} narrator={runtime.health()['narrator_type']}")
    print("[INGRESS] contract={'x': float, 'y': float, 'label': optional str}")

    runtime.start()
    for pose in poses:
        runtime.ingest_pose_payload(pose)
        print(f"[INGEST] {pose}")
        time.sleep(0.02)

    runtime.finish_stream()

    deadline = time.time() + 3.0
    latest_state = runtime.state()
    while time.time() < deadline:
        latest_state = runtime.state()
        if not latest_state.get("is_running"):
            break
        time.sleep(0.05)

    latest_session = runtime.latest_session()
    print(f"[STATE] {latest_state}")
    print(f"[SESSION] {latest_session}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
