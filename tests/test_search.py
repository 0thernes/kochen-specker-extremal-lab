"""test_search.py - the three search engines on the two small pools.

  * ksdfs.KSDfs            exhaustive tree search (with and without symmetry)
  * gen_cert.CertDfs/check search-tree certificates and their re-check
  * ksmaster.Master        CP-SAT counterexample-guided search
  * ksengine.minimum_ks    implicit hitting sets

The values 31 (d = 3, max-norm <= 2, 49 rays) and 18 (d = 4, entries 0, +-1,
40 rays) are the Lean-checked rows A1 and A8 of results/RESULTS.md.  Every KS
set returned by an engine is re-checked by an exhaustive search that uses no
SAT solver (tests/_common.py).

Run alone:  python tests/test_search.py
"""
from __future__ import annotations

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

import gen_cert  # noqa: E402
import ks_cnf  # noqa: E402
import ksdfs  # noqa: E402
import ksengine  # noqa: E402
import ksmaster  # noqa: E402
import pools  # noqa: E402
from ksengine import bits  # noqa: E402


class Fixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p3 = pools.box_pool(3, 2, log=C.quiet)
        cls.p4 = pools.box_pool(4, 1, log=C.quiet)
        assert (cls.p3.n, cls.p4.n) == (49, 40)
        assert C.pool_discrepancies(cls.p3, C.int_orth) == []
        assert C.pool_discrepancies(cls.p4, C.int_orth) == []
        cls.s3 = C.structure_of(cls.p3)
        cls.s4 = C.structure_of(cls.p4)

    def assert_ks(self, pool, structure, S, at_most):
        nb, bases = structure
        S = set(S)
        self.assertTrue(S <= set(range(pool.n)))
        self.assertLessEqual(len(S), at_most)
        self.assertIsNone(C.decide_colorable(nb, bases, S), "the set returned by the engine is colorable")


class TreeSearch(Fixture):
    def run_dfs(self, pool, k, sym):
        return ksdfs.KSDfs(pool, k, sym=sym, log=C.quiet).run()

    def test_49_ray_pool(self):
        for sym in (None, pools.signed_perm_symmetry(self.p3)):
            res = self.run_dfs(self.p3, 30, sym)
            self.assertEqual(res["status"], "none")
            res = self.run_dfs(self.p3, 31, sym)
            self.assertEqual(res["status"], "found")
            self.assertEqual(len(res["ks"]), 31)
            self.assert_ks(self.p3, self.s3, res["ks"], 31)
            self.assertTrue(self.p3.is_critical(res["ks"]))

    def test_40_ray_pool(self):
        for sym in (None, pools.signed_perm_symmetry(self.p4)):
            res = self.run_dfs(self.p4, 17, sym)
            self.assertEqual(res["status"], "none")
            res = self.run_dfs(self.p4, 18, sym)
            self.assertEqual(res["status"], "found")
            self.assertEqual(len(res["ks"]), 18)
            self.assert_ks(self.p4, self.s4, res["ks"], 18)

    def test_smaller_bounds_and_monotonicity(self):
        for k in (3, 10, 29):
            self.assertEqual(self.run_dfs(self.p3, k, None)["status"], "none")
        res = self.run_dfs(self.p3, 49, None)          # no bound at all: some KS set
        self.assertEqual(res["status"], "found")
        self.assert_ks(self.p3, self.s3, res["ks"], 49)

    def test_colorable_pool_is_exhausted_at_every_bound(self):
        # negative control: a pool WITHOUT a KS set (the 49-ray pool minus a minimum
        # correction set) must give "none" even for k = n
        D = self.p3.minimum_correction_set()
        sub = self.p3.restrict([v for v in range(self.p3.n) if v not in D], log=C.quiet)
        nb, bases = C.structure_of(sub)
        self.assertIsNotNone(C.decide_colorable(nb, bases, range(sub.n)))
        self.assertEqual(self.run_dfs(sub, sub.n, None)["status"], "none")
        # and removing nothing gives a KS pool: the same call must then find something
        self.assertEqual(self.run_dfs(self.p3, self.p3.n, None)["status"], "found")

    def test_timeout_is_reported_not_swallowed(self):
        res = ksdfs.KSDfs(self.p4, 17, sym=None, log=C.quiet, max_seconds=1e-9).run()
        self.assertEqual(res["status"], "timeout")


