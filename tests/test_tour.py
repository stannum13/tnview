import unittest

from tnview.tour import render_tour


class TourTests(unittest.TestCase):
    def test_render_tour_explains_motivation_and_next_steps(self) -> None:
        output = render_tour()

        self.assertIn("TNView tour", output)
        self.assertIn("Why this exists", output)
        self.assertIn("Tensor-network runs often fail slowly", output)
        self.assertIn("tnview sketch --wizard", output)
        self.assertIn("tnview animate", output)
        self.assertIn("tnview watch", output)
        self.assertIn("tnview init", output)


if __name__ == "__main__":
    unittest.main()
