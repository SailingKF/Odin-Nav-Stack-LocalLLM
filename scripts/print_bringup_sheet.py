import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.deployment_profile import (
    build_deployment_command_manifest,
    build_deployment_endpoint_contract,
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
    build_guided_bringup_sheet,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the guided bring-up sheet for a config.")
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

    deployment_profile = build_deployment_profile(config)
    deployment_preflight = build_deployment_preflight(config, REPO_ROOT)
    deployment_launch_plan = build_deployment_launch_plan(config)
    deployment_endpoint_contract = build_deployment_endpoint_contract(config, deployment_launch_plan)
    deployment_readiness = build_deployment_readiness(
        deployment_profile,
        deployment_preflight,
        deployment_launch_plan,
    )
    deployment_command_manifest = build_deployment_command_manifest(
        config,
        deployment_launch_plan,
        deployment_endpoint_contract,
    )
    bringup_sheet = build_guided_bringup_sheet(
        deployment_launch_plan,
        deployment_readiness,
        deployment_command_manifest,
    )

    print(json.dumps(bringup_sheet, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
