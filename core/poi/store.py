from typing import Dict, List

from core.interfaces.content_provider import ContentProvider
from core.interfaces.poi_store import PoiStore
from core.poi.models import POI, RouteDefinition


class InMemoryPoiStore(PoiStore, ContentProvider):
    def __init__(self, pois: List[POI]):
        self._pois: Dict[str, POI] = {poi.spot_id: poi for poi in pois}

    def list_pois(self) -> List[POI]:
        return list(self._pois.values())

    def get_poi(self, spot_id: str) -> POI:
        poi = self._pois.get(spot_id)
        if poi is None:
            raise KeyError(f"Unknown POI: {spot_id}")
        return poi

    def get_narration_text(self, spot_id: str) -> str:
        return self.get_poi(spot_id).narration_text

    def route_pois(self, route: RouteDefinition) -> List[POI]:
        return [self.get_poi(spot_id) for spot_id in route.spot_ids]
