from pathlib import Path
from typing import Any, Dict, List

import yaml

from core.poi.models import POI, RouteDefinition


def _load_yaml(path: str) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_pois(path: str) -> List[POI]:
    payload = _load_yaml(path)
    return [POI.from_dict(item) for item in payload.get("pois", [])]


def load_route(path: str) -> RouteDefinition:
    payload = _load_yaml(path)
    return RouteDefinition(
        route_id=str(payload.get("route_id", "default_route")),
        spot_ids=[str(spot_id) for spot_id in payload.get("spot_ids", [])],
    )
