from io import StringIO
import json
import unittest

from tnview import RunLogger
from tnview.events import BondUpdated, Checkpoint, RunStarted, parse_jsonl
from tests.test_quimb_adapter import FakeMPS


class RunLoggerTests(unittest.TestCase):
    def test_logger_writes_valid_core_events(self) -> None:
        handle = StringIO()
        with RunLogger(handle) as logger:
            logger.run_started(run_id="r1", name="demo", simulator="test", algorithm="TEBD")
            logger.model_geometry(
                name="chain",
                sites=3,
                dimensions=[3],
                edges=[{"source": 0, "target": 1}, {"source": 1, "target": 2}],
            )
            logger.ansatz_layout(
                ansatz="MPS",
                ordering=[0, 1, 2],
                tensors=[{"name": "A0", "site": 0}],
            )
            logger.bond_updated(
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
            logger.checkpoint(
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

    def test_observe_mps_records_snapshot_without_setup_by_default(self) -> None:
        handle = StringIO()

        with RunLogger(handle) as logger:
            logger.observe_mps(FakeMPS(), step=3, time=0.3, chi_max=4)

        events = parse_jsonl(handle.getvalue().splitlines())
        bonds = [event for event in events if isinstance(event, BondUpdated)]

        self.assertEqual(len(bonds), 3)
        self.assertIsInstance(events[-1], Checkpoint)
        self.assertNotIsInstance(events[0], RunStarted)

    def test_observe_mps_can_include_setup_events(self) -> None:
        handle = StringIO()

        with RunLogger(handle) as logger:
            logger.observe_mps(FakeMPS(), run_id="fake", include_setup=True)

        events = parse_jsonl(handle.getvalue().splitlines())

        self.assertIsInstance(events[0], RunStarted)


if __name__ == "__main__":
    unittest.main()
