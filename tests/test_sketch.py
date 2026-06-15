import unittest

from tnview.events import parse_jsonl
from tnview.sketch import generate_sketch_replay, parse_sketch_prompt, render_sketch_list
from tnview.state import reduce_events
from tnview.validate import validate_lines


class SketchTests(unittest.TestCase):
    def test_parse_mps_sketch_prompt(self) -> None:
        spec = parse_sketch_prompt("mps sites=20 chi=64 profile=easy checkpoints=3 window=8 run_id=my-run")

        self.assertEqual(spec.topology, "mps")
        self.assertEqual(spec.sites, 20)
        self.assertEqual(spec.chi_max, 64)
        self.assertEqual(spec.profile, "easy")
        self.assertEqual(spec.checkpoints, 3)
        self.assertEqual(spec.window, 8)
        self.assertEqual(spec.run_id, "my-run")

    def test_parse_rejects_unknown_prompt_parts(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected key=value"):
            parse_sketch_prompt("mps sites=20 hard")

        with self.assertRaisesRegex(ValueError, "unsupported sketch topology"):
            parse_sketch_prompt("peps width=4 height=4")

    def test_generate_sketch_replay_is_valid_replay_telemetry(self) -> None:
        spec = parse_sketch_prompt("mps sites=10 chi=32 profile=hard checkpoints=3")
        replay = generate_sketch_replay(spec)
        report = validate_lines(replay.splitlines())
        events = parse_jsonl(replay.splitlines())
        state = reduce_events(events)

        self.assertTrue(report.valid)
        self.assertEqual(report.checkpoint_count, 3)
        self.assertEqual(report.bond_count, 9)
        self.assertEqual(state.run.run_id, "tnview-sketch")

    def test_render_sketch_list_shows_examples(self) -> None:
        output = render_sketch_list()

        self.assertIn("TNView sketches", output)
        self.assertIn("mps sites=32", output)
        self.assertIn("tnview sketch", output)


if __name__ == "__main__":
    unittest.main()
