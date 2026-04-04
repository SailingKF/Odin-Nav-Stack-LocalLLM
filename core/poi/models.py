from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class FAQEntry:
    question: str
    answer: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FAQEntry":
        return cls(
            question=str(data["question"]),
            answer=str(data["answer"]),
        )


@dataclass(frozen=True)
class POI:
    spot_id: str
    name: str
    x: float
    y: float
    trigger_radius: float
    short_text: str
    standard_text: str
    extended_text: str
    facts: List[str] = field(default_factory=list)
    faq: List[FAQEntry] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    persona: Optional[str] = None
    theme: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POI":
        fallback_text = str(data.get("narration_text", data.get("standard_text", ""))).strip()
        short_text = str(data.get("short_text", fallback_text)).strip()
        standard_text = str(data.get("standard_text", fallback_text or short_text)).strip()
        extended_text = str(data.get("extended_text", standard_text or short_text)).strip()

        return cls(
            spot_id=str(data["spot_id"]),
            name=str(data["name"]),
            x=float(data["x"]),
            y=float(data["y"]),
            trigger_radius=float(data["trigger_radius"]),
            short_text=short_text,
            standard_text=standard_text or short_text,
            extended_text=extended_text or standard_text or short_text,
            facts=[str(item) for item in data.get("facts", [])],
            faq=[FAQEntry.from_dict(item) for item in data.get("faq", [])],
            tags=[str(tag) for tag in data.get("tags", [])],
            persona=str(data["persona"]) if "persona" in data and data["persona"] is not None else None,
            theme=str(data["theme"]) if "theme" in data and data["theme"] is not None else None,
        )

    @property
    def narration_text(self) -> str:
        return self.standard_text

    def text_for_mode(self, mode: str) -> str:
        if mode == "short":
            return self.short_text
        if mode == "extended":
            return self.extended_text
        return self.standard_text

    def to_content_dict(self) -> Dict[str, Any]:
        return {
            "spot_id": self.spot_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "trigger_radius": self.trigger_radius,
            "short_text": self.short_text,
            "standard_text": self.standard_text,
            "extended_text": self.extended_text,
            "facts": list(self.facts),
            "faq": [{"question": item.question, "answer": item.answer} for item in self.faq],
            "tags": list(self.tags),
            "persona": self.persona,
            "theme": self.theme,
        }


@dataclass(frozen=True)
class RouteDefinition:
    route_id: str
    spot_ids: List[str]
