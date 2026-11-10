"""test_pools.py - the pools of rays.

Each pool built by src/pools.py and src/pools3d.py is compared with

  * counts that are independent mathematical facts (number of rays, of
    orthogonal pairs, of bases), and
  * a from-scratch recomputation of orthogonality and of all bases from the
    integer vectors (tests/_common.py: itertools and integer dot products).

Negative tests: tampered Pool objects must be flagged by the comparison.

Run alone:  python tests/test_pools.py
"""
from __future__ import annotations

import itertools
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

import pools  # noqa: E402
import pools3d  # noqa: E402
from ksengine import Pool  # noqa: E402


def naive_box_rays(d, H):
    """Rays of Z^d with a representative of max-norm <= H: one vector per
    line through the origin, chosen as the primitive vector whose first
    non-zero entry is positive.  Written without src/pools.py."""
    from math import gcd
    rays = set()
    for v in itertools.product(range(-H, H + 1), repeat=d):
        if not any(v):
            continue
        g = 0
        for x in v:
            g = gcd(g, abs(x))
        if g != 1:
            continue                      # not primitive: its line is represented by v / g
        first = next(x for x in v if x)
        if first < 0:
            continue                      # -v represents the same line
        rays.add(v)
    return rays


class BoxPools(unittest.TestCase):
    def check_box(self, d, H, n_rays, n_pairs=None, n_bases=None):
        pool = pools.box_pool(d, H, log=C.quiet)
        self.assertEqual(pool.n, n_rays)
        self.assertEqual(set(pool.rays), naive_box_rays(d, H))
        self.assertEqual(C.pool_discrepancies(pool, C.int_orth), [])
        if n_pairs is not None:
            self.assertEqual(len(C.pool_pairs(pool)), n_pairs)
            self.assertEqual(len(C.orth_pairs(pool.rays, C.int_orth)), n_pairs)
        if n_bases is not None:
            self.assertEqual(len(pool.bases), n_bases)
        return pool

    def test_d3_maxnorm2(self):
        self.check_box(3, 2, 49, 138, 26)

    def test_d3_maxnorm3(self):
        self.check_box(3, 3, 145)

    def test_d4_entries_0_pm1(self):
        self.check_box(4, 1, 40, 220, 32)

    def test_d5_entries_0_pm1_and_core(self):
        pool = self.check_box(5, 1, 121, n_bases=136)
        core = pool.ks_core(log=C.quiet)
        self.assertEqual(core.n, 105)
        self.assertEqual(C.pool_discrepancies(core, C.int_orth), [])
        # the core, recomputed here: delete rays in no basis or with fewer than d partners
        nb = C.neighbour_sets(pool.n, C.orth_pairs(pool.rays, C.int_orth))
        bases = C.cliques(nb, 5)
        alive = set(range(pool.n))
        while True:
            covered = set()
            for b in bases:
                if set(b) <= alive:
                    covered |= set(b)
            keep = {v for v in alive if v in covered and len(nb[v] & alive) >= 5}
            if keep == alive:
                break
            alive = keep
        self.assertEqual(len(alive), 105)
        self.assertEqual({pool.rays[v] for v in alive}, set(core.rays))
        self.assertEqual(core.parent_index, sorted(alive))

    def test_ray_counts_formula(self):
        # (2H+1)^d - 1 non-zero vectors; lines counted by inclusion-exclusion over the gcd
        # (Moebius function), independent of any enumeration of rays
        def mu(n):
            res, p = 1, 2
            while p * p <= n:
                if n % p == 0:
                    n //= p
                    if n % p == 0:
                        return 0
                    res = -res
                p += 1
            return -res if n > 1 else res

        def count(d, H):
            return sum(mu(g) * ((2 * (H // g) + 1) ** d - 1) for g in range(1, H + 1)) // 2

        for d, H, want in ((3, 2, 49), (3, 3, 145), (4, 1, 40), (5, 1, 121)):
            self.assertEqual(count(d, H), want)
            self.assertEqual(len(pools.box_rays(d, H)), want)


class OtherPools(unittest.TestCase):
    def test_e8(self):
        pool = pools.e8_pool(log=C.quiet)
        self.assertEqual(pool.n, 120)
        self.assertEqual(len(pool.bases), 2025)
        self.assertEqual(C.pool_discrepancies(pool, C.int_orth), [])
        # the 240 roots: 112 of the form +-e_i +- e_j and 128 half-integer ones (scaled by 2)
        kinds = [sum(1 for x in r if x) for r in pool.rays]
        self.assertEqual(kinds.count(2), 56)
        self.assertEqual(kinds.count(8), 64)
        # the documented convention: half-integer roots with an EVEN number of minus signs
        self.assertIn((1,) * 8, pool.rays)
        self.assertNotIn((1,) * 7 + (-1,), pool.rays)
        for r in pool.rays:
            if all(r):
                self.assertEqual(sum(1 for x in r if x < 0) % 2, 0)
        # every root ray is orthogonal to 63 others (the root system E7 has 126 roots)
        nb = C.neighbour_sets(pool.n, C.orth_pairs(pool.rays, C.int_orth))
        self.assertEqual({len(s) for s in nb}, {63})

    def test_two_qubit_stabilizer_states(self):
        pool, sym = pools.stabilizer_pool(2, log=C.quiet)
        self.assertEqual(pool.n, 60)
        self.assertEqual(pool.d, 4)
        self.assertEqual(C.pool_discrepancies(pool, C.gauss_orth), [])
        # every generator of the Clifford action is a permutation that preserves orthogonality
        pairs = C.pool_pairs(pool)
        self.assertTrue(sym.gens)
        for g in sym.gens:
            self.assertEqual(sorted(g), list(range(pool.n)))
            self.assertEqual({(min(g[i], g[j]), max(g[i], g[j])) for i, j in pairs}, pairs)

    def test_three_qubit_stabilizer_states(self):
        # pools.stabilizer_pool(3) would also enumerate every 8-clique of the 1080 rays, which
        # takes far too long for a unit test; the ray set is what stabilizer_pool is built from.
        rays, ops, canon = pools.stabilizer_rays(3)
        self.assertEqual(len(rays), 1080)
        self.assertEqual(len(set(rays)), 1080)
        # known count of n-qubit stabilizer states: 2^n * prod_{k=1..n} (2^k + 1)
        for n, want in ((1, 6), (2, 60), (3, 1080)):
            prod = 2 ** n
            for k in range(1, n + 1):
                prod *= 2 ** k + 1
            self.assertEqual(prod, want)
            self.assertEqual(len(pools.stabilizer_rays(n)[0]), want)
        # the set is closed under the generators, and no two rays are proportional
        # (cross-ratio test in exact Gaussian-integer arithmetic on a sample)
        ray_set = set(rays)
        for r in rays[::37]:
            for op in ops:
                self.assertIn(canon(op(r)), ray_set)

        def gmul(a, b):
            return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])

        def proportional(u, v):
            return all(gmul(u[i], v[j]) == gmul(u[j], v[i])
                       for i in range(len(u)) for j in range(i + 1, len(u)))

        sample = rays[::11]
        for a, b in itertools.combinations(sample, 2):
            self.assertFalse(proportional(a, b))
        self.assertTrue(proportional(rays[5], tuple(gmul((0, 1), z) for z in rays[5])))


class CoreOfSubPools(unittest.TestCase):
    """Pool.ks_core against a direct implementation of Corollary 4 on random
    sub-pools, where rays with exactly d partners occur (the threshold matters)."""

    @staticmethod
    def core_by_definition(nb, bases, d, alive):
        alive = set(alive)
        while True:
            covered = set()
            for b in bases:
                if b <= alive:
                    covered |= b
            keep = {v for v in alive if v in covered and len(nb[v] & alive) >= d}
            if keep == alive:
                return alive
            alive = keep

    def check(self, d, H, sizes, seed):
        import random
        pool = pools.box_pool(d, H, log=C.quiet)
        nb, bases = C.structure_of(pool)
        rng = random.Random(seed)
        nonempty = tight = shrunk = 0
        for _ in range(60):
            keep = sorted(rng.sample(range(pool.n), rng.randint(*sizes)))
            sub = pool.restrict(keep, log=C.quiet)
            self.assertEqual(C.pool_discrepancies(sub, C.int_orth), [])
            core = sub.ks_core(log=C.quiet)
            want = self.core_by_definition(nb, bases, d, keep)
            got = {keep[i] for i in core.parent_index}
            self.assertEqual(got, want)
            self.assertEqual({core.rays[i] for i in range(core.n)}, {pool.rays[v] for v in want})
            if want:
                nonempty += 1
                tight += any(len(nb[v] & want) == d for v in want)
            shrunk += len(want) < len(keep)
        self.assertGreater(nonempty, 10)
        self.assertGreater(tight, 5)          # cores containing a ray with exactly d partners
        self.assertGreater(shrunk, 10)        # and sub-pools that really lose rays

    def test_d3(self):
        self.check(3, 2, (25, 45), 3)

    def test_d4(self):
        self.check(4, 1, (20, 36), 4)


class Box3Builder(unittest.TestCase):
    def test_build_box3_equals_core_of_box_pool(self):
        for H in (2, 3, 4):
            fast = pools3d.build_box3(H, log=C.quiet)
            ref = pools.box_pool(3, H, log=C.quiet).ks_core(log=C.quiet)
            self.assertEqual(fast.d, 3)
            self.assertEqual(set(fast.rays), set(ref.rays), f"H={H}: ray sets differ")
            self.assertEqual(len(fast.rays), len(set(fast.rays)))
            as_vectors = lambda p: {frozenset(p.rays[v] for v in b) for b in p.bases}
            self.assertEqual(as_vectors(fast), as_vectors(ref), f"H={H}: bases differ")
            self.assertEqual(len(fast.bases), len(as_vectors(fast)))
            self.assertEqual(C.pool_discrepancies(fast, C.int_orth), [], f"H={H}")
            self.assertEqual(C.pool_discrepancies(ref, C.int_orth), [], f"H={H}")

    def test_full_box3_structure(self):
        # the un-pruned structure for H = 2: 49 rays, 138 orthogonal pairs, 26 triples
        rays, nbrs, tri = pools3d.box3_structure(2, log=C.quiet)
        self.assertEqual(len(rays), 49)
        self.assertEqual(sum(len(x) for x in nbrs) // 2, 138)
        self.assertEqual(len(tri), 26)
        self.assertEqual(set(rays), naive_box_rays(3, 2))


class TamperedPoolsAreFlagged(unittest.TestCase):
    """The comparison used above must be able to fail."""

    def setUp(self):
        self.pool = pools.box_pool(3, 2, log=C.quiet)
        self.assertEqual(C.pool_discrepancies(self.pool, C.int_orth), [])

    def clone(self, rays=None, adj=None, bases=None):
        p = self.pool
        return Pool(rays if rays is not None else p.rays, p.d, adj if adj is not None else p.adj,
                    bases=bases if bases is not None else p.bases, log=C.quiet)

    def test_extra_orthogonal_pair(self):
        adj = list(self.pool.adj)
        i, j = next((i, j) for i in range(self.pool.n) for j in range(i + 1, self.pool.n)
                    if not (adj[i] >> j) & 1)
        adj[i] |= 1 << j
        adj[j] |= 1 << i
        self.assertTrue(C.pool_discrepancies(self.clone(adj=adj), C.int_orth))

    def test_missing_orthogonal_pair(self):
        adj = list(self.pool.adj)
        i = 0
        j = adj[0].bit_length() - 1
        adj[i] &= ~(1 << j)
        adj[j] &= ~(1 << i)
        self.assertTrue(C.pool_discrepancies(self.clone(adj=adj), C.int_orth))

    def test_dropped_basis(self):
        self.assertTrue(C.pool_discrepancies(self.clone(bases=self.pool.bases[1:]), C.int_orth))

    def test_bogus_basis(self):
        bases = list(self.pool.bases)
        bogus = next(t for t in itertools.combinations(range(self.pool.n), 3) if t not in set(bases))
        self.assertTrue(C.pool_discrepancies(self.clone(bases=bases + [bogus]), C.int_orth))

    def test_changed_ray(self):
        rays = list(self.pool.rays)
        rays[7] = (rays[7][0], rays[7][1], rays[7][2] + 3)
        self.assertTrue(C.pool_discrepancies(self.clone(rays=rays), C.int_orth))

    def test_wrong_orthogonality_notion(self):
        # the two-qubit pool is NOT described by the real (non-conjugating) bilinear form
        pool, _ = pools.stabilizer_pool(2, log=C.quiet)

        def bilinear(u, v):
            re = im = 0
            for (a, b), (c, d) in zip(u, v):
                re += a * c - b * d
                im += a * d + b * c
            return re == 0 and im == 0

        self.assertTrue(C.pool_discrepancies(pool, bilinear))

    def test_wrong_sizes_are_noticed(self):
        # a pool with one ray removed has neither 49 rays nor 26 bases
        sub = self.pool.restrict([v for v in range(self.pool.n) if v != 0], log=C.quiet)
        self.assertNotEqual(sub.n, 49)
        self.assertNotEqual(len(sub.bases), 26)
        self.assertEqual(C.pool_discrepancies(sub, C.int_orth), [])   # but it is self-consistent


if __name__ == "__main__":
    unittest.main(verbosity=2)
