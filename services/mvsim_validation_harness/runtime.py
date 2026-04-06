import copy
import json
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.deployment_profile import build_deployment_endpoint_contract, build_deployment_launch_plan
from services.mvsim_validation_harness.reporting import (
    ValidationReportStore,
    build_latest_mode_comparison,
    build_validation_report,
)
from services.sim_publisher_bridge.http_client import SimIngressHttpClient
from services.sim_publisher_bridge.mvsim_live import (
    describe_mvsim_runtime_mode,
    summarize_live_bridge_result,
)
from services.sim_publisher_bridge.mvsim_live_source import (
    WslMVSimTopicEchoSource,
    describe_mvsim_live_pose_source,
)
from services.sim_publisher_bridge.mvsim_source import YamlFileMVSimPoseSource, describe_mvsim_compat_source
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in dict(override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(dict(merged.get(key) or {}), value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def build_operator_service_check(
    service_id: str,
    display_name: str,
    target_url: str,
    reachable: bool,
    attached_mode: str,
    detail: str,
    launched_by_harness: bool = False,
    port_conflict: bool = False,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    status = "healthy" if reachable else ("port_conflict" if port_conflict else "unreachable")
    return {
        "service_id": service_id,
        "display_name": display_name,
        "target_url": target_url,
        "status": status,
        "reachable": reachable,
        "attached_mode": attached_mode,
        "launched_by_harness": launched_by_harness,
        "port_conflict": port_conflict,
        "detail": detail,
        "extra": extra or {},
    }


def summarize_validation_snapshot(
    sim_ingress_check: Dict[str, Any],
    api_check: Dict[str, Any],
    debug_check: Dict[str, Any],
    mvsim_mode_summary: Dict[str, Any],
    validation_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    live_runtime = dict(mvsim_mode_summary.get("live_runtime") or {})
    if validation_result is None:
        return {
            "overall_status": "idle",
            "validation_mode": mvsim_mode_summary.get("configured_mode") or mvsim_mode_summary.get("effective_mode"),
            "mvsim_mode": mvsim_mode_summary.get("effective_mode"),
            "live_runtime_available": bool(live_runtime.get("runtime_available")),
            "live_first_poi_hit": False,
            "live_second_poi_hit": False,
            "route_completed": False,
            "latest_spot_name": None,
            "latest_narration_text": None,
            "latest_session_id": None,
            "followup_question_ok": False,
            "debug_available": bool(debug_check.get("reachable")),
        }

    sim_result = dict(validation_result.get("sim_ingress_state") or {})
    session_result = dict(validation_result.get("api_latest_session") or {})
    question_result = dict(validation_result.get("question_result") or {})
    live_summary = dict(validation_result.get("live_validation_summary") or {})
    route_completed = bool(sim_result.get("route_completed"))
    return {
        "overall_status": "passed"
        if (
            sim_ingress_check.get("reachable")
            and api_check.get("reachable")
            and debug_check.get("reachable")
            and route_completed
            and bool(question_result.get("ok"))
        )
        else "failed",
        "validation_mode": validation_result.get("validation_mode") or mvsim_mode_summary.get("configured_mode"),
        "mvsim_mode": validation_result.get("mvsim_mode") or mvsim_mode_summary.get("effective_mode"),
        "live_runtime_available": bool(live_runtime.get("runtime_available")),
        "live_first_poi_hit": bool(live_summary.get("live_first_poi_hit_occurred")),
        "live_second_poi_hit": bool(live_summary.get("live_second_poi_hit_occurred")),
        "route_completed": route_completed,
        "latest_spot_name": session_result.get("latest_spot_name") or question_result.get("spot_name"),
        "latest_narration_text": session_result.get("latest_narration_text"),
        "latest_session_id": session_result.get("session_id"),
        "followup_question_ok": bool(question_result.get("ok")),
        "debug_available": bool(debug_check.get("reachable")),
    }


class MVSimValidationHarnessRuntime:
    _PROBE_TIMEOUT_SEC = 1.0
    _SERVICE_START_TIMEOUT_SEC = 15.0
    _VALIDATION_REQUEST_TIMEOUT_SEC = 20.0

    def __init__(
        self,
        config_path: Path,
        repo_root: Path,
        harness_url: str = "http://127.0.0.1:8300",
    ) -> None:
        self._repo_root = repo_root
        self._config_path = config_path if config_path.is_absolute() else repo_root / config_path
        self._harness_url = harness_url.rstrip("/")
        self._base_config = self._load_config(self._config_path)
        self._validation_harness = dict(self._base_config.get("validation_harness") or {})
        configured_mode = str(dict(self._base_config.get("mvsim_integration") or {}).get("mode", "compatibility_shim"))
        configured_modes = list(self._validation_harness.get("available_validation_modes") or [])
        if not configured_modes:
            configured_modes = [configured_mode]
            if configured_mode != "compatibility_shim":
                configured_modes.append("compatibility_shim")
            if configured_mode != "live_runtime":
                configured_modes.append("live_runtime")
        self._available_validation_modes = [str(item) for item in configured_modes if str(item).strip()]
        self._default_validation_mode = str(
            self._validation_harness.get("default_validation_mode") or configured_mode
        )
        if self._default_validation_mode not in self._available_validation_modes:
            self._available_validation_modes.insert(0, self._default_validation_mode)
        self._selected_validation_mode = self._default_validation_mode
        self._managed_service_mode: Optional[str] = None
        self._runtime_dir = repo_root / "session_logs" / "mvsim_validation_harness"
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._report_store = ValidationReportStore(self._runtime_dir / "reports")
        self._managed_processes: Dict[str, subprocess.Popen] = {}
        self._last_validation_result: Optional[Dict[str, Any]] = None

    @staticmethod
    def _load_config(config_path: Path) -> Dict[str, Any]:
        with config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _config_cli_arg(self) -> str:
        try:
            return str(self._config_path.relative_to(self._repo_root))
        except ValueError:
            return str(self._config_path)

    def _resolve_validation_mode(self, validation_mode: Optional[str]) -> str:
        candidate = str(validation_mode or self._selected_validation_mode or self._default_validation_mode).strip()
        if candidate not in self._available_validation_modes:
            raise ValueError(
                f"unsupported validation_mode '{candidate}', expected one of {self._available_validation_modes}"
            )
        self._selected_validation_mode = candidate
        return candidate

    def _config_for_validation_mode(self, validation_mode: str) -> Dict[str, Any]:
        mode = self._resolve_validation_mode(validation_mode)
        config = copy.deepcopy(self._base_config)
        mvsim_config = dict(config.get("mvsim_integration") or {})
        mvsim_config["mode"] = mode
        config["mvsim_integration"] = mvsim_config
        mode_overrides = dict(
            dict(self._validation_harness.get("validation_modes") or {}).get(mode) or {}
        )
        if mode_overrides:
            config = _deep_merge(config, mode_overrides)
        return config

    def _build_service_specs(self, config: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        endpoint_contract = build_deployment_endpoint_contract(
            config,
            build_deployment_launch_plan(config),
        )
        endpoint_by_service = {
            str(item.get("service_id")): item
            for item in list(endpoint_contract.get("services") or [])
            if item.get("service_id")
        }
        sim_endpoint = endpoint_by_service.get("sim_pose_ingress_server") or {}
        api_endpoint = endpoint_by_service.get("api_server") or {}
        return {
            "sim_pose_ingress_server": {
                "display_name": "Sim Pose Ingress",
                "health_path": "/health",
                "command": [
                    "python",
                    "scripts/run_sim_pose_ingress_server.py",
                    "--config",
                    self._config_cli_arg(),
                    "--host",
                    str(sim_endpoint.get("bind_host", "127.0.0.1")),
                    "--port",
                    str(sim_endpoint.get("port", 8100)),
                ],
                "base_url": str(sim_endpoint.get("base_url", "http://127.0.0.1:8100")),
                "connect_host": str(sim_endpoint.get("connect_host", "127.0.0.1")),
                "port": int(sim_endpoint.get("port", 8100)),
            },
            "api_server": {
                "display_name": "Sim API Proxy",
                "health_path": "/health",
                "debug_path": "/debug",
                "question_path": "/tour/question",
                "command": [
                    "python",
                    "scripts/run_api_server.py",
                    "--config",
                    self._config_cli_arg(),
                    "--host",
                    str(api_endpoint.get("bind_host", "127.0.0.1")),
                    "--port",
                    str(api_endpoint.get("port", 8000)),
                ],
                "base_url": str(api_endpoint.get("base_url", "http://127.0.0.1:8000")),
                "connect_host": str(api_endpoint.get("connect_host", "127.0.0.1")),
                "port": int(api_endpoint.get("port", 8000)),
            },
        }

    def _debug_url(self, service_specs: Dict[str, Dict[str, Any]]) -> str:
        return f"{service_specs['api_server']['base_url']}/debug"

    @property
    def debug_url(self) -> str:
        active_config = self._config_for_validation_mode(self._selected_validation_mode)
        return self._debug_url(self._build_service_specs(active_config))

    def latest_report(self) -> Optional[Dict[str, Any]]:
        return self._report_store.read_latest_report()

    def recent_reports(self, limit: int = 5) -> List[Dict[str, Any]]:
        return self._report_store.read_recent_reports(limit=limit)

    def latest_comparison_summary(self) -> Dict[str, Any]:
        latest_live = self._report_store.read_latest_report_for_mode("live_runtime")
        latest_compatibility = self._report_store.read_latest_report_for_mode("compatibility_shim")
        return build_latest_mode_comparison(
            latest_live_report=latest_live,
            latest_compatibility_report=latest_compatibility,
        )

    def _persist_validation_report(self, validation_result: Dict[str, Any], service_specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        active_config = self._config_for_validation_mode(
            str(validation_result.get("validation_mode") or self._selected_validation_mode)
        )
        report = build_validation_report(
            validation_result=validation_result,
            config_path=self._config_path,
            config_payload=active_config,
            harness_url=self._harness_url,
            debug_url=self._debug_url(service_specs),
        )
        persisted = self._report_store.write_report(report)
        validation_result["validation_report"] = persisted
        return validation_result

    def _http_get_json(self, url: str, timeout_sec: float = 5.0) -> Dict[str, Any]:
        request = Request(url=url, method="GET")
        with urlopen(request, timeout=timeout_sec) as response:
            return json.loads(response.read().decode("utf-8"))

    def _http_post_json(self, url: str, payload: Dict[str, Any], timeout_sec: float = 15.0) -> Dict[str, Any]:
        request = Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout_sec) as response:
            return json.loads(response.read().decode("utf-8"))

    def _http_get_status(self, url: str, timeout_sec: float = 5.0) -> Dict[str, Any]:
        request = Request(url=url, method="GET")
        with urlopen(request, timeout=timeout_sec) as response:
            return {"status_code": getattr(response, "status", 200), "content_type": response.headers.get("Content-Type")}

    def _port_is_occupied(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.25)
            return sock.connect_ex((host, port)) == 0

    def _probe_service_health(self, service_id: str, service_specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        spec = service_specs[service_id]
        target_url = f"{spec['base_url']}{spec['health_path']}"
        launched_by_harness = service_id in self._managed_processes
        attached_mode = "launched_by_harness" if launched_by_harness else "attach_existing"
        try:
            payload = self._http_get_json(target_url, timeout_sec=self._PROBE_TIMEOUT_SEC)
            return build_operator_service_check(
                service_id=service_id,
                display_name=spec["display_name"],
                target_url=target_url,
                reachable=True,
                attached_mode=attached_mode,
                launched_by_harness=launched_by_harness,
                detail="health endpoint reachable",
                extra={"payload": payload},
            )
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            port_conflict = self._port_is_occupied(spec["connect_host"], spec["port"])
            detail = (
                f"target port {spec['port']} is occupied but the expected health endpoint did not respond"
                if port_conflict
                else f"health probe failed: {exc}"
            )
            return build_operator_service_check(
                service_id=service_id,
                display_name=spec["display_name"],
                target_url=target_url,
                reachable=False,
                attached_mode=attached_mode,
                launched_by_harness=launched_by_harness,
                port_conflict=port_conflict,
                detail=detail,
                extra={"error": str(exc)},
            )

    def _probe_debug_page(self, service_specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        target_url = self._debug_url(service_specs)
        try:
            payload = self._http_get_status(target_url, timeout_sec=self._PROBE_TIMEOUT_SEC)
            return build_operator_service_check(
                service_id="debug_page",
                display_name="Debug Page",
                target_url=target_url,
                reachable=payload.get("status_code") == 200,
                attached_mode="attach_existing",
                detail="debug page reachable",
                extra=payload,
            )
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            return build_operator_service_check(
                service_id="debug_page",
                display_name="Debug Page",
                target_url=target_url,
                reachable=False,
                attached_mode="attach_existing",
                detail=f"debug page probe failed: {exc}",
                extra={"error": str(exc)},
            )

    def status(self) -> Dict[str, Any]:
        selected_mode = self._selected_validation_mode
        active_config = self._config_for_validation_mode(selected_mode)
        service_specs = self._build_service_specs(active_config)
        sim_check = self._probe_service_health("sim_pose_ingress_server", service_specs)
        api_check = self._probe_service_health("api_server", service_specs)
        debug_check = self._probe_debug_page(service_specs)
        mvsim_mode_summary = describe_mvsim_runtime_mode(active_config, self._repo_root)
        return {
            "status": "ok",
            "service": "mvsim-validation-harness",
            "harness_url": self._harness_url,
            "config_path": str(self._config_path),
            "debug_url": self._debug_url(service_specs),
            "supports_attach_existing": True,
            "supports_local_launch": True,
            "validation_modes": {
                "available": list(self._available_validation_modes),
                "default_validation_mode": self._default_validation_mode,
                "selected_validation_mode": selected_mode,
            },
            "mvsim_mode_summary": mvsim_mode_summary,
            "service_checks": {
                "sim_pose_ingress": sim_check,
                "api_server": api_check,
                "debug_page": debug_check,
            },
            "validation_snapshot": summarize_validation_snapshot(
                sim_ingress_check=sim_check,
                api_check=api_check,
                debug_check=debug_check,
                mvsim_mode_summary=mvsim_mode_summary,
                validation_result=self._last_validation_result,
            ),
            "last_validation_result": self._last_validation_result,
            "latest_report": self.latest_report(),
            "recent_reports": self.recent_reports(),
            "latest_comparison": self.latest_comparison_summary(),
        }

    def _wait_for_service(
        self,
        service_id: str,
        service_specs: Dict[str, Dict[str, Any]],
        timeout_sec: float = _SERVICE_START_TIMEOUT_SEC,
    ) -> Dict[str, Any]:
        deadline = time.time() + timeout_sec
        latest = self._probe_service_health(service_id, service_specs)
        while time.time() < deadline:
            if latest.get("reachable"):
                return latest
            time.sleep(0.35)
            latest = self._probe_service_health(service_id, service_specs)
        return latest

    def _launch_service(self, service_id: str, service_specs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        if service_id in self._managed_processes and self._managed_processes[service_id].poll() is None:
            return self._probe_service_health(service_id, service_specs)
        spec = service_specs[service_id]
        check = self._probe_service_health(service_id, service_specs)
        if check.get("reachable") or check.get("port_conflict"):
            return check
        stdout_path = self._runtime_dir / f"{service_id}.stdout.log"
        stderr_path = self._runtime_dir / f"{service_id}.stderr.log"
        stdout_handle = stdout_path.open("w", encoding="utf-8")
        stderr_handle = stderr_path.open("w", encoding="utf-8")
        self._managed_processes[service_id] = subprocess.Popen(
            spec["command"],
            cwd=str(self._repo_root),
            stdout=stdout_handle,
            stderr=stderr_handle,
        )
        latest = self._wait_for_service(service_id, service_specs)
        latest["log_paths"] = {"stdout": str(stdout_path), "stderr": str(stderr_path)}
        return latest

    def start_local_stack(self, validation_mode: Optional[str] = None) -> Dict[str, Any]:
        mode = self._resolve_validation_mode(validation_mode)
        active_config = self._config_for_validation_mode(mode)
        service_specs = self._build_service_specs(active_config)
        if self._managed_processes and self._managed_service_mode and self._managed_service_mode != mode:
            self.stop_local_stack()
        sim_check = self._launch_service("sim_pose_ingress_server", service_specs)
        api_check = self._launch_service("api_server", service_specs)
        debug_check = self._probe_debug_page(service_specs)
        self._managed_service_mode = mode if self._managed_processes else self._managed_service_mode
        return {
            "ok": bool(sim_check.get("reachable") and api_check.get("reachable")),
            "action": "start_local_stack",
            "validation_mode": mode,
            "service_checks": {
                "sim_pose_ingress": sim_check,
                "api_server": api_check,
                "debug_page": debug_check,
            },
            "debug_url": self._debug_url(service_specs),
        }

    def stop_local_stack(self) -> Dict[str, Any]:
        stopped = []
        for service_id, process in list(self._managed_processes.items()):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
            stopped.append(service_id)
            self._managed_processes.pop(service_id, None)
        self._managed_service_mode = None
        return {"ok": True, "action": "stop_local_stack", "stopped_services": stopped}

    def _build_bridge_runtime(self, sample_source, ingress_base_url: str) -> SimulatorPublisherBridgeRuntime:
        return SimulatorPublisherBridgeRuntime(
            source=sample_source,
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
            ingress_client=SimIngressHttpClient(ingress_base_url),
        )

    def _cleanup_existing_live_runtime(self, probe: Dict[str, Any]) -> None:
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

    def _build_live_launch_command(self, probe: Dict[str, Any]) -> List[str]:
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

    def _run_compatibility_bridge_validation(
        self,
        config: Dict[str, Any],
        service_specs: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        observation_file = dict(config.get("mvsim_integration") or {}).get("observation_file")
        if not observation_file:
            raise ValueError("sim config is missing mvsim_integration.observation_file")
        observation_path = Path(observation_file)
        if not observation_path.is_absolute():
            observation_path = self._repo_root / observation_path

        bridge_runtime = self._build_bridge_runtime(
            sample_source=YamlFileMVSimPoseSource(observation_path),
            ingress_base_url=service_specs["sim_pose_ingress_server"]["base_url"],
        )
        bridge_result = bridge_runtime.run()
        return {
            "bridge_result": bridge_result,
            "mvsim_source": describe_mvsim_compat_source(observation_path),
        }

    def _run_live_bridge_validation(
        self,
        config: Dict[str, Any],
        service_specs: Dict[str, Dict[str, Any]],
        mvsim_mode_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        probe = dict(mvsim_mode_summary.get("live_runtime") or {})
        runtime_process = None
        try:
            self._cleanup_existing_live_runtime(probe)
            runtime_process = subprocess.Popen(
                self._build_live_launch_command(probe),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(2.5)
            if runtime_process.poll() is not None:
                stdout, stderr = runtime_process.communicate(timeout=5)
                raise RuntimeError(
                    "WSL MVSim runtime did not stay alive long enough for harness attachment.\n"
                    f"stdout:\n{stdout}\n\nstderr:\n{stderr}"
                )

            live_sample_count = int(self._validation_harness.get("live_sample_count", 180))
            source = WslMVSimTopicEchoSource(
                distribution=probe["wsl_distribution"],
                user=probe["wsl_user"],
                executable_path=probe["wsl_executable_path"],
                topic_name=str(
                    dict(config.get("mvsim_integration") or {}).get("live_pose_topic", "/tour_bot/pose")
                ),
                sample_limit=live_sample_count,
                timeout_sec=5.0,
            )
            bridge_runtime = self._build_bridge_runtime(
                sample_source=source,
                ingress_base_url=service_specs["sim_pose_ingress_server"]["base_url"],
            )
            bridge_result = bridge_runtime.run()
            return {
                "bridge_result": bridge_result,
                "mvsim_source": describe_mvsim_live_pose_source(
                    distribution=probe["wsl_distribution"],
                    user=probe["wsl_user"],
                    executable_path=probe["wsl_executable_path"],
                    topic_name=str(
                        dict(config.get("mvsim_integration") or {}).get("live_pose_topic", "/tour_bot/pose")
                    ),
                ),
                "live_validation_summary": summarize_live_bridge_result(probe, bridge_result),
            }
        finally:
            if runtime_process is not None:
                runtime_process.terminate()
                try:
                    runtime_process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    runtime_process.kill()
                    runtime_process.communicate(timeout=5)

    def run_validation(
        self,
        question: str = "What does this final stop prove?",
        validation_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        mode = self._resolve_validation_mode(validation_mode)
        active_config = self._config_for_validation_mode(mode)
        service_specs = self._build_service_specs(active_config)
        mvsim_mode_summary = describe_mvsim_runtime_mode(active_config, self._repo_root)
        if mode == "live_runtime":
            live_runtime = dict(mvsim_mode_summary.get("live_runtime") or {})
            if live_runtime.get("blocker"):
                self._last_validation_result = {
                    "status": "blocked_live_runtime_unavailable",
                    "validation_mode": mode,
                    "mvsim_mode": mvsim_mode_summary.get("effective_mode"),
                    "mvsim_mode_summary": mvsim_mode_summary,
                    "detail": (live_runtime.get("blocker") or {}).get(
                        "detail",
                        "live MVSim runtime path is configured but not ready on this PC",
                    ),
                }
                return self._persist_validation_report(self._last_validation_result, service_specs)

        start_result = self.start_local_stack(validation_mode=mode)
        sim_check = start_result["service_checks"]["sim_pose_ingress"]
        api_check = start_result["service_checks"]["api_server"]
        debug_check = start_result["service_checks"]["debug_page"]
        if not (sim_check.get("reachable") and api_check.get("reachable")):
            self._last_validation_result = {
                "status": "failed_precondition",
                "validation_mode": mode,
                "mvsim_mode": mvsim_mode_summary.get("effective_mode"),
                "mvsim_mode_summary": mvsim_mode_summary,
                "service_checks": start_result["service_checks"],
                "detail": "required local services are not reachable",
            }
            return self._persist_validation_report(self._last_validation_result, service_specs)

        try:
            bridge_bundle = (
                self._run_live_bridge_validation(active_config, service_specs, mvsim_mode_summary)
                if mode == "live_runtime"
                else self._run_compatibility_bridge_validation(active_config, service_specs)
            )
        except Exception as exc:
            self._last_validation_result = {
                "status": "failed_bridge_execution",
                "validation_mode": mode,
                "mvsim_mode": mvsim_mode_summary.get("effective_mode"),
                "mvsim_mode_summary": mvsim_mode_summary,
                "service_checks": start_result["service_checks"],
                "detail": str(exc),
            }
            return self._persist_validation_report(self._last_validation_result, service_specs)

        bridge_result = dict(bridge_bundle.get("bridge_result") or {})
        api_base_url = service_specs["api_server"]["base_url"]
        api_state = self._http_get_json(f"{api_base_url}/state", timeout_sec=self._VALIDATION_REQUEST_TIMEOUT_SEC)
        api_session = self._http_get_json(f"{api_base_url}/session/latest", timeout_sec=self._VALIDATION_REQUEST_TIMEOUT_SEC)
        question_result = self._http_post_json(
            f"{api_base_url}/tour/question",
            {"question": question},
            timeout_sec=self._VALIDATION_REQUEST_TIMEOUT_SEC,
        )
        live_validation_summary = dict(bridge_bundle.get("live_validation_summary") or {})
        route_completed = bool(bridge_result.get("final_state", {}).get("route_completed"))
        live_mode_ok = (
            live_validation_summary.get("live_first_poi_hit_occurred")
            and live_validation_summary.get("live_second_poi_hit_occurred")
            and route_completed
        )
        self._last_validation_result = {
            "status": "passed"
            if (
                route_completed
                and api_state.get("api_mode") == "sim_ingress_proxy"
                and bool(question_result.get("ok"))
                and (live_mode_ok if mode == "live_runtime" else True)
            )
            else "failed",
            "validation_mode": mode,
            "mvsim_mode": mvsim_mode_summary.get("effective_mode"),
            "mvsim_mode_summary": mvsim_mode_summary,
            "service_checks": {
                "sim_pose_ingress": sim_check,
                "api_server": api_check,
                "debug_page": debug_check,
            },
            "mvsim_source": bridge_bundle.get("mvsim_source"),
            "bridge_result": bridge_result,
            "live_validation_summary": live_validation_summary or None,
            "sim_ingress_state": bridge_result.get("final_state"),
            "api_state": api_state,
            "api_latest_session": api_session,
            "question_result": question_result,
            "debug_url": self._debug_url(service_specs),
        }
        return self._persist_validation_report(self._last_validation_result, service_specs)
