from typing import Any, Dict

from services.deployment_profile.endpoint_config import build_canonical_endpoint_config


def build_deployment_endpoint_contract(
    config: Dict[str, Any],
    deployment_launch_plan: Dict[str, Any],
) -> Dict[str, Any]:
    canonical_config = build_canonical_endpoint_config(config, deployment_launch_plan)
    return {
        "profile_name": canonical_config.get("profile_name"),
        "preferred_config_shape": canonical_config.get("preferred_config_shape"),
        "services": list(canonical_config.get("services") or []),
        "service_count": canonical_config.get("service_count", 0),
    }
