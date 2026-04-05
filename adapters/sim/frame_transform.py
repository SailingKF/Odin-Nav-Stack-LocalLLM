from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


@dataclass(frozen=True)
class SimFrameTransformConfig:
    raw_x_field: str = "sim_x"
    raw_y_field: str = "sim_y"
    swap_axes: bool = False
    flip_x: bool = False
    flip_y: bool = False
    scale: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SimFrameTransformConfig":
        return cls(
            raw_x_field=str(payload.get("raw_x_field", "sim_x")),
            raw_y_field=str(payload.get("raw_y_field", "sim_y")),
            swap_axes=bool(payload.get("swap_axes", False)),
            flip_x=bool(payload.get("flip_x", False)),
            flip_y=bool(payload.get("flip_y", False)),
            scale=float(payload.get("scale", 1.0)),
            offset_x=float(payload.get("offset_x", 0.0)),
            offset_y=float(payload.get("offset_y", 0.0)),
        )


def normalize_raw_pose_payload(payload: Dict[str, Any], config: SimFrameTransformConfig) -> Dict[str, Any]:
    raw_x = float(payload[config.raw_x_field])
    raw_y = float(payload[config.raw_y_field])

    source_x = raw_y if config.swap_axes else raw_x
    source_y = raw_x if config.swap_axes else raw_y

    if config.flip_x:
        source_x *= -1.0
    if config.flip_y:
        source_y *= -1.0

    normalized = {
        "x": source_x * config.scale + config.offset_x,
        "y": source_y * config.scale + config.offset_y,
        "label": payload.get("label"),
    }
    return normalized


def normalize_raw_pose_payloads(
    payloads: Iterable[Dict[str, Any]],
    config: SimFrameTransformConfig,
) -> List[Dict[str, Any]]:
    return [normalize_raw_pose_payload(payload, config) for payload in payloads]
