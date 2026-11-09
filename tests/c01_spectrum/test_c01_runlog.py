"""Chunk 1: the results logger every experiment uses."""
import csv

import pytest

runlog = pytest.importorskip("gr.runlog")

REQUIRED = {"git_hash", "timestamp", "platform", "machine", "python", "numpy", "scipy", "omp_num_threads"}


def test_metadata_keys():
    meta = runlog.metadata()
    assert REQUIRED <= set(meta)
    assert all(isinstance(v, str) for v in meta.values())


def test_save_results_stamps_every_row(tmp_path):
    rows = [{"N": 10, "value": 1.5}, {"N": 20, "value": 2.5}]
    path = runlog.save_results(rows, "unit_test", outdir=tmp_path)
    assert path.name == "unit_test.csv"
    with open(path) as fh:
        got = list(csv.DictReader(fh))
    assert len(got) == 2
    assert {"N", "value"} | REQUIRED <= set(got[0])
    assert got[1]["N"] == "20" and float(got[1]["value"]) == 2.5
