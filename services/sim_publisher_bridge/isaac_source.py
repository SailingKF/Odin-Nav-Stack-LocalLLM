from pathlib import Path
from typing import Dict, Iterable, Iterator, List

import yaml

from services.sim_publisher_bridge.isaac_contract import IsaacObservationSource
from services.sim_publisher_bridge.isaac_live import IsaacLiveObservationSource, get_isaac_live_adapter_availability
from services.sim_publisher_bridge.source import SimulatorPoseSource


class IterableIsaacObservationSource(IsaacObservationSource):
    def __init__(self, observations: Iterable[Dict]):
        self._observations = list(observations)

    def iter_observations(self) -> Iterator[Dict]:
        for observation in self._observations:
            yield dict(observation)


class YamlFileIsaacObservationSource(IsaacObservationSource):
    def __init__(self, path: Path):
        self._path = Path(path)

    def iter_observations(self) -> Iterator[Dict]:
        with self._path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        observations: List[Dict] = payload.get("observations", [])
        for item in observations:
            yield dict(item)


class IsaacStubPoseSource(SimulatorPoseSource):
    def __init__(self, observation_source: IsaacObservationSource):
        self._observation_source = observation_source

    def iter_payloads(self) -> Iterator[Dict]:
        for observation in self._observation_source.iter_observations():
            translation = observation.get("translation", {})
            orientation = observation.get("orientation", {})
            yield {
                "label": observation.get("label"),
                "position": {
                    "x": translation.get("x", 0.0),
                    "y": translation.get("y", 0.0),
                    "z": translation.get("z", 0.0),
                },
                "orientation": {
                    "yaw_rad": orientation.get("yaw_rad", 0.0),
                },
                "source_metadata": {
                    "prim_path": observation.get("prim_path"),
                    "frame_id": observation.get("frame_id"),
                    "sim_time_sec": observation.get("sim_time_sec"),
                },
            }


def build_isaac_observation_source(config: Dict) -> IsaacObservationSource:
    mode = config.get("mode", "stub")
    if mode == "stub":
        stub_payload_file = config.get("stub_payload_file", "content/sim/demo_isaac_stub_pose_stream.yaml")
        return YamlFileIsaacObservationSource(Path(stub_payload_file))
    if mode == "live":
        live_config = config.get("live", {})
        return IsaacLiveObservationSource(
            robot_prim_path=live_config.get("robot_prim_path", "/World/Robot/base_link"),
            frame_id=live_config.get("frame_id", "odin/base_link"),
            required_modules=live_config.get("required_modules"),
        )
    raise ValueError(f"Unsupported isaac source mode: {mode}")


def build_isaac_pose_source(config: Dict) -> SimulatorPoseSource:
    return IsaacStubPoseSource(build_isaac_observation_source(config))


def describe_isaac_source_selection(config: Dict) -> Dict:
    mode = config.get("mode", "stub")
    description = {
        "mode": mode,
        "stub_payload_file": config.get("stub_payload_file"),
        "live": {},
    }
    if mode == "live":
        live_config = config.get("live", {})
        availability = get_isaac_live_adapter_availability(live_config.get("required_modules")).to_dict()
        description["live"] = {
            "robot_prim_path": live_config.get("robot_prim_path", "/World/Robot/base_link"),
            "frame_id": live_config.get("frame_id", "odin/base_link"),
            "availability": availability,
        }
    return description
