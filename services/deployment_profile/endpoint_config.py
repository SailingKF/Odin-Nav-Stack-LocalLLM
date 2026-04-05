from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


_DEFAULT_ENDPOINTS: Dict[str, Dict[str, Any]] = {
    "api_server": {
        "bind_host": "0.0.0.0",
        "connect_host": "127.0.0.1",
        "port": 8000,
        "scheme": "http",
    },
    "llm_gateway": {
        "bind_host": "0.0.0.0",
        "connect_host": "127.0.0.1",
        "port": 9000,
        "scheme": "http",
    },
    "sim_pose_ingress_server": {
        "bind_host": "127.0.0.1",
        "connect_host": "127.0.0.1",
        "port": 8100,
        "scheme": "http",
    },
}


def _configured_service_ids(deployment_launch_plan: Dict[str, Any]) -> List[str]:
    return [
        str(item.get("step_id"))
        for item in list(deployment_launch_plan.get("steps") or [])
        if item.get("step_id") in _DEFAULT_ENDPOINTS
    ]


def _service_endpoint_overrides(config: Dict[str, Any], service_id: str) -> Dict[str, Any]:
    service_endpoints = config.get("service_endpoints") or {}
    override = service_endpoints.get(service_id) or {}
    if isinstance(override, dict):
        return dict(override)
    return {}


def _parse_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (80 if scheme == "http" else 443)
    return {
        "scheme": scheme,
        "connect_host": host,
        "port": port,
    }


def _legacy_override(config: Dict[str, Any], service_id: str) -> Dict[str, Any]:
    if service_id == "llm_gateway" and config.get("llm_gateway_url"):
        return _parse_url(str(config["llm_gateway_url"]))
    return {}


def _canonicalized_service_entry(service_id: str, profile_name: Optional[str], config: Dict[str, Any]) -> Dict[str, Any]:
    defaults = dict(_DEFAULT_ENDPOINTS[service_id])
    values = dict(defaults)
    sources = {
        "bind_host": "default",
        "connect_host": "default",
        "port": "default",
        "scheme": "default",
        "base_url": "default",
    }

    legacy = _legacy_override(config, service_id)
    if legacy:
        for key, value in legacy.items():
            values[key] = value
            sources[key] = "legacy_compatibility"
            sources["base_url"] = "legacy_compatibility"

    canonical = _service_endpoint_overrides(config, service_id)
    for key in ("bind_host", "connect_host", "port", "scheme"):
        if key in canonical:
            values[key] = canonical[key]
            sources[key] = "canonical_endpoint_config"
            sources["base_url"] = "canonical_endpoint_config"

    values["port"] = int(values["port"])
    values["bind_host"] = str(values["bind_host"])
    values["connect_host"] = str(values["connect_host"])
    values["scheme"] = str(values["scheme"])

    return {
        "service_id": service_id,
        "step_id": service_id,
        "profile_name": profile_name,
        "bind_host": values["bind_host"],
        "connect_host": values["connect_host"],
        "port": values["port"],
        "scheme": values["scheme"],
        "base_url": f"{values['scheme']}://{values['connect_host']}:{values['port']}",
        "bind_host_source": sources["bind_host"],
        "connect_host_source": sources["connect_host"],
        "port_source": sources["port"],
        "scheme_source": sources["scheme"],
        "base_url_source": sources["base_url"],
        "canonical_config_path": f"service_endpoints.{service_id}",
        "legacy_compatibility_fields": ["llm_gateway_url"] if service_id == "llm_gateway" else [],
    }


def build_canonical_endpoint_config(
    config: Dict[str, Any],
    deployment_launch_plan: Dict[str, Any],
) -> Dict[str, Any]:
    profile_name = str(config.get("env_name", "")).strip() or None
    service_ids = _configured_service_ids(deployment_launch_plan)
    services = [_canonicalized_service_entry(service_id, profile_name, config) for service_id in service_ids]
    return {
        "profile_name": profile_name,
        "preferred_config_shape": "service_endpoints.<service_id>",
        "services": services,
        "service_count": len(services),
    }
