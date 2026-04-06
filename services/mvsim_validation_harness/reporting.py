import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_copy(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return json.loads(json.dumps(payload or {}))


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
        "report_path": report.get("report_path"),
    }


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
    if comparison_available:
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
        "differences": differences,
    }


def build_validation_report(
    *,
    validation_result: Dict[str, Any],
    config_path: Path,
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
