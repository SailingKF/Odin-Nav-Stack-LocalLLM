from abc import ABC, abstractmethod


class ContentProvider(ABC):
    @abstractmethod
    def get_narration_text(self, spot_id: str) -> str:
        """Return curated narration text for the requested POI."""
