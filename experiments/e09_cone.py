"""Chunk 9 (checkpoint 3): the cone eigenvalue behind the four-player exponent, computed in the repo.

From (1, 1, 1, N-3), P(the chip leader busts first) decays like N^-alpha with alpha = sqrt(1/4 + lambda) - 1/2,
lambda the first Dirichlet eigenvalue of the Laplace-Beltrami operator on the spherical triangle cut out by the
cone at a vertex of the tetrahedron (O'Connor and Saloff-Coste). The same construction for the octant (the cone
of the three-player corner) has lambda = 12 exactly, so alpha = 3, which checks the method.

Method (the Project chat's script review3_inputs/c09-cone-fem.py; lam1 and alpha are copied unchanged):
  * lam1(V, m): split the flat triangle with vertices V into m^2 small triangles, project every node onto the unit
    sphere, and assemble P1 finite elements (stiffness K, mass M) on that mesh. The smallest eigenvalue of
    K u = lambda M u with u = 0 on the boundary (interior nodes only) approximates lambda with error O(h^2).
  * Richardson: lambda_h2 = (4 lam(2m) - lam(m)) / 3 on the two finest meshes removes the h^2 term;
    lambda = (16 r(2m) - r(m)) / 15 on two such values removes the h^4 term (three finest meshes).
Meshes m = 64, 128, 256, 512 (about 10 s), or 16, 32, 64 with --quick.

Writes results/e09_cone.csv, one row per domain ("octant", "tetrahedron_vertex"): m_finest, lambda_finest,
lambda_h2, lambda, alpha = alpha(lambda), lambda_exact (12 for the octant, NaN otherwise).
    python experiments/e09_cone.py [--quick] [--outdir DIR]
"""
import os

for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(var, "1")

import argparse

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from gr.runlog import save_results

FULL = (64, 128, 256, 512)
QUICK = (16, 32, 64)
DOMAINS = {  # name: (vertices of the flat triangle whose projection is the spherical triangle, exact lambda)
    "octant": ([(1, 0, 0), (0, 1, 0), (0, 0, 1)], 12.0),
    "tetrahedron_vertex": ([(1, 0, 0), (0.5, np.sqrt(3) / 2, 0), (0.5, 1 / (2 * np.sqrt(3)), np.sqrt(2 / 3))],
                           float("nan")),
}


def lam1(V, m):
    V = [np.asarray(v, float) for v in V]
    idx, P = {}, []
    for i in range(m + 1):
        for j in range(m + 1 - i):
            k = m - i - j; p = (i * V[0] + j * V[1] + k * V[2]) / m
            idx[(i, j)] = len(P); P.append(p / np.linalg.norm(p))
    P = np.array(P); n = len(P)
    T = []
    for i in range(m):
        for j in range(m - i):
            T.append((idx[(i, j)], idx[(i + 1, j)], idx[(i, j + 1)]))
            if i + j + 1 < m: T.append((idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]))
    T = np.array(T)
    a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
    cr = np.cross(b - a, c - a); area = 0.5 * np.linalg.norm(cr, axis=1)
    E = [c - b, a - c, b - a]
    R, C, Kv, Mv = [], [], [], []
    for r in range(3):
        for s in range(3):
            R.append(T[:, r]); C.append(T[:, s])
            Kv.append(np.einsum('ij,ij->i', E[r], E[s]) / (4 * area))
            Mv.append(area / 12 * (2 if r == s else 1))
    R, C = np.concatenate(R), np.concatenate(C)
    K = sp.csr_matrix((np.concatenate(Kv), (R, C)), shape=(n, n))
    M = sp.csr_matrix((np.concatenate(Mv), (R, C)), shape=(n, n))
    interior = np.array([q for (i, j), q in idx.items() if i > 0 and j > 0 and m - i - j > 0])
    K, M = K[interior][:, interior], M[interior][:, interior]
    w = spla.eigsh(K.tocsc(), k=1, M=M.tocsc(), sigma=0, which='LM', return_eigenvectors=False)
    return float(w[0])


def alpha(lam): return (-1 + np.sqrt(1 + 4 * lam)) / 2


def run_domain(name, meshes):
    V, exact = DOMAINS[name]
    ls = [lam1(V, m) for m in meshes]
    r1 = [(4 * ls[i + 1] - ls[i]) / 3 for i in range(len(ls) - 1)]  # h^2 removed
    r2 = [(16 * r1[i + 1] - r1[i]) / 15 for i in range(len(r1) - 1)]  # h^4 removed
    row = {"domain": name, "m_finest": meshes[-1], "lambda_finest": ls[-1], "lambda_h2": r1[-1],
           "lambda": r2[-1], "alpha": float(alpha(r2[-1])), "lambda_exact": exact}
    print(f"{name:20s} m = {meshes}  finest {ls[-1]:.8f}  h2 removed {r1[-1]:.9f}  h4 removed {r2[-1]:.9f}  "
          f"alpha {row['alpha']:.8f}", flush=True)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--outdir", default="results")
    args = parser.parse_args()
    np.random.default_rng(221)  # project convention; nothing here is random
    meshes = QUICK if args.quick else FULL
    rows = [run_domain(name, meshes) for name in DOMAINS]
    path = save_results(rows, "e09_cone", outdir=args.outdir)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
