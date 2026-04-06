import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


IDENTITY_VERSION = "validation_asset_identity.v1"
COMPARISON_EXPORT_VERSION = "latest_comparison_export.v1"
_REQUIRED_IDENTITY_FIELDS = (
    "route_file",
    "poi_file",
    "world_file",
    "vehicle_name",
    "alignment_strategy",
    "motion_strategy",
)
_WARNING_IDENTITY_FIELDS = (
    "config_name",
    "config_path",
)


def _utc_timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_copy(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return json.loads(json.dumps(payload or {}))


def _string_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _compact_identity_view(identity: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not identity:
        return None
    return {
        "identity_version": identity.get("identity_version"),
        "validation_mode": identity.get("validation_mode"),
        "config_name": identity.get("config_name"),
        "world_file": identity.get("world_file"),
        "vehicle_name": identity.get("vehicle_name"),
        "route_file": identity.get("route_file"),
        "poi_file": identity.get("poi_file"),
        "alignment_strategy": identity.get("alignment_strategy"),
        "motion_strategy": identity.get("motion_strategy"),
    }


def _build_validation_asset_identity(
    validation_result: Dict[str, Any],
    config_path: Path,
    config_payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    config = _json_copy(config_payload)
    mvsim_integration = dict(config.get("mvsim_integration") or {})
    live_alignment = dict(mvsim_integration.get("live_validation_alignment") or {})
    return {
        "identity_version": IDENTITY_VERSION,
        "validation_mode": _string_or_none(validation_result.get("validation_mode")),
        "mvsim_mode": _string_or_none(validation_result.get("mvsim_mode")),
        "config_name": config_path.name,
        "config_path": str(config_path),
        "route_file": _string_or_none(config.get("current_route_file")),
        "poi_file": _string_or_none(config.get("current_poi_file")),
        "world_file": _string_or_none(mvsim_integration.get("world_file")),
        "vehicle_name": _string_or_none(mvsim_integration.get("vehicle_name")),
        "alignment_strategy": _string_or_none(live_alignment.get("strategy")),
        "motion_strategy": _string_or_none(live_alignment.get("motion_strategy")),
        "target_spot_id": _string_or_none(live_alignment.get("target_spot_id")),
        "second_target_spot_id": _string_or_none(live_alignment.get("second_target_spot_id")),
    }


def _compare_validation_asset_identity(
    live_identity: Optional[Dict[str, Any]],
    compatibility_identity: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if not live_identity or not compatibility_identity:
        reasons = []
        if not live_identity:
            reasons.append("live_runtime report is missing validation_asset_identity")
        if not compatibility_identity:
            reasons.append("compatibility_shim report is missing validation_asset_identity")
        return {
            "comparability_status": "not_directly_comparable",
            "guardrail_reasons": reasons,
            "critical_mismatches": ["validation_asset_identity_missing"],
            "warnings": [],
            "checked_identity_fields": [],
        }

    checked_fields: List[Dict[str, Any]] = []
    critical_mismatches: List[str] = []
    warnings: List[str] = []
    guardrail_reasons: List[str] = []

    for field_name in _REQUIRED_IDENTITY_FIELDS + _WARNING_IDENTITY_FIELDS:
        live_value = _string_or_none(live_identity.get(field_name))
        compatibility_value = _string_or_none(compatibility_identity.get(field_name))
        if live_value and compatibility_value:
            result = "match" if live_value == compatibility_value else "mismatch"
        elif live_value or compatibility_value:
            result = "missing_on_one_side"
        else:
            result = "missing_on_both_sides"

        checked_fields.append(
            {
                "field": field_name,
                "live_runtime": live_value,
                "compatibility_shim": compatibility_value,
                "result": result,
            }
        )

        if field_name in _REQUIRED_IDENTITY_FIELDS:
            if result == "mismatch":
                critical_mismatches.append(field_name)
                guardrail_reasons.append(
                    f"{field_name} differs: live_runtime='{live_value}' vs compatibility_shim='{compatibility_value}'"
                )
            elif result in {"missing_on_one_side", "missing_on_both_sides"}:
                warnings.append(field_name)
                guardrail_reasons.append(
                    f"{field_name} is incomplete across the two reports"
                )
        elif result == "mismatch":
            warnings.append(field_name)
            guardrail_reasons.append(
                f"{field_name} differs but does not block direct asset comparison"
            )
        elif result in {"missing_on_one_side", "missing_on_both_sides"}:
            warnings.append(field_name)
            guardrail_reasons.append(
                f"{field_name} is missing in at least one report"
            )

    if critical_mismatches:
        comparability_status = "not_directly_comparable"
    elif warnings:
        comparability_status = "comparable_with_warnings"
    else:
        comparability_status = "comparable"
        guardrail_reasons.append("required validation assets match across the latest live and compatibility reports")

    return {
        "comparability_status": comparability_status,
        "guardrail_reasons": guardrail_reasons,
        "critical_mismatches": critical_mismatches,
        "warnings": warnings,
        "checked_identity_fields": checked_fields,
    }


def _compact_report_view(report: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not report:
        return None
    return {
        "report_id": report.get("report_id"),
        "created_at": report.get("created_at"),
        "status": report.get("status"),
        "passed": report.get("passed"),
        "validation_mode": report.get("validation_mode"),
        "config_name": report.get("config_name"),
        "route_completed": report.get("route_completed"),
        "live_first_poi_hit_occurred": report.get("live_first_poi_hit_occurred"),
        "live_second_poi_hit_occurred": report.get("live_second_poi_hit_occurred"),
        "live_second_narration_occurred": report.get("live_second_narration_occurred"),
        "latest_spot_name": report.get("latest_spot_name"),
        "latest_narration_text": report.get("latest_narration_text"),
        "recent_triggered_spot_ids": list(report.get("recent_triggered_spot_ids") or []),
        "recent_narrated_spot_ids": list(report.get("recent_narrated_spot_ids") or []),
        "validation_asset_identity": _compact_identity_view(report.get("validation_asset_identity")),
        "report_path": report.get("report_path"),
    }


def _markdown_value(value: Any) -> str:
    if value is None or value == "":
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "N/A"
    return str(value)


def _markdown_identity_summary(report: Dict[str, Any]) -> str:
    identity = _compact_identity_view(report.get("validation_asset_identity"))
    if not identity:
        return "N/A"
    pairs = [
        f"world={_markdown_value(identity.get('world_file'))}",
        f"vehicle={_markdown_value(identity.get('vehicle_name'))}",
        f"route={_markdown_value(identity.get('route_file'))}",
        f"poi={_markdown_value(identity.get('poi_file'))}",
        f"align={_markdown_value(identity.get('alignment_strategy'))}",
        f"motion={_markdown_value(identity.get('motion_strategy'))}",
    ]
    return " | ".join(pairs)


def build_latest_comparison_export(
    comparison_summary: Dict[str, Any],
    *,
    harness_url: str,
) -> Dict[str, Any]:
    export_id = f"{_utc_timestamp_slug()}-latest_comparison_export"
    return {
        "export_id": export_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "export_kind": "latest_live_vs_compatibility_comparison",
        "export_version": COMPARISON_EXPORT_VERSION,
        "harness_url": harness_url,
        "comparison_status": comparison_summary.get("status"),
        "comparison_available": bool(comparison_summary.get("comparison_available")),
        "comparability_status": comparison_summary.get("comparability_status"),
        "missing_modes": list(comparison_summary.get("missing_modes") or []),
        "guardrail_reasons": list(comparison_summary.get("guardrail_reasons") or []),
        "live_runtime_report": _json_copy(comparison_summary.get("live_runtime_report"))
        if comparison_summary.get("live_runtime_report") is not None
        else None,
        "compatibility_shim_report": _json_copy(comparison_summary.get("compatibility_shim_report"))
        if comparison_summary.get("compatibility_shim_report") is not None
        else None,
        "differences": _json_copy(comparison_summary.get("differences")),
    }


def build_human_readable_comparison_export(export_payload: Dict[str, Any]) -> str:
    live_report = dict(export_payload.get("live_runtime_report") or {})
    compatibility_report = dict(export_payload.get("compatibility_shim_report") or {})
    lines = [
        "# Latest Comparison Export",
        "",
        f"- Export ID: {_markdown_value(export_payload.get('export_id'))}",
        f"- Created At: {_markdown_value(export_payload.get('created_at'))}",
        f"- Comparison Status: {_markdown_value(export_payload.get('comparison_status'))}",
        f"- Comparability Status: {_markdown_value(export_payload.get('comparability_status'))}",
        f"- Missing Modes: {_markdown_value(export_payload.get('missing_modes'))}",
        "",
        "## Guardrail Reasons",
    ]
    reasons = list(export_payload.get("guardrail_reasons") or [])
    if reasons:
        lines.extend([f"- {reason}" for reason in reasons])
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Live Runtime Report",
            f"- Report ID: {_markdown_value(live_report.get('report_id'))}",
            f"- Status: {_markdown_value(live_report.get('status'))}",
            f"- Passed: {_markdown_value(live_report.get('passed'))}",
            f"- Route Completed: {_markdown_value(live_report.get('route_completed'))}",
            f"- Triggered Spots: {_markdown_value(live_report.get('recent_triggered_spot_ids'))}",
            f"- Narrated Spots: {_markdown_value(live_report.get('recent_narrated_spot_ids'))}",
            f"- Identity: {_markdown_identity_summary(live_report)}",
            "",
            "## Compatibility Shim Report",
            f"- Report ID: {_markdown_value(compatibility_report.get('report_id'))}",
            f"- Status: {_markdown_value(compatibility_report.get('status'))}",
            f"- Passed: {_markdown_value(compatibility_report.get('passed'))}",
            f"- Route Completed: {_markdown_value(compatibility_report.get('route_completed'))}",
            f"- Triggered Spots: {_markdown_value(compatibility_report.get('recent_triggered_spot_ids'))}",
            f"- Narrated Spots: {_markdown_value(compatibility_report.get('recent_narrated_spot_ids'))}",
            f"- Identity: {_markdown_identity_summary(compatibility_report)}",
            "",
            "## Compared Outcome Flags",
        ]
    )
    differences = dict(export_payload.get("differences") or {})
    if differences:
        lines.extend([f"- {key}: {_markdown_value(value)}" for key, value in differences.items()])
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def build_latest_mode_comparison(
    latest_live_report: Optional[Dict[str, Any]],
    latest_compatibility_report: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    missing_modes: List[str] = []
    if not latest_live_report:
        missing_modes.append("live_runtime")
    if not latest_compatibility_report:
        missing_modes.append("compatibility_shim")

    comparison_available = not missing_modes
    status = "ready" if comparison_available else "missing_reports"

    differences: Dict[str, Any] = {}
    identity_guardrails: Dict[str, Any] = {
        "comparability_status": "not_directly_comparable" if comparison_available else "unknown",
        "guardrail_reasons": [] if comparison_available else ["cannot compare reports until both validation modes exist"],
        "critical_mismatches": [],
        "warnings": [],
        "checked_identity_fields": [],
    }
    if comparison_available:
        identity_guardrails = _compare_validation_asset_identity(
            latest_live_report.get("validation_asset_identity"),
            latest_compatibility_report.get("validation_asset_identity"),
        )
        differences = {
            "passed_equal": bool(latest_live_report.get("passed")) == bool(latest_compatibility_report.get("passed")),
            "route_completed_equal": bool(latest_live_report.get("route_completed")) == bool(latest_compatibility_report.get("route_completed")),
            "live_first_poi_hit_equal": bool(latest_live_report.get("live_first_poi_hit_occurred")) == bool(
                latest_compatibility_report.get("live_first_poi_hit_occurred")
            ),
            "live_second_poi_hit_equal": bool(latest_live_report.get("live_second_poi_hit_occurred")) == bool(
                latest_compatibility_report.get("live_second_poi_hit_occurred")
            ),
            "triggered_spots_equal": list(latest_live_report.get("recent_triggered_spot_ids") or [])
            == list(latest_compatibility_report.get("recent_triggered_spot_ids") or []),
            "narrated_spots_equal": list(latest_live_report.get("recent_narrated_spot_ids") or [])
            == list(latest_compatibility_report.get("recent_narrated_spot_ids") or []),
            "latest_spot_name_equal": latest_live_report.get("latest_spot_name") == latest_compatibility_report.get("latest_spot_name"),
        }

    return {
        "status": status,
        "comparison_available": comparison_available,
        "missing_modes": missing_modes,
        "live_runtime_report": _compact_report_view(latest_live_report),
        "compatibility_shim_report": _compact_report_view(latest_compatibility_report),
        "comparability_status": identity_guardrails.get("comparability_status"),
        "guardrail_reasons": list(identity_guardrails.get("guardrail_reasons") or []),
        "identity_guardrails": identity_guardrails,
        "differences": differences,
    }


def build_validation_report(
    *,
    validation_result: Dict[str, Any],
    config_path: Path,
    config_payload: Optional[Dict[str, Any]] = None,
    harness_url: str,
    debug_url: str,
) -> Dict[str, Any]:
    live_summary = _json_copy(validation_result.get("live_validation_summary"))
    api_session = _json_copy(validation_result.get("api_latest_session"))
    mvsim_source = _json_copy(validation_result.get("mvsim_source"))
    service_checks = _json_copy(validation_result.get("service_checks"))
    bridge_result = _json_copy(validation_result.get("bridge_result"))
    final_state = _json_copy(validation_result.get("sim_ingress_state") or bridge_result.get("final_state"))

    recent_triggered_spot_ids = list(live_summary.get("recent_triggered_spot_ids") or [])
    recent_narrated_spot_ids = list(live_summary.get("recent_narrated_spot_ids") or [])

    if not recent_triggered_spot_ids:
        recent_triggered_spot_ids = [
            str(item.get("spot_id"))
            for item in list(api_session.get("recent_poi_triggers") or [])
            if item.get("spot_id")
        ]
    if not recent_narrated_spot_ids:
        recent_narrated_spot_ids = [
            str(item.get("spot_id"))
            for item in list(api_session.get("recent_narrations") or [])
            if item.get("spot_id")
        ]

    report_id = f"{_utc_timestamp_slug()}-{validation_result.get('validation_mode', 'unknown')}"
    validation_asset_identity = _build_validation_asset_identity(
        validation_result=validation_result,
        config_path=config_path,
        config_payload=config_payload,
    )
    return {
        "report_id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": validation_result.get("status"),
        "validation_mode": validation_result.get("validation_mode"),
        "mvsim_mode": validation_result.get("mvsim_mode"),
        "config_path": str(config_path),
        "config_name": config_path.name,
        "harness_url": harness_url,
        "debug_url": debug_url,
        "passed": validation_result.get("status") == "passed",
        "session_id": api_session.get("session_id"),
        "latest_spot_name": api_session.get("latest_spot_name"),
        "latest_narration_text": api_session.get("latest_narration_text"),
        "route_completed": bool(final_state.get("route_completed")),
        "live_first_poi_hit_occurred": bool(live_summary.get("live_first_poi_hit_occurred")),
        "live_second_poi_hit_occurred": bool(live_summary.get("live_second_poi_hit_occurred")),
        "live_second_narration_occurred": bool(live_summary.get("live_second_narration_occurred")),
        "recent_triggered_spot_ids": recent_triggered_spot_ids,
        "recent_narrated_spot_ids": recent_narrated_spot_ids,
        "validation_asset_identity": validation_asset_identity,
        "mvsim_source_kind": mvsim_source.get("source_kind"),
        "proxy_target": api_session.get("proxy_target") or validation_result.get("api_state", {}).get("proxy_target"),
        "service_targets": {
            "sim_pose_ingress": dict(service_checks.get("sim_pose_ingress") or {}).get("target_url"),
            "api_server": dict(service_checks.get("api_server") or {}).get("target_url"),
            "debug_page": dict(service_checks.get("debug_page") or {}).get("target_url") or debug_url,
        },
        "detail": validation_result.get("detail"),
    }


class ValidationReportStore:
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def _report_path(self, report_id: str) -> Path:
        return self._root_dir / f"{report_id}.json"

    def write_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        report_id = str(report["report_id"])
        path = self._report_path(report_id)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        persisted = dict(report)
        persisted["report_path"] = str(path)
        return persisted

    def _load_report(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["report_path"] = str(path)
        return payload

    def read_latest_report(self) -> Optional[Dict[str, Any]]:
        files = sorted(self._root_dir.glob("*.json"))
        if not files:
            return None
        return self._load_report(files[-1])

    def read_recent_reports(self, limit: int = 5) -> List[Dict[str, Any]]:
        files = sorted(self._root_dir.glob("*.json"), reverse=True)[:limit]
        return [self._load_report(path) for path in files]

    def read_latest_report_for_mode(self, validation_mode: str) -> Optional[Dict[str, Any]]:
        for report in self.read_recent_reports(limit=100):
            if report.get("validation_mode") == validation_mode:
                return report
        return None


class ComparisonExportStore:
    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def _export_path(self, export_id: str) -> Path:
        return self._root_dir / f"{export_id}.json"

    def _human_export_path(self, export_id: str) -> Path:
        return self._root_dir / f"{export_id}.md"

    def write_export(self, export_payload: Dict[str, Any], human_readable_text: Optional[str] = None) -> Dict[str, Any]:
        export_id = str(export_payload["export_id"])
        path = self._export_path(export_id)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(export_payload, handle, ensure_ascii=False, indent=2)
        if human_readable_text is not None:
            self._human_export_path(export_id).write_text(human_readable_text, encoding="utf-8")
        persisted = dict(export_payload)
        persisted["export_path"] = str(path)
        human_path = self._human_export_path(export_id)
        if human_path.exists():
            persisted["human_readable_export_path"] = str(human_path)
        return persisted

    def _load_export(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["export_path"] = str(path)
        human_path = self._human_export_path(path.stem)
        if human_path.exists():
            payload["human_readable_export_path"] = str(human_path)
        return payload

    def read_latest_export(self) -> Optional[Dict[str, Any]]:
        files = sorted(self._root_dir.glob("*.json"))
        if not files:
            return None
        return self._load_export(files[-1])

    def read_latest_human_readable_export(self) -> Optional[Dict[str, Any]]:
        latest = self.read_latest_export()
        if not latest:
            return None
        human_path = latest.get("human_readable_export_path")
        if not human_path:
            return None
        path = Path(human_path)
        return {
            "export_id": latest.get("export_id"),
            "human_readable_export_path": str(path),
            "content": path.read_text(encoding="utf-8"),
        }
