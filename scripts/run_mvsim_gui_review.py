import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
from typing import Optional
from urllib.request import Request, urlopen
import webbrowser

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


def _service_command(config_path: Path, script_name: str, host: str, port: int) -> list[str]:
    return [
        sys.executable,
        str(REPO_ROOT / "scripts" / script_name),
        "--config",
        _config_display_path(config_path),
        "--host",
        host,
        "--port",
        str(port),
    ]


def _build_bridge_command(config_path: Path, base_url: str) -> list[str]:
    return [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_mvsim_live_bridge_stream.py"),
        "--config",
        _config_display_path(config_path),
        "--base-url",
        base_url,
    ]


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


def _health_json(url: str) -> Optional[dict]:
    try:
        request = Request(url=url, method="GET")
        with urlopen(request, timeout=2.5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def _wait_for_health(url: str, process: Optional[subprocess.Popen], timeout_sec: float = 15.0) -> dict:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        payload = _health_json(url)
        if payload is not None:
            return payload
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"Service for {url} exited before becoming healthy (exit={process.returncode}).")
        time.sleep(0.4)
    raise RuntimeError(f"Timed out waiting for health endpoint: {url}")


def _ensure_local_service(
    service_name: str,
    health_url: str,
    command: list[str],
) -> tuple[Optional[subprocess.Popen], str, dict]:
    existing = _health_json(health_url)
    if existing is not None:
        return None, "attached_existing", existing

    process = subprocess.Popen(command, cwd=str(REPO_ROOT))
    health = _wait_for_health(health_url, process)
    return process, "launched_local", health


def _terminate_process(process: Optional[subprocess.Popen], label: str) -> None:
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
    print(json.dumps({"terminated": label}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the repo-owned interactive MVSim GUI review stack with one command."
    )
    parser.add_argument(
        "--config",
        default=str(REPO_ROOT / "configs" / "sim_harness_manual_review.yaml"),
        help="Config file to load.",
    )
    parser.add_argument("--verbosity", default="INFO", help="MVSim verbosity level.")
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open the repo-owned /debug page after the local stack becomes healthy.",
    )
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
    ingress_url = f"http://{ingress_host}:{ingress_port}"
    api_host = str(api_endpoint.get("bind_host", "127.0.0.1"))
    api_port = int(api_endpoint.get("port", 8001))
    api_url = f"http://{api_host}:{api_port}"
    debug_url = f"{api_url}/debug"

    ingress_process = None
    api_process = None
    bridge_process = None
    runtime_process = None

    try:
        ingress_process, ingress_mode, ingress_health = _ensure_local_service(
            "sim_pose_ingress_server",
            f"{ingress_url}/health",
            _service_command(config_path, "run_sim_pose_ingress_server.py", ingress_host, ingress_port),
        )
        api_process, api_mode, api_health = _ensure_local_service(
            "api_server",
            f"{api_url}/health",
            _service_command(config_path, "run_api_server.py", api_host, api_port),
        )

        launch_command = _build_gui_launch_command(probe, REPO_ROOT, args.verbosity)
        runtime_process = subprocess.Popen(launch_command, cwd=str(REPO_ROOT))
        time.sleep(2.5)
        if runtime_process.poll() is not None:
            raise RuntimeError(f"MVSim GUI runtime exited early (exit={runtime_process.returncode}).")

        bridge_process = subprocess.Popen(
            _build_bridge_command(config_path, ingress_url),
            cwd=str(REPO_ROOT),
        )
        time.sleep(2.0)
        if bridge_process.poll() is not None:
            raise RuntimeError(f"Live bridge stream exited early (exit={bridge_process.returncode}).")

        review_sheet = {
            "gui_runtime": {
                "launcher": "scripts/run_mvsim_gui_review.py",
                "config": _config_display_path(config_path),
                "launch_command": launch_command,
                "world_file": probe.get("world_file"),
                "world_file_wsl": probe.get("world_file_wsl"),
            },
            "local_stack": {
                "sim_pose_ingress": {
                    "status": ingress_mode,
                    "health_url": f"{ingress_url}/health",
                    "health": ingress_health,
                },
                "api_server": {
                    "status": api_mode,
                    "health_url": f"{api_url}/health",
                    "health": api_health,
                    "debug_url": debug_url,
                },
                "bridge_stream": {
                    "status": "launched_local",
                    "command": _build_bridge_command(config_path, ingress_url),
                },
            },
            "operator_note": (
                "Focus the MVSim window, keep tour_bot selected, and use W/S to move, A/D to turn, "
                "and Space to stop. The /debug page should use the page origin by default in this flow."
            ),
        }
        print(json.dumps(review_sheet, ensure_ascii=False, indent=2))

        if args.open_browser:
            webbrowser.open(debug_url)

        print("====================================================")
        print("Interactive MVSim manual review stack is running.")
        print(f"Debug page: {debug_url}")
        print("Focus the MVSim window and drive with W/S/A/D, Space to stop.")
        print("Press CTRL+C in this launcher terminal to stop the local review stack.")
        print("====================================================")
        return runtime_process.wait()
    except KeyboardInterrupt:
        return 130
    finally:
        _terminate_process(bridge_process, "bridge_stream")
        _terminate_process(runtime_process, "gui_runtime")
        _terminate_process(api_process, "api_server")
        _terminate_process(ingress_process, "sim_pose_ingress_server")


if __name__ == "__main__":
    raise SystemExit(main())
