from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.scope import render_scope
from tnview.signals import signal_points_from_events


class ScopeRenderTests(unittest.TestCase):
    def test_render_scope_handles_empty_points(self) -> None:
        output = render_scope([], unicode=False)

        self.assertIn("TNView scope", output)
        self.assertIn("no checkpoint signal points", output)

    def test_render_scope_shows_signals_and_markers(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        points = signal_points_from_events(events, selected_bond=1)

        output = render_scope(points, unicode=False, width=120)

        self.assertIn("TNView scope | points=3", output)
        self.assertIn("Signals", output)
        self.assertIn("entropy", output)
        self.assertIn("max chi", output)
        self.assertIn("Event markers", output)
        self.assertIn("chi_saturation", output)
        self.assertIn("selected_pressure", output)

    def test_render_scope_can_filter_signals(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        points = signal_points_from_events(events, selected_bond=1)

        output = render_scope(points, signals=("trunc",), unicode=False, width=120)

        self.assertIn("trunc", output)
        self.assertNotIn("max chi  ", output)


if __name__ == "__main__":
    unittest.main()
