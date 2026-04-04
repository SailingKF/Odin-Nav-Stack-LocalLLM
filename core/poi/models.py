from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class POI:
    spot_id: str
    name: str
    x: float
    y: float
    trigger_radius: float
    narration_text: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POI":
        return cls(
            spot_id=str(data["spot_id"]),
            name=str(data["name"]),
            x=float(data["x"]),
            y=float(data["y"]),
            trigger_radius=float(data["trigger_radius"]),
            narration_text=str(data["narration_text"]),
        )


@dataclass(frozen=True)
class RouteDefinition:
    route_id: str
    spot_ids: List[str]
