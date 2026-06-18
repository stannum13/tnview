import importlib.util
from pathlib import Path
import unittest


def _load_ui_review():
    path = Path("scripts/ui_review.py")
    spec = importlib.util.spec_from_file_location("ui_review", path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class UiReviewTests(unittest.TestCase):
    def test_display_width_treats_wide_symbols_as_terminal_cells(self) -> None:
        review = _load_ui_review()

        self.assertEqual(review._display_width("abc"), 3)
        self.assertEqual(review._display_width("█▲"), 2)
        self.assertEqual(review._display_width("表"), 2)

    def test_ansi_stripping_preserves_visible_text(self) -> None:
        review = _load_ui_review()

        self.assertEqual(review._strip_ansi("\033[1;31mhot\033[0m"), "hot")


if __name__ == "__main__":
    unittest.main()
