import numpy as np
import pytest

from gr.matrix import build_A
from gr.states import MOVES, StateSpace


@pytest.mark.parametrize("N", [3, 4, 7, 20, 101])
def test_state_count(N):
    assert StateSpace(N).n == (N - 1) * (N - 2) // 2


@pytest.mark.parametrize("N", [5, 20, 60])
def test_index_roundtrip(N):
    S = StateSpace(N)
    for i in range(S.n):
        assert S.index(S.state(i)) == i


@pytest.mark.parametrize("N", [4, 20, 60])
def test_sparsity_and_symmetry(N):
    A = build_A(StateSpace(N))
    assert np.diff(A.indptr).max() <= 7
    assert abs(A - A.T).max() == 0
    assert np.allclose(A.diagonal(), 1.0)


@pytest.mark.parametrize("N", [4, 9, 30])
def test_row_sums_of_Q(N):
    """Row x of Q sums to (6 - number of busting moves from x) / 6."""
    S = StateSpace(N)
    Q = -(build_A(S) - np.eye(S.n))
    for i in range(S.n):
        x = S.state(i)
        busts = 0
        for a, b in MOVES:
            y = list(x)
            y[a] += 1
            y[b] -= 1
            busts += min(y) == 0
        assert np.isclose(Q[i].sum(), (6 - busts) / 6)


@pytest.mark.parametrize("N", [10, 40])
def test_positive_definite(N):
    A = build_A(StateSpace(N)).toarray()
    assert np.linalg.eigvalsh(A).min() > 0
