import tempfile
from pathlib import Path
import subprocess
import sys
import unittest

from tnview.events import parse_jsonl
from tnview.fixtures import generate_chain_fixture
from tnview.state import reduce_events
from tnview.validate import validate_lines


class FixtureGenerationTests(unittest.TestCase):
    def test_generate_chain_fixture_validates(self) -> None:
        output = generate_chain_fixture(sites=10, checkpoints=3, chi_max=64, profile="hard")
        report = validate_lines(output.splitlines())

        self.assertTrue(report.valid)
        self.assertEqual(report.checkpoint_count, 3)
        self.assertEqual(report.bond_count, 9)

    def test_hard_profile_can_saturate_chi(self) -> None:
        events = parse_jsonl(generate_chain_fixture(sites=12, checkpoints=4, chi_max=32, profile="hard").splitlines())
        state = reduce_events(events)

        self.assertGreater(state.latest_checkpoint.num_saturated_bonds or 0, 0)

    def test_fixture_cli_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "generated.jsonl"
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tnview.cli",
                    "fixture",
                    "chain",
                    "--sites",
                    "8",
                    "--checkpoints",
                    "2",
                    "--output",
                    str(output),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            report = validate_lines(output.read_text(encoding="utf-8").splitlines())
            self.assertTrue(report.valid)
            self.assertEqual(report.bond_count, 7)


if __name__ == "__main__":
    unittest.main()
