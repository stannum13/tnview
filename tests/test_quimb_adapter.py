import json
from io import StringIO
import unittest

from tnview import RunLogger
from tnview.adapters.quimb import mps_to_events, mps_to_jsonl, tnoptimizer_callback, view_mps
from tnview.events import BondUpdated, parse_jsonl


class FakeMPS:
    L = 4
    tensors = [
        type("Tensor", (), {"shape": (2, 2)})(),
        type("Tensor", (), {"shape": (2, 3, 2)})(),
        type("Tensor", (), {"shape": (3, 2, 2)})(),
        type("Tensor", (), {"shape": (2, 2)})(),
    ]

    def bond_size(self, i: int, j: int) -> int:
        return {(0, 1): 2, (1, 2): 3, (2, 3): 2}[(i, j)]

    def singular_values(self, i: int) -> tuple[float, ...]:
        return {
            0: (0.9, 0.1),
            1: (0.7, 0.2, 0.1),
            2: (0.8, 0.2),
        }[i]


class FakeTNOptimizer:
    nevals = 7
    loss = 0.123
    loss_best = 0.1
    losses = [0.5, 0.2, 0.123]


class QuimbAdapterTests(unittest.TestCase):
    def test_mps_to_events_emits_valid_tnview_telemetry(self) -> None:
        events = mps_to_events(FakeMPS(), run_id="fake", chi_max=4)

        self.assertEqual(events[0]["event"], "run_started")
        self.assertEqual(events[1]["sites"], 4)
        self.assertEqual(events[2]["tensors"][1]["shape"], "2 x 3 x 2")
        self.assertEqual(events[-1]["max_chi"], 3)

        parsed = parse_jsonl(mps_to_jsonl(FakeMPS(), run_id="fake", chi_max=4).splitlines())
        bonds = [event for event in parsed if isinstance(event, BondUpdated)]

        self.assertEqual(len(bonds), 3)
        self.assertEqual(bonds[1].bond, 1)
        self.assertEqual(bonds[1].chi_after, 3)
        self.assertGreater(bonds[1].entropy_after, 0.0)

    def test_view_mps_renders_existing_tnview_surface(self) -> None:
        output = view_mps(FakeMPS(), run_id="fake", chi_max=4, width=100, unicode=False)

        self.assertIn("TNView dynamics viewer", output)
        self.assertIn("MPS topology", output)
        self.assertIn("Selected bond", output)
        self.assertIn("object-inspection", output)

    def test_tnoptimizer_callback_emits_optimizer_step(self) -> None:
        handle = StringIO()
        with RunLogger(handle, run_id="opt-run") as logger:
            callback = tnoptimizer_callback(logger)
            callback(FakeTNOptimizer())

        record = json.loads(handle.getvalue().strip())
        self.assertEqual(record["event"], "optimizer_step")
        self.assertEqual(record["run_id"], "opt-run")
        self.assertEqual(record["library"], "quimb")
        self.assertEqual(record["algorithm"], "tnoptimizer")
        self.assertEqual(record["step"], 7)
        self.assertEqual(record["loss"], 0.123)
        self.assertEqual(record["loss_best"], 0.1)
        self.assertEqual(record["loss_history_len"], 3)
        self.assertEqual(record["schema_version"], "0.1")
        self.assertIn("timestamp", record)


if __name__ == "__main__":
    unittest.main()
