import unittest

from tnview.geometry import GeometryEdge, ModelGeometry, ansatz_mismatch, flattening_stress, geometry_diagnostics
from tnview.events import AnsatzLayoutEvent, ModelGeometryEvent
from tnview.state import BondState, RunState


class GeometryDiagnosticsTests(unittest.TestCase):
    def test_inferred_chain_geometry_is_aligned(self) -> None:
        state = _chain_state(chi=16, chi_max=64)

        diagnostics = geometry_diagnostics(state)

        self.assertEqual(diagnostics.flattening.model_geometry, "inferred 1D chain")
        self.assertEqual(diagnostics.flattening.total_edges, 3)
        self.assertEqual(diagnostics.flattening.long_range_edges, 0)
        self.assertEqual(diagnostics.flattening.diagnosis, "geometry aligned")
        self.assertEqual(diagnostics.mismatch.diagnosis, "ansatz geometry aligned")
        self.assertEqual(diagnostics.mismatch.mismatch_score, 0.0)

    def test_flattened_geometry_reports_high_stress_edges(self) -> None:
        state = _chain_state(chi=64, chi_max=64)
        geometry = ModelGeometry(
            name="2D ladder flattened to 1D",
            ansatz="MPS",
            ansatz_order=(0, 1, 2, 3),
            edges=(GeometryEdge(0, 1), GeometryEdge(0, 3), GeometryEdge(1, 2)),
        )

        diagnostics = geometry_diagnostics(state, geometry)

        self.assertEqual(diagnostics.flattening.total_edges, 3)
        self.assertEqual(diagnostics.flattening.long_range_edges, 1)
        self.assertEqual(len(diagnostics.flattening.high_stress_edges), 1)
        stressed = diagnostics.flattening.high_stress_edges[0]
        self.assertEqual(stressed.edge.sites, (0, 3))
        self.assertEqual(stressed.ansatz_distance, 3)
        self.assertEqual(stressed.crossed_bonds, (0, 1, 2))
        self.assertEqual(stressed.max_chi_pressure, 1.0)
        self.assertEqual(stressed.severity, "high")
        self.assertEqual(diagnostics.mismatch.high_pressure_bonds, (0, 1, 2))
        self.assertEqual(diagnostics.mismatch.diagnosis, "geometry mismatch with chi pressure")
        self.assertIn("try a different site ordering", diagnostics.mismatch.suggestions)

    def test_mapping_metadata_is_accepted_from_telemetry_shape(self) -> None:
        state = _chain_state(chi=8, chi_max=32)
        metadata = {
            "geometry": "custom graph",
            "current_ansatz": "MPS",
            "ordering": [0, 1, 2, 3],
            "physical_edges": [{"source": 0, "target": 2, "label": "diagonal", "weight": 2.0}],
        }

        summary = flattening_stress(state, metadata)

        self.assertEqual(summary.model_geometry, "custom graph")
        self.assertEqual(summary.edge_stress[0].edge.label, "diagonal")
        self.assertEqual(summary.edge_stress[0].stress, 2.0)
        self.assertEqual(summary.diagnosis, "mild flattening stress")

    def test_empty_state_waits_for_geometry_telemetry(self) -> None:
        summary = flattening_stress(RunState())
        mismatch = ansatz_mismatch(RunState())

        self.assertEqual(summary.total_edges, 0)
        self.assertEqual(summary.diagnosis, "waiting for geometry telemetry")
        self.assertEqual(mismatch.diagnosis, "waiting for geometry telemetry")
        self.assertEqual(mismatch.suggestions, ())

    def test_unknown_sites_do_not_crash_diagnostics(self) -> None:
        state = _chain_state(chi=8, chi_max=32)
        geometry = ModelGeometry(edges=(GeometryEdge(0, 99),), ansatz_order=(0, 1, 2, 3))

        summary = flattening_stress(state, geometry)

        self.assertIsNone(summary.edge_stress[0].ansatz_distance)
        self.assertEqual(summary.edge_stress[0].severity, "unknown")
        self.assertEqual(summary.diagnosis, "incomplete geometry telemetry")

    def test_uses_run_state_geometry_metadata_by_default(self) -> None:
        state = _chain_state(chi=64, chi_max=64)
        state.model_geometry = ModelGeometryEvent(
            step=0,
            time=0.0,
            name="ladder",
            sites=4,
            dimensions=(2, 2),
            boundary="open",
            edges=({"source": 0, "target": 3},),
        )
        state.ansatz_layout = AnsatzLayoutEvent(
            step=0,
            time=0.0,
            ansatz="MPS",
            ordering=(0, 1, 2, 3),
        )

        diagnostics = geometry_diagnostics(state)

        self.assertEqual(diagnostics.flattening.model_geometry, "ladder")
        self.assertEqual(diagnostics.flattening.long_range_edges, 1)
        self.assertEqual(diagnostics.mismatch.diagnosis, "geometry mismatch with chi pressure")


def _chain_state(*, chi: int, chi_max: int) -> RunState:
    state = RunState()
    for bond in range(3):
        state.bonds[bond] = BondState(
            bond=bond,
            site_left=bond,
            site_right=bond + 1,
            entropy=1.0 + bond,
            chi=chi,
            chi_max=chi_max,
            trunc_error=1e-8,
        )
    return state


if __name__ == "__main__":
    unittest.main()
