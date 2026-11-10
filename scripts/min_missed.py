"""min_missed.py - the fewest bases that an independent set of a pool can miss, computed exactly.

For a pool, an independent set I (pairwise non-orthogonal rays) "misses" the bases that contain no
ray of I.  The pool is colorable exactly when some I misses no basis.  The minimum number of missed
bases is a weighted MaxSAT optimum: hard clauses forbid two orthogonal rays in I, one soft clause per
basis asks for a ray of I in it.  It is solved here with the exact MaxSAT solver RC2 of PySAT, so
the value is an optimum, not the best value found within a time limit.

usage: python -u scripts/min_missed.py [kind args ...]      default: the five pools of the register
Writes results/min_missed.json.
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from ksdfs import build
from ksengine import bits

DEFAULT = [("box3", "2"), ("box3", "3"), ("box3", "4"), ("box3", "5"), ("box", "5", "1")]


def min_missed(pool):
    w = WCNF()
    for v in range(pool.n):
        for u in bits(pool.adj[v]):
            if u > v:
                w.append([-(v + 1), -(u + 1)])
    for b in pool.bases:
        w.append([v + 1 for v in b], weight=1)
    with RC2(w) as rc2:
        model = rc2.compute()
        cost = rc2.cost
    I = [v for v in range(pool.n) if model[v] > 0]
    assert all(not (pool.adj[v] & sum(1 << u for u in I)) for v in I), "model is not independent"
    missed = sum(1 for b in pool.bases if not any(v in I for v in b))
    assert missed == cost
    return cost, I


def main():
    specs = [tuple(sys.argv[1:])] if len(sys.argv) > 1 else DEFAULT
    out = []
    for spec in specs:
        t0 = time.time()
        pool, _ = build(spec[0], list(spec[1:]), log=lambda *a: None)
        cost, I = min_missed(pool)
        rec = {"pool": pool.name, "rays": pool.n, "bases": len(pool.bases), "fewest_bases_missed": cost,
               "independent_set_size": len(I), "solver": "RC2 (exact MaxSAT)", "seconds": round(time.time() - t0, 1)}
        out.append(rec)
        print(f"{pool.name}: {pool.n} rays, {len(pool.bases)} bases; an independent set misses at least "
              f"{cost} bases (optimum, RC2, {rec['seconds']}s)", flush=True)
    if len(sys.argv) == 1:
        with open(os.path.join(ROOT, "results", "min_missed.json"), "w") as f:
            json.dump(out, f, indent=1)
        print("wrote results/min_missed.json")


if __name__ == "__main__":
    main()
