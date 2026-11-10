"""ks_satcegar.py - the counterexample-guided search of ksmaster.py with a
plain incremental CDCL SAT solver as candidate engine (encoding of ks_cnf.py).

usage: python -u ks_satcegar.py <k> <case|-> <solver> <seedpairs> <kind> [args...]
Writes results/satcegar_<tag>_cuts.json (cuts + witnesses) on success, so that
ks_cnf.py + drup_check can certify the final formula independently.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pysat.solvers import Solver

from ks_cnf import encode, parse_case
from ksdfs import build
from ksmaster import Master

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    k = int(sys.argv[1])
    case = sys.argv[2]
    solver_name = sys.argv[3]
    seedpairs = int(sys.argv[4])
    kind = sys.argv[5]
    args = sys.argv[6:]
    tag = "satcegar_" + "_".join([kind] + args) + f"_k{k}" + ("" if case == "-" else "_" + case.replace(":", "").replace(";", "_").replace(",", ""))
    if os.environ.get("KS_CUBE_TAG"):
        tag += "_cube" + os.environ["KS_CUBE_TAG"]
    logf = open(os.path.join(ROOT, "logs", tag + ".log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    pool, sym = build(kind, args, log=lambda *a: None)
    fix_in, fix_out, groups = parse_case(pool, case)
    ms = Master(pool, k, sym=sym, log=log, workers=3, fix_in=fix_in, fix_out=fix_out)
    n, nb = pool.n, len(pool.bases)
    F = encode(pool, k, [], fix_in, fix_out, groups, symbreak=kind in ("box", "box3"))
    log(f"=== {tag}: CNF {F.nv} vars, {len(F.clauses)} clauses (before cuts)")
    with_proof = solver_name in ("g3", "g4") and os.environ.get("KS_PROOF", "1") == "1"
    sat = Solver(name=solver_name, bootstrap_with=F.clauses, with_proof=with_proof)
    t0 = time.time()
    known = 0

    def push_new_cuts():
        global known
        for cut in ms.cuts[known:]:
            sat.add_clause([n + b + 1 for b in cut])
        known = len(ms.cuts)

    I = ms.best_coloring(())
    ms.add_cut_orbit(ms.missed(I), I)
    if seedpairs:
        ms.seed_cuts(max_pairs=seedpairs)
    push_new_cuts()
    it = 0
    while True:
        it += 1
        ts = time.time()
        ok = sat.solve()
        ts = time.time() - ts
        if not ok:
            log(f"[{time.time()-t0:8.1f}s] it {it}: UNSAT ({ts:.1f}s) - no critical KS set with at most {k} rays "
                f"({len(ms.cuts)} cuts)")
            ms.save_cuts(os.path.join(ROOT, "results", tag + "_cuts.json"))
            if with_proof:
                # The lemmas were derived while cuts were still being added; each is a
                # consequence of the clauses present at that time, hence of the final
                # formula written here (base encoding plus every cut).
                try:
                    proof = sat.get_proof()
                    base = os.path.join(ROOT, "results", tag + "_cuts")
                    allc = F.clauses + [[n + b + 1 for b in cut] for cut in ms.cuts]
                    with open(base + ".cnf", "w") as f:
                        f.write(f"p cnf {F.nv} {len(allc)}\n")
                        for cl in allc:
                            f.write(" ".join(map(str, cl)) + " 0\n")
                    with open(base + ".drat", "w") as f:
                        for line in proof:
                            f.write(line + "\n")
                    log(f"wrote final CNF ({len(allc)} clauses) and DRUP proof ({len(proof)} lines)")
                except Exception as e:      # proof logging must never change the verdict line
                    log(f"proof not written: {e!r}")
            log(f"SATCEGAR RESULT {pool.name} k={k} case={case}: none after {it} iterations, {len(ms.cuts)} cuts")
            break
        model = sat.get_model()
        S = frozenset(v for v in range(n) if model[v] > 0)
        I = ms.best_coloring(S)
        if I is None:
            log(f"[{time.time()-t0:8.1f}s] it {it}: FOUND a KS set: {pool.describe(S)}")
            for v in sorted(S):
                log(f"   ray {pool.rays[v]}")
            log(f"SATCEGAR RESULT {pool.name} k={k} case={case}: found")
            break
        fresh = ms.add_cut_orbit(ms.missed(I), I)
        push_new_cuts()
        log(f"[{time.time()-t0:8.1f}s] it {it}: candidate {len(S)} rays ({ts:.1f}s) colorable; +{fresh} cuts "
            f"(total {len(ms.cuts)})")
