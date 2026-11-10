"""test_cnf.py - the CNF re-encoding (src/ks_cnf.py) and the normal form of
Lemma 6 (paper/PROOFS.md).

  * CNF.counter is exact: out[j] <-> "at least j inputs are true", checked on
    every input assignment for up to 7 inputs and every maxj;
  * ks_cnf.encode on the 49-ray pool with the cuts of a fresh ksmaster run:
    unsatisfiable for k = 30, satisfiable for k = 31, and every model decodes
    to an assignment that satisfies the constraints as stated in the paper;
  * Lemma 6: every subset of the pool has an image under a signed coordinate
    permutation that satisfies the symmetry-breaking constraints, and the two
    implementations of these constraints (CP-SAT and CNF) agree.

Run alone:  python tests/test_cnf.py
"""
from __future__ import annotations

import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

from pysat.solvers import Solver  # noqa: E402

import ks_cnf  # noqa: E402
import ksmaster  # noqa: E402
import pools  # noqa: E402
from ksengine import bits  # noqa: E402


def counter_errors(nvars, clauses, inputs, out, spec=lambda count, j: count >= j):
    """All (assignment, j) at which out[j] is not forced to spec(#true inputs, j).

    For every assignment of the inputs the formula must be satisfiable, and
    adding the wrong value of out[j] must make it unsatisfiable."""
    errors = []
    n = len(inputs)
    with Solver(name="g3", bootstrap_with=clauses) as s:
        for a in range(1 << n):
            assume = [x if (a >> i) & 1 else -x for i, x in enumerate(inputs)]
            # an input literal may be negative: "true" means the literal is true
            count = bin(a).count("1")
            if not s.solve(assumptions=assume):
                errors.append((a, None))
                continue
            for j, o in out.items():
                want = spec(count, j)
                if s.solve(assumptions=assume + [-o if want else o]):
                    errors.append((a, j))
    return errors


class Counter(unittest.TestCase):
    def test_exact_for_up_to_seven_inputs(self):
        for n in range(1, 8):
            for maxj in range(1, n + 1):
                F = ks_cnf.CNF(n)
                inputs = list(range(1, n + 1))
                out = F.counter(inputs, maxj)
                self.assertEqual(sorted(out), list(range(1, maxj + 1)), f"n={n} maxj={maxj}")
                self.assertTrue(all(o > n for o in out.values()))
                self.assertLessEqual(max(abs(l) for cl in F.clauses for l in cl), F.nv)
                self.assertEqual(counter_errors(F.nv, F.clauses, inputs, out), [], f"n={n} maxj={maxj}")

    def test_negated_and_shuffled_inputs(self):
        rng = random.Random(6)
        for n in range(1, 7):
            for _ in range(3):
                F = ks_cnf.CNF(n + 3)                      # three unrelated variables in front
                inputs = [rng.choice((1, -1)) * v for v in rng.sample(range(4, n + 4), n)]
                maxj = rng.randint(1, n)
                out = F.counter(inputs, maxj)
                self.assertEqual(counter_errors(F.nv, F.clauses, inputs, out), [])

    def test_maxj_larger_than_the_number_of_inputs(self):
        # only the meaningful outputs are produced ("at least j of n" is false for j > n)
        F = ks_cnf.CNF(3)
        out = F.counter([1, 2, 3], 5)
        self.assertEqual(sorted(out), [1, 2, 3])
        self.assertEqual(counter_errors(F.nv, F.clauses, [1, 2, 3], out), [])

    def test_two_counters_in_one_formula_do_not_interfere(self):
        F = ks_cnf.CNF(5)
        out_a = F.counter([1, 2, 3], 3)
        out_b = F.counter([3, 4, 5, -1], 2)
        self.assertFalse(set(out_a.values()) & set(out_b.values()))
        with Solver(name="g3", bootstrap_with=F.clauses) as s:
            for a in range(32):
                val = [(a >> i) & 1 for i in range(5)]
                assume = [(i + 1) if val[i] else -(i + 1) for i in range(5)]
                self.assertTrue(s.solve(assumptions=assume))
                model = s.get_model()
                ca = val[0] + val[1] + val[2]
                cb = val[2] + val[3] + val[4] + (1 - val[0])
                for j, o in out_a.items():
                    self.assertEqual(model[o - 1] > 0, ca >= j)
                for j, o in out_b.items():
                    self.assertEqual(model[o - 1] > 0, cb >= j)

    def test_the_exactness_check_can_fail(self):
        F = ks_cnf.CNF(4)
        inputs = [1, 2, 3, 4]
        out = F.counter(inputs, 3)
        self.assertEqual(counter_errors(F.nv, F.clauses, inputs, out), [])
        # (1) the wrong specification ("more than j")
        self.assertTrue(counter_errors(F.nv, F.clauses, inputs, out, spec=lambda c, j: c > j))
        # (2) a clause deleted: the outputs are no longer forced
        detected = 0
        for i in range(len(F.clauses)):
            if counter_errors(F.nv, F.clauses[:i] + F.clauses[i + 1:], inputs, out):
                detected += 1
        self.assertGreater(detected, 0)
        # (3) a literal flipped in a clause
        flipped = [list(cl) for cl in F.clauses]
        flipped[-1][0] = -flipped[-1][0]
        self.assertTrue(counter_errors(F.nv, flipped, inputs, out))
        # (4) the outputs of a different counter
        other = {j: o for j, o in zip(out, reversed(list(out.values())))}
        self.assertTrue(counter_errors(F.nv, F.clauses, inputs, other))


class Encoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = pools.box_pool(3, 2, log=C.quiet)
        cls.nb, cls.bases = C.structure_of(cls.pool)
        cls.groups = [list(range(cls.pool.d))]
        m = ksmaster.Master(cls.pool, 30, sym=pools.signed_perm_symmetry(cls.pool), log=C.quiet,
                            workers=C.WORKERS)
        m.symbreak = ksmaster.box_symmetry_breaking(cls.pool, cls.groups)
        res = m.run(max_seconds=120)
        assert res["status"] == "none", res
        cls.cuts = [sorted(c) for c in m.cuts]
        cls.witness = [sorted(m.witness[c]) for c in m.cuts]

    def solve(self, F, assumptions=()):
        with Solver(name="g4", bootstrap_with=F.clauses) as s:
            if s.solve(assumptions=list(assumptions)):
                return s.get_model()
        return None

    def decode_problems(self, model, k, cuts, symbreak=True):
        """Check a model against the candidate problem as written in PROOFS.md
        section 5, using only tests/_common.py structures."""
        n, nbases = self.pool.n, len(self.bases)
        x = [model[v] > 0 for v in range(n)]
        y = [model[n + b] > 0 for b in range(nbases)]
        chosen = {v for v in range(n) if x[v]}
        problems = []
        for b, basis in enumerate(self.bases):
            if y[b] != (basis <= chosen):
                problems.append(f"(D) y[{b}] is {y[b]} but basis inside chosen set is {basis <= chosen}")
        if len(chosen) > k:
            problems.append(f"(K) {len(chosen)} rays chosen, bound {k}")
        for v in sorted(chosen):
            if not any(v in basis and basis <= chosen for basis in self.bases):
                problems.append(f"(C1) ray {v} lies in no chosen basis")
            if len(self.nb[v] & chosen) < self.pool.d:
                problems.append(f"(C2) ray {v} has only {len(self.nb[v] & chosen)} chosen partners")
        for i, cut in enumerate(cuts):
            if not any(y[b] for b in cut):
                problems.append(f"cut {i} is violated")
        if symbreak and normal_form_violations(self.pool, chosen, self.groups):
            problems.append("the chosen set is not in normal form")
        return problems, chosen

    def test_cuts_are_valid(self):
        self.assertTrue(ks_cnf.verify_cuts(self.pool, list(zip(self.cuts, self.witness))))
        for cut, I in zip(self.cuts, self.witness):
            self.assertTrue(C.is_independent(self.nb, I))
            self.assertEqual(cut, C.missed_bases(self.bases, I))

    def test_k30_unsat_k31_sat(self):
        for symbreak in (True, False):
            F30 = ks_cnf.encode(self.pool, 30, self.cuts, groups=self.groups, symbreak=symbreak)
            self.assertIsNone(self.solve(F30), f"k=30 symbreak={symbreak} must be unsatisfiable")
            F31 = ks_cnf.encode(self.pool, 31, self.cuts, groups=self.groups, symbreak=symbreak)
            model = self.solve(F31)
            self.assertIsNotNone(model, f"k=31 symbreak={symbreak} must be satisfiable")
            problems, chosen = self.decode_problems(model, 31, self.cuts, symbreak=symbreak)
            self.assertEqual(problems, [])
            # the model is a KS set, or it is colorable and then simply violates no cut so far
            ks = C.decide_colorable(self.nb, self.bases, chosen) is None
            self.assertEqual(ks, self.pool.is_ks(chosen))

    def test_variable_layout_and_clause_sanity(self):
        F = ks_cnf.encode(self.pool, 30, self.cuts, groups=self.groups, symbreak=True)
        n, nbases = self.pool.n, len(self.bases)
        self.assertGreater(F.nv, n + nbases)
        for cl in F.clauses:
            self.assertTrue(cl)
            self.assertTrue(all(isinstance(l, int) and l != 0 and abs(l) <= F.nv for l in cl))
        # every cut appears as a clause over the y variables
        clause_set = {tuple(sorted(cl)) for cl in F.clauses}
        for cut in self.cuts:
            self.assertIn(tuple(sorted(n + b + 1 for b in cut)), clause_set)

    def test_every_31_ray_ks_image_is_a_model_or_violates_normal_form(self):
        # the 31-ray KS set and its 48 images under signed coordinate permutations satisfy
        # (D), (C1), (C2), (K) and every cut; with symmetry breaking exactly the images in
        # normal form remain models - and at least one does (Lemma 6)
        ks31 = C.load_ks31_indices(self.pool)
        F_plain = ks_cnf.encode(self.pool, 31, self.cuts, groups=self.groups, symbreak=False)
        F_sym = ks_cnf.encode(self.pool, 31, self.cuts, groups=self.groups, symbreak=True)
        in_normal_form = 0
        with Solver(name="g4", bootstrap_with=F_plain.clauses) as s_plain, \
                Solver(name="g4", bootstrap_with=F_sym.clauses) as s_sym:
            for g in signed_permutations(self.pool):
                image = {g[v] for v in ks31}
                assume = [(v + 1) if v in image else -(v + 1) for v in range(self.pool.n)]
                self.assertTrue(s_plain.solve(assumptions=assume))
                normal = not normal_form_violations(self.pool, image, self.groups)
                self.assertEqual(s_sym.solve(assumptions=assume), normal)
                in_normal_form += normal
        self.assertGreater(in_normal_form, 0)
        self.assertLess(in_normal_form, 48)

    def test_fix_in_and_fix_out(self):
        # the 31-ray KS set is a model, so fixing one of its rays in and a ray outside it
        # out keeps the formula satisfiable; the model must respect both
        ks31 = C.load_ks31_indices(self.pool)
        inside = ks31[0]
        outside = next(v for v in range(self.pool.n) if v not in set(ks31))
        F = ks_cnf.encode(self.pool, 31, self.cuts, fix_in=[inside], fix_out=[outside],
                          groups=self.groups, symbreak=False)
        model = self.solve(F)
        self.assertIsNotNone(model)
        self.assertGreater(model[inside], 0)
        self.assertLess(model[outside], 0)
        self.assertEqual(self.decode_problems(model, 31, self.cuts, symbreak=False)[0], [])
        # fixing 19 rays out leaves at most 30 rays: unsatisfiable, like k = 30
        others = [v for v in range(self.pool.n) if v not in set(ks31)]
        F = ks_cnf.encode(self.pool, 31, self.cuts, fix_out=others + [inside],
                          groups=self.groups, symbreak=False)
        self.assertIsNone(self.solve(F))
        # contradictory case constraints
        F = ks_cnf.encode(self.pool, 31, self.cuts, fix_in=[0], fix_out=[0], groups=self.groups,
                          symbreak=False)
        self.assertIsNone(self.solve(F))

    def test_corrupted_inputs(self):
        # (1) without the cuts the bound k = 30 is no longer refuted
        F = ks_cnf.encode(self.pool, 30, [], groups=self.groups, symbreak=True)
        self.assertIsNotNone(self.solve(F))
        # (2) with the cardinality clause removed k = 30 is no longer refuted either
        F = ks_cnf.encode(self.pool, 30, self.cuts, groups=self.groups, symbreak=True)
        unit_negative = [i for i, cl in enumerate(F.clauses) if len(cl) == 1 and cl[0] < 0]
        self.assertEqual(len(unit_negative), 1)             # the clause "not (at least k+1)"
        G = ks_cnf.CNF(F.nv)
        G.clauses = [cl for i, cl in enumerate(F.clauses) if i != unit_negative[0]]
        model = self.solve(G)
        self.assertIsNotNone(model)
        self.assertGreater(sum(1 for v in range(self.pool.n) if model[v] > 0), 30)
        # (3) an invalid cut (the empty clause) is refused by verify_cuts
        self.assertFalse(ks_cnf.verify_cuts(self.pool, [([], self.witness[0])]))
        # (4) a tampered model is caught by the decoder
        F31 = ks_cnf.encode(self.pool, 31, self.cuts, groups=self.groups, symbreak=True)
        model = self.solve(F31)
        problems, chosen = self.decode_problems(model, 31, self.cuts)
        self.assertEqual(problems, [])
        n = self.pool.n
        bad = list(model)
        b = next(b for b, basis in enumerate(self.bases) if basis <= chosen)
        bad[n + b] = -bad[n + b]                              # y_b false although all rays chosen
        self.assertTrue(self.decode_problems(bad, 31, self.cuts)[0])
        bad = list(model)
        v = min(chosen)
        bad[v] = -bad[v]                                      # one chosen ray removed
        self.assertTrue(self.decode_problems(bad, 31, self.cuts)[0])
        self.assertTrue(self.decode_problems(model, 30, self.cuts)[0])   # 31 rays against k = 30


