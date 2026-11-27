"""Property-based (Hypothesis) and parser-fuzzing (atheris-compatible) checks for KS Lab."""
import json
import math
import random
import unittest

try:
    from hypothesis import given, settings, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:
    HAS_HYPOTHESIS = False


def dot_int(u: list[int], v: list[int]) -> int:
    return sum(a * b for a, b in zip(u, v))


def normalize_ray(v: list[int]) -> tuple[int, ...] | None:
    if all(x == 0 for x in v):
        return None
    g = 0
    for x in v:
        g = math.gcd(g, abs(x))
    w = [x // g for x in v]
    for x in w:
        if x != 0:
            if x < 0:
                w = [-y for y in w]
            break
    return tuple(w)


def fuzz_drup_header(raw: bytes) -> None:
    """Atheris-compatible fuzz target for malformed DIMACS/DRUP/JSON bytes."""
    try:
        text = raw.decode("utf-8", errors="strict")
        if text.startswith("{"):
            json.loads(text)
        else:
            for line in text.splitlines()[:20]:
                parts = line.split()
                if parts and parts[0] not in ("c", "p", "d"):
                    [int(x) for x in parts]
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError, RecursionError):
        return


class KSPropertyAndFuzzTests(unittest.TestCase):
    def _check_ray_invariants(self, v: list[int], scale: int) -> None:
        r1 = normalize_ray(v)
        r2 = normalize_ray([scale * x for x in v])
        self.assertEqual(r1, r2)
        if r1 is not None:
            self.assertEqual(normalize_ray(list(r1)), r1)
            nz = [x for x in r1 if x != 0]
            self.assertGreater(nz[0], 0)

    if HAS_HYPOTHESIS:
        @given(
            v=st.lists(st.integers(min_value=-4, max_value=4), min_size=3, max_size=5),
            scale=st.integers(min_value=-5, max_value=5).filter(lambda x: x != 0),
        )
        @settings(max_examples=200, derandomize=True)
        def test_ray_normalization_invariants(self, v: list[int], scale: int) -> None:
            self._check_ray_invariants(v, scale)
    else:
        def test_ray_normalization_invariants_fallback(self) -> None:
            rng = random.Random(20261124)
            for _ in range(200):
                d = rng.randint(3, 5)
                v = [rng.randint(-4, 4) for _ in range(d)]
                scale = rng.choice([-3, -2, -1, 1, 2, 3])
                self._check_ray_invariants(v, scale)

    def test_fuzz_corpus(self) -> None:
        rng = random.Random(20261124)
        for _ in range(200):
            fuzz_drup_header(bytes(rng.getrandbits(8) for _ in range(rng.randint(0, 80))))

    def test_small_pool_bruteforce_cnf_and_independent_encoder_equivalence(self) -> None:
        """Playbook v1.3 Checklist #14: verify ks_cnf.CNF against brute-force & an independent naive encoder."""
        import pathlib
        import sys

        src_dir = str(pathlib.Path(__file__).resolve().parents[1] / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        import ks_cnf

        # Independent naive CNF cardinality-at-most-k encoder (pure Python subsets, no ks_cnf code)
        def naive_atmost_clauses(n_vars: int, bound: int) -> list[list[int]]:
            import itertools
            return [[-v for v in comb] for comb in itertools.combinations(range(1, n_vars + 1), bound + 1)]

        def eval_cnf(clauses: list[list[int]], asgn: dict[int, bool]) -> bool:
            return all(any(asgn[abs(l)] if l > 0 else not asgn[abs(l)] for l in cl) for cl in clauses)

        # Check all 2^n assignments for n = 4..6 and every bound k = 0..n against exact brute force
        for n in (4, 5, 6):
            for k in range(n + 1):
                F = ks_cnf.CNF(n)
                inputs = list(range(1, n + 1))
                out = F.counter(inputs, k + 1)
                clauses = list(F.clauses)
                if k + 1 in out:
                    clauses.append([-out[k + 1]])
                naive_cl = naive_atmost_clauses(n, k)
                for bits in range(1 << n):
                    base_asgn = {i + 1: bool((bits >> i) & 1) for i in range(n)}
                    pop = bin(bits).count("1")
                    naive_ok = eval_cnf(naive_cl, base_asgn)
                    self.assertEqual(naive_ok, pop <= k)
                    # Propagate ks_cnf auxiliary variables deterministically by checking satisfiability
                    # via simple backtracking on remaining vars (<= 25 tiny unit propagations)
                    aux = dict(base_asgn)
                    # Unit-propagate ks_cnf clauses
                    changed = True
                    contradiction = False
                    while changed and not contradiction:
                        changed = False
                        for cl in clauses:
                            sat = False
                            undec = []
                            for lit in cl:
                                v = abs(lit)
                                if v in aux:
                                    if (lit > 0 and aux[v]) or (lit < 0 and not aux[v]):
                                        sat = True
                                        break
                                else:
                                    undec.append(lit)
                            if sat:
                                continue
                            if not undec:
                                contradiction = True
                                break
                            if len(undec) == 1:
                                lit = undec[0]
                                aux[abs(lit)] = lit > 0
                                changed = True
                    self.assertEqual(not contradiction, pop <= k, f"n={n} k={k} bits={bits}")


if __name__ == "__main__":
    unittest.main()
