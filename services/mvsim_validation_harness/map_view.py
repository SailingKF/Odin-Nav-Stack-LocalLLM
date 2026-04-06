from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.poi.loader import load_pois, load_route
from core.poi.store import InMemoryPoiStore


def _resolve_repo_path(path_value: Optional[str], repo_root: Path) -> Optional[Path]:
    if not path_value:
        return None
    path = Path(str(path_value))
    return path if path.is_absolute() else repo_root / path


def _coerce_pose(payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return None
    if payload.get("x") is None or payload.get("y") is None:
        return None
    try:
        return {
            "x": float(payload["x"]),
            "y": float(payload["y"]),
            "label": payload.get("label"),
        }
    except (TypeError, ValueError):
        return None


def _load_route_bundle(
    repo_root: Path,
    config: Dict[str, Any],
    latest_report: Optional[Dict[str, Any]],
) -> Tuple[Optional[Path], Optional[Path], Optional[List[Any]], Optional[str]]:
    report_identity = dict((latest_report or {}).get("validation_asset_identity") or {})
    route_path = _resolve_repo_path(
        str(config.get("current_route_file") or report_identity.get("route_file") or ""),
        repo_root,
    )
    poi_path = _resolve_repo_path(
        str(config.get("current_poi_file") or report_identity.get("poi_file") or ""),
        repo_root,
    )
    if route_path is None or poi_path is None:
        return route_path, poi_path, None, "route_or_poi_file_missing_from_config"
    if not route_path.exists() or not poi_path.exists():
        missing_bits: List[str] = []
        if not route_path.exists():
            missing_bits.append(f"route file missing: {route_path}")
        if not poi_path.exists():
            missing_bits.append(f"poi file missing: {poi_path}")
        return route_path, poi_path, None, "; ".join(missing_bits)

    route = load_route(str(route_path))
    pois = load_pois(str(poi_path))
    ordered_pois = InMemoryPoiStore(pois).route_pois(route)
    return route_path, poi_path, ordered_pois, None


def _extract_progress(
    latest_report: Optional[Dict[str, Any]],
    last_validation_result: Optional[Dict[str, Any]],
) -> Tuple[List[str], List[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    report = dict(latest_report or {})
    validation = dict(last_validation_result or {})
    live_summary = dict(validation.get("live_validation_summary") or {})
    api_session = dict(validation.get("api_latest_session") or {})

    triggered = list(live_summary.get("recent_triggered_spot_ids") or report.get("recent_triggered_spot_ids") or [])
    narrated = list(live_summary.get("recent_narrated_spot_ids") or report.get("recent_narrated_spot_ids") or [])

    if not triggered:
        triggered = [
            str(item.get("spot_id"))
            for item in list(api_session.get("recent_poi_triggers") or [])
            if item.get("spot_id")
        ]
    if not narrated:
        narrated = [
            str(item.get("spot_id"))
            for item in list(api_session.get("recent_narrations") or [])
            if item.get("spot_id")
        ]

    if live_summary.get("recent_triggered_spot_ids"):
        progress_source = "last_validation_result.live_validation_summary"
    elif report.get("recent_triggered_spot_ids") or report.get("recent_narrated_spot_ids"):
        progress_source = "latest_report"
    elif api_session.get("recent_poi_triggers") or api_session.get("recent_narrations"):
        progress_source = "last_validation_result.api_latest_session"
    else:
        progress_source = None

    latest_spot_name = (
        api_session.get("latest_spot_name")
        or api_session.get("latest_narrated_spot_name")
        or api_session.get("latest_triggered_spot_name")
        or report.get("latest_spot_name")
        or live_summary.get("validated_spot_name")
    )
    latest_spot_id = (
        api_session.get("latest_spot_id")
        or api_session.get("latest_narrated_spot_id")
        or api_session.get("latest_triggered_spot_id")
        or report.get("latest_spot_id")
        or live_summary.get("validated_spot_id")
        or (narrated[-1] if narrated else None)
        or (triggered[-1] if triggered else None)
    )
    latest_narration_text = (
        api_session.get("latest_narration_text")
        or report.get("latest_narration_text")
        or live_summary.get("validated_narration_text")
    )
    return triggered, narrated, latest_spot_id, latest_spot_name, latest_narration_text, progress_source


def _extract_pose(
    current_api_state: Optional[Dict[str, Any]],
    latest_report: Optional[Dict[str, Any]],
    last_validation_result: Optional[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    report = dict(latest_report or {})
    validation = dict(last_validation_result or {})
    candidates = [
        ("api_state", _coerce_pose(dict(current_api_state or {}).get("last_pose"))),
        ("last_validation_result.api_state", _coerce_pose(dict(validation.get("api_state") or {}).get("last_pose"))),
        (
            "last_validation_result.sim_ingress_state",
            _coerce_pose(dict(validation.get("sim_ingress_state") or {}).get("last_pose")),
        ),
        (
            "last_validation_result.live_validation_summary",
            _coerce_pose(dict(validation.get("live_validation_summary") or {}).get("last_pose")),
        ),
        ("latest_report", _coerce_pose(report.get("latest_pose"))),
    ]
    for source, pose in candidates:
        if pose is not None:
            return pose, source
    return None, None


def _extract_active_spot(
    current_api_state: Optional[Dict[str, Any]],
    last_validation_result: Optional[Dict[str, Any]],
) -> Tuple[Optional[str], Optional[str]]:
    current_state = dict(current_api_state or {})
    validation = dict(last_validation_result or {})
    api_state = dict(validation.get("api_state") or {})
    sim_state = dict(validation.get("sim_ingress_state") or {})
    return (
        current_state.get("active_spot_id") or api_state.get("active_spot_id") or sim_state.get("active_spot_id"),
        current_state.get("active_spot_name") or api_state.get("active_spot_name") or sim_state.get("active_spot_name"),
    )


def _normalize_points(
    ordered_pois: List[Any],
    pose: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    world_points = [(float(poi.x), float(poi.y)) for poi in ordered_pois]
    if pose is not None:
        world_points.append((float(pose["x"]), float(pose["y"])))

    min_x = min(point[0] for point in world_points)
    max_x = max(point[0] for point in world_points)
    min_y = min(point[1] for point in world_points)
    max_y = max(point[1] for point in world_points)

    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    padding_ratio = 0.12
    padded_min_x = min_x - (span_x * padding_ratio)
    padded_max_x = max_x + (span_x * padding_ratio)
    padded_min_y = min_y - (span_y * padding_ratio)
    padded_max_y = max_y + (span_y * padding_ratio)

    padded_span_x = max(padded_max_x - padded_min_x, 1.0)
    padded_span_y = max(padded_max_y - padded_min_y, 1.0)
    view_width = 100.0
    view_height = 64.0
    view_padding = 8.0
    inner_width = view_width - (view_padding * 2.0)
    inner_height = view_height - (view_padding * 2.0)

    def _screen_point(x_value: float, y_value: float) -> Dict[str, float]:
        x_ratio = (x_value - padded_min_x) / padded_span_x
        y_ratio = (y_value - padded_min_y) / padded_span_y
        return {
            "x": round(view_padding + (x_ratio * inner_width), 2),
            "y": round(view_height - view_padding - (y_ratio * inner_height), 2),
        }

    return {
        "view_box": {"width": view_width, "height": view_height, "padding": view_padding},
        "world_bounds": {
            "min_x": round(padded_min_x, 3),
            "max_x": round(padded_max_x, 3),
            "min_y": round(padded_min_y, 3),
            "max_y": round(padded_max_y, 3),
        },
        "normalization": {
            "x_span_world": round(padded_span_x, 3),
            "y_span_world": round(padded_span_y, 3),
            "screen_padding": view_padding,
            "screen_inner_width": inner_width,
            "screen_inner_height": inner_height,
            "screen_y_axis": "inverted_from_world_positive_up",
        },
        "to_screen": _screen_point,
    }


def build_validation_map_view(
    *,
    config: Dict[str, Any],
    repo_root: Path,
    latest_report: Optional[Dict[str, Any]],
    last_validation_result: Optional[Dict[str, Any]],
    current_api_state: Optional[Dict[str, Any]] = None,
    selected_validation_mode: Optional[str] = None,
) -> Dict[str, Any]:
    route_path, poi_path, ordered_pois, load_error = _load_route_bundle(repo_root, config, latest_report)
    if ordered_pois is None:
        return {
            "status": "blocked_assets_missing",
            "rendering_strategy": "schematic_svg_topdown_view",
            "active_validation_mode": selected_validation_mode,
            "detail": load_error,
            "data_sources": {
                "route_file": None if route_path is None else str(route_path),
                "poi_file": None if poi_path is None else str(poi_path),
                "pose_source": None,
                "progress_source": None,
            },
            "poi_count": 0,
            "pose": None,
            "pose_available": False,
            "route_polyline": [],
            "poi_markers": [],
        }

    triggered_spot_ids, narrated_spot_ids, latest_spot_id, latest_spot_name, latest_narration_text, progress_source = _extract_progress(
        latest_report,
        last_validation_result,
    )
    pose, pose_source = _extract_pose(current_api_state, latest_report, last_validation_result)
    active_spot_id, active_spot_name = _extract_active_spot(current_api_state, last_validation_result)
    normalization_bundle = _normalize_points(ordered_pois, pose)
    to_screen = normalization_bundle.pop("to_screen")
    triggered_set = set(triggered_spot_ids)
    narrated_set = set(narrated_spot_ids)
    poi_name_by_id = {poi.spot_id: poi.name for poi in ordered_pois}
    if latest_spot_name is None and latest_spot_id is not None:
        latest_spot_name = poi_name_by_id.get(str(latest_spot_id))

    poi_markers: List[Dict[str, Any]] = []
    route_polyline: List[Dict[str, Any]] = []
    for order, poi in enumerate(ordered_pois, start=1):
        screen = to_screen(float(poi.x), float(poi.y))
        is_active = bool(active_spot_id == poi.spot_id or (active_spot_name and active_spot_name == poi.name))
        is_latest = bool((latest_spot_id and latest_spot_id == poi.spot_id) or (latest_spot_name and latest_spot_name == poi.name))
        if is_active:
            visual_status = "active"
        elif poi.spot_id in narrated_set:
            visual_status = "narrated"
        elif poi.spot_id in triggered_set:
            visual_status = "triggered"
        else:
            visual_status = "pending"
        poi_markers.append(
            {
                "spot_id": poi.spot_id,
                "spot_name": poi.name,
                "order_index": order,
                "world": {
                    "x": round(float(poi.x), 3),
                    "y": round(float(poi.y), 3),
                    "trigger_radius": round(float(poi.trigger_radius), 3),
                },
                "screen": screen,
                "is_triggered": poi.spot_id in triggered_set,
                "is_narrated": poi.spot_id in narrated_set,
                "is_active": is_active,
                "is_latest": is_latest,
                "visual_status": visual_status,
            }
        )
        route_polyline.append({"spot_id": poi.spot_id, "x": screen["x"], "y": screen["y"]})

    pose_marker = None
    if pose is not None:
        pose_marker = {
            "world": {
                "x": round(float(pose["x"]), 3),
                "y": round(float(pose["y"]), 3),
                "label": pose.get("label"),
            },
            "screen": to_screen(float(pose["x"]), float(pose["y"])),
        }

    return {
        "status": "ready" if pose_marker is not None else "ready_without_pose",
        "rendering_strategy": "schematic_svg_topdown_view",
        "active_validation_mode": selected_validation_mode
        or dict(last_validation_result or {}).get("validation_mode")
        or dict(latest_report or {}).get("validation_mode"),
        "truthfulness": {
            "poi_state_is_truthful": True,
            "pose_is_truthful": pose_marker is not None,
        },
        "data_sources": {
            "route_file": str(route_path),
            "poi_file": str(poi_path),
            "pose_source": pose_source,
            "progress_source": progress_source,
        },
        "pose": pose_marker,
        "pose_available": pose_marker is not None,
        "active_spot_id": active_spot_id,
        "active_spot_name": active_spot_name,
        "latest_spot_id": latest_spot_id,
        "latest_spot_name": latest_spot_name,
        "latest_narration_text": latest_narration_text,
        "recent_triggered_spot_ids": triggered_spot_ids,
        "recent_narrated_spot_ids": narrated_spot_ids,
        "poi_count": len(poi_markers),
        "poi_markers": poi_markers,
        "route_polyline": route_polyline,
        **normalization_bundle,
    }
