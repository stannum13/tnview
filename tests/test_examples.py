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
        self.assertIn("dmrg_bad_run.jsonl", names)
        self.assertIn("quimb_tnoptimizer_run.jsonl", names)
        kinds = {example.name: example.kind for example in examples}
        self.assertEqual(kinds["dmrg_bad_run.jsonl"], "run-log")
        self.assertEqual(kinds["quimb_tnoptimizer_run.jsonl"], "run-log")

    def test_renders_compare_command(self) -> None:
        output = render_examples(list_examples(Path("examples")))

        self.assertIn("Built-in examples", output)
        self.assertIn("compare replay: tnview compare", output)
        self.assertIn("compare run logs: tnview compare", output)


if __name__ == "__main__":
    unittest.main()
