import importlib.util
from pathlib import Path
import subprocess
import unittest


class ExampleScriptTests(unittest.TestCase):
    def test_quimb_mps_snapshot_example_imports_and_skips_without_quimb(self) -> None:
        path = Path("examples/quimb_mps_snapshot_example.py")
        spec = importlib.util.spec_from_file_location("quimb_mps_snapshot_example", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if importlib.util.find_spec("quimb") is None:
            self.assertEqual(module.main(), 0)
        else:
            self.assertTrue(callable(module.main))

    def test_quimb_tnoptimizer_example_imports_and_skips_without_quimb(self) -> None:
        path = Path("examples/quimb_tnoptimizer_example.py")
        spec = importlib.util.spec_from_file_location("quimb_tnoptimizer_example", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if importlib.util.find_spec("quimb") is None:
            self.assertEqual(module.main(), 0)
        else:
            self.assertTrue(callable(module.main))

    def test_quimb_demo_script_skips_without_quimb(self) -> None:
        result = subprocess.run(
            ["./scripts/demo_quimb.sh"],
            check=True,
            capture_output=True,
            text=True,
        )

        if importlib.util.find_spec("quimb") is None:
            self.assertIn("quimb is not installed", result.stdout)
        else:
            self.assertIn("quimb_mps_snapshot_example.py", result.stdout)

    def test_tenpy_dmrg_observer_example_imports_and_skips_without_tenpy(self) -> None:
        path = Path("examples/tenpy_dmrg_observer_example.py")
        spec = importlib.util.spec_from_file_location("tenpy_dmrg_observer_example", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if importlib.util.find_spec("tenpy") is None:
            self.assertEqual(module.main(), 0)
        else:
            self.assertTrue(callable(module.main))


if __name__ == "__main__":
    unittest.main()
