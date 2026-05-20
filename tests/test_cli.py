import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def test_replay_can_render_earlier_checkpoint(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/tebd_run.jsonl",
                "--checkpoint",
                "1",
                "--ascii",
                "--width",
                "80",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("step 20", result.stdout)
        self.assertIn("healthy growth", result.stdout)
        self.assertNotIn("step 80", result.stdout.splitlines()[0])

    def test_replay_rejects_missing_checkpoint(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/tebd_run.jsonl",
                "--checkpoint",
                "99",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("out of range", result.stderr)

    def test_replay_view_toggles_hide_sections(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/tebd_run.jsonl",
                "--no-updates",
                "--no-inspector",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertNotIn("TEBD brick-wall updates", result.stdout)
        self.assertNotIn("Selected bond", result.stdout)
        self.assertIn("Entanglement heatmap", result.stdout)

    def test_replay_can_export_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "replay",
                    "examples/tebd_run.jsonl",
                    "--snapshot",
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.stdout, "")
            exported = output.read_text()
            self.assertIn('"run_status": "chi-limited run"', exported)
            self.assertIn('"selected_bond"', exported)

    def test_compare_renders_summary_table(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "compare",
                "examples/tebd_run.jsonl",
                "examples/tebd_run.jsonl",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Toy model comparison", result.stdout)
        self.assertIn("tebd_run.jsonl", result.stdout)
        self.assertIn("chi-limited run", result.stdout)


if __name__ == "__main__":
    unittest.main()
