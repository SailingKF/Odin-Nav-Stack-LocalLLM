import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from services.mvsim_validation_harness.reporting import (
    ComparisonExportStore,
    ValidationReportStore,
    build_human_readable_comparison_export,
    build_latest_comparison_export,
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
                "api_state": {"last_pose": {"x": 9.5, "y": -0.5, "label": "tour_bot"}},
                "live_validation_summary": {
                    "live_first_poi_hit_occurred": True,
                    "live_second_poi_hit_occurred": True,
                    "live_second_narration_occurred": True,
                },
            },
            config_path=Path("configs/sim_harness.yaml"),
            config_payload={
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
                "mvsim_integration": {
                    "world_file": "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
                    "vehicle_name": "tour_bot",
                    "live_validation_alignment": {
                        "strategy": "isolated_live_validation_world_with_forward_motion",
                        "motion_strategy": "constant_forward_velocity_along_demo_axis",
                    },
                },
            },
            harness_url="http://127.0.0.1:8301",
            debug_url="http://127.0.0.1:8001/debug",
        )

        self.assertEqual(report["validation_mode"], "live_runtime")
        self.assertTrue(report["passed"])
        self.assertTrue(report["live_first_poi_hit_occurred"])
        self.assertTrue(report["live_second_poi_hit_occurred"])
        self.assertTrue(report["route_completed"])
        self.assertEqual(report["recent_triggered_spot_ids"], ["gate", "plaza", "gallery"])
        self.assertEqual(report["latest_pose"]["x"], 9.5)
        self.assertEqual(report["service_targets"]["api_server"], "http://127.0.0.1:8001/health")
        self.assertEqual(
            report["validation_asset_identity"]["world_file"],
            "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
        )
        self.assertEqual(
            report["validation_asset_identity"]["motion_strategy"],
            "constant_forward_velocity_along_demo_axis",
        )

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

    def test_comparison_export_store_persists_latest_export(self) -> None:
        with TemporaryDirectory() as temp_dir:
            store = ComparisonExportStore(Path(temp_dir))
            first = store.write_export(
                {
                    "export_id": "20260406T120000Z-latest_comparison_export",
                    "comparison_status": "missing_reports",
                    "comparability_status": "unknown",
                }
            )
            second = store.write_export(
                {
                    "export_id": "20260406T120100Z-latest_comparison_export",
                    "comparison_status": "ready",
                    "comparability_status": "comparable",
                },
                human_readable_text="# Latest Comparison Export\n",
            )

            latest = store.read_latest_export()
            latest_human = store.read_latest_human_readable_export()

        self.assertEqual(first["comparison_status"], "missing_reports")
        self.assertEqual(second["comparability_status"], "comparable")
        self.assertEqual(latest["export_id"], "20260406T120100Z-latest_comparison_export")
        self.assertTrue(latest["human_readable_export_path"].endswith(".md"))
        self.assertEqual(latest_human["export_id"], "20260406T120100Z-latest_comparison_export")
        self.assertIn("Latest Comparison Export", latest_human["content"])

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
                "validation_asset_identity": {
                    "config_name": "sim_harness.yaml",
                    "config_path": "configs/sim_harness.yaml",
                    "route_file": "content/routes/demo_route.yaml",
                    "poi_file": "content/poi/demo_pois.yaml",
                    "world_file": "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
                    "vehicle_name": "tour_bot",
                    "alignment_strategy": "isolated_live_validation_world_with_forward_motion",
                    "motion_strategy": "constant_forward_velocity_along_demo_axis",
                },
            },
            latest_compatibility_report={
                "report_id": "compat-1",
                "validation_mode": "compatibility_shim",
                "passed": True,
                "route_completed": True,
                "recent_triggered_spot_ids": ["gate", "plaza", "gallery"],
                "recent_narrated_spot_ids": ["gate", "plaza", "gallery"],
                "latest_spot_name": "History Gallery",
                "validation_asset_identity": {
                    "config_name": "sim_harness.yaml",
                    "config_path": "configs/sim_harness.yaml",
                    "route_file": "content/routes/demo_route.yaml",
                    "poi_file": "content/poi/demo_pois.yaml",
                    "world_file": "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
                    "vehicle_name": "tour_bot",
                    "alignment_strategy": "isolated_live_validation_world_with_forward_motion",
                    "motion_strategy": "constant_forward_velocity_along_demo_axis",
                },
            },
        )

        self.assertEqual(summary["status"], "ready")
        self.assertTrue(summary["comparison_available"])
        self.assertEqual(summary["missing_modes"], [])
        self.assertEqual(summary["comparability_status"], "comparable")
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

    def test_build_latest_comparison_export_keeps_high_signal_fields(self) -> None:
        export_payload = build_latest_comparison_export(
            {
                "status": "ready",
                "comparison_available": True,
                "comparability_status": "comparable",
                "missing_modes": [],
                "guardrail_reasons": ["required validation assets match across the latest live and compatibility reports"],
                "live_runtime_report": {
                    "report_id": "live-1",
                    "validation_asset_identity": {"world_file": "world.xml"},
                },
                "compatibility_shim_report": {
                    "report_id": "compat-1",
                    "validation_asset_identity": {"world_file": "world.xml"},
                },
                "differences": {"triggered_spots_equal": True},
            },
            harness_url="http://127.0.0.1:8304",
        )

        self.assertEqual(export_payload["export_kind"], "latest_live_vs_compatibility_comparison")
        self.assertEqual(export_payload["comparison_status"], "ready")
        self.assertEqual(export_payload["comparability_status"], "comparable")
        self.assertEqual(export_payload["live_runtime_report"]["report_id"], "live-1")
        self.assertEqual(export_payload["compatibility_shim_report"]["report_id"], "compat-1")
        self.assertTrue(export_payload["differences"]["triggered_spots_equal"])

    def test_build_latest_comparison_export_keeps_missing_report_state_explicit(self) -> None:
        export_payload = build_latest_comparison_export(
            {
                "status": "missing_reports",
                "comparison_available": False,
                "comparability_status": "unknown",
                "missing_modes": ["compatibility_shim"],
                "guardrail_reasons": [],
                "live_runtime_report": {"report_id": "live-1"},
                "compatibility_shim_report": None,
                "differences": {},
            },
            harness_url="http://127.0.0.1:8304",
        )

        self.assertEqual(export_payload["comparison_status"], "missing_reports")
        self.assertEqual(export_payload["missing_modes"], ["compatibility_shim"])
        self.assertFalse(export_payload["comparison_available"])
        self.assertIsNone(export_payload["compatibility_shim_report"])

    def test_build_human_readable_comparison_export_is_scan_friendly(self) -> None:
        markdown = build_human_readable_comparison_export(
            {
                "export_id": "20260406T120200Z-latest_comparison_export",
                "created_at": "2026-04-06T12:02:00+00:00",
                "comparison_status": "ready",
                "comparability_status": "comparable",
                "missing_modes": [],
                "guardrail_reasons": ["required validation assets match across the latest live and compatibility reports"],
                "live_runtime_report": {
                    "report_id": "live-1",
                    "status": "passed",
                    "passed": True,
                    "route_completed": True,
                    "latest_pose": {"x": 9.5, "y": -0.5},
                    "recent_triggered_spot_ids": ["gate", "plaza"],
                    "recent_narrated_spot_ids": ["gate", "plaza"],
                    "validation_asset_identity": {"world_file": "world.xml", "vehicle_name": "tour_bot"},
                },
                "compatibility_shim_report": {
                    "report_id": "compat-1",
                    "status": "passed",
                    "passed": True,
                    "route_completed": True,
                    "latest_pose": {"x": 9.5, "y": -0.5},
                    "recent_triggered_spot_ids": ["gate", "plaza"],
                    "recent_narrated_spot_ids": ["gate", "plaza"],
                    "validation_asset_identity": {"world_file": "world.xml", "vehicle_name": "tour_bot"},
                },
                "differences": {"triggered_spots_equal": True},
            }
        )

        self.assertIn("# Latest Comparison Export", markdown)
        self.assertIn("Comparability Status: comparable", markdown)
        self.assertIn("## Guardrail Reasons", markdown)
        self.assertIn("## Live Runtime Report", markdown)
        self.assertIn("## Compatibility Shim Report", markdown)
        self.assertIn("Latest Pose", markdown)

    def test_build_latest_mode_comparison_marks_mismatched_assets_not_directly_comparable(self) -> None:
        summary = build_latest_mode_comparison(
            latest_live_report={
                "report_id": "live-1",
                "validation_mode": "live_runtime",
                "validation_asset_identity": {
                    "route_file": "content/routes/demo_route.yaml",
                    "poi_file": "content/poi/demo_pois.yaml",
                    "world_file": "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
                    "vehicle_name": "tour_bot",
                    "alignment_strategy": "isolated_live_validation_world_with_forward_motion",
                    "motion_strategy": "constant_forward_velocity_along_demo_axis",
                },
            },
            latest_compatibility_report={
                "report_id": "compat-1",
                "validation_mode": "compatibility_shim",
                "validation_asset_identity": {
                    "route_file": "content/routes/demo_route.yaml",
                    "poi_file": "content/poi/demo_pois.yaml",
                    "world_file": "content/sim/mvsim/worlds/other_world.world.xml",
                    "vehicle_name": "tour_bot",
                    "alignment_strategy": "isolated_live_validation_world_with_forward_motion",
                    "motion_strategy": "constant_forward_velocity_along_demo_axis",
                },
            },
        )

        self.assertEqual(summary["comparability_status"], "not_directly_comparable")
        self.assertIn("world_file", summary["identity_guardrails"]["critical_mismatches"])

    def test_build_latest_mode_comparison_marks_missing_identity_as_warning(self) -> None:
        summary = build_latest_mode_comparison(
            latest_live_report={
                "report_id": "live-1",
                "validation_mode": "live_runtime",
                "validation_asset_identity": {
                    "route_file": "content/routes/demo_route.yaml",
                    "poi_file": "content/poi/demo_pois.yaml",
                    "world_file": "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
                    "vehicle_name": "tour_bot",
                    "alignment_strategy": "isolated_live_validation_world_with_forward_motion",
                    "motion_strategy": None,
                    "config_name": "sim_harness.yaml",
                },
            },
            latest_compatibility_report={
                "report_id": "compat-1",
                "validation_mode": "compatibility_shim",
                "validation_asset_identity": {
                    "route_file": "content/routes/demo_route.yaml",
                    "poi_file": "content/poi/demo_pois.yaml",
                    "world_file": "content/sim/mvsim/worlds/odin_live_multistop_tour.world.xml",
                    "vehicle_name": "tour_bot",
                    "alignment_strategy": "isolated_live_validation_world_with_forward_motion",
                    "motion_strategy": "constant_forward_velocity_along_demo_axis",
                    "config_name": "sim_harness_alt.yaml",
                },
            },
        )

        self.assertEqual(summary["comparability_status"], "comparable_with_warnings")
        self.assertIn("motion_strategy", summary["identity_guardrails"]["warnings"])
        self.assertIn("config_name", summary["identity_guardrails"]["warnings"])


if __name__ == "__main__":
    unittest.main()
