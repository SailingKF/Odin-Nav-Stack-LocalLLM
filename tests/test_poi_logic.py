import tempfile
import unittest
from pathlib import Path

from core.interfaces.pose_provider import Pose2D
from core.poi.loader import load_pois
from core.poi.trigger import PoiTriggerEngine, is_pose_within_radius


class PoiLogicTests(unittest.TestCase):
    def test_load_pois_from_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            poi_path = Path(temp_dir) / "pois.yaml"
            poi_path.write_text(
                "\n".join(
                    [
                        "pois:",
                        "  - spot_id: lobby",
                        "    name: Main Lobby",
                        "    x: 1.0",
                        "    y: 2.0",
                        "    trigger_radius: 1.5",
                        "    narration_text: Lobby intro",
                    ]
                ),
                encoding="utf-8",
            )

            pois = load_pois(str(poi_path))

        self.assertEqual(len(pois), 1)
        self.assertEqual(pois[0].spot_id, "lobby")
        self.assertEqual(pois[0].trigger_radius, 1.5)

    def test_radius_trigger(self) -> None:
        poi = load_pois("content/poi/demo_pois.yaml")[0]
        self.assertTrue(is_pose_within_radius(Pose2D(x=0.5, y=0.2), poi))
        self.assertFalse(is_pose_within_radius(Pose2D(x=2.5, y=2.5), poi))

    def test_duplicate_trigger_is_blocked(self) -> None:
        poi = load_pois("content/poi/demo_pois.yaml")[0]
        engine = PoiTriggerEngine()

        first_hit = engine.evaluate(Pose2D(x=0.0, y=0.0), poi)
        second_hit = engine.evaluate(Pose2D(x=0.2, y=0.2), poi)

        self.assertTrue(first_hit)
        self.assertFalse(second_hit)


if __name__ == "__main__":
    unittest.main()
