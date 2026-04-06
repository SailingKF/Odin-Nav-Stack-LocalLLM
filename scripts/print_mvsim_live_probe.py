import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.sim_publisher_bridge.mvsim_live import describe_mvsim_runtime_mode


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the current live MVSim runtime probe result.")
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim.yaml"), help="Simulation config file.")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    print(json.dumps(describe_mvsim_runtime_mode(config, REPO_ROOT), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