def make_cert(pool, k):
    dfs = gen_cert.CertDfs(pool, k, sym=None, log=C.quiet)
    tree = dfs.tree(0, [])
    cert = {
        "pool": pool.name, "d": pool.d, "k": k,
        "rays": [list(r) for r in pool.rays],
        "adj": [sorted(bits(a)) for a in pool.adj],
        "bases": [list(b) for b in pool.bases],
        "tree": tree,
    }
    return cert, dfs.nodes


def count_nodes(node):
    return 1 + sum(count_nodes(child) for _, child in node[1])


def accepted(cert):
    """Full acceptance: pool data re-derived from the vectors, then the tree.
    A crash of the checker on malformed input counts as a rejection."""
    try:
        return bool(gen_cert.check_pool(cert)) and bool(gen_cert.check(cert)[0])
    except (IndexError, KeyError, TypeError, ValueError):
        return False


class Certificates(Fixture):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cert, cls.nodes = make_cert(cls.p3, 30)

    def test_certificate_of_the_49_ray_pool(self):
        self.assertEqual(self.nodes, 255)
        self.assertEqual(count_nodes(self.cert["tree"]), 255)
        ok, replayed = gen_cert.check(self.cert)
        self.assertTrue(ok)
        self.assertEqual(replayed, 255)
        self.assertTrue(gen_cert.check_pool(self.cert))
        self.assertTrue(accepted(self.cert))

    def test_certificate_of_the_40_ray_pool(self):
        cert, nodes = make_cert(self.p4, 17)
        self.assertEqual(count_nodes(cert["tree"]), nodes)
        self.assertEqual(gen_cert.check(cert), (True, nodes))
        self.assertTrue(gen_cert.check_pool(cert))
        bad = copy.deepcopy(cert)
        bad["k"] = 18
        self.assertFalse(gen_cert.check(bad)[0])

    def test_corruption_1_k_raised(self):
        bad = copy.deepcopy(self.cert)
        bad["k"] = 31                       # false statement: a 31-ray KS set exists
        self.assertFalse(gen_cert.check(bad)[0])
        self.assertFalse(accepted(bad))

    def test_corruption_2_child_deleted(self):
        # every single child deletion, anywhere in the tree
        def paths(node, path=()):
            for i, (_, child) in enumerate(node[1]):
                yield path + (i,)
                yield from paths(child, path + (i,))

        total = wrongly_accepted = 0
        for path in paths(self.cert["tree"]):
            bad = copy.deepcopy(self.cert)
            node = bad["tree"]
            for i in path[:-1]:
                node = node[1][i][1]
            del node[1][path[-1]]
            total += 1
            wrongly_accepted += gen_cert.check(bad)[0]
        self.assertEqual(total, 254)
        self.assertEqual(wrongly_accepted, 0)

    def test_corruption_3_independent_set_changed(self):
        root_I = self.cert["tree"][0]
        # (a) a ray replaced by one orthogonal to another ray of I: rule 1 fails
        bad = copy.deepcopy(self.cert)
        bad["tree"][0][0] = self.cert["adj"][root_I[1]][0]
        self.assertFalse(gen_cert.check(bad)[0])
        # (b) a ray dropped from I: some basis is no longer hit and rule 2 fails
        rejected = 0
        for pos in range(len(root_I)):
            bad = copy.deepcopy(self.cert)
            del bad["tree"][0][pos]
            rejected += not gen_cert.check(bad)[0]
        self.assertGreater(rejected, 0)
        # (c) the empty I at the root
        bad = copy.deepcopy(self.cert)
        bad["tree"][0] = []
        self.assertFalse(gen_cert.check(bad)[0])
        # (d) a ray ADDED that is orthogonal to a ray of I: every basis is still hit, so only
        #     rule 1 (independence) can reject this one
        extra = next(w for w in self.cert["adj"][root_I[0]] if w not in root_I)
        bad = copy.deepcopy(self.cert)
        bad["tree"][0].append(extra)
        self.assertFalse(gen_cert.check(bad)[0])
        # ... the same deep inside the tree (first leaf)
        bad = copy.deepcopy(self.cert)
        node = bad["tree"]
        while node[1]:
            node = node[1][0][1]
        if node[0]:
            w = next(x for x in self.cert["adj"][node[0][0]] if x not in node[0])
            node[0].append(w)
            self.assertFalse(gen_cert.check(bad)[0])

    def test_corruption_4_pool_data_changed(self):
        # a basis dropped from the list (rule 2 would then be checked against too few bases)
        for pos in (0, 5, len(self.cert["bases"]) - 1):
            bad = copy.deepcopy(self.cert)
            del bad["bases"][pos]
            self.assertFalse(gen_cert.check_pool(bad))
            self.assertFalse(accepted(bad))
        # an orthogonality removed, a coordinate changed, a bogus basis added
        bad = copy.deepcopy(self.cert)
        bad["adj"][0] = bad["adj"][0][1:]
        self.assertFalse(accepted(bad))
        bad = copy.deepcopy(self.cert)
        bad["rays"][3][2] += 1
        self.assertFalse(accepted(bad))
        bad = copy.deepcopy(self.cert)
        bad["bases"].append([0, 1, 2])
        self.assertFalse(accepted(bad))

    def test_certificate_refuses_a_bound_that_is_false(self):
        # CertDfs must not return a tree for k = 31 (a KS set with 31 rays exists)
        dfs = gen_cert.CertDfs(self.p3, 31, sym=None, log=C.quiet)
        with self.assertRaises(RuntimeError):
            dfs.tree(0, [])

    def test_stored_certificates_match_fresh_ones_in_content(self):
        import json
        path = os.path.join(C.RESULTS, "cert_box3_H2_k30.json")
        if not os.path.exists(path):
            self.skipTest("results/cert_box3_H2_k30.json is not present")
        with open(path) as f:
            stored = json.load(f)
        self.assertEqual(stored["k"], 30)
        self.assertEqual(sorted(map(tuple, stored["rays"])), sorted(self.p3.rays))
        self.assertTrue(accepted(stored))
        self.assertEqual(count_nodes(stored["tree"]), 255)


