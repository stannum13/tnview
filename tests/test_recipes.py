import unittest

from tnview.recipes import recipes_payload, render_recipes


class RecipesTests(unittest.TestCase):
    def test_render_recipes_shows_workflows(self) -> None:
        output = render_recipes()

        self.assertIn("TNView recipes", output)
        self.assertIn("Watch a run over SSH", output)
        self.assertIn("tnview watch", output)
        self.assertIn("tnview scope", output)
        self.assertIn("tnview sketch", output)

    def test_recipes_payload_is_stable(self) -> None:
        payload = recipes_payload()

        self.assertEqual(payload["kind"], "recipes")
        self.assertGreaterEqual(len(payload["recipes"]), 4)
        self.assertEqual(payload["recipes"][0]["name"], "watch-run")


if __name__ == "__main__":
    unittest.main()
