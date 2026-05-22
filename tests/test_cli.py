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

    def test_replay_can_limit_bond_viewport(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/ladder_snake_mismatch.jsonl",
                "--bond-start",
                "2",
                "--bond-limit",
                "3",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("viewport b2-b4 of 7 bonds", result.stdout)
        self.assertIn("bond:       2 3 4", result.stdout)

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
                "examples/easy_chain.jsonl",
                "examples/long_range_chi_limited.jsonl",
                "examples/ladder_snake_mismatch.jsonl",
                "examples/blocked_ladder.jsonl",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Toy model comparison", result.stdout)
        self.assertIn("easy_chain.jsonl", result.stdout)
        self.assertIn("long_range_chi_limited", result.stdout)
        self.assertIn("ladder_snake_mismatch", result.stdout)
        self.assertIn("blocked_ladder.jsonl", result.stdout)
        self.assertIn("chi-limited run", result.stdout)
        self.assertIn("geometry", result.stdout)

    def test_compare_can_sort_by_risk_and_emit_csv(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "compare",
                "examples/easy_chain.jsonl",
                "examples/long_range_chi_limited.jsonl",
                "examples/blocked_ladder.jsonl",
                "--sort",
                "risk",
                "--csv",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        lines = result.stdout.splitlines()
        self.assertTrue(lines[0].startswith("model,step,time,max_entropy"))
        self.assertIn("long_range_chi_limited.jsonl", lines[1])
        self.assertIn("easy_chain.jsonl", result.stdout)

    def test_search_finds_tagged_bond(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "search",
                "examples/tebd_run.jsonl",
                "tag:chi_saturated",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Search: tag:chi_saturated", result.stdout)
        self.assertIn("b1", result.stdout)
        self.assertIn("chi-limited local bottleneck", result.stdout)

    def test_validate_command_reports_replay_shape(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "validate",
                "examples/tebd_run.jsonl",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Replay validation: valid", result.stdout)
        self.assertIn("checkpoints:       3", result.stdout)
        self.assertIn("bonds:             3", result.stdout)

    def test_export_command_writes_manifest(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "export",
                "examples/tebd_run.jsonl",
                "--format",
                "manifest",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn('"checkpoint_count":3', result.stdout)
        self.assertIn('"bond_count":3', result.stdout)

    def test_examples_command_lists_fixtures(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "examples",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Built-in replay examples", result.stdout)
        self.assertIn("easy_chain.jsonl", result.stdout)
        self.assertIn("tnview compare", result.stdout)


if __name__ == "__main__":
    unittest.main()
