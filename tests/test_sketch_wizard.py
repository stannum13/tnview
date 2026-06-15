import unittest

from tnview.sketch import parse_sketch_prompt
from tnview.sketch_wizard import run_sketch_wizard


class SketchWizardTests(unittest.TestCase):
    def test_wizard_defaults_build_parseable_prompt(self) -> None:
        output: list[str] = []
        result = run_sketch_wizard(
            input_fn=_answers(["", "", "", "", "", "", "", ""]),
            output_fn=output.append,
        )
        spec = parse_sketch_prompt(result.prompt)

        self.assertEqual(result.prompt, "mps sites=32 chi=128 profile=hard checkpoints=10 window=16")
        self.assertTrue(result.interactive)
        self.assertIsNone(result.output)
        self.assertEqual(spec.sites, 32)
        self.assertIn("Equivalent command:", output)

    def test_wizard_custom_values_and_output_path(self) -> None:
        result = run_sketch_wizard(
            input_fn=_answers(["mps", "48", "256", "12", "easy", "20", "n", "y", "runs/sketch.jsonl"]),
            output_fn=lambda _: None,
        )

        self.assertEqual(result.prompt, "mps sites=48 chi=256 profile=easy checkpoints=12 window=20")
        self.assertFalse(result.interactive)
        self.assertEqual(result.output, "runs/sketch.jsonl")

    def test_wizard_reprompts_invalid_integer(self) -> None:
        output: list[str] = []
        result = run_sketch_wizard(
            input_fn=_answers(["", "abc", "64", "", "", "", "", "", ""]),
            output_fn=output.append,
        )

        self.assertIn("Please enter an integer.", output)
        self.assertIn("sites=64", result.prompt)

    def test_wizard_reprompts_invalid_profile_and_yes_no(self) -> None:
        output: list[str] = []
        result = run_sketch_wizard(
            input_fn=_answers(["", "", "", "", "medium", "hard", "", "", "maybe", "n"]),
            output_fn=output.append,
        )

        self.assertIn("Please choose one of: easy/hard.", output)
        self.assertIn("Please answer yes or no.", output)
        self.assertTrue(result.interactive)
        self.assertIsNone(result.output)


def _answers(values: list[str]):
    iterator = iter(values)

    def answer(_: str) -> str:
        return next(iterator)

    return answer


if __name__ == "__main__":
    unittest.main()
