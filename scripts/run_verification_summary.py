import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.deployment_profile import (
    build_bringup_verification_sheet,
    build_deployment_command_manifest,
    build_deployment_launch_plan,
    build_deployment_preflight,
    build_deployment_profile,
    build_deployment_readiness,
    build_deployment_verification_manifest,
    build_verification_result_summary,
    run_deployment_verification_once,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one-shot deployment verification checks and print a result summary.")
    parser.add_argument(
        "--config",
        default="configs/dev.yaml",
        help="Config file path relative to repo root or absolute path.",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=2.0,
        help="Per-check timeout in seconds.",
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
    deployment_readiness = build_deployment_readiness(
        deployment_profile,
        deployment_preflight,
        deployment_launch_plan,
    )
    deployment_command_manifest = build_deployment_command_manifest(config, deployment_launch_plan)
    deployment_verification_manifest = build_deployment_verification_manifest(deployment_command_manifest)
    bringup_verification_sheet = build_bringup_verification_sheet(
        deployment_readiness,
        deployment_command_manifest,
        deployment_verification_manifest,
    )
    verification_run_result = run_deployment_verification_once(
        deployment_verification_manifest,
        timeout_sec=args.timeout_sec,
    )
    verification_summary = build_verification_result_summary(
        bringup_verification_sheet,
        verification_run_result,
    )

    print(json.dumps(verification_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
