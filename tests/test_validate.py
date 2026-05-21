import unittest

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


if __name__ == "__main__":
    unittest.main()
