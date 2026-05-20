import subprocess
import sys
import unittest


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


if __name__ == "__main__":
    unittest.main()
