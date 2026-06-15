from io import StringIO
import os
import unittest

from tnview.terminal import ansi, compact_event_time, render_meter, render_status_dot, supports_color


class TerminalPrimitiveTests(unittest.TestCase):
    def test_ansi_is_plain_when_disabled(self) -> None:
        self.assertEqual(ansi("ok", color="green", enabled=False), "ok")

    def test_ansi_applies_style_when_enabled(self) -> None:
        self.assertEqual(ansi("ok", color="green", bold=True, enabled=True), "\033[1;32mok\033[0m")

    def test_render_meter_has_ascii_fallback(self) -> None:
        self.assertEqual(render_meter("chi", 0.5, 1.0, width=4, unicode=False), "chi       [##..] ok")

    def test_render_meter_marks_warning(self) -> None:
        self.assertIn("[██░░]", render_meter("trunc", 0.5, 1.0, width=4, severity="warning"))
        self.assertIn("warning", render_meter("trunc", 0.5, 1.0, width=4, severity="warning"))

    def test_render_status_dot_has_ascii_fallback(self) -> None:
        self.assertEqual(render_status_dot("live", unicode=False), "*")

    def test_compact_event_time_prefers_timestamp(self) -> None:
        self.assertEqual(compact_event_time({"timestamp": "2026-06-10T01:02:03.000Z"}), "01:02:03")
        self.assertEqual(compact_event_time({"time": 1.25}), "t=1.25")
        self.assertEqual(compact_event_time({}), "--:--:--")

    def test_supports_color_respects_no_color(self) -> None:
        stream = StringIO()
        stream.isatty = lambda: True  # type: ignore[method-assign]
        old = os.environ.get("NO_COLOR")
        os.environ["NO_COLOR"] = "1"
        try:
            self.assertFalse(supports_color(stream))
        finally:
            if old is None:
                os.environ.pop("NO_COLOR", None)
            else:
                os.environ["NO_COLOR"] = old


if __name__ == "__main__":
    unittest.main()
