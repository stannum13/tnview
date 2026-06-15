from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.preview import complexity_preview, render_preview
from tnview.state import RunState


class ComplexityPreviewTests(unittest.TestCase):
    def test_easy_chain_preview_is_low_risk(self) -> None:
        state = _setup_state("examples/easy_chain.jsonl")

        preview = complexity_preview(state)

        self.assertEqual(preview.sites, 6)
        self.assertEqual(preview.interaction_range, "nearest-neighbor")
        self.assertEqual(preview.expected_lightcone, "linear")
        self.assertEqual(preview.early_chi_pressure, "mild")
        self.assertEqual(preview.contraction_risk, "low")
        self.assertEqual(preview.recommended_ansatz, "MPS / TEBD")

    def test_ladder_preview_flags_flattened_mps_risk(self) -> None:
        state = _setup_state("examples/ladder_snake_mismatch.jsonl")

        preview = complexity_preview(state)

        self.assertEqual(preview.geometry, "2D ladder")
        self.assertEqual(preview.interaction_range, "long-range")
        self.assertEqual(preview.early_chi_pressure, "high")
        self.assertEqual(preview.contraction_risk, "high")
        self.assertIn("MPS ordering is likely poor", preview.diagnosis)
        self.assertIn("try a different site ordering", preview.suggestions)

    def test_render_preview_contains_core_fields(self) -> None:
        state = _setup_state("examples/ladder_snake_mismatch.jsonl")

        output = render_preview(complexity_preview(state), width=100)

        self.assertIn("Model complexity preview", output)
        self.assertIn("sites:              8", output)
        self.assertIn("recommended ansatz:", output)
        self.assertIn("suggestions:", output)


def _setup_state(path: str) -> RunState:
    state = RunState()
    for event in parse_jsonl(Path(path).read_text().splitlines()):
        if event.__class__.__name__ in {"BondUpdated", "Checkpoint", "ObservableUpdated", "TdvpSweep"}:
            break
        state.apply(event)
    return state


if __name__ == "__main__":
    unittest.main()