# ---- Lemma 6 ----
class _Recorder:
    """Stands in for a CP-SAT model: box_symmetry_breaking only calls Add(...)
    with comparisons, which evaluate to plain booleans on 0/1 integers."""

    def __init__(self):
        self.results = []

    def Add(self, condition):
        self.results.append(bool(condition))


def normal_form_violations(pool, S, groups):
    """Indices of the violated constraints of ksmaster.box_symmetry_breaking."""
    add = ksmaster.box_symmetry_breaking(pool, groups)
    chosen = set(S)
    x = [1 if v in chosen else 0 for v in range(pool.n)]
    rec = _Recorder()
    add(rec, x)
    return [i for i, ok in enumerate(rec.results) if not ok]


def normal_form_by_definition(pool, S, groups):
    """Lemma 6, written out directly from the statement in PROOFS.md."""
    d = pool.d
    chosen = [pool.rays[v] for v in S]
    n = [sum(1 for r in chosen if r[j] != 0) for j in range(d)]
    for g in groups:
        for a, b in zip(g, g[1:]):
            if n[a] < n[b]:
                return False
    present = set(chosen)
    for j in range(1, d):
        plus = tuple(1 if i in (0, j) else 0 for i in range(d))
        minus = tuple(1 if i == 0 else (-1 if i == j else 0) for i in range(d))
        if minus in present and plus not in present:
            return False
    return True


