from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.interactive import ReplayController, _footer


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

    def test_help_toggle_renders_help_text(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.handle_key("?")
        output = controller.render(width=100, unicode=False)

        self.assertIn("TNView interactive replay help", output)
        self.assertIn("jump to checkpoint", output)

    def test_jump_checkpoint_and_bond_input_modes(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.handle_key("g")
        controller.handle_key("1")
        self.assertIn("jump checkpoint", _footer(controller))
        controller.handle_key("\n")
        self.assertEqual(controller.checkpoint_index, 1)

        controller.handle_key("b")
        controller.handle_key("2")
        controller.handle_key("\n")
        self.assertEqual(controller.selected_bond, 2)

    def test_jump_methods_are_bounded(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.jump_checkpoint(99)
        self.assertEqual(controller.checkpoint_index, 2)
        controller.jump_checkpoint(-10)
        self.assertEqual(controller.checkpoint_index, 0)
        controller.jump_bond(99)
        self.assertNotEqual(controller.selected_bond, 99)

    def test_bond_window_navigation_is_bounded(self) -> None:
        events = parse_jsonl(Path("examples/ladder_snake_mismatch.jsonl").read_text().splitlines())
        controller = ReplayController(events, bond_limit=3)

        controller.next_bond_window()
        self.assertEqual(controller.bond_start, 3)
        controller.next_bond_window()
        self.assertEqual(controller.bond_start, 4)
        controller.previous_bond_window()
        self.assertEqual(controller.bond_start, 1)
        controller.previous_bond_window()
        self.assertEqual(controller.bond_start, 0)

    def test_render_uses_current_controller_state(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)
        controller.previous_checkpoint()

        output = controller.render(width=100, unicode=False)

        self.assertIn("step 20", output)
        self.assertIn("healthy growth", output)


if __name__ == "__main__":
    unittest.main()
