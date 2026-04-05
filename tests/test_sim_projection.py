import unittest

from adapters.sim.frame_transform import SimFrameTransformConfig, normalize_raw_pose_payload
from adapters.sim.projection import (
    SimPoseProjectionConfig,
    project_richer_pose_payload,
    project_richer_pose_payloads,
)


class SimProjectionTests(unittest.TestCase):
    def test_projection_extracts_nested_fields_into_planar_payload(self) -> None:
        config = SimPoseProjectionConfig(
            projected_x_field="sim_x",
            projected_y_field="sim_y",
            planar_x_source_path="position.x",
            planar_y_source_path="position.y",
            planar_z_source_path="position.z",
            yaw_source_path="orientation.yaw_rad",
            label_field="label",
        )

        projected = project_richer_pose_payload(
            {
                "label": "sample",
                "position": {"x": 1.25, "y": -2.5, "z": 0.3},
                "orientation": {"yaw_rad": 0.75},
            },
            config,
        )

        self.assertEqual(projected["sim_x"], 1.25)
        self.assertEqual(projected["sim_y"], -2.5)
        self.assertEqual(projected["source_position_z"], 0.3)
        self.assertEqual(projected["source_yaw"], 0.75)
        self.assertEqual(projected["label"], "sample")

    def test_projection_and_transform_end_in_http_bridge_shape(self) -> None:
        projection_config = SimPoseProjectionConfig()
        transform_config = SimFrameTransformConfig(
            raw_x_field="sim_x",
            raw_y_field="sim_y",
            swap_axes=True,
            flip_x=True,
            flip_y=True,
        )

        projected = project_richer_pose_payload(
            {
                "label": "gate_approach_richer",
                "position": {"x": 0.7, "y": 1.8, "z": 0.0},
                "orientation": {"yaw_rad": 0.0},
            },
            projection_config,
        )
        normalized = normalize_raw_pose_payload(projected, transform_config)

        self.assertEqual(normalized, {"x": -1.8, "y": -0.7, "label": "gate_approach_richer"})

    def test_projection_batch_handles_multiple_payloads(self) -> None:
        projection_config = SimPoseProjectionConfig()
        projected = project_richer_pose_payloads(
            [
                {
                    "label": "first",
                    "position": {"x": 0.7, "y": 1.8, "z": 0.0},
                    "orientation": {"yaw_rad": 0.0},
                },
                {
                    "label": "second",
                    "position": {"x": 0.0, "y": 0.6, "z": 0.0},
                    "orientation": {"yaw_rad": 0.1},
                },
            ],
            projection_config,
        )

        self.assertEqual(projected[0]["sim_x"], 0.7)
        self.assertEqual(projected[0]["sim_y"], 1.8)
        self.assertEqual(projected[1]["sim_x"], 0.0)
        self.assertEqual(projected[1]["sim_y"], 0.6)


if __name__ == "__main__":
    unittest.main()