class MasterSearch(Fixture):
    def run_master(self, pool, k, symbreak, sym=True):
        m = ksmaster.Master(pool, k, sym=pools.signed_perm_symmetry(pool) if sym else None,
                            log=C.quiet, workers=C.WORKERS)
        if symbreak:
            m.symbreak = ksmaster.box_symmetry_breaking(pool, [list(range(pool.d))])
        res = m.run(max_seconds=120)
        return m, res

    def check_cuts(self, pool, structure, m):
        nb, bases = structure
        self.assertTrue(m.cuts)
        self.assertTrue(ks_cnf.verify_cuts(pool, [(sorted(c), sorted(m.witness[c])) for c in m.cuts]))
        for cut in m.cuts:                                  # and without the project's code
            I = m.witness[cut]
            self.assertTrue(C.is_independent(nb, I))
            self.assertEqual(sorted(cut), C.missed_bases(bases, I))

    def test_49_ray_pool_k30_infeasible(self):
        for symbreak in (False, True):
            m, res = self.run_master(self.p3, 30, symbreak)
            self.assertEqual(res["status"], "none", f"symbreak={symbreak}")
            self.check_cuts(self.p3, self.s3, m)

    def test_49_ray_pool_k31_finds_a_set(self):
        for symbreak in (False, True):
            m, res = self.run_master(self.p3, 31, symbreak)
            self.assertEqual(res["status"], "found", f"symbreak={symbreak}")
            self.assert_ks(self.p3, self.s3, res["ks"], 31)
            self.assertEqual(len(res["ks"]), 31)
            self.check_cuts(self.p3, self.s3, m)
            if symbreak:
                self.assertEqual(normal_form_violations(self.p3, res["ks"]), [])

    def test_40_ray_pool(self):
        m, res = self.run_master(self.p4, 17, True)
        self.assertEqual(res["status"], "none")
        self.check_cuts(self.p4, self.s4, m)
        m, res = self.run_master(self.p4, 18, True)
        self.assertEqual(res["status"], "found")
        self.assert_ks(self.p4, self.s4, res["ks"], 18)

    def test_without_symmetric_cut_images(self):
        m, res = self.run_master(self.p3, 30, False, sym=False)
        self.assertEqual(res["status"], "none")
        self.check_cuts(self.p3, self.s3, m)

    def test_tampered_cuts_are_rejected(self):
        m, _ = self.run_master(self.p3, 30, False)
        good = [(sorted(c), sorted(m.witness[c])) for c in m.cuts]
        self.assertTrue(ks_cnf.verify_cuts(self.p3, good))
        nb, _ = self.s3
        cut, I = good[0]
        # a basis removed from the cut (the clause would be too strong)
        self.assertFalse(ks_cnf.verify_cuts(self.p3, [(cut[1:], I)] + good[1:]))
        # a witness that is not independent
        v = I[0]
        self.assertFalse(ks_cnf.verify_cuts(self.p3, [(cut, I + [min(nb[v])])] + good[1:]))
        # a witness that misses more bases than the cut lists
        self.assertFalse(ks_cnf.verify_cuts(self.p3, good[:-1] + [(good[-1][0], good[-1][1][1:])]))

    def test_a_too_small_time_limit_is_reported(self):
        m = ksmaster.Master(self.p3, 30, sym=None, log=C.quiet, workers=C.WORKERS)
        res = m.run(max_seconds=1e-9)
        # one iteration cannot settle k = 30 (the first candidate is colorable), so the
        # run must stop with "timeout" and must not claim infeasibility
        self.assertEqual(res["status"], "timeout")
        self.assertEqual(res.get("iterations"), 1)


