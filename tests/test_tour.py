import unittest

from tnview.tour import render_tour, tour_payload


class TourTests(unittest.TestCase):
    def test_render_tour_explains_motivation_and_next_steps(self) -> None:
        output = render_tour()

        self.assertIn("TNView tour", output)
        self.assertIn("Why this exists", output)
        self.assertIn("Choose your path", output)
        self.assertIn("Tensor-network runs often fail slowly", output)
        self.assertIn("tnview sketch --wizard", output)
        self.assertIn("tnview scope", output)
        self.assertIn("tnview animate", output)
        self.assertIn("tnview watch", output)
        self.assertIn("tnview init", output)

    def test_tour_payload_lists_stable_steps(self) -> None:
        payload = tour_payload()

        self.assertEqual(payload["kind"], "tour")
        steps = payload["steps"]
        self.assertIsInstance(steps, list)
        self.assertGreaterEqual(len(steps), 3)
        self.assertEqual(steps[0]["name"], "try_without_data")


if __name__ == "__main__":
    unittest.main()
