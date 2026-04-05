import unittest

from adapters.sim.frame_transform import (
    SimFrameTransformConfig,
    normalize_raw_pose_payload,
    normalize_raw_pose_payloads,
)


class SimFrameTransformTests(unittest.TestCase):
    def test_transform_supports_swap_flip_scale_and_offset(self) -> None:
        config = SimFrameTransformConfig(
            raw_x_field="sim_x",
            raw_y_field="sim_y",
            swap_axes=True,
            flip_x=True,
            flip_y=False,
            scale=2.0,
            offset_x=1.0,
            offset_y=-3.0,
        )

        normalized = normalize_raw_pose_payload({"sim_x": 4.0, "sim_y": 1.5, "label": "sample"}, config)

        self.assertEqual(normalized["x"], -2.0)
        self.assertEqual(normalized["y"], 5.0)
        self.assertEqual(normalized["label"], "sample")

    def test_transform_preserves_http_bridge_contract_shape(self) -> None:
        config = SimFrameTransformConfig()

        normalized = normalize_raw_pose_payload({"sim_x": 1.0, "sim_y": 2.0}, config)

        self.assertEqual(set(normalized.keys()), {"x", "y", "label"})
        self.assertEqual(normalized["x"], 1.0)
        self.assertEqual(normalized["y"], 2.0)

    def test_transform_batch_normalizes_multiple_raw_payloads(self) -> None:
        config = SimFrameTransformConfig(swap_axes=True, flip_x=True, flip_y=True)
        raw_payloads = [
            {"sim_x": 0.7, "sim_y": 1.8, "label": "gate_approach_raw"},
            {"sim_x": 0.0, "sim_y": 0.6, "label": "gate_trigger_edge_raw"},
        ]

        normalized = normalize_raw_pose_payloads(raw_payloads, config)

        self.assertEqual(
            normalized,
            [
                {"x": -1.8, "y": -0.7, "label": "gate_approach_raw"},
                {"x": -0.6, "y": -0.0, "label": "gate_trigger_edge_raw"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
