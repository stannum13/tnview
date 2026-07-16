import json
import os
from pathlib import Path
import unittest

from scripts.measure_logger_overhead import measure


ROOT = Path(__file__).resolve().parents[1]


class E001PlanTests(unittest.TestCase):
    def test_smoke_config_references_existing_fixture_logs(self) -> None:
        config = json.loads((ROOT / "experiments/e001/configs/smoke.json").read_text())

        self.assertEqual(config["schema_version"], 1)
        self.assertEqual(config["mode"], "smoke")
        for fixture in config["fixture_logs"]:
            self.assertTrue((ROOT / fixture["path"]).exists(), fixture["path"])

    def test_canonical_config_preregisters_controls_and_limits(self) -> None:
        config = json.loads((ROOT / "experiments/e001/configs/canonical.json").read_text())

        self.assertEqual(config["mode"], "canonical")
        self.assertEqual(config["status"], "preregistered_not_run")
        self.assertLessEqual(config["false_stop_rate_max"], 0.05)
        self.assertIn("held_out_system_size", config["controls"])
        self.assertIn("exclude_energy_or_loss_features", config["controls"])
        self.assertGreaterEqual(len(config["seeds"]), 3)

    def test_reproduce_script_is_executable(self) -> None:
        script = ROOT / "scripts/reproduce_e001.sh"

        self.assertTrue(script.exists())
        self.assertTrue(os.access(script, os.X_OK))

    def test_logger_overhead_smoke_measurement_shape(self) -> None:
        result = measure(5)

        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["events_requested"], 5)
        self.assertEqual(result["records_written"], 7)
        self.assertGreater(result["events_per_second"], 0)


if __name__ == "__main__":
    unittest.main()
