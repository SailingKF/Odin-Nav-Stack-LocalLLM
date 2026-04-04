from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass(frozen=True)
class Pose2D:
    x: float
    y: float
    label: Optional[str] = None


class PoseProvider(ABC):
    @abstractmethod
    def iter_poses(self) -> Iterator[Pose2D]:
        """Yield the current pose stream for the active environment."""

    @abstractmethod
    def reset(self) -> None:
        """Reset the provider to its initial state."""
