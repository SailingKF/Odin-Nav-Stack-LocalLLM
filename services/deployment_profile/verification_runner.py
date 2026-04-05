import json
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


FetchJsonFn = Callable[[str, float], Dict[str, Any]]


def _default_fetch_json(url: str, timeout_sec: float) -> Dict[str, Any]:
    with urlopen(url, timeout=timeout_sec) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return json.loads(response.read().decode(charset))


def _run_http_json_health_verification(
    verification: Dict[str, Any],
    fetch_json: FetchJsonFn,
    timeout_sec: float,
) -> Dict[str, Any]:
    target_url = str(verification.get("target_url") or "")
    try:
        payload = fetch_json(target_url, timeout_sec)
    except HTTPError as exc:
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_unreachable",
            "observed_status": None,
            "missing_fields": [],
            "error_detail": f"http error: {exc.code}",
        }
    except URLError as exc:
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_unreachable",
            "observed_status": None,
            "missing_fields": [],
            "error_detail": f"url error: {exc.reason}",
        }
    except OSError as exc:
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_unreachable",
            "observed_status": None,
            "missing_fields": [],
            "error_detail": str(exc),
        }
    except Exception as exc:
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_invalid_payload",
            "observed_status": None,
            "missing_fields": [],
            "error_detail": str(exc),
        }

    if not isinstance(payload, dict):
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_invalid_payload",
            "observed_status": None,
            "missing_fields": [],
            "error_detail": "payload was not a JSON object",
        }

    observed_status = payload.get("status")
    expected_statuses = [str(item) for item in list(verification.get("expected_statuses") or [])]
    if observed_status not in expected_statuses:
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_invalid_status",
            "observed_status": observed_status,
            "missing_fields": [],
            "error_detail": f"expected status in {expected_statuses} but got {observed_status!r}",
        }

    missing_fields = [field for field in list(verification.get("expected_fields") or []) if field not in payload]
    if missing_fields:
        return {
            "verification_id": verification.get("verification_id"),
            "step_id": verification.get("step_id"),
            "command_id": verification.get("command_id"),
            "verification_kind": verification.get("verification_kind"),
            "target_url": target_url,
            "result_status": "failed_missing_fields",
            "observed_status": observed_status,
            "missing_fields": missing_fields,
            "error_detail": None,
        }

    return {
        "verification_id": verification.get("verification_id"),
        "step_id": verification.get("step_id"),
        "command_id": verification.get("command_id"),
        "verification_kind": verification.get("verification_kind"),
        "target_url": target_url,
        "result_status": "passed",
        "observed_status": observed_status,
        "missing_fields": [],
        "error_detail": None,
    }


def run_deployment_verification_once(
    deployment_verification_manifest: Dict[str, Any],
    fetch_json: Optional[FetchJsonFn] = None,
    timeout_sec: float = 2.0,
) -> Dict[str, Any]:
    active_fetch_json = fetch_json or _default_fetch_json
    verifications = list(deployment_verification_manifest.get("verifications") or [])
    step_manifest = list(deployment_verification_manifest.get("steps") or [])
    verification_by_step_id = {
        str(item.get("step_id")): item
        for item in verifications
        if item.get("step_id")
    }

    verification_results: List[Dict[str, Any]] = []
    step_results: List[Dict[str, Any]] = []
    passed_verification_count = 0
    failed_verification_count = 0
    skipped_manual_step_count = 0

    for step in step_manifest:
        step_id = str(step.get("step_id"))
        verification = verification_by_step_id.get(step_id)
        if verification is None:
            skipped_manual_step_count += 1
            step_results.append(
                {
                    "step_id": step_id,
                    "name": step.get("name"),
                    "result_status": str(step.get("verification_type") or "manual_optional"),
                    "verification_available": False,
                    "verification_target": step.get("verification_target"),
                    "observed_status": None,
                    "missing_fields": [],
                    "error_detail": None,
                }
            )
            continue

        kind = str(verification.get("verification_kind"))
        if kind == "http_json_health":
            result = _run_http_json_health_verification(verification, active_fetch_json, timeout_sec)
        else:
            result = {
                "verification_id": verification.get("verification_id"),
                "step_id": verification.get("step_id"),
                "command_id": verification.get("command_id"),
                "verification_kind": kind,
                "target_url": verification.get("target_url"),
                "result_status": "failed_unsupported_kind",
                "observed_status": None,
                "missing_fields": [],
                "error_detail": f"unsupported verification kind: {kind}",
            }

        verification_results.append(result)
        if result["result_status"] == "passed":
            passed_verification_count += 1
        else:
            failed_verification_count += 1

        step_results.append(
            {
                "step_id": step_id,
                "name": step.get("name"),
                "result_status": result["result_status"],
                "verification_available": True,
                "verification_target": result.get("target_url"),
                "observed_status": result.get("observed_status"),
                "missing_fields": list(result.get("missing_fields") or []),
                "error_detail": result.get("error_detail"),
            }
        )

    if failed_verification_count > 0:
        overall_result_status = "failed"
    elif verification_results:
        overall_result_status = "passed"
    else:
        overall_result_status = "manual_only"

    return {
        "profile_name": deployment_verification_manifest.get("profile_name"),
        "config_path": deployment_verification_manifest.get("config_path"),
        "overall_result_status": overall_result_status,
        "verification_result_count": len(verification_results),
        "passed_verification_count": passed_verification_count,
        "failed_verification_count": failed_verification_count,
        "skipped_manual_step_count": skipped_manual_step_count,
        "results": verification_results,
        "steps": step_results,
    }


def build_verification_result_summary(
    bringup_verification_sheet: Dict[str, Any],
    verification_run_result: Dict[str, Any],
) -> Dict[str, Any]:
    results_by_step_id = {
        str(item.get("step_id")): item
        for item in list(verification_run_result.get("steps") or [])
        if item.get("step_id")
    }

    summarized_steps: List[Dict[str, Any]] = []
    for step in list(bringup_verification_sheet.get("steps") or []):
        step_id = str(step.get("step_id"))
        result = results_by_step_id.get(step_id, {})
        summarized_steps.append(
            {
                "step_id": step_id,
                "order": step.get("order"),
                "name": step.get("name"),
                "status": step.get("status"),
                "required": bool(step.get("required")),
                "category": step.get("category"),
                "action_type": step.get("action_type"),
                "display_command": step.get("display_command"),
                "verification_available": bool(step.get("verification_available")),
                "verification_target": step.get("verification_target"),
                "verification_kind": step.get("verification_kind"),
                "expected_statuses": list(step.get("expected_statuses") or []),
                "result_status": result.get("result_status"),
                "observed_status": result.get("observed_status"),
                "missing_fields": list(result.get("missing_fields") or []),
                "error_detail": result.get("error_detail"),
                "blocking_reasons": list(step.get("blocking_reasons") or []),
            }
        )

    return {
        "profile_name": verification_run_result.get("profile_name"),
        "config_path": verification_run_result.get("config_path"),
        "overall_status": bringup_verification_sheet.get("overall_status"),
        "overall_result_status": verification_run_result.get("overall_result_status"),
        "passed_verification_count": verification_run_result.get("passed_verification_count", 0),
        "failed_verification_count": verification_run_result.get("failed_verification_count", 0),
        "skipped_manual_step_count": verification_run_result.get("skipped_manual_step_count", 0),
        "verification_result_count": verification_run_result.get("verification_result_count", 0),
        "blocking_reasons": list(bringup_verification_sheet.get("blocking_reasons") or []),
        "steps": summarized_steps,
        "step_count": len(summarized_steps),
    }
