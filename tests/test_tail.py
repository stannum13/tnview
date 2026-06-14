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
        self.assertIn("Trends:", output)
        self.assertIn("energy", output)

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


if __name__ == "__main__":
    unittest.main()
