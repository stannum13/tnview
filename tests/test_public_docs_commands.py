import json
import subprocess
import sys
import unittest


class PublicDocsCommandTests(unittest.TestCase):
    def test_onboarding_json_commands_have_expected_shape(self) -> None:
        tour = _json("tour", "--json")
        self.assertEqual(tour["kind"], "tour")
        self.assertEqual(tour["steps"][0]["name"], "try_without_data")
        self.assertIn("tnview watch", " ".join(tour["steps"][1]["commands"]))

        recipes = _json("recipes", "--json")
        self.assertEqual(recipes["kind"], "recipes")
        self.assertGreaterEqual(
            {recipe["name"] for recipe in recipes["recipes"]},
            {"watch-run", "compare-runs", "oscilloscope", "build-sketch"},
        )

        examples = _json("examples", "--json")
        self.assertEqual(examples["kind"], "examples")
        example_names = {entry["path"].split("/")[-1] for entry in examples["examples"]}
        self.assertGreaterEqual(
            example_names,
            {"tebd_run.jsonl", "dmrg_bad_run.jsonl", "quimb_tnoptimizer_run.jsonl"},
        )

    def test_core_workflow_json_commands_have_expected_shape(self) -> None:
        tail = _json("tail", "examples/quimb_tnoptimizer_run.jsonl", "--json")
        self.assertTrue(tail["ok"])
        self.assertEqual(tail["kind"], "run-log-tail")
        self.assertEqual(tail["event_count"], 6)
        self.assertEqual(tail["current"]["run_id"], "quimb-opt")
        self.assertEqual(tail["current"]["loss"], 0.07)

        diagnose = _json("diagnose", "examples/dmrg_bad_run.jsonl", "--profile", "default", "--json")
        self.assertFalse(diagnose["ok"])
        self.assertEqual(diagnose["warning_count"], 4)
        self.assertEqual(
            {diagnostic["code"] for diagnostic in diagnose["diagnostics"]},
            {"energy_plateau", "chi_saturation", "truncation_floor", "memory_growth"},
        )

    def test_lively_demo_commands_run_with_stable_landmarks(self) -> None:
        demo = _text(
            "demo",
            "--sites",
            "8",
            "--checkpoints",
            "3",
            "--chi-max",
            "64",
            "--ascii",
            "--no-color",
            "--width",
            "80",
        )
        self.assertIn("TNView instrument frame", demo)
        self.assertIn("MPS topology", demo)
        self.assertIn("Entanglement heatmap", demo)

        animated = _text(
            "demo",
            "--animate",
            "--frames",
            "1",
            "--interval",
            "0",
            "--no-clear",
            "--ascii",
            "--width",
            "80",
        )
        self.assertIn("TNView instrument frame 1/1", animated)
        self.assertIn("SIGNALS", animated)
        self.assertIn("MOTION", animated)

    def test_underrepresented_readme_commands_run_with_stable_landmarks(self) -> None:
        tail = _text("tail", "examples/quimb_tnoptimizer_run.jsonl", "--width", "100")
        self.assertIn("TNView run tail", tail)
        self.assertIn("run_id=quimb-opt", tail)
        self.assertIn("no warnings", tail)

        replay = _text("replay-runlog", "examples/quimb_tnoptimizer_run.jsonl", "--index", "2", "--ascii", "--width", "100")
        self.assertIn("Run-log replay event 2/5", replay)
        self.assertIn("run_id=quimb-opt", replay)
        self.assertIn("loss          0.42", replay)

        comparison = _text(
            "compare",
            "examples/dmrg_bad_run.jsonl",
            "examples/quimb_tnoptimizer_run.jsonl",
            "--sort",
            "risk",
            "--width",
            "120",
        )
        self.assertIn("Run-log comparison", comparison)
        self.assertIn("dmrg_bad_run.jsonl", comparison)
        self.assertIn("quimb_tnoptimizer_run", comparison)


def _json(*args: str) -> dict:
    return json.loads(_text(*args))


def _text(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "tnview.cli", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


if __name__ == "__main__":
    unittest.main()
