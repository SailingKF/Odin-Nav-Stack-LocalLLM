import math
from typing import Set

from core.interfaces.pose_provider import Pose2D
from core.poi.models import POI


def is_pose_within_radius(pose: Pose2D, poi: POI) -> bool:
    return math.hypot(pose.x - poi.x, pose.y - poi.y) <= poi.trigger_radius


class PoiTriggerEngine:
    def __init__(self) -> None:
        self._triggered_spot_ids: Set[str] = set()

    def has_triggered(self, spot_id: str) -> bool:
        return spot_id in self._triggered_spot_ids

    def evaluate(self, pose: Pose2D, poi: POI) -> bool:
        if self.has_triggered(poi.spot_id):
            return False
        if not is_pose_within_radius(pose, poi):
            return False
        self._triggered_spot_ids.add(poi.spot_id)
        return True

    def reset(self) -> None:
        self._triggered_spot_ids.clear()
