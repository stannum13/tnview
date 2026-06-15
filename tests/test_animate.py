from pathlib import Path
import unittest

from tnview.animate import animation_frame_indices, checkpoint_count, render_animation_frame
from tnview.events import parse_jsonl


class AnimateTests(unittest.TestCase):
    def test_animation_frame_indices_are_evenly_spaced(self) -> None:
        self.assertEqual(animation_frame_indices(5, None), [0, 1, 2, 3, 4])
        self.assertEqual(animation_frame_indices(5, 3), [0, 2, 4])
        self.assertEqual(animation_frame_indices(5, 1), [0])
        self.assertEqual(animation_frame_indices(0, 3), [])

    def test_render_animation_frame_uses_time_window(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        frame = render_animation_frame(
            events,
            checkpoint_index=1,
            frame_number=1,
            frame_count=1,
            window_radius=0.0,
            width=100,
            unicode=False,
        )

        self.assertEqual(checkpoint_count(events), 3)
        self.assertIn("TNView oscilloscope frame 1/1", frame.text)
        self.assertIn("T=0.2", frame.text)
        self.assertIn("t=0.2", frame.text)
        self.assertNotIn("t=0  ", frame.text)

    def test_render_animation_frame_rejects_invalid_inputs(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())

        with self.assertRaisesRegex(ValueError, "checkpoint_index"):
            render_animation_frame(
                events,
                checkpoint_index=-1,
                frame_number=1,
                frame_count=1,
                window_radius=0.0,
            )
        with self.assertRaisesRegex(ValueError, "out of range"):
            render_animation_frame(
                events,
                checkpoint_index=99,
                frame_number=1,
                frame_count=1,
                window_radius=0.0,
            )
        with self.assertRaisesRegex(ValueError, "window_radius"):
            render_animation_frame(
                events,
                checkpoint_index=0,
                frame_number=1,
                frame_count=1,
                window_radius=-1.0,
            )


if __name__ == "__main__":
    unittest.main()
