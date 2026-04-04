from abc import ABC, abstractmethod

from core.poi.models import POI


class Narrator(ABC):
    @abstractmethod
    def generate_narration(self, spot: POI, mode: str = "standard") -> str:
        """Generate the narration text for the requested spot and mode."""

    @abstractmethod
    def answer_question(self, spot: POI, question: str) -> str:
        """Answer a follow-up question using the structured POI content."""
