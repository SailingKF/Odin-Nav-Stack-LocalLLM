from pathlib import Path
from typing import Dict, Iterator, List

import yaml

from services.sim_publisher_bridge.source import SimulatorPoseSource


def mvsim_observation_to_richer_payload(observation: Dict) -> Dict:
    pose2d = dict(observation.get("pose2d") or {})
    velocity2d = dict(observation.get("velocity2d") or {})
    label = observation.get("label") or observation.get("note") or observation.get("vehicle")

    return {
        "label": str(label) if label is not None else None,
        "position": {
            "x": float(pose2d.get("x_m", 0.0)),
            "y": float(pose2d.get("y_m", 0.0)),
            "z": 0.0,
        },
        "orientation": {
            "yaw_rad": float(pose2d.get("yaw_rad", 0.0)),
        },
        "twist": {
            "vx_mps": float(velocity2d.get("vx_mps", 0.0)),
            "vy_mps": float(velocity2d.get("vy_mps", 0.0)),
            "yaw_rate_radps": float(velocity2d.get("yaw_rate_radps", 0.0)),
        },
        "mvsim": {
            "world_name": observation.get("world_name"),
            "vehicle_name": observation.get("vehicle"),
            "sim_time_sec": observation.get("sim_time_sec"),
            "frame_id": observation.get("frame_id", "map"),
        },
    }


class YamlFileMVSimPoseSource(SimulatorPoseSource):
    def __init__(self, path: Path):
        self._path = Path(path)

    def iter_payloads(self) -> Iterator[Dict]:
        with self._path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}

        world_name = payload.get("world_name")
        default_vehicle = payload.get("vehicle_name")
        observations: List[Dict] = list(payload.get("observations") or [])
        for item in observations:
            observation = dict(item)
            observation.setdefault("world_name", world_name)
            observation.setdefault("vehicle", default_vehicle)
            yield mvsim_observation_to_richer_payload(observation)


def describe_mvsim_compat_source(path: Path) -> Dict:
    return {
        "source_kind": "mvsim_compatibility_shim",
        "observation_file": str(Path(path)),
        "telemetry_contract": "MVSim-style planar pose2d + velocity2d observation stream",
        "runtime_mode": "offline_observation_playback",
    }
