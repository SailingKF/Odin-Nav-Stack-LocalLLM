import unittest
from pathlib import Path

from services.sim_publisher_bridge.mvsim_live import (
    describe_mvsim_runtime_mode,
    evaluate_wsl_enablement,
    probe_mvsim_live_runtime,
)


class MVSimLiveRuntimeTests(unittest.TestCase):
    def test_evaluate_wsl_enablement_reports_elevation_blocker(self) -> None:
        result = evaluate_wsl_enablement(
            status_probe={
                "ok": True,
                "returncode": 1,
                "stdout": "",
                "stderr": "The Windows Subsystem for Linux is not installed. You can install by running 'wsl.exe --install'.",
            },
            elevated=False,
        )

        self.assertTrue(result["wsl_command_available"])
        self.assertFalse(result["wsl_installed"])
        self.assertFalse(result["current_shell_elevated"])
        self.assertEqual(result["blocker"]["code"], "wsl_requires_elevation")

    def test_evaluate_wsl_enablement_accepts_installed_status(self) -> None:
        result = evaluate_wsl_enablement(
            status_probe={
                "ok": True,
                "returncode": 0,
                "stdout": "Default Distribution: Ubuntu\nDefault Version: 2",
                "stderr": "",
            },
            elevated=False,
        )

        self.assertTrue(result["wsl_installed"])
        self.assertIsNone(result["blocker"])

    def test_probe_reports_missing_runtime_and_existing_world_file(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = {
            "mvsim_integration": {
                "mode": "live_runtime",
                "executable": "definitely_missing_mvsim_binary",
                "world_file": "content/sim/mvsim/worlds/odin_minimal_tour.world.xml",
                "vehicle_name": "tour_bot",
            }
        }

        probe = probe_mvsim_live_runtime(config, repo_root)

        self.assertEqual(probe["runtime_kind"], "live_mvsim_runtime")
        self.assertFalse(probe["runtime_available"])
        self.assertTrue(probe["world_file_exists"])
        self.assertEqual(probe["blocker"]["code"], "mvsim_executable_not_found")

    def test_describe_mode_keeps_compatibility_source_visible(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        config = {
            "mvsim_integration": {
                "mode": "compatibility_shim",
                "executable": "mvsim",
                "world_file": "content/sim/mvsim/worlds/odin_minimal_tour.world.xml",
                "observation_file": "content/sim/demo_mvsim_pose_stream.yaml",
                "vehicle_name": "tour_bot",
            }
        }

        summary = describe_mvsim_runtime_mode(config, repo_root)

        self.assertEqual(summary["configured_mode"], "compatibility_shim")
        self.assertEqual(summary["effective_mode"], "compatibility_shim")
        self.assertEqual(summary["compatibility_source"]["source_kind"], "mvsim_compatibility_shim")
        self.assertTrue(summary["compatibility_source"]["observation_file_exists"])
        self.assertIn("wsl_enablement", summary)


if __name__ == "__main__":
    unittest.main()
