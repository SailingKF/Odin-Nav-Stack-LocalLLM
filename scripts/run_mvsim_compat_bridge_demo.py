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
from services.sim_publisher_bridge.mvsim_source import (
    YamlFileMVSimPoseSource,
    describe_mvsim_compat_source,
)
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MVSim-oriented compatibility bridge demo.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100", help="HTTP bridge base URL.")
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim.yaml"), help="Simulation config file.")
    parser.add_argument(
        "--observation-file",
        default=None,
        help="Optional MVSim-style observation YAML. Defaults to config mvsim_integration.observation_file.",
    )
    args = parser.parse_args()

    config = load_yaml(Path(args.config))
    mvsim_config = dict(config.get("mvsim_integration") or {})
    observation_file = args.observation_file or mvsim_config.get("observation_file")
    if not observation_file:
        raise ValueError("sim config must provide mvsim_integration.observation_file for this demo.")

    observation_path = Path(observation_file)
    if not observation_path.is_absolute():
        observation_path = REPO_ROOT / observation_path

    runtime = SimulatorPublisherBridgeRuntime(
        source=YamlFileMVSimPoseSource(observation_path),
        projection_config=SimPoseProjectionConfig(),
        transform_config=SimFrameTransformConfig(
            raw_x_field="sim_x",
            raw_y_field="sim_y",
            swap_axes=False,
            flip_x=False,
            flip_y=False,
            scale=1.0,
            offset_x=0.0,
            offset_y=0.0,
        ),
        ingress_client=SimIngressHttpClient(args.base_url),
    )
    result = runtime.run()

    print(json.dumps({"mvsim_integration": mvsim_config}, ensure_ascii=False, indent=2))
    print(json.dumps({"mvsim_source": describe_mvsim_compat_source(observation_path)}, ensure_ascii=False, indent=2))
    for key in (
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
        print(json.dumps({key: result[key]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
