import unittest
from pathlib import Path
import tempfile

from tnview.runlog import JsonlFollower, is_run_log_record, read_jsonl_records


class RunLogTests(unittest.TestCase):
    def test_read_jsonl_records_reports_invalid_lines(self) -> None:
        report = read_jsonl_records(['{"event":"run_start"}', "{bad json}"])

        self.assertFalse(report.valid)
        self.assertEqual(len(report.records), 1)
        self.assertIn("invalid JSON", report.errors[0])

    def test_read_jsonl_records_can_treat_partial_final_line_as_pending(self) -> None:
        report = read_jsonl_records(
            ['{"event":"run_start"}\n', '{"event":"sweep_end"'],
            allow_partial_final=True,
        )

        self.assertTrue(report.valid)
        self.assertEqual(len(report.records), 1)
        self.assertTrue(report.has_pending_final_record)

    def test_read_jsonl_records_still_reports_invalid_middle_line(self) -> None:
        report = read_jsonl_records(
            ['{"event":"run_start"}\n', '{"event":\n', '{"event":"sweep_end"}\n'],
            allow_partial_final=True,
        )

        self.assertFalse(report.valid)
        self.assertEqual(len(report.records), 2)
        self.assertIn("line 2", report.errors[0])

    def test_jsonl_follower_reads_only_new_complete_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            path.write_text('{"event":"run_start"}\n{"event":"sweep', encoding="utf-8")
            follower = JsonlFollower(path)

            first = follower.read_new_lines()
            self.assertEqual(first.lines, ('{"event":"run_start"}\n',))
            self.assertEqual(first.pending_final_line, '{"event":"sweep')

            with path.open("a", encoding="utf-8") as handle:
                handle.write('_end"}\n{"event":"run_end"}\n')
            second = follower.read_new_lines()

        self.assertFalse(second.reset)
        self.assertEqual(
            second.lines,
            ('{"event":"sweep_end"}\n', '{"event":"run_end"}\n'),
        )

    def test_jsonl_follower_resets_after_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            path.write_text('{"event":"run_start"}\n{"event":"run_end"}\n', encoding="utf-8")
            follower = JsonlFollower(path)
            self.assertEqual(len(follower.read_new_lines().lines), 2)

            path.write_text('{"event":"run_start","run_id":"new"}\n', encoding="utf-8")
            update = follower.read_new_lines()

        self.assertTrue(update.reset)
        self.assertEqual(update.lines, ('{"event":"run_start","run_id":"new"}\n',))

    def test_is_run_log_record_recognizes_run_events(self) -> None:
        self.assertTrue(is_run_log_record({"event": "sweep_end"}))
        self.assertFalse(is_run_log_record({"event": "bond_updated"}))


if __name__ == "__main__":
    unittest.main()
