import unittest

from tnview.events import (
    AnsatzLayoutEvent,
    BondUpdated,
    ContractionPathEvent,
    EventParseError,
    ModelGeometryEvent,
    ObservableUpdated,
    RunStarted,
    TdvpSweep,
    parse_jsonl_line,
)


class EventParsingTests(unittest.TestCase):
    def test_parse_bond_updated_event(self) -> None:
        event = parse_jsonl_line(
            '{"event":"bond_updated","step":1,"time":0.1,"layer":"odd","bond":2,'
            '"site_left":2,"site_right":3,"entropy_before":0.4,"entropy_after":0.8,'
            '"renyi2_before":0.3,"renyi2_after":0.6,"chi_before":16,"chi_after":32,'
            '"chi_max":64,"trunc_error":1e-9,"discarded_weight":1e-9,'
            '"walltime_ms":2.5,"schmidt_values":[0.7,0.2,0.1],"diagnostic_tags":["healthy"]}'
        )

        self.assertIsInstance(event, BondUpdated)
        assert isinstance(event, BondUpdated)
        self.assertEqual(event.bond, 2)
        self.assertEqual(event.entropy_after, 0.8)
        self.assertEqual(event.schmidt_values, (0.7, 0.2, 0.1))
        self.assertEqual(event.diagnostic_tags, ("healthy",))

    def test_rejects_unknown_event(self) -> None:
        with self.assertRaisesRegex(EventParseError, "unknown event"):
            parse_jsonl_line('{"event":"tensor_dump"}')

    def test_parse_tdvp_sweep_event(self) -> None:
        event = parse_jsonl_line(
            '{"event":"tdvp_sweep","step":3,"time":0.3,"direction":"right",'
            '"start_site":0,"end_site":7,"max_residual":1e-8,'
            '"max_entropy_delta":0.12,"max_trunc_error":1e-10,'
            '"walltime_ms":42.0,"diagnostic_tags":["converged"]}'
        )

        self.assertIsInstance(event, TdvpSweep)
        assert isinstance(event, TdvpSweep)
        self.assertEqual(event.direction, "right")
        self.assertEqual(event.start_site, 0)
        self.assertEqual(event.diagnostic_tags, ("converged",))

    def test_parse_contraction_path_event(self) -> None:
        event = parse_jsonl_line(
            '{"event":"contraction_path","step":5,"time":0.5,"name":"path",'
            '"optimizer":"greedy","tensors":4,"steps":[{"left":"A","right":"B"}],'
            '"estimated_flops":1000000,"estimated_memory_mb":32.5,'
            '"peak_intermediate":"64 x 64","diagnostic_tags":["hot"]}'
        )

        self.assertIsInstance(event, ContractionPathEvent)
        assert isinstance(event, ContractionPathEvent)
        self.assertEqual(event.steps[0]["left"], "A")
        self.assertEqual(event.estimated_memory_mb, 32.5)

    def test_parse_run_metadata_events(self) -> None:
        run = parse_jsonl_line(
            '{"event":"run_started","run_id":"r1","time":0.0,"name":"ladder",'
            '"simulator":"toy","algorithm":"TEBD","parameters":{"dt":0.01}}'
        )
        geometry = parse_jsonl_line(
            '{"event":"model_geometry","step":0,"time":0.0,"name":"ladder",'
            '"sites":4,"dimensions":[2,2],"boundary":"open",'
            '"edges":[{"source":0,"target":1}]}'
        )
        ansatz = parse_jsonl_line(
            '{"event":"ansatz_layout","step":0,"time":0.0,"ansatz":"MPS",'
            '"ordering":[0,1,2,3],"tensors":[{"name":"A0","site":0}]}'
        )
        observable = parse_jsonl_line(
            '{"event":"observable_updated","step":4,"time":0.4,"name":"energy",'
            '"value":-3.14,"error":1e-9,"diagnostic_tags":["stable"]}'
        )

        self.assertIsInstance(run, RunStarted)
        self.assertIsInstance(geometry, ModelGeometryEvent)
        self.assertIsInstance(ansatz, AnsatzLayoutEvent)
        self.assertIsInstance(observable, ObservableUpdated)
        assert isinstance(geometry, ModelGeometryEvent)
        assert isinstance(ansatz, AnsatzLayoutEvent)
        assert isinstance(observable, ObservableUpdated)
        self.assertEqual(geometry.dimensions, (2, 2))
        self.assertEqual(ansatz.ordering, (0, 1, 2, 3))
        self.assertEqual(observable.diagnostic_tags, ("stable",))


if __name__ == "__main__":
    unittest.main()
