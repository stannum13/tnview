import unittest

from tnview.drift import drift_diagnostics
from tnview.events import Checkpoint
from tnview.state import RunState


def checkpoint(
    step: int,
    time: float,
    *,
    energy: float | None = -3.0,
    energy_drift: float | None = None,
    norm: float | None = 1.0,
) -> Checkpoint:
    return Checkpoint(
        step=step,
        time=time,
        max_entropy=None,
        mean_entropy=None,
        max_chi=None,
        num_saturated_bonds=None,
        total_trunc_error=None,
        energy=energy,
        energy_drift=energy_drift,
        norm=norm,
        complexity_status=None,
    )


class DriftDiagnosticsTests(unittest.TestCase):
    def test_waiting_for_conservation_telemetry(self) -> None:
        diagnostics = drift_diagnostics(RunState())

        self.assertEqual(diagnostics.points, ())
        self.assertEqual(diagnostics.risk, "unknown")
        self.assertEqual(diagnostics.energy.trend, "unknown")
        self.assertEqual(diagnostics.norm.severity, "unknown")
        self.assertIn("emit checkpoint energy and norm", diagnostics.recommendation)

    def test_classifies_visible_energy_and_norm_drift(self) -> None:
        state = RunState(
            checkpoints=[
                checkpoint(0, 0.0, energy_drift=0.0, norm=1.0),
                checkpoint(20, 0.2, energy_drift=1e-7, norm=0.999999999),
                checkpoint(80, 0.8, energy_drift=1.8e-6, norm=0.99999996),
            ]
        )

        diagnostics = drift_diagnostics(state)

        self.assertEqual(len(diagnostics.points), 3)
        self.assertEqual(diagnostics.energy.latest, 1.8e-6)
        self.assertAlmostEqual(diagnostics.norm.latest or 0.0, 4e-8)
        self.assertEqual(diagnostics.energy.severity, "watch")
        self.assertEqual(diagnostics.norm.severity, "watch")
        self.assertEqual(diagnostics.energy.trend, "rising")
        self.assertEqual(diagnostics.risk, "medium")
        self.assertIn("visible", diagnostics.diagnosis)

    def test_falls_back_to_energy_delta_from_first_checkpoint(self) -> None:
        state = RunState(
            checkpoints=[
                checkpoint(0, 0.0, energy=-12.0, energy_drift=None),
                checkpoint(10, 0.5, energy=-12.00000005, energy_drift=None),
            ]
        )

        diagnostics = drift_diagnostics(state)

        self.assertEqual(diagnostics.points[0].energy_drift, 0.0)
        self.assertAlmostEqual(diagnostics.points[1].energy_drift or 0.0, 5e-8)
        self.assertEqual(diagnostics.energy.severity, "ok")

    def test_flags_critical_accelerating_drift(self) -> None:
        state = RunState(
            checkpoints=[
                checkpoint(0, 0.0, energy_drift=1e-9, norm=1.0),
                checkpoint(1, 0.1, energy_drift=2e-5, norm=0.999998),
            ]
        )

        diagnostics = drift_diagnostics(state)

        self.assertEqual(diagnostics.risk, "high")
        self.assertEqual(diagnostics.energy.severity, "critical")
        self.assertEqual(diagnostics.norm.severity, "critical")
        self.assertEqual(diagnostics.energy.trend, "rising sharply")
        self.assertGreater(diagnostics.energy.slope_per_time or 0.0, 0.0)
        self.assertIn("reduce time step", diagnostics.recommendation)

    def test_recovering_trend_when_latest_drift_drops(self) -> None:
        state = RunState(
            checkpoints=[
                checkpoint(0, 0.0, energy_drift=5e-6, norm=0.999999),
                checkpoint(1, 1.0, energy_drift=2e-6, norm=0.9999999),
            ]
        )

        diagnostics = drift_diagnostics(state)

        self.assertEqual(diagnostics.energy.trend, "recovering")
        self.assertEqual(diagnostics.norm.trend, "recovering")


if __name__ == "__main__":
    unittest.main()
