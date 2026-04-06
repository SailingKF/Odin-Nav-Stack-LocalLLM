import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from services.mvsim_validation_harness.reporting import (
    ValidationReportStore,
    build_latest_mode_comparison,
    build_validation_report,
)


class MVSimValidationReportingTests(unittest.TestCase):
    def test_build_validation_report_captures_live_truth_fields(self) -> None:
        report = build_validation_report(
            validation_result={
                "status": "passed",
                "validation_mode": "live_runtime",
                "mvsim_mode": "live_runtime",
                "mvsim_source": {"source_kind": "mvsim_live_topic_echo"},
                "service_checks": {
                    "sim_pose_ingress": {"target_url": "http://127.0.0.1:8110/health"},
                    "api_server": {"target_url": "http://127.0.0.1:8001/health"},
                    "debug_page": {"target_url": "http://127.0.0.1:8001/debug"},
                },
                "sim_ingress_state": {"route_completed": True},
                "api_latest_session": {
                    "session_id": "mock_tour_123",
                    "latest_spot_name": "History Gallery",
                    "latest_narration_text": "Final stop narration.",
                    "recent_poi_triggers": [
                        {"spot_id": "gate"},
                        {"spot_id": "plaza"},
                        {"spot_id": "gallery"},
                    ],
                    "recent_narrations": [
                        {"spot_id": "gate"},
                        {"spot_id": "plaza"},
                        {"spot_id": "gallery"},
                    ],
                    "proxy_target": "http://127.0.0.1:8110",
                },
                "live_validation_summary": {
                    "live_first_poi_hit_occurred": True,
                    "live_second_poi_hit_occurred": True,
                    "live_second_narration_occurred": True,
                },
            },
            config_path=Path("configs/sim_harness.yaml"),
            harness_url="http://127.0.0.1:8301",
            debug_url="http://127.0.0.1:8001/debug",
        )

        self.assertEqual(report["validation_mode"], "live_runtime")
        self.assertTrue(report["passed"])
        self.assertTrue(report["live_first_poi_hit_occurred"])
        self.assertTrue(report["live_second_poi_hit_occurred"])
        self.assertTrue(report["route_completed"])
        self.assertEqual(report["recent_triggered_spot_ids"], ["gate", "plaza", "gallery"])
        self.assertEqual(report["service_targets"]["api_server"], "http://127.0.0.1:8001/health")

    def test_report_store_persists_latest_and_recent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = ValidationReportStore(Path(temp_dir))
            first = store.write_report(
                {
                    "report_id": "20260406T120000Z-compatibility_shim",
                    "status": "passed",
                    "validation_mode": "compatibility_shim",
                }
            )
            second = store.write_report(
                {
                    "report_id": "20260406T120100Z-live_runtime",
                    "status": "passed",
                    "validation_mode": "live_runtime",
                }
            )

            latest = store.read_latest_report()
            recent = store.read_recent_reports(limit=2)

        self.assertEqual(first["validation_mode"], "compatibility_shim")
        self.assertEqual(second["validation_mode"], "live_runtime")
        self.assertEqual(latest["report_id"], "20260406T120100Z-live_runtime")
        self.assertEqual(recent[0]["report_id"], "20260406T120100Z-live_runtime")
        self.assertEqual(recent[1]["report_id"], "20260406T120000Z-compatibility_shim")

    def test_build_latest_mode_comparison_handles_both_modes(self) -> None:
        summary = build_latest_mode_comparison(
            latest_live_report={
                "report_id": "live-1",
                "validation_mode": "live_runtime",
                "passed": True,
                "route_completed": True,
                "recent_triggered_spot_ids": ["gate", "plaza", "gallery"],
                "recent_narrated_spot_ids": ["gate", "plaza", "gallery"],
                "latest_spot_name": "History Gallery",
            },
            latest_compatibility_report={
                "report_id": "compat-1",
                "validation_mode": "compatibility_shim",
                "passed": True,
                "route_completed": True,
                "recent_triggered_spot_ids": ["gate", "plaza", "gallery"],
                "recent_narrated_spot_ids": ["gate", "plaza", "gallery"],
                "latest_spot_name": "History Gallery",
            },
        )

        self.assertEqual(summary["status"], "ready")
        self.assertTrue(summary["comparison_available"])
        self.assertEqual(summary["missing_modes"], [])
        self.assertTrue(summary["differences"]["triggered_spots_equal"])
        self.assertTrue(summary["differences"]["narrated_spots_equal"])
        self.assertTrue(summary["differences"]["latest_spot_name_equal"])

    def test_build_latest_mode_comparison_handles_missing_live_report(self) -> None:
        summary = build_latest_mode_comparison(
            latest_live_report=None,
            latest_compatibility_report={"report_id": "compat-1", "validation_mode": "compatibility_shim"},
        )

        self.assertEqual(summary["status"], "missing_reports")
        self.assertFalse(summary["comparison_available"])
        self.assertEqual(summary["missing_modes"], ["live_runtime"])


if __name__ == "__main__":
    unittest.main()
