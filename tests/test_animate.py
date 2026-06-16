from pathlib import Path
import unittest

from tnview.animate import (
    animation_frame_indices,
    animation_frame_indices_for_times,
    checkpoint_count,
    checkpoint_times,
    render_animation_frame,
)
from tnview.events import parse_jsonl


class AnimateTests(unittest.TestCase):
    def test_animation_frame_indices_are_evenly_spaced(self) -> None:
        self.assertEqual(animation_frame_indices(5, None), [0, 1, 2, 3, 4])
        self.assertEqual(animation_frame_indices(5, 3), [0, 2, 4])
        self.assertEqual(animation_frame_indices(5, 1), [0])
        self.assertEqual(animation_frame_indices(0, 3), [])

    def test_animation_frame_indices_can_filter_by_checkpoint_time(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())

        self.assertEqual(checkpoint_times(events), [0.0, 0.2, 0.8])
        self.assertEqual(animation_frame_indices_for_times(events, time_min=0.1, time_max=0.8), [1, 2])
        self.assertEqual(animation_frame_indices_for_times(events, frames=1, time_min=0.1), [1])

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
        self.assertIn("Oscilloscope signals", frame.text)
        self.assertIn("Event ticks", frame.text)
        self.assertIn("entropy", frame.text)
        self.assertIn("front", frame.text)
        self.assertIn("T=0.2", frame.text)
        self.assertIn("t=0.2", frame.text)
        self.assertNotIn("t=0  ", frame.text)

    def test_render_animation_frame_can_filter_signals(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        frame = render_animation_frame(
            events,
            checkpoint_index=2,
            frame_number=1,
            frame_count=1,
            window_radius=0.8,
            width=100,
            unicode=False,
            signals=("trunc",),
        )

        signal_block = frame.text.split("\n\n", 1)[0]
        self.assertIn("trunc", signal_block)
        self.assertNotIn("entropy", signal_block)
        self.assertNotIn("front", signal_block)

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
