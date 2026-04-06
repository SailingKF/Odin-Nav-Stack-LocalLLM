import ctypes
import shlex
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List


def resolve_repo_relative_path(path_value: str, repo_root: Path) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else repo_root / path


def _to_wsl_path(path: Path) -> str:
    text = str(path)
    drive = path.drive.rstrip(":")
    if drive:
        relative = text[len(path.drive) :].replace("\\", "/")
        return f"/mnt/{drive.lower()}{relative}"
    return text.replace("\\", "/")


def _decode_command_output(raw: bytes) -> str:
    if not raw:
        return ""
    if b"\x00" in raw:
        try:
            return raw.decode("utf-16le", errors="replace")
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="replace")


def _run_command(command: List[str], timeout_sec: float = 15.0) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
        return {
            "ok": True,
            "returncode": completed.returncode,
            "stdout": _decode_command_output(completed.stdout).strip(),
            "stderr": _decode_command_output(completed.stderr).strip(),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
        }


def _is_current_process_elevated() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def evaluate_wsl_enablement(status_probe: Dict[str, Any], elevated: bool) -> Dict[str, Any]:
    status_text = " ".join(
        part for part in [status_probe.get("stdout", ""), status_probe.get("stderr", "")] if part
    ).strip()
    normalized = status_text.lower()

    installed = bool(status_probe.get("ok") and status_probe.get("returncode") == 0)
    blocker = None
    recommended_action = None

    if not status_probe.get("ok"):
        blocker = {
            "code": "wsl_command_failed",
            "detail": status_probe.get("stderr") or "unable to execute wsl probe command",
        }
    elif "subsystem for linux is not installed" in normalized:
        installed = False
        blocker = {
            "code": "wsl_not_installed",
            "detail": "Windows Subsystem for Linux is not installed on this PC",
        }
        recommended_action = "Run 'wsl.exe --install -d Ubuntu' from an elevated command prompt."
        if not elevated:
            blocker = {
                "code": "wsl_requires_elevation",
                "detail": "WSL is not installed and the current shell is not elevated, so enablement cannot proceed in this session",
            }
    elif status_probe.get("returncode") not in (0, None):
        blocker = {
            "code": "wsl_probe_failed",
            "detail": status_text or "wsl probe returned a non-zero status",
        }

    return {
        "wsl_command_available": True,
        "wsl_installed": installed,
        "current_shell_elevated": elevated,
        "status_probe": status_probe,
        "recommended_install_command": ["wsl.exe", "--install", "-d", "Ubuntu"],
        "recommended_action": recommended_action,
        "blocker": blocker,
    }


def probe_wsl_enablement() -> Dict[str, Any]:
    wsl_executable = shutil.which("wsl.exe") or shutil.which("wsl")
    if not wsl_executable:
        return {
            "wsl_command_available": False,
            "wsl_installed": False,
            "current_shell_elevated": _is_current_process_elevated(),
            "status_probe": {
                "ok": False,
                "returncode": None,
                "stdout": "",
                "stderr": "wsl.exe command was not found",
            },
            "recommended_install_command": ["wsl.exe", "--install", "-d", "Ubuntu"],
            "recommended_action": "Install or restore the Windows WSL feature from an elevated command prompt.",
            "blocker": {
                "code": "wsl_command_missing",
                "detail": "wsl.exe command was not found on this PC",
            },
        }

    status_probe = _run_command([wsl_executable, "--status"])
    return evaluate_wsl_enablement(status_probe=status_probe, elevated=_is_current_process_elevated())


def probe_mvsim_live_runtime(config: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    mvsim_config = dict(config.get("mvsim_integration") or {})
    mode = str(mvsim_config.get("mode", "compatibility_shim"))
    executable = str(mvsim_config.get("executable", "mvsim"))
    runtime_host = str(mvsim_config.get("runtime_host", "windows")).strip().lower() or "windows"
    wsl_distribution = str(mvsim_config.get("wsl_distribution", "Ubuntu")).strip() or "Ubuntu"
    wsl_user = str(mvsim_config.get("wsl_user", "root")).strip() or "root"
    wsl_executable_path = str(mvsim_config.get("wsl_executable_path", "")).strip()
    world_file = str(mvsim_config.get("world_file", "")).strip()
    world_path = resolve_repo_relative_path(world_file, repo_root) if world_file else None
    world_exists = bool(world_path and world_path.exists())
    resolved_executable = shutil.which(executable)
    wsl_enablement = probe_wsl_enablement()
    runtime_check = None
    launch_command = None
    blocker = None

    if runtime_host == "wsl":
        if not wsl_enablement.get("wsl_installed"):
            blocker = {
                "code": "wsl_not_ready",
                "detail": "WSL runtime host was requested but WSL is not installed or not ready on this PC",
            }
        elif not wsl_executable_path:
            blocker = {
                "code": "wsl_mvsim_path_missing",
                "detail": "WSL runtime host was requested but mvsim_integration.wsl_executable_path is empty",
            }
        else:
            runtime_check = _run_command(
                [
                    "wsl.exe",
                    "-d",
                    wsl_distribution,
                    "-u",
                    wsl_user,
                    "--",
                    "bash",
                    "-lc",
                    f"test -x {shlex.quote(wsl_executable_path)}",
                ]
            )
            if not runtime_check.get("ok") or runtime_check.get("returncode") != 0:
                blocker = {
                    "code": "wsl_mvsim_executable_not_found",
                    "detail": (
                        f"configured WSL MVSim executable '{wsl_executable_path}' "
                        f"was not executable inside distribution '{wsl_distribution}'"
                    ),
                }
            elif not world_exists:
                blocker = {
                    "code": "mvsim_world_missing",
                    "detail": f"configured MVSim world file is missing: {world_path}",
                }
            elif world_path:
                launch_command = [
                    "wsl.exe",
                    "-d",
                    wsl_distribution,
                    "-u",
                    wsl_user,
                    "--",
                    "bash",
                    "-lc",
                    (
                        f"{shlex.quote(wsl_executable_path)} launch "
                        f"{shlex.quote(_to_wsl_path(world_path))}"
                    ),
                ]
    else:
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

        if world_path:
            launch_command = [resolved_executable or executable, "launch", str(world_path)]

    return {
        "configured_mode": mode,
        "runtime_kind": "live_mvsim_runtime",
        "runtime_host": runtime_host,
        "runtime_available": False if blocker else bool(wsl_executable_path if runtime_host == "wsl" else resolved_executable),
        "executable": executable,
        "resolved_executable": resolved_executable,
        "wsl_distribution": wsl_distribution if runtime_host == "wsl" else None,
        "wsl_user": wsl_user if runtime_host == "wsl" else None,
        "wsl_executable_path": wsl_executable_path if runtime_host == "wsl" else None,
        "runtime_check": runtime_check,
        "world_file": str(world_path) if world_path else None,
        "world_file_wsl": _to_wsl_path(world_path) if runtime_host == "wsl" and world_path else None,
        "world_file_exists": world_exists,
        "launch_command": launch_command,
        "vehicle_name": mvsim_config.get("vehicle_name"),
        "assumed_frame_id": mvsim_config.get("assumed_frame_id", "map"),
        "blocker": blocker,
    }


def describe_mvsim_runtime_mode(config: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    live_runtime = probe_mvsim_live_runtime(config, repo_root)
    wsl_enablement = probe_wsl_enablement()
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
        "wsl_enablement": wsl_enablement,
        "compatibility_source": compatibility_source,
    }
