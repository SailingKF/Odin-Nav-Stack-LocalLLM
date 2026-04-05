import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.sim_publisher_bridge.http_client import SimIngressHttpClient
from services.sim_publisher_bridge.isaac_source import build_isaac_pose_source, describe_isaac_source_selection
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the publisher bridge through the Isaac-oriented stub source path.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100", help="HTTP bridge base URL.")
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim.yaml"), help="Simulation config file.")
    parser.add_argument(
        "--mode",
        choices=("stub", "live"),
        default=None,
        help="Override the isaac source mode from config.",
    )
    args = parser.parse_args()

    config = load_yaml(Path(args.config))
    isaac_source_config = dict(config.get("isaac_source", {}))
    if args.mode:
        isaac_source_config["mode"] = args.mode
    runtime = SimulatorPublisherBridgeRuntime(
        source=build_isaac_pose_source(isaac_source_config),
        projection_config=SimPoseProjectionConfig.from_dict(config.get("publisher_pose_projection", {})),
        transform_config=SimFrameTransformConfig.from_dict(config.get("publisher_frame_transform", {})),
        ingress_client=SimIngressHttpClient(args.base_url),
    )
    result = runtime.run()

    print(json.dumps({"isaac_source_selection": describe_isaac_source_selection(isaac_source_config)}, indent=2))
    for key in (
        "projection_config",
        "transform_config",
        "richer_payload_sample",
        "projected_payload_sample",
        "normalized_payload_sample",
        "health",
        "start_response",
        "batch_response",
        "finish_response",
        "final_state",
        "latest_session",
    ):
        print(json.dumps({key: result[key]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
