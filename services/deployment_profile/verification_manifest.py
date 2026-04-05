from typing import Any, Dict, List, Optional


def _endpoint_by_service_id(deployment_endpoint_contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("service_id")): item
        for item in list(deployment_endpoint_contract.get("services") or [])
        if item.get("service_id")
    }


def _verification_entry(
    verification_id: str,
    step: Dict[str, Any],
    command_id: str,
    verification_kind: str,
    target_path: str,
    expected_statuses: List[str],
    expected_fields: List[str],
    description: str,
    endpoint: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    base_url = endpoint.get("base_url") if endpoint else None
    return {
        "verification_id": verification_id,
        "step_id": step.get("step_id"),
        "command_id": command_id,
        "order": step.get("order"),
        "profile_name": step.get("profile_name"),
        "verification_kind": verification_kind,
        "method": "GET",
        "base_url": base_url,
        "target_path": target_path,
        "target_url": f"{base_url}{target_path}" if base_url else None,
        "expected_statuses": expected_statuses,
        "expected_fields": expected_fields,
        "description": description,
    }


def _build_known_verification(
    step: Dict[str, Any],
    command_by_step_id: Dict[str, Dict[str, Any]],
    endpoint_by_service_id: Dict[str, Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    step_id = str(step.get("step_id"))
    command = command_by_step_id.get(step_id)
    if command is None:
        return None

    verification_id = f"{step_id}_verification"
    endpoint = endpoint_by_service_id.get(step_id)

    if step_id == "llm_gateway":
        return _verification_entry(
            verification_id,
            step,
            str(command.get("command_id")),
            "http_json_health",
            "/health",
            ["ok", "degraded"],
            ["service", "active_backend_type", "fallback_active"],
            "Verify that the local LLM gateway is reachable and exposes a usable backend status.",
            endpoint,
        )

    if step_id == "api_server":
        return _verification_entry(
            verification_id,
            step,
            str(command.get("command_id")),
            "http_json_health",
            "/health",
            ["ok"],
            ["service", "env_name", "deployment_profile"],
            "Verify that the backend API server is reachable and serving the operator/runtime health surface.",
            endpoint,
        )

    if step_id == "sim_pose_ingress_server":
        return _verification_entry(
            verification_id,
            step,
            str(command.get("command_id")),
            "http_json_health",
            "/health",
            ["ok"],
            ["service", "ingress_contract", "deployment_profile"],
            "Verify that the sim pose ingress server is reachable and exposes the expected ingress contract.",
            endpoint,
        )

    return None


def build_deployment_verification_manifest(
    deployment_command_manifest: Dict[str, Any],
    deployment_endpoint_contract: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    profile_name = deployment_command_manifest.get("profile_name")
    config_path = deployment_command_manifest.get("config_path")
    steps = list(deployment_command_manifest.get("steps") or [])
    command_by_step_id = {
        str(item.get("step_id")): item
        for item in list(deployment_command_manifest.get("commands") or [])
        if item.get("step_id")
    }
    endpoint_by_service_id = _endpoint_by_service_id(deployment_endpoint_contract or {})

    verifications: List[Dict[str, Any]] = []
    step_checks: List[Dict[str, Any]] = []

    for step in steps:
        step_with_profile = dict(step)
        step_with_profile["profile_name"] = profile_name
        verification = _build_known_verification(step_with_profile, command_by_step_id, endpoint_by_service_id)
        if verification is not None:
            verifications.append(verification)
            verification_type = "repo_verification"
        elif step.get("action_type") == "manual_external":
            verification_type = "manual_external"
        else:
            verification_type = "manual_optional"

        step_checks.append(
            {
                "step_id": step.get("step_id"),
                "order": step.get("order"),
                "name": step.get("name"),
                "action_type": step.get("action_type"),
                "verification_type": verification_type,
                "verification_available": verification is not None,
                "verification_id": verification.get("verification_id") if verification else None,
                "verification_target": verification.get("target_url") if verification else None,
                "detail": step.get("detail"),
            }
        )

    return {
        "profile_name": profile_name,
        "config_path": config_path,
        "verifications": verifications,
        "steps": step_checks,
        "verification_count": len(verifications),
        "repo_verification_step_count": sum(1 for item in step_checks if item.get("verification_available")),
        "manual_step_count": sum(1 for item in step_checks if not item.get("verification_available")),
    }


def build_bringup_verification_sheet(
    deployment_readiness: Dict[str, Any],
    deployment_command_manifest: Dict[str, Any],
    deployment_verification_manifest: Dict[str, Any],
) -> Dict[str, Any]:
    command_by_step_id = {
        str(item.get("step_id")): item
        for item in list(deployment_command_manifest.get("commands") or [])
        if item.get("step_id")
    }
    verification_by_step_id = {
        str(item.get("step_id")): item
        for item in list(deployment_verification_manifest.get("verifications") or [])
        if item.get("step_id")
    }

    steps: List[Dict[str, Any]] = []
    for item in list(deployment_readiness.get("steps") or []):
        step_id = str(item.get("step_id"))
        command = command_by_step_id.get(step_id)
        verification = verification_by_step_id.get(step_id)
        steps.append(
            {
                "step_id": step_id,
                "order": item.get("order"),
                "name": item.get("name"),
                "status": item.get("status"),
                "required": bool(item.get("required")),
                "category": item.get("category"),
                "action_type": "repo_command" if command else (
                    "manual_external" if item.get("category") == "external_dependency" else "manual_optional"
                ),
                "display_command": command.get("display_command") if command else None,
                "verification_available": verification is not None,
                "verification_target": verification.get("target_url") if verification else None,
                "verification_kind": verification.get("verification_kind") if verification else None,
                "expected_statuses": list(verification.get("expected_statuses") or []) if verification else [],
                "blocking_reasons": list(item.get("blocking_reasons") or []),
            }
        )

    return {
        "profile_name": deployment_verification_manifest.get("profile_name"),
        "config_path": deployment_verification_manifest.get("config_path"),
        "overall_status": deployment_readiness.get("overall_status"),
        "blocking_reasons": list(deployment_readiness.get("blocking_reasons") or []),
        "steps": steps,
        "step_count": len(steps),
        "verification_count": deployment_verification_manifest.get("verification_count", 0),
    }
