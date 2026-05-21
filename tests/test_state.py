from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.compute import compute_cost
from tnview.render import RenderOptions, render_run
from tnview.state import diagnose_run, entanglement_front, reduce_events
from tnview.warnings import early_warning


class StateRenderingTests(unittest.TestCase):
    def test_reduce_example_and_diagnose_chi_limited(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)

        self.assertIsNotNone(state.latest_checkpoint)
        assert state.latest_checkpoint is not None
        self.assertEqual(state.latest_checkpoint.step, 80)
        self.assertIsNotNone(state.run)
        self.assertIsNotNone(state.model_geometry)
        self.assertIsNotNone(state.ansatz_layout)
        self.assertIn("magnetization@site1", state.observables)
        self.assertTrue(state.bonds[1].saturated)
        self.assertEqual(len(state.sweeps), 2)
        self.assertEqual(diagnose_run(state), "chi-limited run")

    def test_render_contains_core_mvp_views(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)
        state.select_bond(1)

        output = render_run(state, RenderOptions(width=90, unicode=False))

        self.assertIn("MPS topology", output)
        self.assertIn("TEBD brick-wall updates", output)
        self.assertIn("TDVP sweep view", output)
        self.assertIn("Observables", output)
        self.assertIn("Entanglement heatmap", output)
        self.assertIn("Complexity rows", output)
        self.assertIn("Selected bond b1", output)
        self.assertIn("chi-limited", output)
        self.assertIn("drift diagnosis", output)
        self.assertIn("ansatz mismatch", output)
        self.assertIn("model geometry", output)

    def test_topology_rows_keep_bonds_between_sites(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)

        output = render_run(state, RenderOptions(width=90, unicode=False))

        self.assertIn("sites: 0    1    2    3", output)
        self.assertIn("bonds:    --   !!   --", output)

    def test_topology_alignment_handles_multi_digit_sites(self) -> None:
        lines = []
        for bond in range(9, 12):
            lines.append(
                '{"event":"bond_updated","step":1,"time":0.1,"layer":"even",'
                f'"bond":{bond},"site_left":{bond},"site_right":{bond + 1},'
                '"entropy_before":0.1,"entropy_after":0.2,'
                '"renyi2_before":0.1,"renyi2_after":0.2,'
                '"chi_before":8,"chi_after":16,"chi_max":32,'
                '"trunc_error":1e-12,"discarded_weight":1e-12,'
                '"walltime_ms":1.0,"diagnostic_tags":[]}'
            )
        state = reduce_events(parse_jsonl(lines))

        output = render_run(state, RenderOptions(width=90, unicode=False))

        self.assertIn("sites: 9    10   11   12", output)
        self.assertIn("bonds:    --   --   --", output)

    def test_entanglement_front_tracks_active_span(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)

        front = entanglement_front(state)

        self.assertIsNotNone(front)
        assert front is not None
        self.assertEqual(front.active_bonds, (1,))
        self.assertEqual(front.span, 1)
        self.assertIsNotNone(front.velocity_bonds_per_time)

    def test_early_warning_flags_saturated_run(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)

        warning = early_warning(state)

        self.assertEqual(warning.risk, "high")
        self.assertEqual(warning.estimated_chi_need, 512)
        self.assertIn("increase chi_max", warning.recommendation)

    def test_compute_cost_localizes_slowest_bond(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())
        state = reduce_events(events)

        cost = compute_cost(state)

        self.assertIsNotNone(cost.slowest_bond)
        assert cost.slowest_bond is not None
        self.assertEqual(cost.slowest_bond.bond, 1)
        self.assertEqual(cost.estimated_largest_tensor, "256 x 2 x 256")


if __name__ == "__main__":
    unittest.main()
