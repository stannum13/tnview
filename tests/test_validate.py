import unittest
from pathlib import Path

from tnview.validate import render_validation, validate_lines, validation_payload


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

    def test_validate_accepts_mixed_replay_and_run_log_events(self) -> None:
        report = validate_lines(
            [
                '{"event":"checkpoint","step":1,"time":0.1}\n',
                '{"event":"bond_updated","step":1,"time":0.1,"layer":"odd","bond":0,'
                '"site_left":0,"site_right":1,"entropy_before":0.1,"entropy_after":0.2,'
                '"chi_before":2,"chi_after":4,"chi_max":8,"trunc_error":1e-9}\n',
                '{"schema_version":"0.1","run_id":"r1","time":"2026-06-10T00:00:01Z",'
                '"event":"sweep_end","sweep":1}\n',
            ]
        )

        self.assertTrue(report.valid)
        self.assertEqual(report.event_count, 2)
        self.assertEqual(report.run_log_count, 1)
        self.assertEqual(report.warnings, ())

    def test_strict_validate_requires_run_log_metadata(self) -> None:
        report = validate_lines(['{"event":"sweep_end","sweep":1}'], strict=True)

        self.assertFalse(report.valid)
        self.assertIn("schema_version must be a string", "\n".join(report.errors))
        self.assertIn("run_id must be a string", "\n".join(report.errors))
        self.assertIn("timestamp or time is required", "\n".join(report.errors))

    def test_strict_validate_rejects_unknown_run_log_schema_version(self) -> None:
        report = validate_lines(
            [
                '{"schema_version":"9.9","run_id":"r1","time":"2026-06-10T00:00:00Z",'
                '"event":"run_start"}'
            ],
            strict=True,
        )

        self.assertFalse(report.valid)
        self.assertIn("unsupported schema_version '9.9'; expected '0.1'", "\n".join(report.errors))

    def test_validation_payload_is_stable(self) -> None:
        report = validate_lines(
            [
                '{"schema_version":"0.1","run_id":"r1","timestamp":"2026-06-10T00:00:00Z","event":"run_start"}'
            ],
            strict=True,
        )

        self.assertEqual(
            validation_payload(report),
            {
                "ok": True,
                "event_count": 0,
                "run_log_count": 1,
                "checkpoint_count": 0,
                "bond_count": 0,
                "warnings": [],
                "errors": [],
            },
        )

    def test_all_examples_validate(self) -> None:
        for path in Path("examples").glob("*.jsonl"):
            with self.subTest(path=path):
                report = validate_lines(path.read_text(encoding="utf-8").splitlines())
                self.assertTrue(report.valid)
                if report.run_log_count:
                    self.assertGreater(report.run_log_count, 0)
                else:
                    self.assertGreater(report.event_count, 0)
                    self.assertGreater(report.checkpoint_count, 0)


if __name__ == "__main__":
    unittest.main()
