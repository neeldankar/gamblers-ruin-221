# Three-player gambler's ruin as a sparse linear system

Math 221 final project, Fall 2026. Neel Dankar and David Heli Collin.

## Setup
```
conda env create -f environment.yml
conda activate gr221
pytest -q
```
If conda can't resolve an exact version in environment.yml, loosen that line (e.g. `scipy>=1.14`).

## Layout
- `gr/states.py`: live states (x1, x2, x3) and their indices
- `gr/matrix.py`: A = I - Q, right-hand sides, the reference solve, all six orders from one solve
- `gr/exact.py`: the same system in exact rational arithmetic (independent code, for tests)
- `gr/montecarlo.py`: simulation of the full game (cross-check only)
- `tests/`: exact-answer tests every solver must pass
- `experiments/` -> `results/*.csv` -> `figures/`
- `notes/decisions.md`: lab notebook

Status: phase 1 (core + tests) done. Next: direct solvers and conditioning.
