import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.sim_publisher_bridge.http_client import SimIngressHttpClient
from services.sim_publisher_bridge.mvsim_live import probe_mvsim_live_runtime
from services.sim_publisher_bridge.mvsim_live_source import (
    WslMVSimTopicEchoSource,
    describe_mvsim_live_pose_source,
)
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _build_launch_command(probe: dict) -> list:
    return [
        "wsl.exe",
        "-d",
        probe["wsl_distribution"],
        "-u",
        probe["wsl_user"],
        "--",
        probe["wsl_executable_path"],
        "launch",
        probe["world_file_wsl"],
        "--headless",
        "-v",
        "INFO",
    ]


def _cleanup_existing_runtime(probe: dict) -> None:
    subprocess.run(
        [
            "wsl.exe",
            "-d",
            probe["wsl_distribution"],
            "-u",
            probe["wsl_user"],
            "--",
            "bash",
            "-lc",
            f"pkill -f '{probe['wsl_executable_path']}' || true",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the minimal live MVSim pose bridge into sim_pose_ingress.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100", help="sim_pose_ingress HTTP base URL.")
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim.yaml"), help="Simulation config file.")
    parser.add_argument("--sample-count", type=int, default=3, help="Number of live pose samples to bridge.")
    parser.add_argument(
        "--attach-existing-runtime",
        action="store_true",
        help="Do not launch a fresh WSL MVSim runtime; attach to the currently running one.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = REPO_ROOT / config_path
    config = load_yaml(config_path)

    probe = probe_mvsim_live_runtime(config, REPO_ROOT)
    if probe.get("blocker"):
        raise RuntimeError(f"Live MVSim runtime is not ready: {probe['blocker']['detail']}")
    if probe.get("runtime_host") != "wsl":
        raise RuntimeError("This baseline only supports runtime_host=wsl.")

    runtime_process = None
    try:
        if not args.attach_existing_runtime:
            _cleanup_existing_runtime(probe)
            runtime_process = subprocess.Popen(
                _build_launch_command(probe),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(2.5)
            if runtime_process.poll() is not None:
                stdout, stderr = runtime_process.communicate(timeout=5)
                raise RuntimeError(
                    "WSL MVSim runtime did not stay alive long enough for bridge attachment.\n"
                    f"stdout:\n{stdout}\n\nstderr:\n{stderr}"
                )

        source = WslMVSimTopicEchoSource(
            distribution=probe["wsl_distribution"],
            user=probe["wsl_user"],
            executable_path=probe["wsl_executable_path"],
            topic_name=str(config.get("mvsim_integration", {}).get("live_pose_topic", "/tour_bot/pose")),
            sample_limit=args.sample_count,
            timeout_sec=5.0,
        )
        bridge_runtime = SimulatorPublisherBridgeRuntime(
            source=source,
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
        result = bridge_runtime.run()

        print(json.dumps({"live_runtime": probe}, ensure_ascii=False, indent=2))
        print(
            json.dumps(
                {
                    "mvsim_live_pose_source": describe_mvsim_live_pose_source(
                        distribution=probe["wsl_distribution"],
                        user=probe["wsl_user"],
                        executable_path=probe["wsl_executable_path"],
                        topic_name=str(config.get("mvsim_integration", {}).get("live_pose_topic", "/tour_bot/pose")),
                    )
                },
                ensure_ascii=False,
                indent=2,
            )
        )
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
    finally:
        if runtime_process is not None:
            runtime_process.terminate()
            try:
                runtime_process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                runtime_process.kill()
                runtime_process.communicate(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
