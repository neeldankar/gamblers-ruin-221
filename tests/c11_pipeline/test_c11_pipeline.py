"""Chunk 11 pipeline test: every experiment and figure script runs end to end in quick mode.

Spec: plan/c11_final_run.md. Opt-in because it takes several minutes:
    GR_PIPELINE=1 pytest tests/c11_pipeline -v
"""
import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENTS = sorted((ROOT / "experiments").glob("e[0-9][0-9]*.py"))
FIGURES = sorted((ROOT / "figures").glob("f[0-9][0-9]*.py"))
META = {"git_hash", "timestamp", "platform", "machine", "python", "numpy", "scipy", "omp_num_threads"}

pytestmark = pytest.mark.skipif(os.environ.get("GR_PIPELINE") != "1", reason="set GR_PIPELINE=1 to run")


def run(script, *args, timeout=900):
    env = dict(os.environ, PYTHONPATH=str(ROOT), OMP_NUM_THREADS="1", MPLBACKEND="Agg")
    return subprocess.run([sys.executable, str(script), *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, timeout=timeout)


@pytest.fixture(scope="module")
def quick_results(tmp_path_factory):
    out = tmp_path_factory.mktemp("results")
    logs = {}
    for script in EXPERIMENTS:
        p = run(script, "--quick", "--outdir", str(out))
        logs[script.name] = p
    return out, logs


def test_there_is_something_to_run():
    assert EXPERIMENTS, "no experiments/eNN_*.py found"
    assert FIGURES, "no figures/fNN_*.py found"


@pytest.mark.parametrize("name", [s.name for s in EXPERIMENTS])
def test_experiment_runs_in_quick_mode(quick_results, name):
    _, logs = quick_results
    p = logs[name]
    assert p.returncode == 0, f"{name} failed:\n{p.stderr[-3000:]}"


def test_every_csv_is_stamped(quick_results):
    out, _ = quick_results
    csvs = sorted(out.glob("*.csv"))
    assert len(csvs) >= len(EXPERIMENTS), "each experiment writes at least one CSV"
    hashes = set()
    for path in csvs:
        with open(path) as fh:
            rows = list(csv.DictReader(fh))
        assert rows, f"{path.name} is empty"
        assert META <= set(rows[0]), f"{path.name} is missing metadata columns"
        hashes |= {r["git_hash"] for r in rows}
    assert len(hashes) == 1, f"all quick results should come from one commit, got {hashes}"


@pytest.mark.parametrize("name", [s.name for s in FIGURES])
def test_figure_scripts_run_from_csvs_only(quick_results, tmp_path, name):
    out, _ = quick_results
    p = run(ROOT / "figures" / name, "--results", str(out), "--outdir", str(tmp_path))
    assert p.returncode == 0, f"{name} failed:\n{p.stderr[-3000:]}"
    assert any(tmp_path.iterdir()), f"{name} wrote no figure"
