from typing import Any, Dict, List, Set


_TRACKED_SOURCE_FIELDS = (
    "bind_host",
    "connect_host",
    "port",
    "scheme",
)


def _legacy_fields_present(config: Dict[str, Any]) -> Set[str]:
    present: Set[str] = set()
    if config.get("llm_gateway_url"):
        present.add("llm_gateway_url")
    return present


def _service_hygiene_status(
    canonical_fields_in_use: List[str],
    legacy_fields_in_use: List[str],
    default_fields_in_use: List[str],
) -> str:
    if canonical_fields_in_use and legacy_fields_in_use:
        return "mixed_canonical_and_legacy"
    if legacy_fields_in_use:
        return "legacy_dependent"
    if canonical_fields_in_use and not default_fields_in_use:
        return "fully_canonicalized"
    if canonical_fields_in_use:
        return "partially_canonicalized"
    return "default_heavy"


def _service_recommended_actions(
    service: Dict[str, Any],
    hygiene_status: str,
    legacy_fields_present: List[str],
) -> List[str]:
    service_id = str(service.get("service_id"))
    canonical_path = str(service.get("canonical_config_path"))
    actions: List[str] = []

    if hygiene_status == "mixed_canonical_and_legacy":
        actions.append(
            f"Complete {canonical_path} so {service_id} no longer mixes canonical endpoint fields with legacy compatibility values."
        )
    elif hygiene_status == "legacy_dependent":
        actions.append(
            f"Add explicit {canonical_path} settings for {service_id} so endpoint resolution no longer depends on legacy compatibility fields."
        )
    elif hygiene_status == "partially_canonicalized":
        actions.append(
            f"Fill in the remaining explicit fields under {canonical_path} for {service_id} to remove default-derived endpoint values."
        )
    elif hygiene_status == "default_heavy":
        actions.append(
            f"Add an explicit {canonical_path} block for {service_id} to replace default-only endpoint assumptions with canonical config."
        )

    if legacy_fields_present:
        field_list = ", ".join(sorted(legacy_fields_present))
        if hygiene_status == "fully_canonicalized":
            actions.append(
                f"Remove deprecated compatibility field(s) {field_list} after confirming {canonical_path} is the intended long-term endpoint source for {service_id}."
            )
        else:
            actions.append(
                f"Keep deprecated compatibility field(s) {field_list} only during migration, then remove them after {canonical_path} is complete for {service_id}."
            )

    return actions


def _build_service_hygiene_entry(
    service: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    tracked_sources = {
        field_name: str(service.get(f"{field_name}_source"))
        for field_name in _TRACKED_SOURCE_FIELDS
    }

    canonical_fields_in_use = [
        field_name
        for field_name, source in tracked_sources.items()
        if source == "canonical_endpoint_config"
    ]
    legacy_fields_in_use = [
        field_name
        for field_name, source in tracked_sources.items()
        if source == "legacy_compatibility"
    ]
    default_fields_in_use = [
        field_name
        for field_name, source in tracked_sources.items()
        if source == "default"
    ]

    supported_legacy_fields = [str(item) for item in list(service.get("legacy_compatibility_fields") or [])]
    legacy_fields_present = [field_name for field_name in supported_legacy_fields if config.get(field_name)]
    hygiene_status = _service_hygiene_status(
        canonical_fields_in_use=canonical_fields_in_use,
        legacy_fields_in_use=legacy_fields_in_use,
        default_fields_in_use=default_fields_in_use,
    )

    return {
        "service_id": service.get("service_id"),
        "step_id": service.get("step_id"),
        "profile_name": service.get("profile_name"),
        "base_url": service.get("base_url"),
        "canonical_config_path": service.get("canonical_config_path"),
        "hygiene_status": hygiene_status,
        "uses_canonical_config": bool(canonical_fields_in_use),
        "legacy_compatibility_in_use": bool(legacy_fields_in_use),
        "default_values_in_use": bool(default_fields_in_use),
        "legacy_compatibility_fields_supported": supported_legacy_fields,
        "legacy_compatibility_fields_present": legacy_fields_present,
        "canonical_fields_in_use": canonical_fields_in_use,
        "legacy_fields_in_use": legacy_fields_in_use,
        "default_fields_in_use": default_fields_in_use,
        "source_counts": {
            "canonical": len(canonical_fields_in_use),
            "legacy": len(legacy_fields_in_use),
            "default": len(default_fields_in_use),
        },
        "recommended_actions": _service_recommended_actions(
            service=service,
            hygiene_status=hygiene_status,
            legacy_fields_present=legacy_fields_present,
        ),
    }


def _overall_hygiene_status(services: List[Dict[str, Any]]) -> str:
    if not services:
        return "no_repo_owned_service_endpoints"

    statuses = [str(service.get("hygiene_status")) for service in services]
    if "mixed_canonical_and_legacy" in statuses:
        return "mixed_canonical_and_legacy"
    if "legacy_dependent" in statuses:
        return "legacy_dependent"
    if all(status == "fully_canonicalized" for status in statuses):
        return "fully_canonicalized"
    if statuses.count("default_heavy") >= max(1, len(statuses) // 2 + (len(statuses) % 2)):
        return "default_heavy"
    return "partially_canonicalized"


def _unique_actions(services: List[Dict[str, Any]]) -> List[str]:
    seen: Set[str] = set()
    actions: List[str] = []
    for service in services:
        for action in list(service.get("recommended_actions") or []):
            action_text = str(action)
            if action_text not in seen:
                seen.add(action_text)
                actions.append(action_text)
    return actions


def build_deployment_config_hygiene(
    config: Dict[str, Any],
    deployment_endpoint_contract: Dict[str, Any],
) -> Dict[str, Any]:
    services = [
        _build_service_hygiene_entry(service=item, config=config)
        for item in list(deployment_endpoint_contract.get("services") or [])
    ]

    legacy_fields_present = sorted(_legacy_fields_present(config))
    legacy_fields_in_use: Set[str] = set()
    for service in services:
        for field_name in list(service.get("legacy_compatibility_fields_present") or []):
            if service.get("legacy_compatibility_in_use"):
                legacy_fields_in_use.add(str(field_name))

    overall_status = _overall_hygiene_status(services)

    return {
        "profile_name": deployment_endpoint_contract.get("profile_name"),
        "preferred_config_shape": deployment_endpoint_contract.get("preferred_config_shape"),
        "overall_hygiene_status": overall_status,
        "legacy_compatibility_present": bool(legacy_fields_present),
        "legacy_compatibility_in_use": bool(legacy_fields_in_use),
        "deprecation_cleanup_needed": bool(legacy_fields_present),
        "legacy_compatibility_fields_present": legacy_fields_present,
        "legacy_compatibility_fields_in_use": sorted(legacy_fields_in_use),
        "service_count": len(services),
        "fully_canonicalized_service_count": sum(
            1 for item in services if item.get("hygiene_status") == "fully_canonicalized"
        ),
        "partially_canonicalized_service_count": sum(
            1 for item in services if item.get("hygiene_status") == "partially_canonicalized"
        ),
        "mixed_service_count": sum(
            1 for item in services if item.get("hygiene_status") == "mixed_canonical_and_legacy"
        ),
        "legacy_dependent_service_count": sum(
            1 for item in services if item.get("hygiene_status") == "legacy_dependent"
        ),
        "default_heavy_service_count": sum(
            1 for item in services if item.get("hygiene_status") == "default_heavy"
        ),
        "services": services,
        "recommended_actions": _unique_actions(services),
    }
