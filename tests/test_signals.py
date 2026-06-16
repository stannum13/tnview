from pathlib import Path
import unittest

from tnview.events import parse_jsonl
from tnview.signals import (
    SignalPoint,
    detect_signal_markers,
    signal_payload,
    signal_points,
    signal_points_from_events,
    signal_series,
)
from tnview.state import reduce_events


class SignalExtractionTests(unittest.TestCase):
    def test_signal_points_capture_checkpoint_metrics(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        state = reduce_events(events)

        points = signal_points(state, selected_bond=1)

        self.assertEqual(len(points), 3)
        self.assertEqual(points[-1].step, 80)
        self.assertEqual(points[-1].time, 0.8)
        self.assertEqual(points[-1].entropy_max, 2.94)
        self.assertEqual(points[-1].max_chi, 256)
        self.assertEqual(points[-1].saturated_bonds, 1)
        self.assertEqual(points[-1].energy, -2.9999982)
        self.assertEqual(points[-1].complexity_status, "chi_limited")
        self.assertEqual(points[-1].front_bonds, (1,))
        self.assertEqual(points[-1].front_span, 1)
        self.assertEqual(points[-1].selected_bond, 1)
        self.assertEqual(points[-1].selected_chi, 256)

    def test_signal_points_can_filter_time_window(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        state = reduce_events(events)

        points = signal_points(state, time_min=0.1, time_max=0.3)

        self.assertEqual([point.time for point in points], [0.2])

    def test_signal_points_from_events_can_stop_at_checkpoint(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())

        points = signal_points_from_events(events, checkpoint_index=1)

        self.assertEqual([point.time for point in points], [0.0, 0.2])
        with self.assertRaisesRegex(ValueError, "out of range"):
            signal_points_from_events(events, checkpoint_index=99)

    def test_signal_series_uses_stable_names(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        points = signal_points_from_events(events, selected_bond=1)

        self.assertEqual(signal_series(points, "chi"), [2.0, 32.0, 256.0])
        self.assertEqual(signal_series(points, "selected_chi"), [2.0, 32.0, 256.0])
        with self.assertRaisesRegex(ValueError, "unknown signal"):
            signal_series(points, "unknown")

    def test_signal_payload_is_json_ready(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        points = signal_points_from_events(events, selected_bond=1)

        payload = signal_payload(points)

        self.assertEqual(len(payload["points"]), 3)
        latest = payload["points"][-1]
        self.assertEqual(latest["front_bonds"], [1])
        self.assertEqual(latest["saturated_bonds"], 1)
        self.assertEqual(latest["complexity_status"], "chi_limited")
        self.assertEqual(latest["selected_chi"], 256)

    def test_detect_signal_markers_finds_checkpoint_and_pressure(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text(encoding="utf-8").splitlines())
        points = signal_points_from_events(events, selected_bond=1)

        markers = detect_signal_markers(points)
        codes = [marker.code for marker in markers]

        self.assertEqual(codes.count("checkpoint"), 3)
        self.assertIn("chi_saturation", codes)
        self.assertIn("selected_pressure", codes)

    def test_detect_signal_markers_finds_front_growth_and_truncation_spike(self) -> None:
        points = [
            _point(step=0, time=0.0, front_span=1, trunc=1e-12),
            _point(step=1, time=0.1, front_span=3, trunc=2e-7),
        ]

        markers = detect_signal_markers(points)
        codes = [marker.code for marker in markers]

        self.assertIn("front_growth", codes)
        self.assertIn("truncation_spike", codes)

def _point(*, step: int, time: float, front_span: int, trunc: float) -> SignalPoint:
    return SignalPoint(
        step=step,
        time=time,
        entropy_max=float(front_span),
        entropy_mean=float(front_span) / 2.0,
        max_chi=16,
        max_trunc_error=trunc,
        total_trunc_error=trunc,
        front_span=front_span,
        front_bonds=tuple(range(front_span)),
    )


if __name__ == "__main__":
    unittest.main()
