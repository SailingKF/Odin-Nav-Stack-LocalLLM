from abc import ABC, abstractmethod
from typing import Dict, Iterator


class IsaacObservationSource(ABC):
    @abstractmethod
    def iter_observations(self) -> Iterator[Dict]:
        """Yield Isaac-oriented pose observations without depending on Isaac SDK packages."""
