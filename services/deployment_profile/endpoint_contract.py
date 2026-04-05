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
        if item.get("category") == "internal_service"
    ]


def _service_endpoint_overrides(config: Dict[str, Any], service_id: str) -> Dict[str, Any]:
    service_endpoints = config.get("service_endpoints") or {}
    override = service_endpoints.get(service_id) or {}
    if isinstance(override, dict):
        return dict(override)
    return {}


def _parse_config_url(url: str) -> Dict[str, Any]:
    parsed = urlparse(url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port
    default_port = 80 if scheme == "http" else 443
    actual_port = port or default_port
    return {
        "scheme": scheme,
        "connect_host": host,
        "port": actual_port,
        "base_url": f"{scheme}://{host}:{actual_port}",
    }


def _endpoint_entry(service_id: str, profile_name: Optional[str], values: Dict[str, Any], sources: Dict[str, str]) -> Dict[str, Any]:
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
    }


def _derive_endpoint(service_id: str, config: Dict[str, Any], profile_name: Optional[str]) -> Dict[str, Any]:
    defaults = dict(_DEFAULT_ENDPOINTS[service_id])
    values = dict(defaults)
    sources = {
        "bind_host": "defaulted",
        "connect_host": "defaulted",
        "port": "defaulted",
        "scheme": "defaulted",
        "base_url": "defaulted",
    }

    overrides = _service_endpoint_overrides(config, service_id)
    if service_id == "llm_gateway" and config.get("llm_gateway_url"):
        parsed = _parse_config_url(str(config["llm_gateway_url"]))
        values["connect_host"] = parsed["connect_host"]
        values["port"] = parsed["port"]
        values["scheme"] = parsed["scheme"]
        sources["connect_host"] = "config-driven"
        sources["port"] = "config-driven"
        sources["scheme"] = "config-driven"
        sources["base_url"] = "config-driven"

    if "bind_host" in overrides:
        values["bind_host"] = str(overrides["bind_host"])
        sources["bind_host"] = "config-driven"
    if "connect_host" in overrides:
        values["connect_host"] = str(overrides["connect_host"])
        sources["connect_host"] = "config-driven"
        sources["base_url"] = "config-driven"
    if "port" in overrides:
        values["port"] = int(overrides["port"])
        sources["port"] = "config-driven"
        sources["base_url"] = "config-driven"
    if "scheme" in overrides:
        values["scheme"] = str(overrides["scheme"])
        sources["scheme"] = "config-driven"
        sources["base_url"] = "config-driven"

    return _endpoint_entry(service_id, profile_name, values, sources)


def build_deployment_endpoint_contract(
    config: Dict[str, Any],
    deployment_launch_plan: Dict[str, Any],
) -> Dict[str, Any]:
    profile_name = str(config.get("env_name", "")).strip() or None
    service_ids = [item for item in _configured_service_ids(deployment_launch_plan) if item in _DEFAULT_ENDPOINTS]
    endpoints = [_derive_endpoint(service_id, config, profile_name) for service_id in service_ids]
    return {
        "profile_name": profile_name,
        "services": endpoints,
        "service_count": len(endpoints),
    }
