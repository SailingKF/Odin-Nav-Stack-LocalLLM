import shutil
from pathlib import Path
from typing import Any, Dict


def resolve_repo_relative_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else repo_root / path


def probe_mvsim_live_runtime(config: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    mvsim_config = dict(config.get("mvsim_integration") or {})
    mode = str(mvsim_config.get("mode", "compatibility_shim"))
    executable = str(mvsim_config.get("executable", "mvsim"))
    world_file = str(mvsim_config.get("world_file", "")).strip()
    world_path = resolve_repo_relative_path(world_file, repo_root) if world_file else None
    world_exists = bool(world_path and world_path.exists())
    resolved_executable = shutil.which(executable)

    blocker = None
    if mode == "live_runtime":
        if not resolved_executable:
            blocker = {
                "code": "mvsim_executable_not_found",
                "detail": f"configured live MVSim executable '{executable}' was not found on this PC",
            }
        elif not world_exists:
            blocker = {
                "code": "mvsim_world_missing",
                "detail": f"configured MVSim world file is missing: {world_path}",
            }

    launch_command = None
    if world_path:
        launch_command = [resolved_executable or executable, "launch", str(world_path)]

    return {
        "configured_mode": mode,
        "runtime_kind": "live_mvsim_runtime",
        "runtime_available": bool(resolved_executable),
        "executable": executable,
        "resolved_executable": resolved_executable,
        "world_file": str(world_path) if world_path else None,
        "world_file_exists": world_exists,
        "launch_command": launch_command,
        "vehicle_name": mvsim_config.get("vehicle_name"),
        "assumed_frame_id": mvsim_config.get("assumed_frame_id", "map"),
        "blocker": blocker,
    }


def describe_mvsim_runtime_mode(config: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    live_runtime = probe_mvsim_live_runtime(config, repo_root)
    mode = live_runtime["configured_mode"]
    compatibility_observation = dict(config.get("mvsim_integration") or {}).get("observation_file")
    compatibility_source = None
    if compatibility_observation:
        compatibility_path = resolve_repo_relative_path(str(compatibility_observation), repo_root)
        compatibility_source = {
            "source_kind": "mvsim_compatibility_shim",
            "observation_file": str(compatibility_path),
            "observation_file_exists": compatibility_path.exists(),
        }

    effective_mode = mode
    if mode == "live_runtime" and live_runtime.get("blocker"):
        effective_mode = "blocked_live_runtime"

    return {
        "configured_mode": mode,
        "effective_mode": effective_mode,
        "live_runtime": live_runtime,
        "compatibility_source": compatibility_source,
    }
