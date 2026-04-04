import tempfile
import unittest

from core.interfaces.pose_provider import Pose2D
from core.narrator.mock_narrator import MockNarrator
from core.poi.loader import load_pois
from core.session.logger import JsonlSessionStore
from core.tour_orchestrator.orchestrator import TourOrchestrator


class NarratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.poi = load_pois("content/poi/demo_pois.yaml")[0]

    def test_mock_narrator_generates_standard_text(self) -> None:
        narrator = MockNarrator()

        narration_text = narrator.generate_narration(self.poi, "standard")

        self.assertEqual(narration_text, self.poi.standard_text)

    def test_mock_narrator_answers_question_from_faq(self) -> None:
        narrator = MockNarrator()

        answer_text = narrator.answer_question(self.poi, "Why does the tour start here?")

        self.assertIn("first stop", answer_text)

    def test_orchestrator_uses_narrator_output(self) -> None:
        narrator = MockNarrator()
        with tempfile.TemporaryDirectory() as temp_dir:
            session_store = JsonlSessionStore(temp_dir)
            session_store.start_session({"test_case": "orchestrator_uses_narrator"})
            orchestrator = TourOrchestrator(
                route_pois=[self.poi],
                narrator=narrator,
                session_store=session_store,
                narration_mode_default="extended",
            )

            orchestrator.handle_pose(Pose2D(x=self.poi.x, y=self.poi.y))
            state = orchestrator.get_state()
            session_store.close()

        self.assertIn(self.poi.extended_text, state["last_narration_text"])
        self.assertEqual(state["narrator_type"], "MockNarrator")


if __name__ == "__main__":
    unittest.main()
