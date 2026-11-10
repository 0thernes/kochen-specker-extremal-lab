"""test_colouring.py - the colorability decision (ksengine.Pool.coloring / is_ks /
is_critical) and Lemmas 1 and 3 of paper/PROOFS.md.

Oracles that share no code with the engine (tests/_common.py):
  * brute force over all 0/1 assignments (sets of at most 18 rays);
  * an exhaustive backtracking search without a SAT solver.

Run alone:  python tests/test_colouring.py
"""
from __future__ import annotations

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

import pools  # noqa: E402


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = pools.box_pool(3, 2, log=C.quiet)
        cls.nb, cls.bases = C.structure_of(cls.pool)
        assert C.pool_discrepancies(cls.pool, C.int_orth) == []
        cls.ks31 = C.load_ks31_indices(cls.pool)
        cls.others = [v for v in range(cls.pool.n) if v not in set(cls.ks31)]


class BruteForce(Fixture):
    def random_subsets(self, rng, count):
        """Subsets with at most 16 rays; most are unions of a few bases plus
        some extra rays so that the basis condition actually bites."""
        n = self.pool.n
        for t in range(count):
            size = rng.randint(6, 16)
            S = set()
            if t % 4:
                while True:
                    b = rng.choice(self.bases)
                    if len(S | b) > size:
                        break
                    S |= b
            while len(S) < size:
                S.add(rng.randrange(n))
            yield sorted(S)

    def test_small_sets_against_all_assignments(self):
        rng = random.Random(49)
        with_bases = 0
        for S in self.random_subsets(rng, 60):
            self.assertLessEqual(len(S), 16)
            count = C.colorings_bruteforce(self.nb, self.bases, S)
            ones = self.pool.coloring(S)
            self.assertEqual(ones is not None, count > 0, f"S={S}")
            self.assertEqual(self.pool.is_ks(S), count == 0)
            if ones is not None:
                self.assertTrue(C.valid_coloring(self.nb, self.bases, S, ones), f"S={S} ones={sorted(ones)}")
            self.assertEqual(C.decide_colorable(self.nb, self.bases, S) is not None, count > 0)
            with_bases += any(b <= set(S) for b in self.bases)
        self.assertGreater(with_bases, 30)

    def test_brute_force_counts_on_hand_checked_sets(self):
        # one basis: exactly three colorings (which ray is 1)
        b = sorted(self.bases[0])
        self.assertEqual(C.colorings_bruteforce(self.nb, self.bases, b), 3)
        # two non-orthogonal rays, no basis: all four assignments
        v = 0
        w = next(x for x in range(1, self.pool.n) if x not in self.nb[v])
        self.assertEqual(C.colorings_bruteforce(self.nb, self.bases, [v, w]), 4)
        # two orthogonal rays: three assignments
        w = min(self.nb[v])
        self.assertEqual(C.colorings_bruteforce(self.nb, self.bases, [v, w]), 3)
        self.assertEqual(C.colorings_bruteforce(self.nb, self.bases, []), 1)

    def test_a_ks_set_small_enough_for_brute_force(self):
        # dimension 4, entries 0, +-1: the search finds an 18-ray KS set; all 2^18
        # assignments are enumerated, and all 2^17 for each one-ray deletion
        import ksdfs
        pool4 = pools.box_pool(4, 1, log=C.quiet)
        res = ksdfs.KSDfs(pool4, 18, sym=None, log=C.quiet).run()
        self.assertEqual(res["status"], "found")
        S = sorted(res["ks"])
        self.assertEqual(len(S), 18)
        nb4, bases4 = C.structure_of(pool4)
        self.assertEqual(C.colorings_bruteforce(nb4, bases4, S), 0)
        self.assertTrue(pool4.is_ks(S))
        self.assertIsNone(C.decide_colorable(nb4, bases4, S))
        for v in S:
            T = [x for x in S if x != v]
            self.assertGreater(C.colorings_bruteforce(nb4, bases4, T), 0)
            ones = pool4.coloring(T)
            self.assertIsNotNone(ones)
            self.assertTrue(C.valid_coloring(nb4, bases4, T, ones))
        self.assertTrue(pool4.is_critical(S))

    def test_invalid_colorings_are_rejected_by_the_checker(self):
        S = sorted(self.ks31[:-1])                       # 30 rays: colorable
        ones = set(self.pool.coloring(S))
        self.assertTrue(C.valid_coloring(self.nb, self.bases, S, ones))
        # (1) drop the 1 of some basis inside S
        b = next(b for b in self.bases if b <= set(S))
        self.assertFalse(C.valid_coloring(self.nb, self.bases, S, ones - b))
        # (2) add a ray orthogonal to a ray of value 1
        v = next(iter(ones))
        w = next(x for x in self.nb[v] if x in set(S))
        self.assertFalse(C.valid_coloring(self.nb, self.bases, S, ones | {w}))
        # (3) a ray of value 1 outside S
        outside = next(x for x in range(self.pool.n) if x not in set(S))
        self.assertFalse(C.valid_coloring(self.nb, self.bases, S, ones | {outside}))
        # (4) the all-zero assignment fails as soon as S contains a basis
        self.assertFalse(C.valid_coloring(self.nb, self.bases, S, set()))


