"""test_cyclo.py - exact arithmetic with roots of unity (src/cyclo.py).

  * cyclotomic_poly against the known polynomials and against the identity
    prod_{d | N} Phi_d(x) = x^N - 1;
  * RootSums.is_zero against a high-precision numerical evaluation
    (decimal, 150 digits) with a rigorous separation bound;
  * the pools of rays with entries 0 or N-th roots of unity, with the
    orthogonality relation recomputed in exact Gaussian-integer (N = 4) and
    Eisenstein-integer (N = 6) arithmetic and numerically (N = 5, 12).

Run alone:  python tests/test_cyclo.py
"""
from __future__ import annotations

import os
import random
import sys
import types
import unittest
from decimal import Decimal, getcontext
from math import gcd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

import cyclo  # noqa: E402

KNOWN = {            # coefficients, low degree first
    1: [-1, 1],
    2: [1, 1],
    3: [1, 1, 1],
    4: [1, 0, 1],
    5: [1, 1, 1, 1, 1],
    6: [1, -1, 1],
    7: [1, 1, 1, 1, 1, 1, 1],
    8: [1, 0, 0, 0, 1],
    9: [1, 0, 0, 1, 0, 0, 1],
    10: [1, -1, 1, -1, 1],
    11: [1] * 11,
    12: [1, 0, -1, 0, 1],
}

# ---- high-precision evaluation of sums of roots of unity (standard library only) ----
PREC = 150
getcontext().prec = PREC + 20


def _atan_inv(n):
    """atan(1/n) by its Taylor series."""
    n = Decimal(n)
    term = 1 / n
    total = term
    n2 = n * n
    k = 1
    eps = Decimal(10) ** -(PREC + 15)
    while abs(term) > eps:
        term = -term / n2
        k += 2
        total += term / k
    return total


PI = 16 * _atan_inv(5) - 4 * _atan_inv(239)          # Machin's formula


def _cos_sin(x):
    eps = Decimal(10) ** -(PREC + 15)
    c = s = Decimal(0)
    term = Decimal(1)
    k = 0
    while abs(term) > eps:
        if k % 4 == 0:
            c += term
        elif k % 4 == 1:
            s += term
        elif k % 4 == 2:
            c -= term
        else:
            s -= term
        k += 1
        term = term * x / k
    return c, s


_ROOTS = {}


def roots(N):
    if N not in _ROOTS:
        _ROOTS[N] = [_cos_sin(2 * PI * k / N) for k in range(N)]
    return _ROOTS[N]


def phi_euler(N):
    return sum(1 for k in range(1, N + 1) if gcd(k, N) == 1)


def numeric_abs2(N, counts):
    re = im = Decimal(0)
    for k, c in enumerate(counts):
        if c:
            re += c * roots(N)[k][0]
            im += c * roots(N)[k][1]
    return re * re + im * im


def numerically_zero(N, counts):
    """Rigorous zero test.  alpha = sum c_k zeta^k is an algebraic integer of
    the N-th cyclotomic field; if alpha != 0 its norm is a non-zero integer and
    every conjugate has absolute value at most B = sum |c_k|, hence
    |alpha| >= B^-(phi(N)-1).  The evaluation carries 150 digits."""
    B = sum(abs(c) for c in counts)
    a2 = numeric_abs2(N, counts)
    if B == 0:
        return True
    bound2 = Decimal(B) ** (-2 * (phi_euler(N) - 1))
    assert bound2 > Decimal(10) ** -120, "separation bound too small for the working precision"
    if a2 < Decimal(10) ** -200:
        return True
    assert a2 >= bound2 / 2, "value neither zero nor above the separation bound"
    return False


def polymul(a, b):
    out = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


class CyclotomicPolynomials(unittest.TestCase):
    def test_known_polynomials(self):
        for N, want in KNOWN.items():
            self.assertEqual(cyclo.cyclotomic_poly(N), want, f"Phi_{N}")

    def test_two_more_known_ones(self):
        self.assertEqual(cyclo.cyclotomic_poly(30), [1, 1, 0, -1, -1, -1, 0, 1, 1])
        p105 = cyclo.cyclotomic_poly(105)        # the first one with a coefficient outside {0, 1, -1}
        self.assertEqual(len(p105) - 1, 48)
        self.assertEqual(min(p105), -2)
        self.assertEqual(p105[7], -2)
        self.assertEqual(p105[41], -2)

    def test_product_over_divisors(self):
        for N in range(1, 61):
            prod = [1]
            for d in range(1, N + 1):
                if N % d == 0:
                    prod = polymul(prod, cyclo.cyclotomic_poly(d))
            self.assertEqual(prod, [-1] + [0] * (N - 1) + [1], f"N={N}")
            p = cyclo.cyclotomic_poly(N)
            self.assertEqual(len(p) - 1, phi_euler(N))
            self.assertEqual(p[-1], 1)

    def test_a_wrong_polynomial_is_noticed(self):
        wrong = dict(KNOWN)
        wrong[6] = [1, 1, 1]                      # that is Phi_3
        self.assertNotEqual(cyclo.cyclotomic_poly(6), wrong[6])
        self.assertNotEqual(cyclo.cyclotomic_poly(12), [1, 0, 1, 0, 1])