class _Recorder:
    """Stands in for a CP-SAT model: box_symmetry_breaking only calls Add(...)
    with comparisons, which evaluate to plain booleans on integer inputs."""

    def __init__(self):
        self.results = []

    def Add(self, condition):
        self.results.append(bool(condition))


def normal_form_violations(pool, S, groups=None):
    add = ksmaster.box_symmetry_breaking(pool, groups or [list(range(pool.d))])
    x = [1 if v in set(S) else 0 for v in range(pool.n)]
    rec = _Recorder()
    add(rec, x)
    return [i for i, ok in enumerate(rec.results) if not ok]


class MinimumSearch(Fixture):
    def check(self, pool, structure, want, backend):
        nb, bases = structure
        res = ksengine.minimum_ks(pool, sym=pools.signed_perm_symmetry(pool), log=C.quiet,
                                  backend=backend, workers=C.WORKERS, max_seconds=120)
        self.assertEqual(res["status"], "optimal")
        self.assertEqual(res["lower"], want)
        self.assertEqual(len(res["best"]), want)
        self.assert_ks(pool, structure, res["best"], want)
        # every correction set is certified: its complement is colorable
        self.assertTrue(res["corrections"])
        for D in res["corrections"][:: max(1, len(res["corrections"]) // 25)]:
            rest = [v for v in range(pool.n) if v not in D]
            self.assertTrue(pool.check_correction_set(D))
            self.assertIsNotNone(C.decide_colorable(nb, bases, rest))
        # the minimum KS set meets every correction set (Corollary 2)
        for D in res["corrections"]:
            self.assertTrue(set(D) & set(res["best"]))
        return res

    def test_box_3_2_gives_31(self):
        for backend in ("cpsat", "rc2"):
            self.check(self.p3, self.s3, 31, backend)

    def test_box_4_1_gives_18(self):
        for backend in ("cpsat", "rc2"):
            self.check(self.p4, self.s4, 18, backend)

    def test_colorable_pool(self):
        D = self.p3.minimum_correction_set()
        sub = self.p3.restrict([v for v in range(self.p3.n) if v not in D], log=C.quiet)
        res = ksengine.minimum_ks(sub, log=C.quiet, workers=C.WORKERS)
        self.assertEqual(res["status"], "colorable")
        self.assertIsNone(res["best"])

    def test_wrong_correction_sets_are_rejected(self):
        self.assertFalse(self.p3.check_correction_set(set()))            # the pool itself is KS
        D = self.p3.minimum_correction_set()
        self.assertTrue(self.p3.check_correction_set(D))
        for v in D:                                                       # D is minimum, so minimal
            self.assertFalse(self.p3.check_correction_set(set(D) - {v}))
        # hitting-set layer: the minimum of {0,1},{1,2},{3} is 2, and "upper=2" proves it
        for backend in ("cpsat", "rc2"):
            hs = ksengine.HittingSets(5, backend=backend, workers=C.WORKERS)
            for s in ({0, 1}, {1, 2}, {3}):
                hs.add(s)
            H = hs.minimum()
            self.assertEqual(len(H), 2)
            self.assertTrue(all(H & s for s in ({0, 1}, {1, 2}, {3})))
        hs = ksengine.HittingSets(5, backend="cpsat", workers=C.WORKERS)
        for s in ({0, 1}, {1, 2}, {3}):
            hs.add(s)
        self.assertIsNone(hs.minimum(upper=2))
        self.assertIsNotNone(hs.minimum(upper=3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
