from io import StringIO
import json
import unittest

from tnview import Recorder
from tnview.events import BondUpdated, Checkpoint, RunStarted, parse_jsonl


class RecorderTests(unittest.TestCase):
    def test_recorder_writes_valid_core_events(self) -> None:
        handle = StringIO()
        with Recorder(handle) as recorder:
            recorder.run_started(run_id="r1", name="demo", simulator="test", algorithm="TEBD")
            recorder.model_geometry(
                name="chain",
                sites=3,
                dimensions=[3],
                edges=[{"source": 0, "target": 1}, {"source": 1, "target": 2}],
            )
            recorder.ansatz_layout(
                ansatz="MPS",
                ordering=[0, 1, 2],
                tensors=[{"name": "A0", "site": 0}],
            )
            recorder.bond_updated(
                step=1,
                time=0.1,
                layer="odd",
                bond=1,
                site_left=1,
                site_right=2,
                entropy_before=0.2,
                entropy_after=0.4,
                chi_before=8,
                chi_after=16,
                chi_max=32,
                trunc_error=1e-10,
                schmidt_values=[0.7, 0.2, 0.1],
            )
            recorder.checkpoint(
                step=1,
                time=0.1,
                max_entropy=0.4,
                mean_entropy=0.3,
                max_chi=16,
                num_saturated_bonds=0,
                total_trunc_error=1e-10,
                complexity_status="healthy_growth",
            )

        lines = handle.getvalue().splitlines()
        events = parse_jsonl(lines)

        self.assertIsInstance(events[0], RunStarted)
        self.assertIsInstance(events[3], BondUpdated)
        self.assertIsInstance(events[4], Checkpoint)
        self.assertEqual(json.loads(lines[0])["run_id"], "r1")


if __name__ == "__main__":
    unittest.main()
