"""Property-based (Hypothesis) and parser-fuzzing (atheris-compatible) checks for KS Lab."""
from __future__ import annotations

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

    def test_ast_source_code_mutation_killing(self) -> None:
        """Isolated AST source-code mutation testing (Build Standard B13):
        mutate real operators in in-memory AST copies of src/pools.py and src/ks_cnf.py
        and assert that core invariants kill 100% of source mutants."""
        import ast
        import pathlib
        import sys
        import types

        root = pathlib.Path(__file__).resolve().parents[1]
        src_dir = str(root / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        import ks_cnf
        import pools

        def load_mutated(path: pathlib.Path, fn_name: str, target_op: type, replacement_op: type) -> types.ModuleType:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            mutated = False

            class OpMutator(ast.NodeTransformer):
                def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
                    nonlocal mutated
                    if node.name != fn_name:
                        return node
                    return self.generic_visit(node)

                def visit_Compare(self, node: ast.Compare) -> ast.AST:
                    nonlocal mutated
                    if not mutated:
                        new_ops = []
                        for op in node.ops:
                            if not mutated and isinstance(op, target_op):
                                new_ops.append(replacement_op())
                                mutated = True
                            else:
                                new_ops.append(op)
                        node.ops = new_ops
                    return node

                def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
                    nonlocal mutated
                    if not mutated and isinstance(node.op, target_op):
                        node.op = replacement_op()
                        mutated = True
                    return self.generic_visit(node)

            # Mutate ONLY inside the target function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == fn_name:
                    OpMutator().visit(node)
                    break
            self.assertTrue(mutated, f"AST mutant not applied to {path.name}:{fn_name}")
            ast.fix_missing_locations(tree)
            mod = types.ModuleType(f"_mut_{path.stem}_{fn_name}")
            mod.__file__ = str(path)
            exec(compile(tree, str(path), "exec"), mod.__dict__)
            return mod

        # Baseline valid inputs
        p_b32 = pools.box_pool(3, 2, log=lambda *_a: None)
        self.assertEqual(p_b32.n, 49)
        valid_cut = ([i for i, b in enumerate(p_b32.bases) if 0 not in b], [0])
        self.assertTrue(ks_cnf.verify_cuts(p_b32, [valid_cut]))

        killed = 0
        mutants = [
            # Mutant 1: invert orthogonality check dot(u, v) == 0 -> != 0 in pools.int_orth
            ("pools.int_orth: == -> !=", root / "src" / "pools.py", "int_orth", ast.Eq, ast.NotEq,
             lambda m: m.int_orth((1, 0, 0), (0, 1, 0)) is True),
            # Mutant 2: flip canonical sign test x < 0 -> x > 0 in pools.primitive
            ("pools.primitive: < -> >", root / "src" / "pools.py", "primitive", ast.Lt, ast.Gt,
             lambda m: m.primitive((-2, 4, 0)) == (1, -2, 0)),
            # Mutant 3: corrupt dot product sum(a * b) -> sum(a + b) in pools.dot
            ("pools.dot: * -> +", root / "src" / "pools.py", "dot", ast.Mult, ast.Add,
             lambda m: m.dot((1, 0, 0), (0, 1, 0)) == 0),
            # Mutant 4: invert cut equality sorted(cut) != missed -> == in ks_cnf.verify_cuts
            ("ks_cnf.verify_cuts: != -> ==", root / "src" / "ks_cnf.py", "verify_cuts", ast.NotEq, ast.Eq,
             lambda m: m.verify_cuts(p_b32, [valid_cut]) is True),
            # Mutant 5: weaken independence check pool.adj[v] & Im -> | in ks_cnf.verify_cuts
            ("ks_cnf.verify_cuts: & -> |", root / "src" / "ks_cnf.py", "verify_cuts", ast.BitAnd, ast.BitOr,
             lambda m: m.verify_cuts(p_b32, [valid_cut]) is True),
            # Mutant 6: break closed_under generator check
            ("ks_cnf.closed_under: In -> NotIn", root / "src" / "ks_cnf.py", "closed_under", ast.In, ast.NotIn,
             lambda m: m.closed_under(pools.signed_perm_symmetry(p_b32), [list(range(p_b32.n))]) is True),
        ]
        for label, path, fn_name, old_op, new_op, invariant in mutants:
            with self.subTest(ast_mutant=label):
                mod = load_mutated(path, fn_name, old_op, new_op)
                try:
                    ok = bool(invariant(mod))
                except Exception:
                    ok = False
                self.assertFalse(ok, f"AST source mutant survived: {label}")
                killed += 1
        self.assertEqual(killed, len(mutants))


if __name__ == "__main__":
    unittest.main()
