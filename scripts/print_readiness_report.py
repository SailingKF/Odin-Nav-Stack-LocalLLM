import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.deployment_profile import (  # noqa: E402
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the deployment readiness report for a config.")
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

    profile = build_deployment_profile(config)
    preflight = build_deployment_preflight(config, REPO_ROOT)
    launch_plan = build_deployment_launch_plan(config)
    readiness = build_deployment_readiness(profile, preflight, launch_plan)
    print(json.dumps(readiness, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