class RootSumsZeroTest(unittest.TestCase):
    def test_high_precision_helpers(self):
        # sanity of the numerical side: zeta^N = 1 and |zeta^k| = 1 to 140 digits
        tiny = Decimal(10) ** -140
        self.assertLess(abs(PI - Decimal("3.14159265358979323846264338327950288419716939937510")), Decimal(10) ** -49)
        for N in (3, 7, 30):
            for c, s in roots(N):
                self.assertLess(abs(c * c + s * s - 1), tiny)
            c, s = roots(N)[1]
            re, im = Decimal(1), Decimal(0)
            for _ in range(N):
                re, im = re * c - im * s, re * s + im * c
            self.assertLess(abs(re - 1) + abs(im), tiny)

    def test_named_vanishing_sums(self):
        self.assertTrue(cyclo.RootSums(3).is_zero([1, 1, 1]))               # 1 + w + w^2
        self.assertTrue(numerically_zero(3, [1, 1, 1]))
        for N in range(2, 31, 2):
            rs = cyclo.RootSums(N)
            for k in range(N):
                counts = [0] * N
                counts[k] += 1
                counts[(k + N // 2) % N] += 1
                self.assertTrue(rs.is_zero(counts), f"N={N} k={k}")
                self.assertTrue(numerically_zero(N, counts))
        # weight six, N = 30: z5 + z5^2 + z5^3 + z5^4 = -1 = w + w^2, so
        # z5 + z5^2 + z5^3 + z5^4 + (-w) + (-w^2) = 0 with -w = zeta30^25, -w^2 = zeta30^5
        rs = cyclo.RootSums(30)
        base = [6, 12, 18, 24, 5, 25]
        for shift in range(30):
            counts = [0] * 30
            for e in base:
                counts[(e + shift) % 30] += 1
            self.assertEqual(sum(counts), 6)
            self.assertTrue(rs.is_zero(counts), f"shift {shift}")
            self.assertTrue(numerically_zero(30, counts))

    def test_named_non_vanishing_sums(self):
        self.assertFalse(cyclo.RootSums(3).is_zero([1, 1, 0]))              # 1 + w = -w^2
        self.assertFalse(cyclo.RootSums(4).is_zero([1, 1, 1, 0]))           # 1 + i - 1 = i
        self.assertFalse(cyclo.RootSums(5).is_zero([1, 1, 1, 1, 0]))
        rs = cyclo.RootSums(30)
        for wrong in ([6, 12, 18, 24, 5, 24], [6, 12, 18, 24, 5, 26], [6, 12, 18, 24, 10, 20],
                      [6, 12, 18, 24, 5], [6, 12, 18, 5, 25, 0]):
            counts = [0] * 30
            for e in wrong:
                counts[e] += 1
            self.assertFalse(rs.is_zero(counts), str(wrong))
            self.assertFalse(numerically_zero(30, counts), str(wrong))
        # no proper non-empty subsum of the weight-six relation vanishes (it is minimal)
        base = [6, 12, 18, 24, 5, 25]
        for m in range(1, 2 ** 6 - 1):
            counts = [0] * 30
            for i, e in enumerate(base):
                if (m >> i) & 1:
                    counts[e] += 1
            self.assertFalse(rs.is_zero(counts))

    def test_random_integer_combinations(self):
        rng = random.Random(20261109)
        seen = {True: 0, False: 0}
        for N in list(range(1, 31)) * 3:
            rs = cyclo.RootSums(N)
            primes = [p for p in range(2, N + 1) if N % p == 0 and all(p % q for q in range(2, p))]
            for trial in range(12):
                kind = trial % 3
                counts = [0] * N
                if kind == 0 or not primes:
                    counts = [rng.randint(-3, 3) for _ in range(N)]
                else:
                    # an integer combination of the relations  sum_{j<p} zeta^(k + j N/p) = 0
                    for _ in range(rng.randint(1, 4)):
                        p = rng.choice(primes)
                        k = rng.randrange(N)
                        m = rng.randint(-2, 2)
                        for j in range(p):
                            counts[(k + j * (N // p)) % N] += m
                    if kind == 2:
                        counts[rng.randrange(N)] += rng.choice((1, -1))   # no longer zero
                want = numerically_zero(N, counts)
                self.assertEqual(rs.is_zero(counts), want, f"N={N} counts={counts}")
                if kind == 1 and primes:
                    self.assertTrue(want)
                if kind == 2 and primes:
                    self.assertFalse(want)
                seen[want] += 1
        self.assertGreater(seen[True], 200)
        self.assertGreater(seen[False], 200)

    def test_is_zero_does_not_modify_its_argument(self):
        counts = [2, -1, 0, 3, 1, 1, 0, 0, 0, 0, 0, 5]
        copy = list(counts)
        cyclo.RootSums(12).is_zero(counts)
        self.assertEqual(counts, copy)


# ---- pools ----
EISENSTEIN = [(1, 0), (1, 1), (0, 1), (-1, 0), (-1, -1), (0, -1)]     # zeta6^k = a + b w
GAUSS = [(1, 0), (0, 1), (-1, 0), (0, -1)]                            # i^k


def eisenstein_orth(u, v):
    """sum conj(u_i) v_i = 0 in Z[w], w^2 = -1 - w; entries are (a, b) = a + b w."""
    re = om = 0
    for (a, b), (c, d) in zip(u, v):
        a, b = a - b, -b                       # conj(a + b w) = (a - b) - b w
        re += a * c - b * d
        om += a * d + b * c - b * d
    return re == 0 and om == 0


def as_vectors(pool, table):
    zero = (0, 0)
    return types.SimpleNamespace(
        rays=[tuple(table[e] if e >= 0 else zero for e in r) for r in pool.rays],
        n=pool.n, d=pool.d, adj=pool.adj, bases=pool.bases)


def numeric_orth(N):
    def orth(u, v):
        counts = [0] * N
        for a, b in zip(u, v):
            if a >= 0 and b >= 0:
                counts[(b - a) % N] += 1
        return numerically_zero(N, counts)
    return orth


class RootPools(unittest.TestCase):
    def test_ray_counts(self):
        # d = 3: three axes, 3 N rays of weight two, N^2 of weight three
        for N in (2, 3, 4, 5, 6, 12):
            rays = cyclo.root_rays(3, N)
            self.assertEqual(len(rays), 3 + 3 * N + N * N)
            self.assertEqual(len(set(rays)), len(rays))
            for r in rays:
                self.assertEqual(next(e for e in r if e >= 0), 0)        # first non-zero entry is 1

    def test_sixth_roots(self):
        pool = cyclo.root_pool(3, 6, log=C.quiet)
        self.assertEqual(pool.n, 57)
        self.assertEqual(C.pool_discrepancies(as_vectors(pool, EISENSTEIN), eisenstein_orth), [])
        self.assertEqual(C.pool_discrepancies(pool, numeric_orth(6)), [])
        self.assertIsNone(pool.coloring(range(pool.n)))                  # not colorable
        nb, bases = C.structure_of(pool)
        self.assertIsNone(C.decide_colorable(nb, bases, range(pool.n)))  # ... by exhaustive search too
        core = pool.ks_core(log=C.quiet)
        self.assertIsNone(core.coloring(range(core.n)))

    def test_fourth_roots(self):
        pool = cyclo.root_pool(3, 4, log=C.quiet)
        self.assertEqual(pool.n, 31)
        self.assertEqual(C.pool_discrepancies(as_vectors(pool, GAUSS), C.gauss_orth), [])
        core = pool.ks_core(log=C.quiet)
        colorable = core.n == 0 or core.coloring(range(core.n)) is not None
        self.assertTrue(colorable, "the core of the 4th-root pool must be empty or colorable")
        # hence the whole pool is colorable (Corollary 4), also by exhaustive search
        ones = pool.coloring(range(pool.n))
        self.assertIsNotNone(ones)
        nb, bases = C.structure_of(pool)
        self.assertTrue(C.valid_coloring(nb, bases, range(pool.n), ones))
        self.assertIsNotNone(C.decide_colorable(nb, bases, range(pool.n)))

    def test_fifth_and_twelfth_roots_orthogonality(self):
        for N in (5, 12):
            pool = cyclo.root_pool(3, N, log=C.quiet)
            self.assertEqual(C.pool_discrepancies(pool, numeric_orth(N)), [], f"N={N}")

    def test_symmetry_generators_preserve_orthogonality(self):
        pool = cyclo.root_pool(3, 6, log=C.quiet)
        sym = cyclo.root_symmetry(pool, 6)
        pairs = C.pool_pairs(pool)
        self.assertTrue(sym.gens)
        for g in sym.gens:
            self.assertEqual(sorted(g), list(range(pool.n)))
            self.assertEqual({(min(g[i], g[j]), max(g[i], g[j])) for i, j in pairs}, pairs)

    def test_tampering_is_noticed(self):
        pool = cyclo.root_pool(3, 6, log=C.quiet)
        # (1) the wrong ring: reading the exponents as powers of i gives a different relation
        wrong = types.SimpleNamespace(
            rays=[tuple(GAUSS[e % 4] if e >= 0 else (0, 0) for e in r) for r in pool.rays],
            n=pool.n, d=pool.d, adj=pool.adj, bases=pool.bases)
        self.assertTrue(C.pool_discrepancies(wrong, C.gauss_orth))
        # (2) one orthogonal pair removed from the stored relation
        adj = list(pool.adj)
        j = adj[0].bit_length() - 1
        adj[0] &= ~(1 << j)
        adj[j] &= ~1
        bad = types.SimpleNamespace(rays=as_vectors(pool, EISENSTEIN).rays, n=pool.n, d=pool.d,
                                    adj=adj, bases=pool.bases)
        self.assertTrue(C.pool_discrepancies(bad, eisenstein_orth))
        # (3) a colorable sub-pool is not reported as a KS set
        self.assertIsNotNone(pool.coloring(range(20)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
