import unittest

from tnview.events import parse_jsonl_line
from tnview.focus import choose_focus, choose_focus_for_bond
from tnview.state import RunState


def load_state(path: str) -> RunState:
    state = RunState()
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            event = parse_jsonl_line(line, line_number=line_number)
            if event is not None:
                state.apply(event)
    return state


class FocusTests(unittest.TestCase):
    def test_bottleneck_focus_selects_truncation_hotspot(self) -> None:
        state = load_state("examples/ladder_snake_mismatch.jsonl")

        focus = choose_focus(state, strategy="bottleneck", window=3)

        self.assertEqual(focus.bond, 3)
        self.assertEqual(focus.bond_start, 2)
        self.assertEqual(focus.bond_limit, 3)
        self.assertEqual(focus.reason, "truncation/chi bottleneck")

    def test_compute_focus_selects_slowest_update(self) -> None:
        state = load_state("examples/ladder_snake_mismatch.jsonl")

        focus = choose_focus(state, strategy="compute", window=5)

        self.assertEqual(focus.bond, 3)
        self.assertEqual(focus.reason, "slowest update")

    def test_choose_focus_for_bond_centers_existing_bond(self) -> None:
        state = load_state("examples/ladder_snake_mismatch.jsonl")

        focus = choose_focus_for_bond(state, 5, 3)

        self.assertEqual(focus.bond, 5)
        self.assertEqual(focus.bond_start, 4)
        self.assertEqual(focus.bond_limit, 3)

    def test_choose_focus_for_bond_handles_missing_bond(self) -> None:
        state = load_state("examples/ladder_snake_mismatch.jsonl")

        focus = choose_focus_for_bond(state, 99, 3)

        self.assertIsNone(focus.bond)
        self.assertIsNone(focus.bond_start)
        self.assertEqual(focus.bond_limit, 3)
        self.assertEqual(focus.reason, "bond not found")


if __name__ == "__main__":
    unittest.main()