class The31RaySet(Fixture):
    def test_file_is_a_set_of_31_pool_rays(self):
        self.assertEqual(len(self.ks31), 31)
        self.assertEqual(len(set(self.ks31)), 31)
        Sset = set(self.ks31)
        pairs = sum(len(self.nb[v] & Sset) for v in Sset) // 2
        nbases = sum(1 for b in self.bases if b <= Sset)
        self.assertEqual(self.pool.describe(self.ks31), f"31 rays, {pairs} orthogonal pairs, {nbases} bases")

    def test_ks_and_critical(self):
        S = self.ks31
        self.assertTrue(self.pool.is_ks(S))
        self.assertIsNone(self.pool.coloring(S))
        self.assertIsNone(C.decide_colorable(self.nb, self.bases, S))      # exhaustive, no SAT
        self.assertTrue(self.pool.is_critical(S))
        for v in S:                                                         # criticality, re-derived
            T = [x for x in S if x != v]
            ones = self.pool.coloring(T)
            self.assertIsNotNone(ones)
            self.assertTrue(C.valid_coloring(self.nb, self.bases, T, ones))
            self.assertIsNotNone(C.decide_colorable(self.nb, self.bases, T))

    def test_corrupted_sets_are_not_critical_ks_sets(self):
        S = set(self.ks31)
        # one ray missing: not a KS set at all
        self.assertFalse(self.pool.is_ks(S - {self.ks31[0]}))
        self.assertFalse(self.pool.is_critical(S - {self.ks31[0]}))
        # one extra ray: still a KS set, no longer critical
        bigger = S | {self.others[0]}
        self.assertTrue(self.pool.is_ks(bigger))
        self.assertFalse(self.pool.is_critical(bigger))
        # one ray replaced by another ray of the pool: every such set is examined, both
        # deciders must agree, and at least one replacement must destroy the KS property
        destroyed = 0
        for a in self.ks31[::5]:
            for b in self.others:
                T = (S - {a}) | {b}
                sat = self.pool.is_ks(T)
                self.assertEqual(sat, C.decide_colorable(self.nb, self.bases, T) is None)
                destroyed += not sat
        self.assertGreater(destroyed, 0)

    def test_shrink_returns_a_critical_ks_subset(self):
        everything = list(range(self.pool.n))
        for seed in (1, 2, 3):
            T = self.pool.shrink(everything, rng=random.Random(seed))
            self.assertTrue(set(T) <= set(everything))
            self.assertIsNone(C.decide_colorable(self.nb, self.bases, T))
            self.assertTrue(self.pool.is_critical(T))
        core = self.pool.ks_core_of(self.ks31)
        self.assertTrue(core <= set(self.ks31))
        self.assertIsNone(C.decide_colorable(self.nb, self.bases, core))
        self.assertIsNone(self.pool.ks_core_of(self.ks31[:-1]))             # colorable: no core


