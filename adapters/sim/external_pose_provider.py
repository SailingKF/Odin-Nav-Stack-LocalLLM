from queue import Empty, Queue
from typing import Any, Dict, Iterator, Optional

from core.interfaces.pose_provider import Pose2D, PoseProvider

_STREAM_END = object()


def pose_from_payload(payload: Dict[str, Any]) -> Pose2D:
    return Pose2D(
        x=float(payload["x"]),
        y=float(payload["y"]),
        label=None if payload.get("label") is None else str(payload["label"]),
    )


class ExternalPoseProvider(PoseProvider):
    def __init__(self) -> None:
        self._queue: Queue = Queue()
        self._closed = False

    def push_pose(self, pose: Pose2D) -> None:
        if self._closed:
            raise RuntimeError("Pose stream is closed.")
        self._queue.put(pose)

    def push_payload(self, payload: Dict[str, Any]) -> Pose2D:
        pose = pose_from_payload(payload)
        self.push_pose(pose)
        return pose

    def close_stream(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._queue.put(_STREAM_END)

    def iter_poses(self) -> Iterator[Pose2D]:
        while True:
            item = self._queue.get()
            if item is _STREAM_END:
                break
            yield item

    def reset(self) -> None:
        self._queue = Queue()
        self._closed = False

    def drain_pending(self) -> int:
        drained = 0
        while True:
            try:
                self._queue.get_nowait()
                drained += 1
            except Empty:
                break
        return drained
