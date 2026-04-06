import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utc_timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _json_copy(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return json.loads(json.dumps(payload or {}))


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
