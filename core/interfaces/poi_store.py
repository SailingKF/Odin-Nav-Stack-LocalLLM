from abc import ABC, abstractmethod
from typing import List, Optional

from core.poi.models import POI


class PoiStore(ABC):
    @abstractmethod
    def list_pois(self) -> List[POI]:
        """Return all configured POIs."""

    @abstractmethod
    def get_poi(self, spot_id: str) -> Optional[POI]:
        """Return a POI by spot id when available."""
