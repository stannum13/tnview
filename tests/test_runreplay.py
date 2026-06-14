import unittest

from tnview.runreplay import RunLogReplayController, render_run_log_replay


class RunLogReplayTests(unittest.TestCase):
    def test_render_run_log_replay_limits_records_by_index(self) -> None:
        records = [
            {"event": "run_start", "run_id": "r"},
            {"event": "optimizer_step", "step": 1, "loss": 0.5},
            {"event": "optimizer_step", "step": 2, "loss": 0.25},
        ]

        output = render_run_log_replay(records, index=1, width=100, unicode=False)

        self.assertIn("Run-log replay event 1/2", output)
        self.assertIn("step          1", output)
        self.assertNotIn("step          2", output)

    def test_controller_navigation_clamps_to_bounds(self) -> None:
        controller = RunLogReplayController(
            [
                {"event": "run_start"},
                {"event": "optimizer_step", "step": 1},
            ],
            index=0,
        )

        controller.previous_event()
        self.assertEqual(controller.index, 0)
        controller.next_event()
        controller.next_event()
        self.assertEqual(controller.index, 1)
        controller.first_event()
        self.assertEqual(controller.index, 0)
        controller.last_event()
        self.assertEqual(controller.index, 1)


if __name__ == "__main__":
    unittest.main()
