from pathlib import Path
import unittest

from tnview.examples import list_examples, render_examples


class ExamplesTests(unittest.TestCase):
    def test_lists_builtin_replays(self) -> None:
        examples = list_examples(Path("examples"))

        names = {example.name for example in examples}
        self.assertIn("easy_chain.jsonl", names)
        self.assertIn("long_range_chi_limited.jsonl", names)
        self.assertIn("ladder_snake_mismatch.jsonl", names)
        self.assertIn("blocked_ladder.jsonl", names)

    def test_renders_compare_command(self) -> None:
        output = render_examples(list_examples(Path("examples")))

        self.assertIn("Built-in replay examples", output)
        self.assertIn("tnview compare", output)


if __name__ == "__main__":
    unittest.main()
