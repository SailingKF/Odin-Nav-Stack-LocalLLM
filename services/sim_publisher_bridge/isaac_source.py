from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

import yaml

from services.sim_publisher_bridge.source import SimulatorPoseSource


class IsaacObservationSource(ABC):
    @abstractmethod
    def iter_observations(self) -> Iterator[Dict]:
        """Yield Isaac-oriented pose observations without depending on Isaac SDK packages."""


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
