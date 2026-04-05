from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, Iterator, List

import yaml


class SimulatorPoseSource(ABC):
    @abstractmethod
    def iter_payloads(self) -> Iterator[Dict]:
        """Yield richer simulator-side payloads."""


class IterableSimulatorPoseSource(SimulatorPoseSource):
    def __init__(self, payloads: Iterable[Dict]):
        self._payloads = list(payloads)

    def iter_payloads(self) -> Iterator[Dict]:
        for payload in self._payloads:
            yield dict(payload)


class YamlFileRicherPoseSource(SimulatorPoseSource):
    def __init__(self, path: Path):
        self._path = Path(path)

    def iter_payloads(self) -> Iterator[Dict]:
        with self._path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        poses: List[Dict] = payload.get("poses", [])
        for item in poses:
            yield dict(item)
