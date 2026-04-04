from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.mock.mock_pose_provider import MockPoseProvider
from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore
from core.session.logger import JsonlSessionStore
from core.tour_orchestrator.orchestrator import TourOrchestrator


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    config_path = REPO_ROOT / "configs" / "dev.yaml"
    config = load_config(config_path)

    poi_file = REPO_ROOT / config["current_poi_file"]
    route_file = REPO_ROOT / config["current_route_file"]

    pois = load_pois(str(poi_file))
    route = load_route(str(route_file))
    poi_store = InMemoryPoiStore(pois)
    route_pois = poi_store.route_pois(route)

    if config["pose_provider_type"] != "mock":
        raise ValueError("dev.yaml must use the mock pose provider in this foundation bundle.")

    session_store = JsonlSessionStore(str(REPO_ROOT / config["session_log_dir"]))
    session_store.start_session(
        {
            "env_name": config["env_name"],
            "pose_provider_type": config["pose_provider_type"],
            "route_id": route.route_id,
            "recording_enabled": bool(config["recording_enabled"]),
        }
    )

    orchestrator = TourOrchestrator(
        route_pois=route_pois,
        content_provider=poi_store,
        session_store=session_store,
        event_callback=print,
    )

    provider = MockPoseProvider.from_route_pois(route_pois)

    print(f"[CONFIG] env={config['env_name']} pose_provider={config['pose_provider_type']} route={route.route_id}")
    for pose in provider.iter_poses():
        print(f"[POSE] x={pose.x:.2f} y={pose.y:.2f}")
        orchestrator.handle_pose(pose)

    session_store.close()
    print(f"[SESSION] log saved to {session_store.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
