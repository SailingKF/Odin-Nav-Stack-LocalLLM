import unittest
from pathlib import Path

from services.mvsim_validation_harness.map_view import build_validation_map_view


class MVSimValidationMapViewTests(unittest.TestCase):
    def test_build_validation_map_view_uses_route_assets_and_last_pose(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        payload = build_validation_map_view(
            config={
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
            },
            repo_root=repo_root,
            latest_report={
                "validation_mode": "live_runtime",
                "recent_triggered_spot_ids": ["gate", "plaza"],
                "recent_narrated_spot_ids": ["gate"],
                "latest_spot_name": "Central Plaza",
                "latest_narration_text": "Central Plaza narration.",
            },
            last_validation_result={
                "validation_mode": "live_runtime",
                "sim_ingress_state": {
                    "last_pose": {"x": 5.0, "y": 1.0, "label": "tour_bot"},
                    "active_spot_id": "plaza",
                    "active_spot_name": "Central Plaza",
                },
            },
            current_api_state=None,
            selected_validation_mode="live_runtime",
        )

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["active_validation_mode"], "live_runtime")
        self.assertEqual(payload["poi_count"], 3)
        self.assertTrue(payload["pose_available"])
        self.assertEqual(payload["data_sources"]["pose_source"], "last_validation_result.sim_ingress_state")
        self.assertEqual(payload["recent_triggered_spot_ids"], ["gate", "plaza"])
        self.assertEqual(payload["recent_narrated_spot_ids"], ["gate"])
        self.assertEqual(payload["pose"]["world"]["label"], "tour_bot")
        self.assertEqual(payload["poi_markers"][0]["visual_status"], "narrated")
        self.assertEqual(payload["poi_markers"][1]["visual_status"], "active")
        self.assertEqual(payload["poi_markers"][2]["visual_status"], "pending")
        self.assertEqual(len(payload["route_polyline"]), 3)
        self.assertIn("screen_y_axis", payload["normalization"])

    def test_build_validation_map_view_can_use_current_api_state_without_new_validation(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        payload = build_validation_map_view(
            config={
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
            },
            repo_root=repo_root,
            latest_report={
                "validation_mode": "compatibility_shim",
                "recent_triggered_spot_ids": ["gate", "plaza", "gallery"],
                "recent_narrated_spot_ids": ["gate", "plaza", "gallery"],
                "latest_spot_name": "History Gallery",
                "latest_pose": {"x": 9.5, "y": -0.5, "label": "persisted_pose"},
            },
            last_validation_result=None,
            current_api_state={
                "last_pose": {"x": 9.25, "y": -0.4, "label": "tour_bot"},
                "active_spot_id": "gallery",
                "active_spot_name": "History Gallery",
            },
            selected_validation_mode="compatibility_shim",
        )

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["data_sources"]["pose_source"], "api_state")
        self.assertEqual(payload["active_spot_id"], "gallery")
        self.assertEqual(payload["latest_spot_name"], "History Gallery")
        self.assertEqual(payload["poi_markers"][-1]["visual_status"], "active")

    def test_build_validation_map_view_uses_report_only_latest_spot_fallback_after_stack_stops(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        payload = build_validation_map_view(
            config={
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
            },
            repo_root=repo_root,
            latest_report={
                "validation_mode": "compatibility_shim",
                "latest_spot_id": "gallery",
                "latest_spot_name": None,
                "latest_pose": {"x": 9.5, "y": -0.5, "label": "gallery_inside"},
                "recent_triggered_spot_ids": ["gate", "plaza", "gallery"],
                "recent_narrated_spot_ids": ["gate", "plaza", "gallery"],
            },
            last_validation_result=None,
            current_api_state=None,
            selected_validation_mode="compatibility_shim",
        )

        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["data_sources"]["pose_source"], "latest_report")
        self.assertEqual(payload["data_sources"]["progress_source"], "latest_report")
        self.assertEqual(payload["latest_spot_id"], "gallery")
        self.assertEqual(payload["latest_spot_name"], "History Gallery")
        self.assertTrue(payload["poi_markers"][-1]["is_latest"])


if __name__ == "__main__":
    unittest.main()
