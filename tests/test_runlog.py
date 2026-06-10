import unittest

from tnview.runlog import is_run_log_record, read_jsonl_records


class RunLogTests(unittest.TestCase):
    def test_read_jsonl_records_reports_invalid_lines(self) -> None:
        report = read_jsonl_records(['{"event":"run_start"}', "{bad json}"])

        self.assertFalse(report.valid)
        self.assertEqual(len(report.records), 1)
        self.assertIn("invalid JSON", report.errors[0])

    def test_is_run_log_record_recognizes_run_events(self) -> None:
        self.assertTrue(is_run_log_record({"event": "sweep_end"}))
        self.assertFalse(is_run_log_record({"event": "bond_updated"}))


if __name__ == "__main__":
    unittest.main()
