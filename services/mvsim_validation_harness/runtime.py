import json
import socket
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

from adapters.sim.frame_transform import SimFrameTransformConfig
from adapters.sim.projection import SimPoseProjectionConfig
from services.deployment_profile import build_deployment_endpoint_contract, build_deployment_launch_plan
from services.sim_publisher_bridge.http_client import SimIngressHttpClient
from services.sim_publisher_bridge.mvsim_source import YamlFileMVSimPoseSource, describe_mvsim_compat_source
from services.sim_publisher_bridge.runtime import SimulatorPublisherBridgeRuntime


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
    validation_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if validation_result is None:
        return {
            "overall_status": "idle",
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
        self._config = self._load_config(self._config_path)
        self._endpoint_contract = build_deployment_endpoint_contract(
            self._config,
            build_deployment_launch_plan(self._config),
        )
        self._service_specs = self._build_service_specs()
        self._runtime_dir = repo_root / "session_logs" / "mvsim_validation_harness"
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._managed_processes: Dict[str, subprocess.Popen] = {}
        self._last_validation_result: Optional[Dict[str, Any]] = None

    @staticmethod
    def _load_config(config_path: Path) -> Dict[str, Any]:
        with config_path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def _build_service_specs(self) -> Dict[str, Dict[str, Any]]:
        endpoint_by_service = {
            str(item.get("service_id")): item
            for item in list(self._endpoint_contract.get("services") or [])
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
                    str(self._config_path.relative_to(self._repo_root)),
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
                    str(self._config_path.relative_to(self._repo_root)),
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

    @property
    def debug_url(self) -> str:
        return f"{self._service_specs['api_server']['base_url']}/debug"

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

    def _probe_service_health(self, service_id: str) -> Dict[str, Any]:
        spec = self._service_specs[service_id]
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

    def _probe_debug_page(self) -> Dict[str, Any]:
        target_url = self.debug_url
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
        sim_check = self._probe_service_health("sim_pose_ingress_server")
        api_check = self._probe_service_health("api_server")
        debug_check = self._probe_debug_page()
        return {
            "status": "ok",
            "service": "mvsim-validation-harness",
            "harness_url": self._harness_url,
            "config_path": str(self._config_path),
            "debug_url": self.debug_url,
            "supports_attach_existing": True,
            "supports_local_launch": True,
            "service_checks": {
                "sim_pose_ingress": sim_check,
                "api_server": api_check,
                "debug_page": debug_check,
            },
            "validation_snapshot": summarize_validation_snapshot(
                sim_ingress_check=sim_check,
                api_check=api_check,
                debug_check=debug_check,
                validation_result=self._last_validation_result,
            ),
            "last_validation_result": self._last_validation_result,
        }

    def _wait_for_service(self, service_id: str, timeout_sec: float = _SERVICE_START_TIMEOUT_SEC) -> Dict[str, Any]:
        deadline = time.time() + timeout_sec
        latest = self._probe_service_health(service_id)
        while time.time() < deadline:
            if latest.get("reachable"):
                return latest
            time.sleep(0.35)
            latest = self._probe_service_health(service_id)
        return latest

    def _launch_service(self, service_id: str) -> Dict[str, Any]:
        if service_id in self._managed_processes and self._managed_processes[service_id].poll() is None:
            return self._probe_service_health(service_id)
        spec = self._service_specs[service_id]
        check = self._probe_service_health(service_id)
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
        latest = self._wait_for_service(service_id)
        latest["log_paths"] = {"stdout": str(stdout_path), "stderr": str(stderr_path)}
        return latest

    def start_local_stack(self) -> Dict[str, Any]:
        sim_check = self._launch_service("sim_pose_ingress_server")
        api_check = self._launch_service("api_server")
        debug_check = self._probe_debug_page()
        return {
            "ok": bool(sim_check.get("reachable") and api_check.get("reachable")),
            "action": "start_local_stack",
            "service_checks": {
                "sim_pose_ingress": sim_check,
                "api_server": api_check,
                "debug_page": debug_check,
            },
            "debug_url": self.debug_url,
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
        return {"ok": True, "action": "stop_local_stack", "stopped_services": stopped}

    def run_validation(self, question: str = "What does this final stop prove?") -> Dict[str, Any]:
        start_result = self.start_local_stack()
        sim_check = start_result["service_checks"]["sim_pose_ingress"]
        api_check = start_result["service_checks"]["api_server"]
        debug_check = start_result["service_checks"]["debug_page"]
        if not (sim_check.get("reachable") and api_check.get("reachable")):
            self._last_validation_result = {
                "status": "failed_precondition",
                "service_checks": start_result["service_checks"],
                "detail": "required local services are not reachable",
            }
            return self._last_validation_result

        observation_file = dict(self._config.get("mvsim_integration") or {}).get("observation_file")
        if not observation_file:
            self._last_validation_result = {
                "status": "failed_precondition",
                "service_checks": start_result["service_checks"],
                "detail": "sim config is missing mvsim_integration.observation_file",
            }
            return self._last_validation_result
        observation_path = Path(observation_file)
        if not observation_path.is_absolute():
            observation_path = self._repo_root / observation_path

        bridge_runtime = SimulatorPublisherBridgeRuntime(
            source=YamlFileMVSimPoseSource(observation_path),
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
            ingress_client=SimIngressHttpClient(self._service_specs["sim_pose_ingress_server"]["base_url"]),
        )
        bridge_result = bridge_runtime.run()
        api_base_url = self._service_specs["api_server"]["base_url"]
        api_state = self._http_get_json(f"{api_base_url}/state", timeout_sec=self._VALIDATION_REQUEST_TIMEOUT_SEC)
        api_session = self._http_get_json(f"{api_base_url}/session/latest", timeout_sec=self._VALIDATION_REQUEST_TIMEOUT_SEC)
        question_result = self._http_post_json(
            f"{api_base_url}/tour/question",
            {"question": question},
            timeout_sec=self._VALIDATION_REQUEST_TIMEOUT_SEC,
        )
        self._last_validation_result = {
            "status": "passed"
            if (
                bridge_result.get("final_state", {}).get("route_completed")
                and api_state.get("api_mode") == "sim_ingress_proxy"
                and bool(question_result.get("ok"))
            )
            else "failed",
            "service_checks": {
                "sim_pose_ingress": sim_check,
                "api_server": api_check,
                "debug_page": debug_check,
            },
            "mvsim_source": describe_mvsim_compat_source(observation_path),
            "bridge_result": bridge_result,
            "sim_ingress_state": bridge_result.get("final_state"),
            "api_state": api_state,
            "api_latest_session": api_session,
            "question_result": question_result,
            "debug_url": self.debug_url,
        }
        return self._last_validation_result
