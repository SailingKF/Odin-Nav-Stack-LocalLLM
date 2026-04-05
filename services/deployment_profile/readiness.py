from typing import Any, Dict, List, Optional, Tuple


_STEP_READY_STATUSES = {
    "ready",
    "blocked",
    "optional",
    "external_unverified",
    "not_applicable",
}


def _preflight_checks_by_name(preflight: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(item.get("name")): item
        for item in list(preflight.get("checks") or [])
        if item.get("name")
    }


def _parse_gate(gate: str) -> Tuple[str, Optional[str]]:
    if "=" in gate:
        key, expected = gate.split("=", 1)
        return key.strip(), expected.strip()
    return gate.strip(), None


def _evaluate_gate(gate: str, checks_by_name: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    key, expected = _parse_gate(gate)
    if not key.startswith("deployment_preflight."):
        return {
            "gate": gate,
            "kind": "informational",
            "satisfied": None,
            "actual_status": None,
            "detail": "gate is advisory and not mapped to a preflight check",
        }

    check_name = key.split(".", 1)[1]
    check = checks_by_name.get(check_name)
    if check is None:
        return {
            "gate": gate,
            "kind": "preflight",
            "check_name": check_name,
            "satisfied": False,
            "actual_status": "missing",
            "detail": "preflight check not found",
        }

    actual_status = str(check.get("status"))
    if expected is None:
        satisfied = actual_status not in {"missing", "unreachable"}
    else:
        satisfied = actual_status == expected

    return {
        "gate": gate,
        "kind": "preflight",
        "check_name": check_name,
        "expected_status": expected,
        "actual_status": actual_status,
        "satisfied": satisfied,
        "detail": str(check.get("detail", "")),
    }


def _derive_step_status(step: Dict[str, Any], gate_results: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    category = str(step.get("category"))
    required = bool(step.get("required"))
    blocking_reasons: List[str] = []

    preflight_results = [item for item in gate_results if item.get("kind") == "preflight"]
    actual_statuses = [str(item.get("actual_status")) for item in preflight_results if item.get("actual_status")]

    if not required:
        if "not_applicable" in actual_statuses:
            return "not_applicable", []
        return "optional", []

    if any(status in {"missing", "unreachable"} for status in actual_statuses):
        for item in preflight_results:
            if item.get("actual_status") in {"missing", "unreachable"}:
                blocking_reasons.append(
                    f"{item.get('check_name')} is {item.get('actual_status')}: {item.get('detail')}"
                )
        return "blocked", blocking_reasons

    if category == "external_dependency" and "unverified_external" in actual_statuses:
        return "external_unverified", []

    if any(item.get("satisfied") is False for item in preflight_results):
        for item in preflight_results:
            if item.get("satisfied") is False:
                expected = item.get("expected_status")
                if expected:
                    blocking_reasons.append(
                        f"{item.get('check_name')} expected {expected} but got {item.get('actual_status')}"
                    )
                else:
                    blocking_reasons.append(
                        f"{item.get('check_name')} did not satisfy launch gate"
                    )
        return "blocked", blocking_reasons

    return "ready", []


def build_deployment_readiness(
    deployment_profile: Dict[str, Any],
    deployment_preflight: Dict[str, Any],
    deployment_launch_plan: Dict[str, Any],
) -> Dict[str, Any]:
    checks_by_name = _preflight_checks_by_name(deployment_preflight)
    steps = list(deployment_launch_plan.get("steps") or [])

    step_summaries: List[Dict[str, Any]] = []
    blockers: List[str] = [str(item) for item in list(deployment_profile.get("errors") or [])]

    required_ready_count = 0
    required_blocked_count = 0
    required_external_unverified_count = 0
    optional_step_count = 0
    not_applicable_step_count = 0

    for step in steps:
        gate_results = [_evaluate_gate(str(gate), checks_by_name) for gate in list(step.get("readiness_gates") or [])]
        step_status, step_blockers = _derive_step_status(step, gate_results)

        if step_status not in _STEP_READY_STATUSES:
            step_status = "blocked"

        summary = {
            "step_id": step.get("step_id"),
            "order": step.get("order"),
            "category": step.get("category"),
            "required": bool(step.get("required")),
            "name": step.get("name"),
            "status": step_status,
            "startup_hint": step.get("startup_hint"),
            "readiness_gates": list(step.get("readiness_gates") or []),
            "gate_results": gate_results,
            "detail": step.get("detail"),
            "blocking_reasons": step_blockers,
        }
        step_summaries.append(summary)

        if summary["required"]:
            if step_status == "ready":
                required_ready_count += 1
            elif step_status == "blocked":
                required_blocked_count += 1
                blockers.extend(step_blockers or [f"{summary['step_id']} is blocked"])
            elif step_status == "external_unverified":
                required_external_unverified_count += 1
        else:
            if step_status == "not_applicable":
                not_applicable_step_count += 1
            else:
                optional_step_count += 1

    profile_status = str(deployment_profile.get("readiness_status", "unknown"))
    if profile_status == "invalid" or required_blocked_count > 0:
        overall_status = "blocked"
    elif required_external_unverified_count > 0:
        overall_status = "external_verification_needed"
    else:
        overall_status = "ready_for_guided_bringup"

    if profile_status == "placeholder" and overall_status == "ready_for_guided_bringup":
        overall_status = "ready_with_placeholders"

    return {
        "profile_name": deployment_profile.get("profile_name"),
        "profile_readiness_status": profile_status,
        "overall_status": overall_status,
        "required_ready_count": required_ready_count,
        "required_blocked_count": required_blocked_count,
        "required_external_unverified_count": required_external_unverified_count,
        "optional_step_count": optional_step_count,
        "not_applicable_step_count": not_applicable_step_count,
        "step_count": len(step_summaries),
        "blocking_reasons": blockers,
        "steps": step_summaries,
    }