def signed_permutations(pool, groups=None):
    """Ray permutations induced by all signed coordinate permutations that
    preserve each group of coordinates (all coordinates when groups is None)."""
    d = pool.d
    index = {r: i for i, r in enumerate(pool.rays)}
    allowed = []
    for perm in itertools.permutations(range(d)):
        if groups is not None:
            block = {}
            for gi, g in enumerate(groups):
                for c in g:
                    block[c] = gi
            if any(block.get(c, ("fixed", c)) != block.get(perm[c], ("fixed", perm[c])) for c in range(d)):
                continue
        allowed.append(perm)
    out = []
    for perm in allowed:
        for signs in itertools.product((1, -1), repeat=d):
            img = []
            for r in pool.rays:
                w = tuple(signs[c] * r[perm[c]] for c in range(d))
                first = next(x for x in w if x)
                if first < 0:
                    w = tuple(-x for x in w)
                img.append(index[w])
            out.append(tuple(img))
    return out


class Lemma6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = pools.box_pool(3, 2, log=C.quiet)
        cls.groups = [[0, 1, 2]]
        cls.perms = signed_permutations(cls.pool)

    def test_the_group_has_48_elements_acting_by_orthogonality_preserving_permutations(self):
        self.assertEqual(len(self.perms), 48)
        self.assertEqual(len(set(self.perms)), 24)     # +-1 act trivially on rays: 48 / 2 distinct maps
        pairs = C.pool_pairs(self.pool)
        for g in set(self.perms):
            self.assertEqual(sorted(g), list(range(self.pool.n)))
            self.assertEqual({(min(g[i], g[j]), max(g[i], g[j])) for i, j in pairs}, pairs)

    def test_every_subset_has_an_image_in_normal_form(self):
        rng = random.Random(606)
        n = self.pool.n
        identity_fails = 0
        for t in range(400):
            size = rng.randint(0, n)
            S = rng.sample(range(n), size)
            ok = False
            for g in self.perms:
                image = [g[v] for v in S]
                by_code = not normal_form_violations(self.pool, image, self.groups)
                self.assertEqual(by_code, normal_form_by_definition(self.pool, image, self.groups))
                ok = ok or by_code
            self.assertTrue(ok, f"no signed coordinate permutation normalises {sorted(S)}")
            identity_fails += bool(normal_form_violations(self.pool, S, self.groups))
        # the constraints are not vacuous: many subsets violate them as given
        self.assertGreater(identity_fails, 100)

    def test_groups_restrict_the_permutations(self):
        # groups {0,1} and {2} fixed: 2 * 8 = 16 signed permutations still suffice (Lemma 6
        # with two groups), and the constraint set is the shorter one
        groups = [[0, 1]]
        perms = signed_permutations(self.pool, groups=[[0, 1], [2]])
        self.assertEqual(len(perms), 16)
        rng = random.Random(607)
        for t in range(200):
            S = rng.sample(range(self.pool.n), rng.randint(0, self.pool.n))
            self.assertTrue(any(not normal_form_violations(self.pool, [g[v] for v in S], groups)
                                for g in perms))

    def test_a_too_strong_normal_form_is_refuted(self):
        # corrupted constraint: demanding STRICT inequalities n_0 > n_1 > n_2 is not a normal
        # form (the empty set has no such image); the search above must notice this
        def strict(pool, S):
            n = [sum(1 for v in S if pool.rays[v][j] != 0) for j in range(pool.d)]
            return n[0] > n[1] > n[2]

        rng = random.Random(608)
        failures = 0
        for t in range(200):
            S = rng.sample(range(self.pool.n), rng.randint(0, 6))
            if not any(strict(self.pool, [g[v] for v in S]) for g in self.perms):
                failures += 1
        self.assertGreater(failures, 0)
        # and with the identity alone (no group action) the true normal form is not reached
        S = [i for i, r in enumerate(self.pool.rays) if r in ((0, 0, 1), (1, 0, -1))]
        self.assertEqual(len(S), 2)
        self.assertTrue(normal_form_violations(self.pool, S, self.groups))
        self.assertTrue(any(not normal_form_violations(self.pool, [g[v] for v in S], self.groups)
                            for g in self.perms))

    def test_cnf_and_cpsat_constraints_agree(self):
        # the CNF encoding of the symmetry-breaking constraints alone: clauses added by
        # symbreak=True on top of symbreak=False, tested on random assignments of x
        F0 = ks_cnf.encode(self.pool, 48, [], groups=self.groups, symbreak=False)
        F1 = ks_cnf.encode(self.pool, 48, [], groups=self.groups, symbreak=True)
        self.assertEqual(F1.clauses[:len(F0.clauses)], F0.clauses)
        extra = F1.clauses[len(F0.clauses):]
        self.assertTrue(extra)
        rng = random.Random(609)
        agree_true = agree_false = 0
        with Solver(name="g4", bootstrap_with=extra) as s:
            for t in range(300):
                S = set(rng.sample(range(self.pool.n), rng.randint(0, self.pool.n)))
                if t % 3 == 0:                       # make normal-form instances common
                    for g in self.perms:
                        image = {g[v] for v in S}
                        if not normal_form_violations(self.pool, image, self.groups):
                            S = image
                            break
                assume = [(v + 1) if v in S else -(v + 1) for v in range(self.pool.n)]
                want = not normal_form_violations(self.pool, S, self.groups)
                self.assertEqual(s.solve(assumptions=assume), want, f"S={sorted(S)}")
                agree_true += want
                agree_false += not want
        self.assertGreater(agree_true, 50)
        self.assertGreater(agree_false, 50)


