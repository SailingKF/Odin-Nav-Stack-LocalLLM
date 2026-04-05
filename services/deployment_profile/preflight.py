from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


_PREFLIGHT_STATUSES = {
    "ok",
    "unreachable",
    "missing",
    "unverified_external",
    "not_applicable",
}


def _default_url_probe(url: str, timeout_sec: float) -> Dict[str, Any]:
    request = Request(url, method="GET")
    with urlopen(request, timeout=timeout_sec) as response:
        status_code = getattr(response, "status", None) or response.getcode()
    return {"status": "ok", "http_status": status_code}


def _check_file(path: Path, label: str) -> Dict[str, Any]:
    if path.exists():
        return {
            "name": label,
            "status": "ok",
            "kind": "file",
            "path": str(path),
            "detail": "file exists",
        }
    return {
        "name": label,
        "status": "missing",
        "kind": "file",
        "path": str(path),
        "detail": "configured file is missing",
    }


def _check_session_log_dir(path: Path) -> Dict[str, Any]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path, prefix=".preflight_", suffix=".tmp", delete=True) as handle:
            handle.write("ok")
            handle.flush()
        return {
            "name": "session_log_dir",
            "status": "ok",
            "kind": "directory",
            "path": str(path),
            "detail": "directory is creatable and writable",
        }
    except OSError as exc:
        return {
            "name": "session_log_dir",
            "status": "missing",
            "kind": "directory",
            "path": str(path),
            "detail": f"directory is not writable: {exc}",
        }


def _check_url(
    name: str,
    url: str,
    timeout_sec: float,
    probe: Callable[[str, float], Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        payload = probe(url, timeout_sec)
        status = str(payload.get("status", "ok"))
        if status not in _PREFLIGHT_STATUSES:
            status = "ok"
        return {
            "name": name,
            "status": status,
            "kind": "http",
            "url": url,
            "detail": payload.get("detail", "dependency responded"),
            "http_status": payload.get("http_status"),
        }
    except HTTPError as exc:
        return {
            "name": name,
            "status": "unreachable",
            "kind": "http",
            "url": url,
            "detail": f"http error: {exc.code}",
            "http_status": exc.code,
        }
    except URLError as exc:
        return {
            "name": name,
            "status": "unreachable",
            "kind": "http",
            "url": url,
            "detail": f"url error: {exc.reason}",
        }
    except OSError as exc:
        return {
            "name": name,
            "status": "unreachable",
            "kind": "http",
            "url": url,
            "detail": str(exc),
        }


def _build_counts(checks: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {status: 0 for status in sorted(_PREFLIGHT_STATUSES)}
    for item in checks:
        status = str(item.get("status"))
        if status in counts:
            counts[status] += 1
    return counts


def build_deployment_preflight(
    config: Dict[str, Any],
    repo_root: Path,
    url_probe: Optional[Callable[[str, float], Dict[str, Any]]] = None,
    http_timeout_sec: float = 0.35,
) -> Dict[str, Any]:
    probe = _default_url_probe if url_probe is None else url_probe
    profile_name = str(config.get("env_name", "")).strip() or None
    checks: List[Dict[str, Any]] = []

    route_path = Path(repo_root) / str(config.get("current_route_file", ""))
    poi_path = Path(repo_root) / str(config.get("current_poi_file", ""))
    session_log_dir = Path(repo_root) / str(config.get("session_log_dir", "session_logs"))

    checks.append(_check_file(route_path, "route_file"))
    checks.append(_check_file(poi_path, "poi_file"))
    checks.append(_check_session_log_dir(session_log_dir))

    narrator_type = str(config.get("narrator_type", "mock"))
    llm_gateway_url = str(config.get("llm_gateway_url", "")).strip()
    if narrator_type == "local_llm":
        if llm_gateway_url:
            checks.append(
                _check_url(
                    "llm_gateway",
                    urljoin(f"{llm_gateway_url.rstrip('/')}/", "health"),
                    timeout_sec=http_timeout_sec,
                    probe=probe,
                )
            )
        else:
            checks.append(
                {
                    "name": "llm_gateway",
                    "status": "missing",
                    "kind": "http",
                    "url": None,
                    "detail": "local_llm narrator requires llm_gateway_url",
                }
            )
    else:
        checks.append(
            {
                "name": "llm_gateway",
                "status": "not_applicable",
                "kind": "http",
                "url": None,
                "detail": "current narrator path does not require llm gateway",
            }
        )

    llm_backend_type = str(config.get("llm_backend_type", "mock"))
    llm_base_url = str(config.get("llm_base_url", "")).strip()
    if llm_backend_type == "ollama":
        if llm_base_url:
            checks.append(
                _check_url(
                    "ollama_runtime",
                    urljoin(f"{llm_base_url.rstrip('/')}/", "api/tags"),
                    timeout_sec=http_timeout_sec,
                    probe=probe,
                )
            )
        else:
            checks.append(
                {
                    "name": "ollama_runtime",
                    "status": "missing",
                    "kind": "http",
                    "url": None,
                    "detail": "ollama backend requires llm_base_url",
                }
            )
    else:
        checks.append(
            {
                "name": "ollama_runtime",
                "status": "not_applicable",
                "kind": "http",
                "url": None,
                "detail": "current llm backend does not use Ollama",
            }
        )

    pose_provider_type = str(config.get("pose_provider_type", ""))
    if pose_provider_type == "odin_ros":
        checks.append(
            {
                "name": "hardware_pose_dependency",
                "status": "unverified_external",
                "kind": "external",
                "detail": "odin_ros pose dependency cannot be safely verified in this preflight baseline",
            }
        )
    elif pose_provider_type == "sim_ingress" and str((config.get("isaac_source") or {}).get("mode", "stub")) == "live":
        checks.append(
            {
                "name": "isaac_live_dependency",
                "status": "unverified_external",
                "kind": "external",
                "detail": "live Isaac integration remains external to this preflight baseline",
            }
        )
    else:
        checks.append(
            {
                "name": "external_pose_dependency",
                "status": "not_applicable",
                "kind": "external",
                "detail": "current pose path does not require an external live dependency probe",
            }
        )

    audio_output_type = str(config.get("audio_output_type", "mock"))
    if audio_output_type == "mock":
        checks.append(
            {
                "name": "audio_device_dependency",
                "status": "not_applicable",
                "kind": "external",
                "detail": "mock audio output does not require a real audio device",
            }
        )
    else:
        checks.append(
            {
                "name": "audio_device_dependency",
                "status": "unverified_external",
                "kind": "external",
                "detail": "real audio device playback remains external to this preflight baseline",
            }
        )

    counts = _build_counts(checks)
    if counts["missing"] > 0:
        summary_status = "missing"
    elif counts["unreachable"] > 0:
        summary_status = "unreachable"
    elif counts["unverified_external"] > 0:
        summary_status = "needs_external_verification"
    else:
        summary_status = "ok"

    return {
        "profile_name": profile_name,
        "summary_status": summary_status,
        "http_timeout_sec": http_timeout_sec,
        "counts": counts,
        "checks": checks,
    }
