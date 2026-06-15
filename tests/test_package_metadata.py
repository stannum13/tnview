import tomllib
from pathlib import Path
import unittest


class PackageMetadataTests(unittest.TestCase):
    def test_pyproject_declares_cli_and_optional_integrations(self) -> None:
        data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        project = data["project"]

        self.assertEqual(project["scripts"]["tnview"], "tnview.cli:main")
        self.assertEqual(project["license"], "MIT")
        self.assertEqual(project["license-files"], ["LICENSE"])
        self.assertIn("quimb", project["optional-dependencies"])
        self.assertIn("networkx>=3.0", project["optional-dependencies"]["quimb"])
        self.assertIn("physics-tenpy>=1.0", project["optional-dependencies"]["tenpy"])
        self.assertIn("https://github.com/stannum13/tnview", project["urls"]["Repository"])


if __name__ == "__main__":
    unittest.main()
