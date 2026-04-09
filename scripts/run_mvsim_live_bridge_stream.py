import argparse
import json
from pathlib import Path
import sys
import time

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from adapters.sim.frame_transform import SimFrameTransformConfig, normalize_raw_pose_payload
from adapters.sim.projection import SimPoseProjectionConfig, project_richer_pose_payload
from services.sim_publisher_bridge.http_client import SimIngressHttpClient
from services.sim_publisher_bridge.mvsim_live import probe_mvsim_live_runtime
from services.sim_publisher_bridge.mvsim_live_source import (
    WslMVSimTopicEchoSource,
    describe_mvsim_live_pose_source,
)


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Continuously relay live MVSim pose from an already-running runtime into sim_pose_ingress."
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8110", help="sim_pose_ingress HTTP base URL.")
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "sim_harness_manual_review.yaml"),
        help="Simulation config file.",
    )
    parser.add_argument(
        "--status-interval-sec",
        type=float,
        default=2.0,
        help="How often to print a compact relay status summary while streaming.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=None,
        help="Optional hard cap for the number of live samples to relay before stopping.",
    )
    parser.add_argument(
        "--stop-on-route-complete",
        action="store_true",
        help="Stop the relay once the sim_ingress runtime reports route_completed=true.",
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
        raise RuntimeError("This bridge stream currently supports runtime_host=wsl only.")

    source = WslMVSimTopicEchoSource(
        distribution=probe["wsl_distribution"],
        user=probe["wsl_user"],
        executable_path=probe["wsl_executable_path"],
        topic_name=str(config.get("mvsim_integration", {}).get("live_pose_topic", "/tour_bot/pose")),
        sample_limit=args.max_samples,
        timeout_sec=5.0,
    )
    projection_config = SimPoseProjectionConfig()
    transform_config = SimFrameTransformConfig(
        raw_x_field="sim_x",
        raw_y_field="sim_y",
        swap_axes=False,
        flip_x=False,
        flip_y=False,
        scale=1.0,
        offset_x=0.0,
        offset_y=0.0,
    )
    ingress_client = SimIngressHttpClient(args.base_url)

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
    print(json.dumps({"health": ingress_client.health()}, ensure_ascii=False, indent=2))
    print(json.dumps({"start_response": ingress_client.start_runtime()}, ensure_ascii=False, indent=2))

    sample_count = 0
    last_status_print = 0.0
    latest_state = {}
    latest_session = {}

    try:
        for richer_payload in source.iter_payloads():
            projected_payload = project_richer_pose_payload(richer_payload, projection_config)
            normalized_payload = normalize_raw_pose_payload(projected_payload, transform_config)
            pose_response = ingress_client.ingest_pose(normalized_payload)
            latest_state = dict(pose_response.get("state") or {})
            sample_count += 1

            now = time.time()
            should_print = sample_count == 1 or now - last_status_print >= args.status_interval_sec
            if should_print:
                status_payload = {
                    "bridge_stream_status": {
                        "sample_count": sample_count,
                        "latest_pose": latest_state.get("last_pose"),
                        "active_spot_name": latest_state.get("active_spot_name"),
                        "route_completed": latest_state.get("route_completed"),
                        "last_event_type": latest_state.get("last_event_type"),
                    }
                }
                print(json.dumps(status_payload, ensure_ascii=False, indent=2))
                last_status_print = now

            if args.stop_on_route_complete and latest_state.get("route_completed"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        print(json.dumps({"finish_response": ingress_client.finish_stream()}, ensure_ascii=False, indent=2))
        latest_state = ingress_client.state()
        latest_session = ingress_client.latest_session()
        print(json.dumps({"final_state": latest_state}, ensure_ascii=False, indent=2))
        print(json.dumps({"latest_session": latest_session}, ensure_ascii=False, indent=2))
        print(
            json.dumps(
                {
                    "bridge_stream_summary": {
                        "sample_count": sample_count,
                        "route_completed": latest_state.get("route_completed"),
                        "latest_spot_name": latest_session.get("latest_spot_name") or latest_session.get("latest_spot_id"),
                        "latest_narration_text": latest_session.get("latest_narration_text"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