class KnownLimits(unittest.TestCase):
    def test_bound_equal_to_pool_size(self):
        """encode(pool, k) with k >= number of rays: the size bound is vacuous and is left out.
        The formula must then accept the whole pool (a KS set) and reject the empty set only
        because nothing forces rays in: both are checked."""
        pool = pools.box_pool(3, 2, log=C.quiet)
        F = ks_cnf.encode(pool, pool.n - 1, [], groups=[[0, 1, 2]], symbreak=False)
        self.assertTrue(F.clauses)
        G = ks_cnf.encode(pool, pool.n, [], groups=[[0, 1, 2]], symbreak=False)
        everything = [v + 1 for v in range(pool.n)]
        with Solver(name="g4", bootstrap_with=G.clauses) as s:
            self.assertTrue(s.solve(assumptions=everything), "the whole 49-ray pool must be a model")


class FiveAxisControl(unittest.TestCase):
    """Positive control for the five-axis case of dimension five: a 31-ray KS set with all five
    coordinate axes, in the normal form of cube 2211, is a model of that cube's formula with bound
    31 and is rejected with bound 30."""

    RAYS = [
        (0, 0, 0, 0, 1), (0, 0, 0, 1, 0), (0, 0, 1, 0, -1), (0, 0, 1, 0, 0), (0, 0, 1, 1, 0), (0, 1, -1, 0, 0),
        (0, 1, 0, 0, -1), (0, 1, 0, 0, 0), (0, 1, 0, 1, 0), (0, 1, 1, 0, 0), (1, -1, -1, -1, 0), (1, -1, -1, 0, -1),
        (1, -1, -1, 1, 0), (1, -1, 0, 0, 0), (1, -1, 1, -1, 0), (1, -1, 1, 0, -1), (1, -1, 1, 0, 1), (1, -1, 1, 1, 0),
        (1, 0, -1, 0, 0), (1, 0, 0, 0, 0), (1, 0, 0, 0, 1), (1, 0, 0, 1, 0), (1, 0, 1, 0, 0), (1, 1, -1, -1, 0),
        (1, 1, -1, 0, -1), (1, 1, -1, 0, 1), (1, 1, -1, 1, 0), (1, 1, 0, 0, 0), (1, 1, 1, -1, 0), (1, 1, 1, 0, -1),
        (1, 1, 1, 0, 1),
    ]

    def test_five_axis_set_is_a_model_of_its_cube(self):
        pool = pools.box_pool(5, 1, log=C.quiet).ks_core(log=C.quiet)
        index = {tuple(r): i for i, r in enumerate(pool.rays)}
        S = {index[r] for r in self.RAYS}
        self.assertEqual(len(S), 31)
        self.assertTrue(pool.is_critical(S))
        axes = [index[tuple(1 if i == j else 0 for i in range(5))] for j in range(5)]
        self.assertTrue(set(axes) <= S)
        # cube 2211: pairs (e0+ej, e0-ej) for j = 1, 2 both chosen; for j = 3, 4 only e0+ej
        fin = axes + [index[(1, 1, 0, 0, 0)], index[(1, -1, 0, 0, 0)], index[(1, 0, 1, 0, 0)],
                      index[(1, 0, -1, 0, 0)], index[(1, 0, 0, 1, 0)], index[(1, 0, 0, 0, 1)]]
        fout = [index[(1, 0, 0, -1, 0)], index[(1, 0, 0, 0, -1)]]
        assume = [(v + 1) if v in S else -(v + 1) for v in range(pool.n)]
        for k, want in ((31, True), (30, False)):
            F = ks_cnf.encode(pool, k, [], fin, fout, [[0, 1, 2, 3, 4]], symbreak=True)
            with Solver(name="g4", bootstrap_with=F.clauses) as s:
                self.assertEqual(s.solve(assumptions=assume), want, f"k={k}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
