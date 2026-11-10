"""cyclo.py - pools of complex rays whose entries are 0 or N-th roots of unity.

A ray is stored as a tuple of exponents: -1 for the entry 0, k in [0, N) for
the entry zeta^k (zeta = exp(2 pi i / N)), with the first non-zero entry 1
(exponent 0).  Two such vectors span the same ray iff they are equal.

Orthogonality <u, v> = sum_i conj(u_i) v_i is a sum of N-th roots of unity.
It is decided EXACTLY: the sum is the polynomial P(x) = sum_k c_k x^k at
x = zeta, and P(zeta) = 0 iff the N-th cyclotomic polynomial divides P in
Z[x].  Floating point is used only to shortlist candidate pairs.
"""
from __future__ import annotations

import itertools
import time

import numpy as np

from ksengine import Pool, Symmetry


def cyclotomic_poly(N):
    """Coefficients (low degree first) of the N-th cyclotomic polynomial."""
    def polydiv(a, b):
        a = a[:]
        q = [0] * (len(a) - len(b) + 1)
        for i in range(len(a) - len(b), -1, -1):
            c = a[i + len(b) - 1]
            if c % b[-1] != 0:
                raise ValueError("non-exact division")
            c //= b[-1]
            q[i] = c
            for j, bj in enumerate(b):
                a[i + j] -= c * bj
        if any(a):
            raise ValueError("non-zero remainder")
        return q

    cache = {}

    def phi(n):
        if n in cache:
            return cache[n]
        p = [-1] + [0] * (n - 1) + [1]
        for dd in range(1, n):
            if n % dd == 0:
                p = polydiv(p, phi(dd))
        cache[n] = p
        return p

    return phi(N)


class RootSums:
    """Exact zero test for integer combinations of N-th roots of unity."""

    def __init__(self, N):
        self.N = N
        self.phi = cyclotomic_poly(N)
        self.deg = len(self.phi) - 1

    def is_zero(self, counts):
        """counts[k] = integer coefficient of zeta^k, k = 0..N-1."""
        a = list(counts)
        phi, deg = self.phi, self.deg
        for i in range(len(a) - 1, deg - 1, -1):
            c = a[i]
            if c:
                for j in range(deg + 1):
                    a[i - deg + j] -= c * phi[j]
        return not any(a[:deg])


def root_rays(d, N, max_weight=None, min_weight=1):
    """All vectors in ({0} u mu_N)^d with first non-zero entry 1."""
    rays = []
    for support in itertools.product((0, 1), repeat=d):
        w = sum(support)
        if w < min_weight or (max_weight is not None and w > max_weight):
            continue
        pos = [i for i in range(d) if support[i]]
        for exps in itertools.product(range(N), repeat=w - 1):
            v = [-1] * d
            v[pos[0]] = 0
            for p, e in zip(pos[1:], exps):
                v[p] = e
            rays.append(tuple(v))
    rays.sort()
    return rays


def root_pool(d, N, log=print, max_weight=None, name=None):
    t0 = time.time()
    rays = root_rays(d, N, max_weight=max_weight)
    n = len(rays)
    rs = RootSums(N)
    E = np.array(rays, dtype=np.int64)
    Z = np.where(E >= 0, np.exp(2j * np.pi * np.maximum(E, 0) / N), 0.0)
    adj = [0] * n
    block = 1024
    pairs = 0
    for s in range(0, n, block):
        G = np.conj(Z[s:s + block]) @ Z.T
        cand = np.argwhere(np.abs(G) < 1e-7)
        for k, j in cand:
            i = s + int(k)
            j = int(j)
            if j <= i:
                continue
            counts = [0] * N
            u, v = rays[i], rays[j]
            for a, b in zip(u, v):
                if a >= 0 and b >= 0:
                    counts[(b - a) % N] += 1
            if rs.is_zero(counts):
                adj[i] |= 1 << j
                adj[j] |= 1 << i
                pairs += 1
    log(f"root pool d={d} N={N}: {n} rays, {pairs} orthogonal pairs ({time.time()-t0:.1f}s)")
    pool = Pool(rays, d, adj, name=name or f"roots(d={d},N={N})", log=log)
    return pool


def root_symmetry(pool, N):
    """Generators: coordinate transposition, multiplying one coordinate by
    zeta, and complex conjugation (an anti-unitary map preserves orthogonality)."""
    d = pool.d
    index = {r: i for i, r in enumerate(pool.rays)}

    def canon(v):
        first = next(e for e in v if e >= 0)
        return tuple((e - first) % N if e >= 0 else -1 for e in v)

    gens = []

    def add(fn):
        img = []
        for r in pool.rays:
            j = index.get(canon(fn(r)))
            if j is None:
                return
            img.append(j)
        gens.append(tuple(img))

    for i in range(d - 1):
        def sw(r, i=i):
            r = list(r)
            r[i], r[i + 1] = r[i + 1], r[i]
            return tuple(r)
        add(sw)
    for i in range(d):
        def ph(r, i=i):
            r = list(r)
            if r[i] >= 0:
                r[i] = (r[i] + 1) % N
            return tuple(r)
        add(ph)
    add(lambda r: tuple((-e) % N if e >= 0 else -1 for e in r))
    return Symmetry(gens, pool.n)


if __name__ == "__main__":
    import sys
    d = int(sys.argv[1])
    for N in map(int, sys.argv[2:]):
        p = root_pool(d, N)
        c = p.ks_core()
        print(f"d={d} N={N}: core {c.n} rays, {len(c.bases)} bases; colorable={c.coloring(range(c.n)) is not None}", flush=True)
