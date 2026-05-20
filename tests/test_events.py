import unittest

from tnview.events import BondUpdated, EventParseError, parse_jsonl_line


class EventParsingTests(unittest.TestCase):
    def test_parse_bond_updated_event(self) -> None:
        event = parse_jsonl_line(
            '{"event":"bond_updated","step":1,"time":0.1,"layer":"odd","bond":2,'
            '"site_left":2,"site_right":3,"entropy_before":0.4,"entropy_after":0.8,'
            '"renyi2_before":0.3,"renyi2_after":0.6,"chi_before":16,"chi_after":32,'
            '"chi_max":64,"trunc_error":1e-9,"discarded_weight":1e-9,'
            '"walltime_ms":2.5,"diagnostic_tags":["healthy"]}'
        )

        self.assertIsInstance(event, BondUpdated)
        assert isinstance(event, BondUpdated)
        self.assertEqual(event.bond, 2)
        self.assertEqual(event.entropy_after, 0.8)
        self.assertEqual(event.diagnostic_tags, ("healthy",))

    def test_rejects_unknown_event(self) -> None:
        with self.assertRaisesRegex(EventParseError, "unknown event"):
            parse_jsonl_line('{"event":"tensor_dump"}')


if __name__ == "__main__":
    unittest.main()
