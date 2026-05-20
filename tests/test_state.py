from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.render import RenderOptions, render_run
from tnview.state import diagnose_run, reduce_events


class StateRenderingTests(unittest.TestCase):
    def test_reduce_example_and_diagnose_chi_limited(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)

        self.assertIsNotNone(state.latest_checkpoint)
        assert state.latest_checkpoint is not None
        self.assertEqual(state.latest_checkpoint.step, 80)
        self.assertTrue(state.bonds[1].saturated)
        self.assertEqual(diagnose_run(state), "chi-limited run")

    def test_render_contains_core_mvp_views(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)
        state.select_bond(1)

        output = render_run(state, RenderOptions(width=90, unicode=False))

        self.assertIn("MPS topology", output)
        self.assertIn("TEBD brick-wall updates", output)
        self.assertIn("Entanglement heatmap", output)
        self.assertIn("Complexity rows", output)
        self.assertIn("Selected bond b1", output)
        self.assertIn("chi-limited", output)


if __name__ == "__main__":
    unittest.main()
