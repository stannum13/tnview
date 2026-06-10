import unittest
from pathlib import Path

from tnview.validate import render_validation, validate_lines


class ValidationTests(unittest.TestCase):
    def test_validate_good_replay(self) -> None:
        with open("examples/tebd_run.jsonl", encoding="utf-8") as handle:
            report = validate_lines(handle.readlines())

        self.assertTrue(report.valid)
        self.assertEqual(report.event_count, 18)
        self.assertEqual(report.checkpoint_count, 3)
        self.assertEqual(report.bond_count, 3)

    def test_validate_reports_parse_errors(self) -> None:
        report = validate_lines(['{"event":"checkpoint","step":"bad"}\n'])

        self.assertFalse(report.valid)
        self.assertIn("errors:", render_validation(report))

    def test_validate_accepts_run_log_events(self) -> None:
        report = validate_lines(
            [
                '{"schema_version":"0.1","run_id":"r1","time":"2026-06-10T00:00:00Z","event":"run_start"}',
                '{"schema_version":"0.1","run_id":"r1","time":"2026-06-10T00:00:01Z","event":"sweep_end","sweep":1}',
            ]
        )

        self.assertTrue(report.valid)
        self.assertEqual(report.event_count, 0)
        self.assertEqual(report.run_log_count, 2)
        self.assertIn("run-log events:    2", render_validation(report))

    def test_all_example_replays_validate(self) -> None:
        for path in Path("examples").glob("*.jsonl"):
            with self.subTest(path=path):
                report = validate_lines(path.read_text(encoding="utf-8").splitlines())
                self.assertTrue(report.valid)
                self.assertGreater(report.event_count, 0)
                self.assertGreater(report.checkpoint_count, 0)


if __name__ == "__main__":
    unittest.main()
