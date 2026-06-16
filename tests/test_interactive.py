from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.interactive import ReplayController, _canvas_width, _footer, _viewport_lines


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
        self.assertTrue(controller.handle_key("s"))
        self.assertTrue(controller.show_scope)
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

    def test_command_mode_dispatches_navigation_and_toggles(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.execute_command("checkpoint 1")
        self.assertEqual(controller.checkpoint_index, 1)
        controller.execute_command("next")
        self.assertEqual(controller.checkpoint_index, 2)
        controller.execute_command("time 0.2")
        self.assertEqual(controller.checkpoint_index, 1)
        controller.execute_command("bond 2")
        self.assertEqual(controller.selected_bond, 2)
        controller.execute_command("focus front")
        self.assertIsNotNone(controller.selected_bond)
        controller.execute_command("toggle entropy")
        self.assertFalse(controller.show_entropy)
        controller.execute_command("scope")
        self.assertTrue(controller.show_scope)
        controller.execute_command("diagnostics")
        self.assertFalse(controller.show_diagnostics)
        controller.execute_command("help")
        self.assertTrue(controller.show_help)

    def test_colon_key_enters_command_mode(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.handle_key(":")
        for char in "checkpoint 0":
            controller.handle_key(char)
        self.assertIn(":checkpoint 0_", _footer(controller))
        controller.handle_key("\n")

        self.assertEqual(controller.checkpoint_index, 0)

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

    def test_vertical_scroll_navigation_is_bounded(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.handle_key("KEY_NPAGE")
        self.assertEqual(controller.scroll_offset, 10)
        controller.handle_key("KEY_PPAGE")
        self.assertEqual(controller.scroll_offset, 0)

        controller.scroll_down(99)
        controller.clamp_scroll(lines=["line"] * 30, viewport_lines=10, viewport_columns=80)
        self.assertEqual(controller.scroll_offset, 20)

        controller.handle_key("KEY_END")
        controller.clamp_scroll(lines=["line"] * 30, viewport_lines=10, viewport_columns=80)
        self.assertEqual(controller.scroll_offset, 20)
        controller.handle_key("KEY_HOME")
        self.assertEqual(controller.scroll_offset, 0)

    def test_horizontal_scroll_navigation_is_bounded(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.handle_key(">")
        self.assertEqual(controller.column_offset, 12)
        controller.handle_key("<")
        self.assertEqual(controller.column_offset, 0)

        controller.scroll_right(99)
        controller.clamp_scroll(lines=["short", "0123456789" * 4], viewport_lines=10, viewport_columns=10)
        self.assertEqual(controller.column_offset, 30)

    def test_navigation_resets_two_axis_scroll(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.scroll_down(10)
        controller.scroll_right(10)
        controller.previous_checkpoint()

        self.assertEqual(controller.scroll_offset, 0)
        self.assertEqual(controller.column_offset, 0)

    def test_focus_keys_select_hotspots_and_center_window(self) -> None:
        events = parse_jsonl(Path("examples/ladder_snake_mismatch.jsonl").read_text().splitlines())
        controller = ReplayController(events, bond_limit=3)

        controller.handle_key("f")
        self.assertEqual(controller.selected_bond, 3)
        self.assertEqual(controller.bond_start, 2)

        controller.handle_key("m")
        self.assertEqual(controller.selected_bond, 3)
        self.assertEqual(controller.bond_start, 2)

        controller.handle_key("x")
        self.assertEqual(controller.selected_bond, 3)
        self.assertEqual(controller.bond_start, 2)

    def test_manual_bond_jump_centers_window(self) -> None:
        events = parse_jsonl(Path("examples/ladder_snake_mismatch.jsonl").read_text().splitlines())
        controller = ReplayController(events, bond_limit=3)

        controller.jump_bond(5)

        self.assertEqual(controller.selected_bond, 5)
        self.assertEqual(controller.bond_start, 4)

    def test_render_uses_current_controller_state(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)
        controller.previous_checkpoint()

        output = controller.render(width=100, unicode=False)

        self.assertIn("step 20", output)
        self.assertIn("healthy growth", output)

    def test_render_can_include_scope_panel(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events, show_scope=True)

        output = controller.render(width=120, unicode=False)

        self.assertIn("TNView scope", output)
        self.assertIn("Event ticks", output)
        self.assertIn("TNView dynamics viewer", output)

    def test_footer_and_help_advertise_scrolling(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)
        controller.scroll_down(5)
        controller.scroll_right(12)

        self.assertIn("scroll 5,12", _footer(controller))
        self.assertIn("T=", _footer(controller))
        self.assertIn(": commands", _footer(controller))
        self.assertLessEqual(len(_footer(controller)), 120)

        controller.handle_key("?")
        output = controller.render(width=100, unicode=False)

        self.assertIn("pgup/pgdn", output)
        self.assertIn("shift-left/right", output)
        self.assertIn("</>", output)
        self.assertIn("top/bottom", output)
        self.assertIn(":toggle", output)
        self.assertIn(":scope", output)
        self.assertIn(":diagnostics", output)
        self.assertIn("scope panel", output)

    def test_command_mode_footer_suggests_help(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        controller.handle_key(":")

        self.assertIn("try :help", _footer(controller))

    def test_viewport_lines_crop_rows_and_columns(self) -> None:
        lines = ["0123456789", "abcdefghij", "ABCDEFGHIJ"]

        output = _viewport_lines(
            lines,
            row_offset=1,
            column_offset=2,
            viewport_lines=2,
            viewport_columns=4,
        )

        self.assertEqual(output, ["cdef", "CDEF"])

    def test_canvas_width_leaves_room_for_horizontal_scroll(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        controller = ReplayController(events)

        self.assertEqual(_canvas_width(80, controller), 160)
        controller.scroll_right(200)
        self.assertGreaterEqual(_canvas_width(80, controller), 281)


if __name__ == "__main__":
    unittest.main()
