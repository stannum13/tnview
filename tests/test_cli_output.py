import unittest

from tnview.cli_output import CliError, error_payload, render_error


class CliOutputTests(unittest.TestCase):
    def test_render_error_uses_sections(self) -> None:
        error = CliError(
            code="RUN_LOG_PARSE_ERROR",
            message="Could not read run log",
            path="bad.jsonl",
            reason="line 1: invalid JSON",
            suggestions=("tnview validate bad.jsonl",),
        )

        output = render_error(error)

        self.assertIn("Could not read run log", output)
        self.assertIn("Path:\n  bad.jsonl", output)
        self.assertIn("Reason:\n  line 1: invalid JSON", output)
        self.assertIn("Try:\n  tnview validate bad.jsonl", output)

    def test_error_payload_is_stable(self) -> None:
        payload = error_payload(CliError(code="X", message="failed", path="p"))

        self.assertEqual(
            payload,
            {"ok": False, "error": {"code": "X", "message": "failed", "path": "p"}},
        )


if __name__ == "__main__":
    unittest.main()
