import unittest

from tnview.tail import render_run_log_tail


class TailTests(unittest.TestCase):
    def test_render_run_log_tail_shows_current_state_and_diagnostics(self) -> None:
        output = render_run_log_tail(
            [
                {"event": "run_start", "run_id": "r1", "library": "quimb", "algorithm": "dmrg"},
                {"event": "sweep_end", "sweep": 1, "energy": -1.0, "delta_energy": 1e-9, "max_chi": 128, "chi_max_configured": 128},
                {"event": "sweep_end", "sweep": 2, "energy": -1.0, "delta_energy": 1e-9, "max_chi": 128, "chi_max_configured": 128},
                {"event": "sweep_end", "sweep": 3, "energy": -1.0, "delta_energy": 1e-9, "max_chi": 128, "chi_max_configured": 128},
                {"event": "sweep_end", "sweep": 4, "energy": -1.0, "delta_energy": 1e-9, "max_chi": 128, "chi_max_configured": 128},
            ],
            width=120,
        )

        self.assertIn("TNView run tail", output)
        self.assertIn("run_id=r1", output)
        self.assertIn("sweep", output)
        self.assertIn("energy_plateau", output)
        self.assertIn("chi_saturation", output)
        self.assertIn("Pressure:", output)
        self.assertIn("health", output)
        self.assertIn("progress", output)
        self.assertIn("Trends:", output)
        self.assertIn("energy", output)
        self.assertIn("Events:", output)

    def test_render_run_log_tail_can_use_ascii_sparklines(self) -> None:
        output = render_run_log_tail(
            [
                {"event": "optimizer_step", "step": 1, "loss": 0.5},
                {"event": "optimizer_step", "step": 2, "loss": 0.25},
                {"event": "optimizer_step", "step": 3, "loss": 0.1},
            ],
            width=100,
            unicode=False,
        )

        self.assertIn("Trends:", output)
        self.assertIn("loss", output)
        self.assertIn("latest=0.1", output)

    def test_render_run_log_tail_marks_changed_fields(self) -> None:
        output = render_run_log_tail(
            [
                {"event": "optimizer_step", "step": 1, "loss": 0.5, "rss_mb": 100},
                {"event": "optimizer_step", "step": 2, "loss": 0.25, "rss_mb": 120},
            ],
            width=120,
            unicode=False,
        )

        self.assertIn("* step", output)
        self.assertIn("* loss", output)
        self.assertIn("(was 0.5)", output)
        self.assertIn("* rss", output)

    def test_render_run_log_tail_can_show_live_status_line(self) -> None:
        output = render_run_log_tail(
            [
                {"event": "run_start", "run_id": "r1", "library": "quimb", "algorithm": "tnoptimizer"},
                {"event": "optimizer_step", "step": 1, "loss": 0.5, "rss_mb": 100},
            ],
            width=120,
            unicode=False,
            live=True,
        )

        self.assertIn("* live", output)
        self.assertIn("run=r1", output)
        self.assertIn("Events:", output)
        self.assertIn("optimizer_step", output)


if __name__ == "__main__":
    unittest.main()
