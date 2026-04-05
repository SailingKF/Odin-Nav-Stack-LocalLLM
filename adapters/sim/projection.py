from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


def _get_path_value(payload: Dict[str, Any], path: str) -> Any:
    current: Any = payload
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Missing path '{path}' in payload.")
        current = current[part]
    return current


@dataclass(frozen=True)
class SimPoseProjectionConfig:
    projected_x_field: str = "sim_x"
    projected_y_field: str = "sim_y"
    planar_x_source_path: str = "position.x"
    planar_y_source_path: str = "position.y"
    planar_z_source_path: str = "position.z"
    yaw_source_path: Optional[str] = "orientation.yaw_rad"
    label_field: str = "label"

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SimPoseProjectionConfig":
        yaw_source_path = payload.get("yaw_source_path", "orientation.yaw_rad")
        return cls(
            projected_x_field=str(payload.get("projected_x_field", "sim_x")),
            projected_y_field=str(payload.get("projected_y_field", "sim_y")),
            planar_x_source_path=str(payload.get("planar_x_source_path", "position.x")),
            planar_y_source_path=str(payload.get("planar_y_source_path", "position.y")),
            planar_z_source_path=str(payload.get("planar_z_source_path", "position.z")),
            yaw_source_path=None if yaw_source_path in (None, "") else str(yaw_source_path),
            label_field=str(payload.get("label_field", "label")),
        )


def project_richer_pose_payload(payload: Dict[str, Any], config: SimPoseProjectionConfig) -> Dict[str, Any]:
    projected = {
        config.projected_x_field: float(_get_path_value(payload, config.planar_x_source_path)),
        config.projected_y_field: float(_get_path_value(payload, config.planar_y_source_path)),
        "label": payload.get(config.label_field),
    }

    try:
        projected["source_position_z"] = float(_get_path_value(payload, config.planar_z_source_path))
    except (KeyError, TypeError, ValueError):
        projected["source_position_z"] = None

    if config.yaw_source_path:
        try:
            projected["source_yaw"] = float(_get_path_value(payload, config.yaw_source_path))
        except (KeyError, TypeError, ValueError):
            projected["source_yaw"] = None
    else:
        projected["source_yaw"] = None

    return projected


def project_richer_pose_payloads(
    payloads: Iterable[Dict[str, Any]],
    config: SimPoseProjectionConfig,
) -> List[Dict[str, Any]]:
    return [project_richer_pose_payload(payload, config) for payload in payloads]
