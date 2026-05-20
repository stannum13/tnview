import json
from pathlib import Path
import unittest

from tnview.events import parse_jsonl, parse_jsonl_line
from tnview.export import export_manifest, export_manifest_json, export_replay_jsonl, normalize_event


class ReplayExportTests(unittest.TestCase):
    def test_normalize_event_re_emits_defaults_for_replay(self) -> None:
        event = parse_jsonl_line(
            '{"event":"bond_updated","step":1,"time":0.1,"layer":"odd","bond":2,'
            '"site_left":2,"site_right":3,"entropy_before":0.4,"entropy_after":0.8,'
            '"renyi2_before":0.3,"renyi2_after":0.6,"chi_before":16,"chi_after":32,'
            '"chi_max":64,"trunc_error":1e-9,"discarded_weight":null,"walltime_ms":2.5}'
        )
        assert event is not None

        normalized = normalize_event(event)

        self.assertEqual(normalized["event"], "bond_updated")
        self.assertEqual(normalized["schmidt_values"], [])
        self.assertEqual(normalized["diagnostic_tags"], [])
        self.assertIsNone(normalized["discarded_weight"])

    def test_export_replay_jsonl_round_trips_parsed_events(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())

        exported = export_replay_jsonl(events)
        reparsed = parse_jsonl(exported.splitlines())

        self.assertTrue(exported.endswith("\n"))
        self.assertEqual(reparsed, events)

    def test_export_manifest_summarizes_replay_metadata(self) -> None:
        events = parse_jsonl(Path("examples/tebd_run.jsonl").read_text().splitlines())

        manifest = export_manifest(events)

        self.assertEqual(manifest["event_count"], len(events))
        self.assertEqual(manifest["checkpoint_count"], 3)
        self.assertEqual(manifest["bond_count"], 3)
        self.assertEqual(manifest["time_range"], {"start": 0.0, "end": 0.8})
        self.assertEqual(
            manifest["statuses"],
            [
                "trivial dynamics",
                "healthy growth",
                "chi_limited",
            ],
        )

    def test_export_manifest_json_is_compact_and_parseable(self) -> None:
        events = parse_jsonl(
            [
                '{"event":"checkpoint","step":0,"time":0.0,"max_entropy":null,'
                '"mean_entropy":null,"max_chi":null,"num_saturated_bonds":null,'
                '"total_trunc_error":null,"energy":null,"energy_drift":null,'
                '"norm":null,"complexity_status":"waiting"}'
            ]
        )

        exported = export_manifest_json(events)

        self.assertNotIn("\n", exported)
        self.assertEqual(json.loads(exported)["statuses"], ["waiting"])


if __name__ == "__main__":
    unittest.main()