class Lemma1(Fixture):
    """S is a KS set iff S contains a basis of Miss(I) for every independent I."""

    def random_maximal_independent_set(self, rng):
        order = list(range(self.pool.n))
        rng.shuffle(order)
        I = set()
        for v in order:
            if not (self.nb[v] & I):
                I.add(v)
        return I

    def test_ks_set_contains_a_missed_basis_for_every_independent_set(self):
        rng = random.Random(1)
        S = set(self.ks31)
        seen = set()
        for _ in range(200):
            I = self.random_maximal_independent_set(rng)
            self.assertTrue(C.is_independent(self.nb, I))
            self.assertTrue(all(self.nb[v] & I for v in range(self.pool.n) if v not in I))   # maximal
            missed = C.missed_bases(self.bases, I)
            self.assertTrue(any(self.bases[i] <= S for i in missed),
                            f"the 31-ray set contains no basis missed by I={sorted(I)}")
            seen.add(frozenset(I))
        self.assertGreater(len(seen), 150)        # the sample is not one set repeated

    def test_colorable_set_has_an_independent_set_missing_no_basis_inside(self):
        rng = random.Random(2)
        escaped = 0
        for v in self.ks31:
            T = set(self.ks31) - {v}
            ones = self.pool.coloring(T)
            self.assertIsNotNone(ones)
            I = set(ones)
            self.assertTrue(C.is_independent(self.nb, I))
            missed = C.missed_bases(self.bases, I)
            self.assertFalse(any(self.bases[i] <= T for i in missed))
            # the same holds after extending I to a maximal independent set of the pool
            order = list(range(self.pool.n))
            rng.shuffle(order)
            for w in order:
                if not (self.nb[w] & I):
                    I.add(w)
            self.assertFalse(any(self.bases[i] <= T for i in C.missed_bases(self.bases, I)))
            # ... but not for arbitrary independent sets: the statement can fail
            for _ in range(5):
                J = self.random_maximal_independent_set(rng)
                escaped += any(self.bases[i] <= T for i in C.missed_bases(self.bases, J))
        self.assertGreater(escaped, 0)

    def test_the_property_fails_for_a_colorable_set(self):
        # the Lemma 1 test used above must reject a colorable set: for the coloring I of
        # the 30-ray set T, T contains no basis of Miss(I)
        T = set(self.ks31[1:])
        I = set(self.pool.coloring(T))

        def lemma1_holds_for(S, I):
            return any(self.bases[i] <= S for i in C.missed_bases(self.bases, I))

        self.assertFalse(lemma1_holds_for(T, I))
        self.assertTrue(lemma1_holds_for(set(self.ks31), I))


class Lemma3(Fixture):
    """Every ray of a critical KS set lies in a basis inside it (C1) and has at
    least d orthogonal partners inside it (C2)."""

    def violations(self, S):
        S = set(S)
        out = []
        for v in sorted(S):
            in_basis = any(v in b and b <= S for b in self.bases)
            partners = len(self.nb[v] & S)
            if not in_basis or partners < self.pool.d:
                out.append((v, in_basis, partners))
        return out

    def test_the_31_ray_set_satisfies_c1_and_c2(self):
        self.assertEqual(self.violations(self.ks31), [])

    def test_violations_are_detected(self):
        # the first ray of the set and one of its partners: no basis inside, one partner each
        v = self.ks31[0]
        w = min(self.nb[v])
        self.assertEqual(len(self.violations([v, w])), 2)
        # a single basis: C1 holds, C2 fails (two partners, three needed)
        b = sorted(self.bases[0])
        self.assertEqual([(x, True, 2) for x in b], self.violations(b))
        # removing a ray from the 31-ray set breaks C1 or C2 for some remaining ray, for
        # at least one choice of the ray (the set is tight)
        broken = sum(1 for x in self.ks31 if self.violations(set(self.ks31) - {x}))
        self.assertGreater(broken, 0)

    def test_core_of_the_pool_consists_of_rays_satisfying_c1_c2(self):
        core = self.pool.ks_core(log=C.quiet)
        self.assertEqual(self.violations(core.parent_index), [])
        # every ray of the 31-ray set survives in the core (Corollary 4)
        self.assertTrue(set(self.ks31) <= set(core.parent_index))


if __name__ == "__main__":
    unittest.main(verbosity=2)
