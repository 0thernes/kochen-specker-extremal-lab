"""test_verify_tools.py - the independent checking tools.

  * verify/drup_check (C): built with gcc into a temporary directory when no
    up-to-date binary is present; tests/test_drup.py is run as a subprocess;
    a fresh proof is produced and checked, and wrong formula/proof pairs must
    be rejected;
  * verify/verify_cert.mjs and verify/test_verify.mjs (JavaScript; skipped
    with a message when node is not installed);
  * results/lemma7_d5_axes.json: re-checked with integer arithmetic and
    recomputed by scripts/lemma7.py.

Nothing is written into the repository: programs that write next to their
sources are run from a temporary copy (tests/_common.make_sandbox).

Environment:  KS_SKIP_JS_SUITE=1 skips the half-minute run of
verify/test_verify.mjs (scripts/run_all.py runs it as its own stage).

Run alone:  python tests/test_verify_tools.py
"""
from __future__ import annotations

import copy
import itertools
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

from pysat.solvers import Solver  # noqa: E402

import gen_cert  # noqa: E402
import ks_cnf  # noqa: E402
import ksmaster  # noqa: E402
import pools  # noqa: E402
from ksengine import bits  # noqa: E402

PY = sys.executable


class NaiveUnitPropagation:
    """Unit propagation by occurrence lists, written for these tests only."""

    def __init__(self, clauses):
        self.clauses = [list(cl) for cl in clauses]
        self.occ = {}
        for i, cl in enumerate(self.clauses):
            for lit in cl:
                self.occ.setdefault(lit, []).append(i)
        self.units = [cl[0] for cl in self.clauses if len(cl) == 1]
        self.has_empty = any(not cl for cl in self.clauses)

    def conflict(self, assumed):
        """True iff propagating the literals `assumed` (all true) runs into a conflict."""
        if self.has_empty:
            return True
        val = {}
        queue = []

        def assign(lit):
            cur = val.get(abs(lit))
            if cur is None:
                val[abs(lit)] = lit > 0
                queue.append(lit)
                return True
            return cur == (lit > 0)

        for lit in list(assumed) + self.units:
            if not assign(lit):
                return True
        while queue:
            lit = queue.pop()
            for i in self.occ.get(-lit, ()):
                free, n_free, satisfied = None, 0, False
                for x in self.clauses[i]:
                    cur = val.get(abs(x))
                    if cur is None:
                        free = x
                        n_free += 1
                    elif cur == (x > 0):
                        satisfied = True
                        break
                if satisfied:
                    continue
                if n_free == 0:
                    return True
                if n_free == 1 and not assign(free):
                    return True
        return False


class DrupChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="ks_drup_")
        cls.in_repo = C.drup_binary_in_repo()
        if cls.in_repo:
            cls.exe, cls.how = cls.in_repo, "binary found in verify/"
        else:
            cls.exe, cls.how = C.build_drup(cls.tmp)
        cls.pool = pools.box_pool(3, 2, log=C.quiet)
        m = ksmaster.Master(cls.pool, 30, sym=pools.signed_perm_symmetry(cls.pool), log=C.quiet,
                            workers=C.WORKERS)
        assert m.run(max_seconds=120)["status"] == "none"
        cls.cuts = [sorted(c) for c in m.cuts]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        if self.exe is None:
            self.skipTest("drup_check is not available: " + self.how)

    def formula(self, k):
        F = ks_cnf.encode(self.pool, k, self.cuts, groups=[[0, 1, 2]], symbreak=True)
        path = os.path.join(self.tmp, f"k{k}.cnf")
        C.write_cnf(path, F.nv, F.clauses)
        return F, path

    def proof(self, F, name):
        with Solver(name="g4", bootstrap_with=F.clauses, with_proof=True) as s:
            self.assertFalse(s.solve())
            lines = s.get_proof()
        path = os.path.join(self.tmp, name)
        with open(path, "w") as f:
            for line in lines:
                f.write(line + "\n")
        return path, lines

    def test_the_binary_can_be_built_from_source(self):
        exe, msg = C.build_drup(tempfile.mkdtemp(prefix="ks_build_", dir=self.tmp))
        if exe is None and "no C compiler" in msg:
            self.skipTest(msg)
        self.assertIsNotNone(exe, msg)
        # the freshly built checker agrees with the one in use on a tiny example
        cnf = os.path.join(self.tmp, "tiny.cnf")
        C.write_cnf(cnf, 2, [[1, 2], [-1, 2], [1, -2], [-1, -2]])
        good = os.path.join(self.tmp, "tiny_good.drat")
        with open(good, "w") as f:
            f.write("2 0\n0\n")
        bad = os.path.join(self.tmp, "tiny_bad.drat")
        with open(bad, "w") as f:
            f.write("0\n")
        for binary in (exe, self.exe):
            self.assertTrue(C.drup_verified(binary, cnf, good)[0])
            self.assertFalse(C.drup_verified(binary, cnf, bad)[0])

    def test_existing_test_drup_script(self):
        if self.in_repo:
            code, out = C.run([PY, os.path.join(C.TESTS, "test_drup.py")], cwd=C.ROOT, timeout=300)
        else:
            # test_drup.py looks for the binary in ../verify: give it a copy of the layout
            box = C.make_sandbox(with_results=("master_box3_2_k30_cuts.*", "master_box_4_1_k17_cuts.*"))
            try:
                shutil.copy2(self.exe, os.path.join(box, "verify", os.path.basename(self.exe)))
                code, out = C.run([PY, os.path.join(box, "tests", "test_drup.py")], cwd=box, timeout=300)
            finally:
                shutil.rmtree(box, ignore_errors=True)
        self.assertEqual(code, 0, out)
        self.assertIn("failures: 0", out)
        self.assertNotIn("FAIL ", out)
        self.assertGreaterEqual(out.count("PASS "), 8, out)

    def test_fresh_proof_is_verified_and_wrong_pairs_are_rejected(self):
        F30, cnf30 = self.formula(30)
        proof, lines = self.proof(F30, "k30.drat")
        ok, out = C.drup_verified(self.exe, cnf30, proof)
        self.assertTrue(ok, out)
        # (1) the same proof against the satisfiable formula for k = 31
        F31, cnf31 = self.formula(31)
        with Solver(name="g4", bootstrap_with=F31.clauses) as s:
            self.assertTrue(s.solve())
        ok, out = C.drup_verified(self.exe, cnf31, proof)
        self.assertFalse(ok, out)
        self.assertIn("NOT VERIFIED", out)
        # (2) the empty proof
        empty = os.path.join(self.tmp, "empty.drat")
        open(empty, "w").close()
        self.assertFalse(C.drup_verified(self.exe, cnf30, empty)[0])
        # (3) only the final empty clause
        just0 = os.path.join(self.tmp, "just0.drat")
        with open(just0, "w") as f:
            f.write("0\n")
        self.assertFalse(C.drup_verified(self.exe, cnf30, just0)[0])
        # (4) the formula without its cuts (satisfiable) with the real proof
        F = ks_cnf.encode(self.pool, 30, [], groups=[[0, 1, 2]], symbreak=True)
        nocuts = os.path.join(self.tmp, "nocuts.cnf")
        C.write_cnf(nocuts, F.nv, F.clauses)
        self.assertFalse(C.drup_verified(self.exe, nocuts, proof)[0])
        # (5) a first lemma put in front of the real proof: the whole proof must be accepted
        #     exactly when that unit clause follows by unit propagation, which is decided
        #     here by a naive propagation written for this test
        up = NaiveUnitPropagation(F30.clauses)
        self.assertFalse(up.conflict([]))                  # the formula is not refuted by UP alone
        n_rup = n_not_rup = 0
        for lit in (1, -1, 2, -2, 3, -3, 10, -10, 25, -25, 49, -49):
            is_rup = up.conflict([-lit])
            path = os.path.join(self.tmp, "prefixed.drat")
            with open(path, "w") as f:
                f.write(f"{lit} 0\n" + "\n".join(lines) + "\n")
            ok, out = C.drup_verified(self.exe, cnf30, path)
            self.assertEqual(ok, is_rup, f"first lemma {lit}: naive propagation says RUP={is_rup}\n{out}")
            n_rup += is_rup
            n_not_rup += not is_rup
        self.assertGreater(n_not_rup, 0)                   # at least one bogus lemma was rejected
        # (6) missing files give a non-zero exit status, not a verdict
        code, out = C.run([self.exe, os.path.join(self.tmp, "nope.cnf"), proof])
        self.assertNotEqual(code, 0)
        self.assertNotIn("s VERIFIED", out)

    def test_stored_proofs(self):
        checked = 0
        for base in ("master_box3_2_k30_cuts", "master_box_4_1_k17_cuts"):
            cnf = os.path.join(C.RESULTS, base + ".cnf")
            drat = os.path.join(C.RESULTS, base + ".drat")
            if not (os.path.exists(cnf) and os.path.exists(drat)):
                continue
            ok, out = C.drup_verified(self.exe, cnf, drat)
            self.assertTrue(ok, out)
            checked += 1
        if not checked:
            self.skipTest("no stored .cnf/.drat pairs in results/")
        # the two stored proofs are not interchangeable
        a = os.path.join(C.RESULTS, "master_box3_2_k30_cuts")
        b = os.path.join(C.RESULTS, "master_box_4_1_k17_cuts")
        if checked == 2:
            self.assertFalse(C.drup_verified(self.exe, a + ".cnf", b + ".drat")[0])


