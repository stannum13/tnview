import json
from io import StringIO
import unittest

from tnview import RunLogger
from tnview.adapters.tenpy import DMRGObserver, dmrg_sweep_record, dmrg_sweep_records, emit_dmrg_sweep


class FakeDMRGEngine:
    sweep_stats = {
        "sweep": [0, 1, 2],
        "E": [-1.0, -1.1, -1.12],
        "Delta_E": [-0.1, -0.02, -1e-9],
        "S": [0.4, 0.6, 0.7],
        "Delta_S": [0.2, 0.1, 0.05],
        "max_S": [0.8, 1.0, 1.1],
        "time": [1.0, 2.4, 4.0],
        "max_trunc_err": [1e-9, 2e-9, 3e-9],
        "max_E_trunc": [1e-10, 2e-10, 3e-10],
        "max_chi": [32, 64, 96],
        "norm_err": [1e-12, 2e-12, 3e-12],
    }


class TenpyAdapterTests(unittest.TestCase):
    def test_dmrg_sweep_record_maps_latest_sweep_stats(self) -> None:
        record = dmrg_sweep_record(FakeDMRGEngine())

        self.assertEqual(record["event"], "sweep_end")
        self.assertEqual(record["library"], "tenpy")
        self.assertEqual(record["algorithm"], "dmrg")
        self.assertEqual(record["sweep"], 2)
        self.assertEqual(record["energy"], -1.12)
        self.assertEqual(record["delta_energy"], -1e-9)
        self.assertEqual(record["entropy_max"], 1.1)
        self.assertEqual(record["wall_s"], 4.0)
        self.assertEqual(record["max_trunc_err"], 3e-9)
        self.assertEqual(record["max_chi"], 96)
        self.assertEqual(record["canonical_error"], 3e-12)

    def test_dmrg_sweep_records_maps_all_sweep_stats(self) -> None:
        records = dmrg_sweep_records(FakeDMRGEngine(), chi_max_configured=128)

        self.assertEqual(len(records), 3)
        self.assertEqual([record["sweep"] for record in records], [0, 1, 2])
        self.assertEqual(records[0]["energy"], -1.0)
        self.assertEqual(records[1]["wall_s"], 2.4)
        self.assertEqual(records[2]["chi_max_configured"], 128)

    def test_emit_dmrg_sweep_writes_run_log_event(self) -> None:
        handle = StringIO()
        with RunLogger(handle, run_id="tenpy-run") as logger:
            emit_dmrg_sweep(logger, FakeDMRGEngine())

        record = json.loads(handle.getvalue().strip())
        self.assertEqual(record["event"], "sweep_end")
        self.assertEqual(record["run_id"], "tenpy-run")
        self.assertEqual(record["library"], "tenpy")
        self.assertEqual(record["max_chi"], 96)

    def test_dmrg_observer_accepts_raw_stats(self) -> None:
        handle = StringIO()
        stats = {"sweep": [3], "E": [-2.0], "Delta_E": [-1e-6], "max_chi": [128]}
        with RunLogger(handle) as logger:
            observer = DMRGObserver(logger)
            observer.sweep_end(stats=stats, chi_max_configured=256)

        record = json.loads(handle.getvalue().strip())
        self.assertEqual(record["sweep"], 3)
        self.assertEqual(record["energy"], -2.0)
        self.assertEqual(record["chi_max_configured"], 256)

    def test_dmrg_observer_emits_new_sweeps_without_duplicates(self) -> None:
        handle = StringIO()
        with RunLogger(handle, run_id="tenpy-run") as logger:
            observer = DMRGObserver(logger)
            self.assertEqual(observer.emit_new_sweeps(FakeDMRGEngine(), chi_max_configured=128), 3)
            self.assertEqual(observer.emit_new_sweeps(FakeDMRGEngine(), chi_max_configured=128), 0)

        records = [json.loads(line) for line in handle.getvalue().splitlines()]
        self.assertEqual(len(records), 3)
        self.assertEqual([record["sweep"] for record in records], [0, 1, 2])
        self.assertEqual(records[-1]["max_chi"], 96)

    def test_dmrg_sweep_record_rejects_missing_stats(self) -> None:
        with self.assertRaises(TypeError):
            dmrg_sweep_record(object())


if __name__ == "__main__":
    unittest.main()
