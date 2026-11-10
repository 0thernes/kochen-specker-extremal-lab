"""ks_cnf.py - independent re-proof of a "no critical KS set with at most k rays"
result by a CDCL SAT solver with a DRAT proof.

Input: the cut file written by ksmaster.py (each cut = list of basis indices
plus the independent set that certifies it), the pool, k and the case.
The candidate problem is re-encoded from scratch as plain CNF:

  x_v            ray v chosen                         (variables 1..n)
  y_b            basis b chosen                       (n+1..n+nb)
  (D)  y_b -> x_v ;  AND x_v -> y_b
  (C1) x_v -> OR_{b containing v} y_b
  (C2) x_v -> at least d neighbours chosen            (sequential counter per ray)
  (K)  at most k rays chosen                          (sequential counter)
  (S)  symmetry breaking for box pools                (two-sided counters + binary clauses)
  cuts OR_{b in cut} y_b, each re-verified here from its witness
  case constraints as unit clauses

All counters are two-sided ("s[i][j] <-> at least j of the first i inputs are
true"), so each constraint is encoded exactly.

usage: python -u ks_cnf.py <cuts.json> <k> <case|-> <solver> <kind> [args...]
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pysat.solvers import Solver

from ksdfs import build
from ksengine import bits, mask


class CNF:
    def __init__(self, nvars):
        self.nv = nvars
        self.clauses = []

    def new(self):
        self.nv += 1
        return self.nv

    def add(self, cl):
        self.clauses.append(list(cl))

    def counter(self, lits, maxj):
        """Two-sided sequential counter.  Returns out[j] (1 <= j <= maxj) with
        out[j] <-> (at least j of lits are true)."""
        prev = {}            # prev[j] = literal for "at least j among first i" ; j=0 is True
        for i, x in enumerate(lits, start=1):
            cur = {}
            for j in range(1, min(i, maxj) + 1):
                s = self.new()
                cur[j] = s
                a = prev.get(j)            # at least j among first i-1 (None = False if j > i-1)
                b = prev.get(j - 1) if j > 1 else "T"     # at least j-1 among first i-1
                # s <-> a OR (x AND b)
                # (->): s -> a OR x ; s -> a OR b
                cl1 = [-s, x]
                cl2 = [-s]
                if a is not None:
                    cl1.append(a)
                    cl2.append(a)
                if b == "T":
                    self.add(cl1)
                elif b is None:
                    # x AND b is false: s -> a
                    self.add(cl2 if a is not None else [-s])
                else:
                    self.add(cl1)
                    self.add(cl2 + [b])
                # (<-): a -> s ; (x AND b) -> s
                if a is not None:
                    self.add([-a, s])
                if b == "T":
                    self.add([-x, s])
                elif b is not None:
                    self.add([-x, -b, s])
            prev = cur
        return prev


def encode(pool, k, cuts, fix_in=(), fix_out=(), groups=None, symbreak=True):
    n, d = pool.n, pool.d
    nb = len(pool.bases)
    X = lambda v: v + 1
    Y = lambda b: n + b + 1
    F = CNF(n + nb)
    for b, basis in enumerate(pool.bases):
        for v in basis:
            F.add([-Y(b), X(v)])
        F.add([Y(b)] + [-X(v) for v in basis])
    bases_of = [[] for _ in range(n)]
    for b, basis in enumerate(pool.bases):
        for v in basis:
            bases_of[v].append(b)
    for v in range(n):
        F.add([-X(v)] + [Y(b) for b in bases_of[v]])
    for v in range(n):
        nbrs = [X(w) for w in bits(pool.adj[v])]
        if len(nbrs) < d:
            F.add([-X(v)])
            continue
        out = F.counter(nbrs, d)
        F.add([-X(v), out[d]])
    if k < n:                       # with k >= n the size bound is vacuous
        out = F.counter([X(v) for v in range(n)], k + 1)
        F.add([-out[k + 1]])
    for v in fix_in:
        F.add([X(v)])
    for v in fix_out:
        F.add([-X(v)])
    if symbreak and groups is not None:
        index = {r: i for i, r in enumerate(pool.rays)}
        supp = [[X(i) for i, r in enumerate(pool.rays) if r[j] != 0] for j in range(d)]
        for g in groups:
            for a, b in zip(g, g[1:]):
                oa = F.counter(supp[a], len(supp[a]))
                ob = F.counter(supp[b], len(supp[b]))
                # n_a >= n_b : (count_b >= j) -> (count_a >= j)
                for j in range(1, len(supp[b]) + 1):
                    if j in oa:
                        F.add([-ob[j], oa[j]])
                    else:
                        F.add([-ob[j]])
        for j in range(1, d):
            a = [0] * d
            a[0] = 1
            a[j] = 1
            b = [0] * d
            b[0] = 1
            b[j] = -1
            ia, ib = index.get(tuple(a)), index.get(tuple(b))
            if ia is not None and ib is not None:
                F.add([-X(ib), X(ia)])
    for cut in cuts:
        F.add([Y(b) for b in cut])
    return F


def verify_cuts(pool, cuts_with_witness):
    """Each cut must equal the set of bases missed by its (independent) witness."""
    bm = [mask(b) for b in pool.bases]
    for cut, I in cuts_with_witness:
        Im = mask(I)
        for v in I:
            if pool.adj[v] & Im:
                return False
        missed = [i for i in range(len(bm)) if not (bm[i] & Im)]
        if sorted(cut) != missed:
            return False
    return True


def parse_case(pool, case):
    fix_in, fix_out, ins, outs = [], [], [], []
    d = pool.d
    if case != "-":
        axis = {}
        for i, r in enumerate(pool.rays):
            nz = [j for j, c in enumerate(r) if c != 0]
            if len(nz) == 1:
                axis[nz[0]] = i
        for part in case.split(";"):
            name, vals = part.split(":")
            cs = [int(c) for c in vals.split(",") if c != ""]
            if name == "in":
                ins.extend(cs)
                fix_in.extend(axis[c] for c in cs)
            else:
                outs.extend(cs)
                fix_out.extend(axis[c] for c in cs)
        rest = [j for j in range(d) if j not in ins and j not in outs]
        groups = [g for g in (ins, outs, rest) if len(g) > 1]
    else:
        groups = [list(range(d))]
    # optional extra fixed rays (cube-and-conquer): KS_FIX_IN / KS_FIX_OUT hold ray
    # vectors separated by '|', e.g. "1,1,0,0,0|1,-1,0,0,0".  They are accepted only
    # together with KS_CUBE_TAG, so that variables left over in a shell cannot silently
    # turn a whole-case run into a run for one cube.
    index = {tuple(r): i for i, r in enumerate(pool.rays)}
    for var, target in (("KS_FIX_IN", fix_in), ("KS_FIX_OUT", fix_out)):
        txt = os.environ.get(var, "")
        if txt and not os.environ.get("KS_CUBE_TAG"):
            raise SystemExit(f"{var} is set but KS_CUBE_TAG is not: refusing to fix rays outside a cube run")
        for part in [p for p in txt.split("|") if p]:
            vec = tuple(int(c) for c in part.split(","))
            if vec not in index:
                raise SystemExit(f"{var}: ray {vec} is not in the pool")
            target.append(index[vec])
    return fix_in, fix_out, groups


def closed_under(sym, sets):
    """True if the family of ray sets is mapped into itself by every generator of the symmetry."""
    family = {frozenset(S) for S in sets}
    return all(frozenset(g[v] for v in S) in family for S in family for g in sym.gens)


if __name__ == "__main__":
    cuts_path = sys.argv[1]
    k = int(sys.argv[2])
    case = sys.argv[3]
    solver_name = sys.argv[4]
    kind = sys.argv[5]
    args = sys.argv[6:]
    quiet = lambda *a: None
    pool, sym = build(kind, args, log=quiet)
    data = json.load(open(cuts_path))
    cw = [(c, I) for c, I in data["cuts"]]
    t0 = time.time()
    ok = verify_cuts(pool, cw)
    print(f"{len(cw)} cuts re-verified from their witnesses: {ok} ({time.time()-t0:.1f}s)", flush=True)
    if not ok:
        raise SystemExit(1)
    fix_in, fix_out, groups = parse_case(pool, case)
    symbreak = kind in ("box", "box3")
    print(f"case {case}: rays fixed in {[pool.rays[v] for v in fix_in]}, fixed out "
          f"{[pool.rays[v] for v in fix_out]}; symmetry breaking {'on, groups ' + str(groups) if symbreak else 'off'}",
          flush=True)
    F = encode(pool, k, [c for c, _ in cw], fix_in, fix_out, groups, symbreak=symbreak)
    # Uniqueness runs: KS_BLOCKED names a results/enumerate_*.json file; every KS set listed there
    # is excluded by one clause.  Without symmetry breaking, UNSAT then means "there is no further
    # KS set with at most k rays".  With symmetry breaking it means "every KS set with at most k
    # rays is an image of a listed set under the symmetry group", so the list must be closed under
    # that group for the count to be right; this is checked here and the run stops otherwise.
    blocked_path = os.environ.get("KS_BLOCKED")
    if blocked_path:
        enum = json.load(open(blocked_path))
        sets = enum["sets_as_indices"]
        if len({frozenset(S) for S in sets}) != len(sets):
            raise SystemExit("blocked list contains a set twice")
        for S in sets:
            if not pool.is_ks(S) or len(S) != k:
                raise SystemExit("blocked list contains a set that is not a KS set of size k")
            F.add([-(v + 1) for v in S])
        print(f"{len(sets)} listed KS sets of size {k} excluded (each re-verified as a KS set)", flush=True)
        if symbreak:
            if case != "-":
                raise SystemExit("uniqueness runs with symmetry breaking are supported for the case '-' only")
            if not closed_under(sym, sets):
                raise SystemExit("the blocked list is NOT closed under the signed coordinate permutations: "
                                 "the count of sets would be wrong")
            print(f"the list is closed under the {len(sym.gens)} generators of the signed coordinate "
                  f"permutations (checked)", flush=True)
    print(f"CNF: {F.nv} variables, {len(F.clauses)} clauses", flush=True)
    base = os.path.splitext(cuts_path)[0]
    if os.path.exists(base + ".drat"):
        os.remove(base + ".drat")       # a proof from an earlier run must never be checked against this formula
    with open(base + ".cnf", "w") as f:
        f.write(f"p cnf {F.nv} {len(F.clauses)}\n")
        for cl in F.clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")
    t0 = time.time()
    with_proof = solver_name in ("g3", "g4", "lgl", "mcb")
    s = Solver(name=solver_name, bootstrap_with=F.clauses, with_proof=with_proof)
    r = s.solve()
    dt = time.time() - t0
    print(f"{solver_name}: {'SAT' if r else 'UNSAT'} in {dt:.1f}s", flush=True)
    if r:
        model = s.get_model()
        S = [v for v in range(pool.n) if model[v] > 0]
        print("candidate:", len(S), "rays; KS:", pool.is_ks(S))
        # satisfiable: nothing was proved, and no proof file exists.  os._exit, because on Windows
        # the destructor of a proof-logging Glucose object can end the process with status 127
        # after a satisfiable answer, which would hide the documented status 3.
        sys.stdout.flush()
        os._exit(3)
    elif with_proof:
        proof = s.get_proof()
        with open(base + ".drat", "w") as f:
            for line in proof:
                f.write(line + "\n")
        print(f"DRAT proof: {len(proof)} lines -> {base}.drat", flush=True)
