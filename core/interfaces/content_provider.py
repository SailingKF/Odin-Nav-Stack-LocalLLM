from abc import ABC, abstractmethod

from core.poi.models import POI


class ContentProvider(ABC):
    @abstractmethod
    def get_poi_content(self, spot_id: str) -> POI:
        """Return structured curated content for the requested POI."""

    @abstractmethod
    def get_narration_text(self, spot_id: str, mode: str = "standard") -> str:
        """Return curated narration text for the requested POI and mode."""
