from io import StringIO
import json
from pathlib import Path
import tempfile
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

    def test_logger_adds_run_log_metadata(self) -> None:
        handle = StringIO()

        with RunLogger(handle, run_id="run-1") as logger:
            logger.emit("sweep_end", sweep=2, energy=-1.23)

        record = json.loads(handle.getvalue())

        self.assertEqual(record["event"], "sweep_end")
        self.assertEqual(record["run_id"], "run-1")
        self.assertEqual(record["schema_version"], "0.1")
        self.assertIn("timestamp", record)
        self.assertTrue(record["time"].endswith("Z"))

    def test_logger_appends_and_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "runs" / "run.jsonl"

            with RunLogger(path, run_id="first") as logger:
                logger.emit("run_start")
            with RunLogger(path, run_id="second") as logger:
                logger.emit("run_end", status="ok")

            records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual([record["event"] for record in records], ["run_start", "run_end"])
        self.assertEqual(records[0]["run_id"], "first")
        self.assertEqual(records[1]["run_id"], "second")

    def test_non_strict_logger_does_not_raise_on_write_failure(self) -> None:
        logger = RunLogger(FailingHandle(), strict=False)

        logger.emit("run_start")

    def test_strict_logger_raises_on_write_failure(self) -> None:
        logger = RunLogger(FailingHandle(), strict=True)

        with self.assertRaises(OSError):
            logger.emit("run_start")

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

class FailingHandle:
    def write(self, _value: str) -> int:
        raise OSError("write failed")

    def flush(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
