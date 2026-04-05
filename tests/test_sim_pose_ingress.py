import tempfile
import time
import unittest
from pathlib import Path

from adapters.sim.external_pose_provider import ExternalPoseProvider, pose_from_payload
from services.sim_pose_ingress.runtime import SimPoseIngressRuntime


class SimPoseIngressTests(unittest.TestCase):
    def test_external_pose_provider_yields_supplied_payloads(self) -> None:
        provider = ExternalPoseProvider()
        payloads = [
            {"x": -1.0, "y": 0.0, "label": "approach"},
            {"x": 0.0, "y": 0.0, "label": "inside"},
        ]

        for payload in payloads:
            provider.push_payload(payload)
        provider.close_stream()

        poses = list(provider.iter_poses())

        self.assertEqual(len(poses), 2)
        self.assertEqual(poses[0], pose_from_payload(payloads[0]))
        self.assertEqual(poses[1], pose_from_payload(payloads[1]))

    def test_sim_runtime_external_pose_sequence_triggers_narration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path.cwd()
            config = {
                "env_name": "sim",
                "pose_provider_type": "sim_ingress",
                "narrator_type": "mock",
                "narration_mode_default": "standard",
                "llm_gateway_url": "http://127.0.0.1:9000",
                "llm_backend_type": "mock",
                "llm_model_name": "mock-curated-content",
                "llm_base_url": "http://127.0.0.1:11434",
                "llm_timeout_sec": 8.0,
                "llm_enable_fallback": True,
                "session_log_dir": str(Path(temp_dir) / "session_logs" / "sim"),
                "recording_enabled": False,
                "current_route_file": "content/routes/demo_route.yaml",
                "current_poi_file": "content/poi/demo_pois.yaml",
            }
            runtime = SimPoseIngressRuntime(config=config, repo_root=repo_root)

            runtime.start()
            runtime.ingest_pose_payload({"x": -0.6, "y": 0.0, "label": "gate_edge"})
            runtime.ingest_pose_payload({"x": 0.0, "y": 0.0, "label": "gate_inside"})
            runtime.finish_stream()

            deadline = time.time() + 3.0
            state = runtime.state()
            while time.time() < deadline:
                state = runtime.state()
                if not state["is_running"]:
                    break
                time.sleep(0.05)

            session = runtime.latest_session()

        self.assertIn("East Gate", state["last_narration_text"])
        self.assertEqual(state["active_spot_id"], "plaza")
        self.assertGreater(session["event_count"], 0)
        self.assertIn("East Gate", session["latest_narration_text"])


if __name__ == "__main__":
    unittest.main()
