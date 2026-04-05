import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.deployment_profile import (  # noqa: E402
    build_deployment_config_hygiene,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the deployment endpoint config hygiene summary.")
    parser.add_argument(
        "--config",
        default="configs/dev.yaml",
        help="Config file path relative to repo root or absolute path.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path

    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    deployment_launch_plan = build_deployment_launch_plan(config)
    endpoint_contract = build_deployment_endpoint_contract(config, deployment_launch_plan)
    config_hygiene = build_deployment_config_hygiene(config, endpoint_contract)
    print(json.dumps(config_hygiene, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
