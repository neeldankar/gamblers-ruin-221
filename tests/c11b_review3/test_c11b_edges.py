"""Checkpoint 3, part B: edge cases found by the outside review (Codex F-C3-1, F-C3-2, F-C3-3).

None of these affects a result of the final run; they make the library safe outside the tested range.
Validated in the Project chat on Nov 14 against an independent stand-in package.
"""
import numpy as np
import pytest
import scipy.sparse as sp

from gr.four import FourStateSpace, LumpedSpace
from gr.matrix import build_A
from gr.refine import cg_componentwise
from gr.states import StateSpace
from gr.stationary import gauss_seidel, jacobi, sor


@pytest.mark.parametrize("method", ["jacobi", "gauss_seidel", "sor"])
def test_zero_right_hand_side_returns_the_zero_solution_at_once(method):
    """b = 0 used to give 0/0 = NaN in the stopping test and run to maxiter. Rule: when ||b|| = 0 the residual
    is not scaled, so x0 = 0 has residual 0 and the run stops after 0 sweeps."""
    A = build_A(StateSpace(10))
    b = np.zeros(A.shape[0])
    run = {"jacobi": lambda: jacobi(A, b, maxiter=5), "gauss_seidel": lambda: gauss_seidel(A, b, maxiter=5),
           "sor": lambda: sor(A, b, 1.5, maxiter=5)}[method]
    x, info = run()
    assert info["iterations"] == 0
    assert info["converged"] is True
    assert np.all(x == 0)
    assert not np.any(np.isnan(info["residual_norms"]))


def test_zero_right_hand_side_with_a_nonzero_start_converges_to_zero():
    A = build_A(StateSpace(10))
    b = np.zeros(A.shape[0])
    x, info = gauss_seidel(A, b, rtol=1e-12, x0=np.ones(A.shape[0]))
    assert info["converged"] is True
    assert np.max(np.abs(x)) < 1e-10
    assert info["residual_norms"][0] == pytest.approx(np.linalg.norm(A @ np.ones(A.shape[0])))


def test_cg_componentwise_reports_the_final_iterate_not_the_last_check_point():
    """A = [1], b = [1]: CG is exact after one step, which is not a multiple of check_every. The returned
    `converged` and the last omega must describe the returned x."""
    A = sp.csr_matrix(np.array([[1.0]]))
    x, info = cg_componentwise(A, np.array([1.0]), tol=1e-14, check_every=10)
    assert x[0] == 1.0
    assert info["iterations"] == 1
    assert info["converged"] is True
    assert info["omegas"][-1] == 0.0


def test_cg_componentwise_is_unchanged_when_it_stops_at_a_check_point():
    A = build_A(StateSpace(12))
    b = np.ones(A.shape[0])
    x, info = cg_componentwise(A, b, tol=1e-13, check_every=1)
    assert info["converged"] is True
    assert len(info["omegas"]) == info["iterations"] + 1   # k = 0, 1, ..., iterations: no extra entry
    assert info["omegas"][-1] <= 1e-13


@pytest.mark.parametrize("space", [FourStateSpace, LumpedSpace])
def test_four_player_index_rejects_fractional_chips(space):
    S = space(10)
    assert S.index((1, 1, 1, 7)) == 0
    with pytest.raises(ValueError):
        S.index((1.5, 1.5, 1, 6))
