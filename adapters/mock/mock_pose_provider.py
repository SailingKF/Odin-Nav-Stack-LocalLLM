import math
from typing import Iterator, List, Sequence, Tuple

from core.interfaces.pose_provider import Pose2D, PoseProvider
from core.poi.models import POI


def _interpolate_segment(start: Tuple[float, float], end: Tuple[float, float], step_size: float) -> List[Pose2D]:
    distance = math.hypot(end[0] - start[0], end[1] - start[1])
    steps = max(1, int(distance / step_size))
    return [
        Pose2D(
            x=start[0] + (end[0] - start[0]) * (index / steps),
            y=start[1] + (end[1] - start[1]) * (index / steps),
        )
        for index in range(1, steps + 1)
    ]


def build_demo_trajectory(route_pois: Sequence[POI], step_size: float = 0.75) -> List[Pose2D]:
    if not route_pois:
        return []

    poses: List[Pose2D] = []
    cursor = (route_pois[0].x - 3.0, route_pois[0].y - 2.0)

    for poi in route_pois:
        approach = (poi.x - max(0.2, poi.trigger_radius * 0.6), poi.y)
        inside = (poi.x, poi.y)
        depart = (poi.x + poi.trigger_radius + 0.8, poi.y + 0.2)

        poses.extend(_interpolate_segment(cursor, approach, step_size))
        poses.extend(_interpolate_segment(approach, inside, step_size))
        poses.append(Pose2D(x=inside[0], y=inside[1], label=f"inside:{poi.spot_id}"))
        poses.extend(_interpolate_segment(inside, depart, step_size))
        cursor = depart

    return poses


class MockPoseProvider(PoseProvider):
    def __init__(self, trajectory: Sequence[Pose2D]):
        self._trajectory = list(trajectory)

    @classmethod
    def from_route_pois(cls, route_pois: Sequence[POI]) -> "MockPoseProvider":
        return cls(build_demo_trajectory(route_pois))

    def iter_poses(self) -> Iterator[Pose2D]:
        for pose in self._trajectory:
            yield pose

    def reset(self) -> None:
        return None