def fresh_certificate(pool, k):
    dfs = gen_cert.CertDfs(pool, k, sym=None, log=C.quiet)
    tree = dfs.tree(0, [])
    return {
        "pool": pool.name, "d": pool.d, "k": k,
        "rays": [list(r) for r in pool.rays],
        "adj": [sorted(bits(a)) for a in pool.adj],
        "bases": [list(b) for b in pool.bases],
        "tree": tree,
    }


class JavaScriptVerifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = C.which("node")
        cls.tmp = tempfile.mkdtemp(prefix="ks_js_")
        cls.verifier = os.path.join(C.VERIFY, "verify_cert.mjs")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        if self.node is None:
            self.skipTest("node is not installed: the JavaScript verifier tests are skipped")

    def write(self, name, obj):
        path = os.path.join(self.tmp, name)
        with open(path, "w") as f:
            json.dump(obj, f)
        return path

    def verify(self, *args):
        return C.run([self.node, self.verifier] + list(args), cwd=self.tmp, timeout=300)

    def test_test_verify_mjs(self):
        if os.environ.get("KS_SKIP_JS_SUITE") == "1":
            self.skipTest("KS_SKIP_JS_SUITE=1: verify/test_verify.mjs is run as a separate stage")
        # test_verify.mjs writes ../results/verify_summary.json: run a copy
        box = C.make_sandbox(with_results=("cert_*.json", "ks31_box3_H2.json"))
        try:
            code, out = C.run([self.node, os.path.join(box, "verify", "test_verify.mjs")], cwd=box,
                              timeout=600)
            self.assertEqual(code, 0, out[-3000:])
            with open(os.path.join(box, "results", "verify_summary.json")) as f:
                summary = json.load(f)
            self.assertEqual(summary.get("failures"), [], out[-3000:])
        finally:
            shutil.rmtree(box, ignore_errors=True)

    def test_fresh_certificates_and_their_corruptions(self):
        for d, H, k in ((3, 2, 30), (4, 1, 17)):
            pool = pools.box_pool(d, H, log=C.quiet)
            cert = fresh_certificate(pool, k)
            good = self.write(f"cert_{d}_{H}.json", cert)
            code, out = self.verify(good)
            self.assertEqual(code, 0, out)
            self.assertIn("PASS", out)
            # k raised by one: a false statement
            bad = copy.deepcopy(cert)
            bad["k"] = k + 1
            code, out = self.verify(self.write("bad_k.json", bad))
            self.assertEqual(code, 1, out)
            # the first child of the root deleted
            bad = copy.deepcopy(cert)
            del bad["tree"][1][0]
            code, out = self.verify(self.write("bad_child.json", bad))
            self.assertEqual(code, 1, out)
            # a basis dropped from the list
            bad = copy.deepcopy(cert)
            del bad["bases"][3]
            code, out = self.verify(self.write("bad_basis.json", bad))
            self.assertEqual(code, 1, out)
            # an orthogonality dropped
            bad = copy.deepcopy(cert)
            bad["adj"][0] = bad["adj"][0][1:]
            code, out = self.verify(self.write("bad_adj.json", bad))
            self.assertEqual(code, 1, out)
            # the Python re-check agrees on all of these
            self.assertTrue(gen_cert.check(cert)[0] and gen_cert.check_pool(cert))

    def test_ks_mode(self):
        ks_file = os.path.join(C.RESULTS, "ks31_box3_H2.json")
        code, out = self.verify("--ks", "--require-critical", ks_file)
        self.assertEqual(code, 0, out)
        with open(ks_file) as f:
            data = json.load(f)
        smaller = dict(data)
        smaller["rays"] = data["rays"][1:]                 # 30 rays: colorable
        code, out = self.verify("--ks", self.write("ks30.json", smaller))
        self.assertEqual(code, 1, out)
        bigger = dict(data)
        bigger["rays"] = data["rays"] + [[1, 2, 2]]        # 32 rays: KS but not critical
        path = self.write("ks32.json", bigger)
        self.assertEqual(self.verify("--ks", path)[0], 0)
        self.assertEqual(self.verify("--ks", "--require-critical", path)[0], 1)

    def test_broken_files(self):
        path = os.path.join(self.tmp, "truncated.json")
        with open(os.path.join(C.RESULTS, "ks31_box3_H2.json")) as f:
            text = f.read()
        with open(path, "w") as f:
            f.write(text[: len(text) // 2])
        self.assertNotEqual(self.verify("--ks", path)[0], 0)
        self.assertNotEqual(self.verify(os.path.join(self.tmp, "does_not_exist.json"))[0], 0)


# ---- Lemma 7 ----
def lemma7_problems(data):
    """Re-check the content of lemma7_d5_axes.json with integers only."""
    problems = []
    rays = [tuple(r) for r in data["rays"]]
    want = set()
    for v in itertools.product((-1, 0, 1), repeat=5):
        if any(v) and next(x for x in v if x) > 0:
            want.add(v)
    if set(rays) != want or len(rays) != len(want):
        problems.append("the ray list is not the pool {0, +1, -1}^5 up to sign")
        return problems
    if data.get("n_rays") != len(rays):
        problems.append("n_rays is wrong")
    nb = C.neighbour_sets(len(rays), C.orth_pairs(rays, C.int_orth))
    bases = C.cliques(nb, 5)
    if data.get("n_bases") != len(bases):
        problems.append(f"n_bases is {data.get('n_bases')}, recomputed {len(bases)}")
    axes = {i for i, r in enumerate(rays) if sum(1 for x in r if x) == 1}
    fact1 = all(set(b) & axes for b in bases)
    if data.get("fact1_every_basis_contains_an_axis") is not True or not fact1:
        problems.append("fact 1 (every basis contains an axis) does not hold or is not claimed")
    index = {r: i for i, r in enumerate(rays)}
    try:
        removed = {index[tuple(r)] for r in data["removed_axes"]}
        ones = {index[tuple(r)] for r in data["ones"]}
    except (KeyError, TypeError):
        problems.append("removed_axes / ones are not rays of the pool")
        return problems
    if len(removed) != 3 or not removed <= axes:
        problems.append("removed_axes is not a set of three coordinate axes")
    if ones & removed:
        problems.append("a removed axis has value 1")
    if not C.is_independent(nb, ones):
        problems.append("two rays of value 1 are orthogonal")
    to_hit = [b for b in bases if not (set(b) & removed)]
    if data.get("bases_avoiding_the_three_axes") != len(to_hit):
        problems.append("bases_avoiding_the_three_axes is wrong")
    unhit = [b for b in to_hit if not (set(b) & ones)]
    if unhit:
        problems.append(f"{len(unhit)} bases avoiding the removed axes have no ray of value 1")
    if data.get("fact2_colorable_without_three_axes") is not True:
        problems.append("fact 2 is not claimed")
    return problems


class Lemma7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(C.RESULTS, "lemma7_d5_axes.json")) as f:
            cls.stored = json.load(f)

    def test_stored_file(self):
        self.assertEqual(lemma7_problems(self.stored), [])
        self.assertEqual(self.stored["n_rays"], 121)
        self.assertEqual(self.stored["n_bases"], 136)

    def test_recomputation_by_the_script(self):
        box = C.make_sandbox()
        try:
            code, out = C.run([PY, os.path.join(box, "scripts", "lemma7.py")], cwd=box, timeout=300)
            self.assertEqual(code, 0, out)
            with open(os.path.join(box, "results", "lemma7_d5_axes.json")) as f:
                fresh = json.load(f)
        finally:
            shutil.rmtree(box, ignore_errors=True)
        self.assertEqual(lemma7_problems(fresh), [])
        for key in ("pool", "rays", "n_rays", "n_bases", "fact1_every_basis_contains_an_axis",
                    "removed_axes", "fact2_colorable_without_three_axes",
                    "bases_avoiding_the_three_axes"):
            self.assertEqual(fresh[key], self.stored[key], key)

    def test_corrupted_files_are_rejected(self):
        d = self.stored
        # a ray of value 1 removed
        rejected = 0
        for i in range(len(d["ones"])):
            bad = copy.deepcopy(d)
            del bad["ones"][i]
            rejected += bool(lemma7_problems(bad))
        self.assertGreater(rejected, 0)
        # a ray orthogonal to a ray of value 1 added
        bad = copy.deepcopy(d)
        first = bad["ones"][0]
        partner = next(r for r in d["rays"] if C.int_dot(r, first) == 0 and r not in d["ones"]
                       and r not in d["removed_axes"])
        bad["ones"].append(partner)
        self.assertTrue(lemma7_problems(bad))
        # only two axes removed: the file is refused, and for a mathematical reason too -
        # the stored coloring leaves bases through the third axis without a ray of value 1
        bad = copy.deepcopy(d)
        bad["removed_axes"] = bad["removed_axes"][:2]
        self.assertTrue(lemma7_problems(bad))
        rays = [tuple(r) for r in d["rays"]]
        index = {r: i for i, r in enumerate(rays)}
        bases = C.cliques(C.neighbour_sets(len(rays), C.orth_pairs(rays, C.int_orth)), 5)
        ones = {index[tuple(r)] for r in d["ones"]}
        two = {index[tuple(r)] for r in d["removed_axes"][:2]}
        self.assertTrue([b for b in bases if not (set(b) & two) and not (set(b) & ones)])
        # wrong counts, a changed ray
        bad = copy.deepcopy(d)
        bad["n_bases"] += 1
        self.assertTrue(lemma7_problems(bad))
        bad = copy.deepcopy(d)
        bad["rays"][0] = [0, 0, 0, 1, 1]
        self.assertTrue(lemma7_problems(bad))

    def test_two_axes_are_not_enough(self):
        # consistency of the "at least three axes" statement: the pool minus e0, e1 and e2 is
        # colorable (the stored coloring), and every other triple by a coordinate permutation
        rays = [tuple(r) for r in self.stored["rays"]]
        index = {r: i for i, r in enumerate(rays)}
        nb = C.neighbour_sets(len(rays), C.orth_pairs(rays, C.int_orth))
        bases = C.cliques(nb, 5)
        ones = [tuple(r) for r in self.stored["ones"]]
        for triple in itertools.combinations(range(5), 3):
            perm = list(triple) + [c for c in range(5) if c not in triple]   # coordinate j -> perm[j]
            def move(r):
                w = [0] * 5
                for j in range(5):
                    w[perm[j]] = r[j]
                if next(x for x in w if x) < 0:
                    w = [-x for x in w]
                return index[tuple(w)]
            image = {move(r) for r in ones}
            removed = {index[tuple(1 if c == a else 0 for c in range(5))] for a in triple}
            self.assertTrue(C.is_independent(nb, image))
            self.assertFalse(image & removed)
            for b in bases:
                if not (set(b) & removed):
                    self.assertTrue(set(b) & image, f"triple {triple}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
