from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.search import render_tensor_search, search_tensors
from tnview.state import reduce_events


class TensorSearchTests(unittest.TestCase):
    def test_finds_ansatz_layout_tensor_by_name(self) -> None:
        state = reduce_events(parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines()))

        matches = search_tensors(state, "tensor:A2")

        self.assertEqual(matches[0].name, "A2")
        self.assertEqual(matches[0].source, "ansatz")
        self.assertEqual(matches[0].location, "site 2")

    def test_finds_contraction_path_tensor_by_name(self) -> None:
        state = reduce_events(parse_jsonl(Path("examples/ladder_snake_mismatch.jsonl").read_text().splitlines()))

        matches = search_tensors(state, "tensor:A3")

        self.assertEqual(matches[0].name, "A3")
        self.assertEqual(matches[0].source, "path")
        self.assertIn("ladder boundary contraction", matches[0].detail)

    def test_render_tensor_search_reports_no_matches(self) -> None:
        output = render_tensor_search([], query="tensor:missing", width=100)

        self.assertIn("Search: tensor:missing", output)
        self.assertIn("no matches", output)


if __name__ == "__main__":
    unittest.main()
