import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.sim_publisher_bridge.mvsim_live import probe_mvsim_live_runtime


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _to_wsl_path(path: Path) -> str:
    text = str(path)
    drive = path.drive.rstrip(":")
    if drive:
        relative = text[len(path.drive) :].replace("\\", "/")
        return f"/mnt/{drive.lower()}{relative}"
    return text.replace("\\", "/")


def _config_display_path(config_path: Path) -> str:
    try:
        return str(config_path.resolve().relative_to(REPO_ROOT).as_posix())
    except ValueError:
        return str(config_path)


def _service_command(config_path: Path, script_name: str, host: str, port: int) -> str:
    return (
        f"python scripts/{script_name} --config {_config_display_path(config_path)} "
        f"--host {host} --port {port}"
    )


def _build_gui_launch_command(probe: dict, repo_root: Path, verbosity: str) -> list[str]:
    repo_root_wsl = _to_wsl_path(repo_root)
    world_path = Path(str(probe["world_file"]))
    relative_world = world_path.resolve().relative_to(repo_root.resolve()).as_posix()
    launch = (
        f"cd {shlex.quote(repo_root_wsl)} && "
        f"exec {shlex.quote(str(probe['wsl_executable_path']))} "
        f"launch {shlex.quote(relative_world)} -v {shlex.quote(verbosity)}"
    )
    return [
        "wsl.exe",
        "-d",
        str(probe["wsl_distribution"]),
        "-u",
        str(probe["wsl_user"]),
        "--",
        "bash",
        "-lc",
        launch,
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
            f"pkill -f {shlex.quote(str(probe['wsl_executable_path']))} || true",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=20,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launch the repo-owned MVSim live-validation world with GUI for manual review."
    )
    parser.add_argument("--config", default=str(REPO_ROOT / "configs" / "sim_harness.yaml"), help="Config file to load.")
    parser.add_argument("--verbosity", default="INFO", help="MVSim verbosity level.")
    parser.add_argument(
        "--reuse-existing-runtime",
        action="store_true",
        help="Do not kill an existing WSL MVSim runtime before launching the GUI review runtime.",
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
        raise RuntimeError("The GUI manual-review launcher currently supports only runtime_host=wsl.")

    if not args.reuse_existing_runtime:
        _cleanup_existing_runtime(probe)

    service_endpoints = dict(config.get("service_endpoints") or {})
    ingress_endpoint = dict(service_endpoints.get("sim_pose_ingress_server") or {})
    api_endpoint = dict(service_endpoints.get("api_server") or {})
    ingress_host = str(ingress_endpoint.get("bind_host", "127.0.0.1"))
    ingress_port = int(ingress_endpoint.get("port", 8110))
    api_host = str(api_endpoint.get("bind_host", "127.0.0.1"))
    api_port = int(api_endpoint.get("port", 8001))
    launch_command = _build_gui_launch_command(probe, REPO_ROOT, args.verbosity)

    review_sheet = {
        "gui_runtime": {
            "launcher": "scripts/run_mvsim_gui_review.py",
            "config": _config_display_path(config_path),
            "launch_command": launch_command,
            "world_file": probe.get("world_file"),
            "world_file_wsl": probe.get("world_file_wsl"),
        },
        "follow_up_commands": {
            "sim_pose_ingress_server": _service_command(
                config_path, "run_sim_pose_ingress_server.py", ingress_host, ingress_port
            ),
            "api_server_optional": _service_command(config_path, "run_api_server.py", api_host, api_port),
            "attach_existing_runtime_bridge": (
                f"python scripts/run_mvsim_live_bridge_demo.py --config {_config_display_path(config_path)} "
                f"--base-url http://{ingress_host}:{ingress_port} --sample-count 180 --attach-existing-runtime"
            ),
        },
        "operator_note": (
            "Leave this GUI launcher terminal running while a second terminal starts the ingress server "
            "and a third terminal runs the attach-existing-runtime bridge command."
        ),
    }
    print(json.dumps(review_sheet, ensure_ascii=False, indent=2))

    runtime_process = subprocess.Popen(launch_command)
    try:
        return runtime_process.wait()
    except KeyboardInterrupt:
        runtime_process.terminate()
        try:
            runtime_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            runtime_process.kill()
            runtime_process.wait(timeout=5)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
