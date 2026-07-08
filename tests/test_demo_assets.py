import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


class DemoAssetTests(unittest.TestCase):
    def test_readme_references_public_demo_cards(self) -> None:
        readme = Path("README.md").read_text(encoding="utf-8")

        for filename in (
            "watch-dashboard.svg",
            "demo-instrument.svg",
            "diagnostics.svg",
            "compare-runs.svg",
        ):
            self.assertIn(f"docs/demo/{filename}", readme)

    def test_demo_svg_script_writes_public_cards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/render_demo_svgs.py",
                    "--output-dir",
                    directory,
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            output = Path(directory)
            expected = {
                "demo-instrument.svg": "Generated MPS/TEBD instrument",
                "watch-dashboard.svg": "Live optimizer watch dashboard",
                "diagnostics.svg": "Run diagnostics with recovery hints",
                "compare-runs.svg": "Baseline vs candidate diagnostics",
            }
            self.assertEqual({path.name for path in output.glob("*.svg")}, set(expected))
            self.assertIn("wrote", result.stdout)
            for filename, title in expected.items():
                text = (output / filename).read_text(encoding="utf-8")
                self.assertIn("<svg", text)
                self.assertIn(title, text)
                self.assertIn("$ tnview", text)
                self.assertNotIn("~", text)


if __name__ == "__main__":
    unittest.main()
