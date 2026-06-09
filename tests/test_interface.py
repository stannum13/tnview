import unittest

from tnview import view
from tests.test_quimb_adapter import FakeMPS


class InterfaceTests(unittest.TestCase):
    def test_view_dispatches_mps_like_object(self) -> None:
        output = view(FakeMPS(), run_id="fake", chi_max=4, width=100, unicode=False)

        self.assertIn("TNView dynamics viewer", output)
        self.assertIn("MPS topology", output)

    def test_view_rejects_unknown_object(self) -> None:
        with self.assertRaisesRegex(TypeError, "no TNView adapter"):
            view(object())


if __name__ == "__main__":
    unittest.main()
