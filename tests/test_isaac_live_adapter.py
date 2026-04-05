import importlib
import unittest

from services.sim_publisher_bridge.isaac_contract import IsaacObservationSource
from services.sim_publisher_bridge.isaac_live import IsaacLiveObservationSource, get_isaac_live_adapter_availability
from services.sim_publisher_bridge.isaac_source import (
    IsaacStubPoseSource,
    build_isaac_observation_source,
    build_isaac_pose_source,
    describe_isaac_source_selection,
)


class IsaacLiveAdapterTests(unittest.TestCase):
    def test_live_adapter_module_is_import_safe_without_isaac(self) -> None:
        module = importlib.import_module("services.sim_publisher_bridge.isaac_live")

        self.assertTrue(hasattr(module, "IsaacLiveObservationSource"))
        self.assertTrue(hasattr(module, "get_isaac_live_adapter_availability"))

    def test_availability_reports_missing_dependencies(self) -> None:
        availability = get_isaac_live_adapter_availability(["definitely_missing_isaac_module"])

        self.assertFalse(availability.available)
        self.assertEqual(availability.status, "missing_dependencies")
        self.assertEqual(availability.missing_modules, ["definitely_missing_isaac_module"])

    def test_config_can_select_live_observation_source_without_import_failure(self) -> None:
        source = build_isaac_observation_source(
            {
                "mode": "live",
                "live": {
                    "robot_prim_path": "/World/TestRobot/base_link",
                    "frame_id": "test/base_link",
                    "required_modules": ["definitely_missing_isaac_module"],
                },
            }
        )

        self.assertIsInstance(source, IsaacObservationSource)
        self.assertIsInstance(source, IsaacLiveObservationSource)
        self.assertEqual(source.robot_prim_path, "/World/TestRobot/base_link")
        self.assertEqual(source.frame_id, "test/base_link")

    def test_live_pose_source_raises_clear_error_when_dependencies_are_missing(self) -> None:
        source = build_isaac_pose_source(
            {
                "mode": "live",
                "live": {
                    "required_modules": ["definitely_missing_isaac_module"],
                },
            }
        )

        self.assertIsInstance(source, IsaacStubPoseSource)
        with self.assertRaisesRegex(RuntimeError, "missing: definitely_missing_isaac_module"):
            list(source.iter_payloads())

    def test_describe_selection_reports_live_availability(self) -> None:
        description = describe_isaac_source_selection(
            {
                "mode": "live",
                "live": {
                    "robot_prim_path": "/World/Robot/base_link",
                    "frame_id": "odin/base_link",
                    "required_modules": ["definitely_missing_isaac_module"],
                },
            }
        )

        self.assertEqual(description["mode"], "live")
        self.assertFalse(description["live"]["availability"]["available"])
        self.assertEqual(
            description["live"]["availability"]["missing_modules"],
            ["definitely_missing_isaac_module"],
        )


if __name__ == "__main__":
    unittest.main()
