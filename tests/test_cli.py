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

    def test_replay_can_focus_bottleneck_window(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/ladder_snake_mismatch.jsonl",
                "--focus",
                "bottleneck",
                "--window",
                "3",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Selected bond b3", result.stdout)
        self.assertIn("viewport b2-b4 of 7 bonds", result.stdout)

    def test_replay_window_centers_selected_bond(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/ladder_snake_mismatch.jsonl",
                "-b",
                "5",
                "--window",
                "3",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Selected bond b5", result.stdout)
        self.assertIn("viewport b4-b6 of 7 bonds", result.stdout)

    def test_explicit_bond_overrides_focus_window(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "replay",
                "examples/ladder_snake_mismatch.jsonl",
                "--focus",
                "bottleneck",
                "-b",
                "5",
                "--window",
                "3",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Selected bond b5", result.stdout)
        self.assertIn("viewport b4-b6 of 7 bonds", result.stdout)

    def test_inspect_renders_focused_bottleneck_view(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "inspect",
                "examples/ladder_snake_mismatch.jsonl",
                "--window",
                "3",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Focus: truncation/chi bottleneck at b3", result.stdout)
        self.assertIn("Selected bond b3", result.stdout)
        self.assertIn("viewport b2-b4 of 7 bonds", result.stdout)

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

    def test_demo_command_renders_generated_replay(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "demo",
                "--sites",
                "12",
                "--checkpoints",
                "4",
                "--chi-max",
                "32",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("TNView demo | generated hard MPS/TEBD replay", result.stdout)
        self.assertIn("TNView", result.stdout)
        self.assertIn("Entanglement heatmap", result.stdout)
        self.assertIn("Selected bond", result.stdout)

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

    def test_compare_renders_run_log_summary_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            good = Path(directory) / "good.jsonl"
            bad = Path(directory) / "bad.jsonl"
            good.write_text(
                "\n".join(
                    [
                        '{"event":"run_start","run_id":"good","library":"quimb","algorithm":"dmrg"}',
                        '{"event":"sweep_end","sweep":3,"energy":-1.1,"delta_energy":1e-5,"max_chi":64,"max_trunc_err":1e-9,"rss_mb":512}',
                    ]
                ),
                encoding="utf-8",
            )
            bad.write_text(
                "\n".join(
                    [
                        '{"event":"run_start","run_id":"bad","library":"quimb","algorithm":"dmrg"}',
                        '{"event":"sweep_end","sweep":1,"energy":-1.0,"delta_energy":1e-9,"max_chi":128,"chi_max_configured":128,"max_trunc_err":2e-7,"rss_mb":700}',
                        '{"event":"sweep_end","sweep":2,"energy":-1.0,"delta_energy":1e-9,"max_chi":128,"chi_max_configured":128}',
                        '{"event":"sweep_end","sweep":3,"energy":-1.0,"delta_energy":1e-9,"max_chi":128,"chi_max_configured":128}',
                        '{"event":"sweep_end","sweep":4,"energy":-1.0,"delta_energy":1e-9}',
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "compare",
                    str(good),
                    str(bad),
                    "--sort",
                    "risk",
                    "--width",
                    "160",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("Run-log comparison", result.stdout)
        self.assertIn("good.jsonl", result.stdout)
        self.assertIn("bad.jsonl", result.stdout)
        self.assertIn("energy_plateau", result.stdout)
        self.assertLess(result.stdout.index("bad.jsonl"), result.stdout.index("good.jsonl"))

    def test_compare_run_log_csv_can_sort_by_metric(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            low = Path(directory) / "low.jsonl"
            high = Path(directory) / "high.jsonl"
            low.write_text(
                '{"event":"optimizer_step","run_id":"low","library":"quimb","algorithm":"tnoptimizer","step":1,"loss":0.2}\n',
                encoding="utf-8",
            )
            high.write_text(
                '{"event":"optimizer_step","run_id":"high","library":"quimb","algorithm":"tnoptimizer","step":1,"loss":0.9}\n',
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "compare",
                    str(low),
                    str(high),
                    "--metric",
                    "loss",
                    "--csv",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        lines = result.stdout.splitlines()
        self.assertTrue(lines[0].startswith("run,run_id,library,algorithm"))
        self.assertIn("high.jsonl,high", lines[1])
        self.assertIn("low.jsonl,low", lines[2])

    def test_preview_command_renders_setup_risk(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "preview",
                "examples/ladder_snake_mismatch.jsonl",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Toy model complexity preview", result.stdout)
        self.assertIn("geometry:           2D ladder", result.stdout)
        self.assertIn("interaction range:  long-range", result.stdout)
        self.assertIn("contraction risk:   high", result.stdout)
        self.assertIn("MPS ordering is likely poor", result.stdout)

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

    def test_search_finds_tensor_names(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "search",
                "examples/tebd_run.jsonl",
                "tensor:A2",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Search: tensor:A2", result.stdout)
        self.assertIn("ansatz", result.stdout)
        self.assertIn("A2", result.stdout)
        self.assertIn("site 2", result.stdout)

    def test_search_finds_contraction_path_tensor_names(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "search",
                "examples/ladder_snake_mismatch.jsonl",
                "tensor:A3",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Search: tensor:A3", result.stdout)
        self.assertIn("path", result.stdout)
        self.assertIn("A3", result.stdout)
        self.assertIn("ladder boundary contraction", result.stdout)

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

    def test_diagnose_command_reports_run_log_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            path.write_text(
                "\n".join(
                    [
                        '{"event":"sweep_end","run_id":"r","delta_energy":1e-9,"max_chi":256,"chi_max_configured":256}',
                        '{"event":"sweep_end","run_id":"r","delta_energy":1e-9,"max_chi":256,"chi_max_configured":256}',
                        '{"event":"sweep_end","run_id":"r","delta_energy":1e-9,"max_chi":256,"chi_max_configured":256}',
                        '{"event":"sweep_end","run_id":"r","delta_energy":1e-9,"max_trunc_err":2e-7}',
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "diagnose",
                    str(path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("TNView diagnostics", result.stdout)
        self.assertIn("energy_plateau", result.stdout)
        self.assertIn("chi_saturation", result.stdout)
        self.assertIn("truncation_floor", result.stdout)

    def test_tail_command_renders_run_log_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            path.write_text(
                "\n".join(
                    [
                        '{"event":"run_start","run_id":"r","library":"quimb","algorithm":"dmrg"}',
                        '{"event":"sweep_end","sweep":1,"energy":-1.0,"delta_energy":1e-4,"max_chi":64}',
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "tail",
                    str(path),
                    "--width",
                    "100",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("TNView run tail", result.stdout)
        self.assertIn("run_id=r", result.stdout)
        self.assertIn("Recent events", result.stdout)

    def test_tail_follow_renders_once_for_run_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run.jsonl"
            path.write_text(
                "\n".join(
                    [
                        '{"event":"run_start","run_id":"r","library":"quimb","algorithm":"tnoptimizer"}',
                        '{"event":"optimizer_step","step":1,"loss":0.5}',
                        '{"event":"optimizer_step","step":2,"loss":0.25}',
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "tail",
                    str(path),
                    "--follow",
                    "--max-refreshes",
                    "1",
                    "--interval",
                    "0.01",
                    "--no-clear",
                    "--ascii",
                    "--width",
                    "100",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertIn("TNView run tail", result.stdout)
        self.assertIn("Trends:", result.stdout)
        self.assertIn("loss", result.stdout)

    def test_tail_command_falls_back_to_replay_rendering(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "tail",
                "examples/tebd_run.jsonl",
                "--no-clear",
                "--ascii",
                "--width",
                "100",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("TNView dynamics viewer", result.stdout)
        self.assertIn("Entanglement heatmap", result.stdout)

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

    def test_export_command_writes_run_log_csv(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tnview.cli",
                "export",
                "examples/quimb_tnoptimizer_run.jsonl",
                "--format",
                "csv",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        lines = result.stdout.splitlines()
        self.assertTrue(lines[0].startswith("event,schema_version,run_id,timestamp"))
        self.assertIn("optimizer_step,0.1,quimb-opt", result.stdout)
        self.assertIn("loss", lines[0])

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

        self.assertIn("Built-in examples", result.stdout)
        self.assertIn("easy_chain.jsonl", result.stdout)
        self.assertIn("tnview compare", result.stdout)


if __name__ == "__main__":
    unittest.main()
