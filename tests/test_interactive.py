from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.interactive import ReplayController


class ReplayControllerTests(unittest.TestCase):
    def test_checkpoint_navigation_is_bounded(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        self.assertEqual(controller.checkpoint_index, 2)
        controller.next_checkpoint()
        self.assertEqual(controller.checkpoint_index, 2)
        controller.previous_checkpoint()
        self.assertEqual(controller.checkpoint_index, 1)
        controller.previous_checkpoint()
        controller.previous_checkpoint()
        self.assertEqual(controller.checkpoint_index, 0)

    def test_bond_navigation_is_bounded(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.next_bond()
        self.assertEqual(controller.selected_bond, 1)
        controller.previous_bond()
        self.assertEqual(controller.selected_bond, 0)
        controller.previous_bond()
        self.assertEqual(controller.selected_bond, 0)

    def test_overlay_keys_toggle_sections(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        self.assertTrue(controller.handle_key("u"))
        self.assertFalse(controller.show_updates)
        self.assertFalse(controller.handle_key("q"))

    def test_render_uses_current_controller_state(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)
        controller.previous_checkpoint()

        output = controller.render(width=100, unicode=False)

        self.assertIn("step 20", output)
        self.assertIn("healthy growth", output)


if __name__ == "__main__":
    unittest.main()
