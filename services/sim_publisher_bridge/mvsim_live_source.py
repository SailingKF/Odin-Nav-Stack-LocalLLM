import subprocess
from typing import Dict, Iterable, Iterator, List, Optional

from services.sim_publisher_bridge.source import SimulatorPoseSource


def _build_pose_sample(current: Dict[str, object]) -> Optional[Dict]:
    if "x" not in current or "y" not in current:
        return None
    return {
        "label": current.get("object_id"),
        "position": {
            "x": float(current.get("x", 0.0)),
            "y": float(current.get("y", 0.0)),
            "z": float(current.get("z", 0.0)),
        },
        "orientation": {
            "yaw_rad": float(current.get("yaw", 0.0)),
        },
        "mvsim": {
            "object_id": current.get("object_id"),
            "topic_name": current.get("topic_name"),
            "message_type": current.get("message_type", "mvsim_msgs.TimeStampedPose"),
            "unix_timestamp": float(current.get("unix_timestamp", 0.0)),
            "frame_id": current.get("frame_id", "map"),
            "runtime_mode": "wsl_live_topic_echo",
        },
    }


def iter_time_stamped_pose_samples(lines: Iterable[str]) -> Iterator[Dict]:
    current: Dict[str, object] = {}
    in_pose = False

    def finalize() -> Optional[Dict]:
        nonlocal current, in_pose
        sample = _build_pose_sample(current)
        current = {}
        in_pose = False
        return sample

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("[") and "Received data" in line:
            sample = finalize()
            if sample is not None:
                yield sample
            continue
        if line.startswith("unixTimestamp:"):
            current["unix_timestamp"] = float(line.split(":", 1)[1].strip())
            continue
        if line.startswith("objectId:"):
            current["object_id"] = line.split('"', 2)[1]
            continue
        if line.startswith("- typeName:"):
            current["message_type"] = line.split(":", 1)[1].strip().strip('"')
            continue
        if line == "pose {":
            in_pose = True
            continue
        if in_pose and line == "}":
            continue
        if in_pose and ":" in line:
            key, value = line.split(":", 1)
            try:
                current[key.strip()] = float(value.strip())
            except ValueError:
                current[key.strip()] = value.strip()

    sample = finalize()
    if sample is not None:
        yield sample


def parse_time_stamped_pose_blocks(text: str) -> List[Dict]:
    return list(iter_time_stamped_pose_samples(text.splitlines()))


class WslMVSimTopicEchoSource(SimulatorPoseSource):
    def __init__(
        self,
        distribution: str,
        user: str,
        executable_path: str,
        topic_name: str,
        sample_limit: Optional[int] = 3,
        timeout_sec: float = 5.0,
    ) -> None:
        self._distribution = distribution
        self._user = user
        self._executable_path = executable_path
        self._topic_name = topic_name
        self._sample_limit = sample_limit
        self._timeout_sec = timeout_sec

    def _build_command(self) -> List[str]:
        return [
            "wsl.exe",
            "-d",
            self._distribution,
            "-u",
            self._user,
            "--",
            self._executable_path,
            "topic",
            "echo",
            self._topic_name,
        ]

    def iter_payloads(self) -> Iterator[Dict]:
        process = subprocess.Popen(
            self._build_command(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        yielded_count = 0
        try:
            if process.stdout is None:
                return
            for sample in iter_time_stamped_pose_samples(process.stdout):
                yield sample
                yielded_count += 1
                if self._sample_limit is not None and yielded_count >= self._sample_limit:
                    return
        finally:
            process.terminate()
            try:
                process.wait(timeout=self._timeout_sec)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=self._timeout_sec)


def describe_mvsim_live_pose_source(
    distribution: str,
    user: str,
    executable_path: str,
    topic_name: str,
) -> Dict:
    return {
        "source_kind": "mvsim_live_topic_echo",
        "runtime_host": "wsl",
        "distribution": distribution,
        "user": user,
        "executable_path": executable_path,
        "topic_name": topic_name,
        "message_type": "mvsim_msgs.TimeStampedPose",
        "bridge_contract": "TimeStampedPose -> richer payload -> sim_ingress {x,y,label}",
    }
