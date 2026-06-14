import unittest

from tnview.diagnose import diagnose_events, render_diagnostics


class DiagnoseTests(unittest.TestCase):
    def test_healthy_log_has_no_warnings(self) -> None:
        diagnostics = diagnose_events(
            [
                {"event": "sweep_end", "delta_energy": -1e-4, "max_chi": 64, "chi_max_configured": 256},
                {"event": "sweep_end", "delta_energy": -1e-5, "max_chi": 80, "chi_max_configured": 256},
            ]
        )

        self.assertEqual(diagnostics, [])
        self.assertIn("no warnings", render_diagnostics(diagnostics))

    def test_energy_plateau_rule(self) -> None:
        diagnostics = diagnose_events([{"event": "sweep_end", "delta_energy": 1e-9} for _ in range(4)])

        self.assertTrue(_has(diagnostics, "energy_plateau"))

    def test_chi_saturation_rule(self) -> None:
        diagnostics = diagnose_events(
            [{"event": "sweep_end", "max_chi": 256, "chi_max_configured": 256} for _ in range(3)]
        )

        self.assertTrue(_has(diagnostics, "chi_saturation"))

    def test_truncation_floor_rule(self) -> None:
        diagnostics = diagnose_events(
            [{"event": "sweep_end", "max_trunc_err": 2e-7, "delta_energy": 1e-9}]
        )

        self.assertTrue(_has(diagnostics, "truncation_floor"))

    def test_runtime_regression_rule(self) -> None:
        diagnostics = diagnose_events(
            [{"event": "sweep_end", "step_wall_s": value} for value in [10, 10, 11, 10, 10, 25]]
        )

        self.assertTrue(_has(diagnostics, "runtime_regression"))

    def test_memory_growth_rule(self) -> None:
        diagnostics = diagnose_events(
            [{"event": "sweep_end", "rss_mb": value} for value in [100, 110, 120, 125, 130]]
        )

        self.assertTrue(_has(diagnostics, "memory_growth"))

    def test_optimizer_stagnation_rule(self) -> None:
        diagnostics = diagnose_events(
            [{"event": "optimizer_step", "loss": 1.0 + idx * 1e-8} for idx in range(10)]
        )

        self.assertTrue(_has(diagnostics, "optimizer_stagnation"))

    def test_nonfinite_metric_rule(self) -> None:
        diagnostics = diagnose_events([{"event": "optimizer_step", "loss": float("nan")}])

        self.assertTrue(_has(diagnostics, "nonfinite_metric"))

    def test_canonical_form_drift_rule(self) -> None:
        diagnostics = diagnose_events([{"event": "sweep_end", "canonical_error": 2e-8}])

        self.assertTrue(_has(diagnostics, "canonical_form_drift"))

    def test_entropy_growth_rule(self) -> None:
        diagnostics = diagnose_events(
            [{"event": "sweep_end", "entropy_max": value} for value in [1.0, 1.1, 1.25, 1.4, 1.6]]
        )

        self.assertTrue(_has(diagnostics, "entropy_growth"))


def _has(diagnostics: list[object], code: str) -> bool:
    return any(getattr(diagnostic, "code", None) == code for diagnostic in diagnostics)


if __name__ == "__main__":
    unittest.main()
