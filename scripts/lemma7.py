"""lemma7.py - the two finite facts behind Lemma 7 of paper/PROOFS.md, for the
pool of rays of Z^5 with entries 0, +1, -1 (121 rays):

  (1) every basis (5 mutually orthogonal rays) contains a coordinate axis;
  (2) the pool with the three axes e0, e1, e2 removed is colorable.

(2) is certified by an explicit set I of pairwise non-orthogonal rays that
hits every basis avoiding the three axes; the set is found with a SAT solver
and then re-checked here with integer arithmetic only.  Writes
results/lemma7_d5_axes.json and exits non-zero if a check fails.
"""
from __future__ import annotations

import itertools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import pools
from ksengine import mask


def main():
    quiet = lambda *a: None
    pool = pools.box_pool(5, 1, log=quiet)
    rays = pool.rays
    n = len(rays)
    dot = lambda u, v: sum(a * b for a, b in zip(u, v))
    # independent recomputation of the bases (cliques of size 5), integers only
    adj = [[j for j in range(n) if j != i and dot(rays[i], rays[j]) == 0] for i in range(n)]
    aset = [set(a) for a in adj]
    bases = []

    def rec(cl, cand):
        if len(cl) == 5:
            bases.append(tuple(cl))
            return
        for v in cand:
            rec(cl + [v], [w for w in cand if w > v and w in aset[v]])

    rec([], list(range(n)))
    assert sorted(bases) == sorted(pool.bases), "basis list mismatch"
    axes = [i for i, r in enumerate(rays) if sum(1 for c in r if c) == 1]
    assert len(axes) == 5
    fact1 = all(any(v in axes for v in b) for b in bases)
    axis_of = {next(j for j, c in enumerate(rays[i]) if c): i for i in axes}
    removed = [axis_of[0], axis_of[1], axis_of[2]]
    rest = [v for v in range(n) if v not in removed]
    ones = pool.coloring(rest)
    fact2 = ones is not None
    if fact2:
        ones = sorted(ones)
        # re-check with integers only
        for a, b in itertools.combinations(ones, 2):
            assert dot(rays[a], rays[b]) != 0, "coloring has an orthogonal pair of ones"
        for b in bases:
            if any(v in removed for v in b):
                continue
            assert any(v in ones for v in b), "a basis without the three axes has no 1"
    out = {
        "pool": "rays of Z^5 with entries 0, +1, -1",
        "rays": [list(r) for r in rays],
        "n_rays": n,
        "n_bases": len(bases),
        "fact1_every_basis_contains_an_axis": fact1,
        "removed_axes": [list(rays[v]) for v in removed],
        "fact2_colorable_without_three_axes": fact2,
        "ones": [list(rays[v]) for v in ones] if fact2 else None,
        "bases_avoiding_the_three_axes": sum(1 for b in bases if not any(v in removed for v in b)),
    }
    with open(os.path.join(ROOT, "results", "lemma7_d5_axes.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"pool: {n} rays, {len(bases)} bases; every basis contains an axis: {fact1}; "
          f"pool minus e0,e1,e2 colorable: {fact2} ({len(ones) if fact2 else 0} rays of value 1, "
          f"{out['bases_avoiding_the_three_axes']} bases to hit)")
    sys.exit(0 if (fact1 and fact2) else 1)


if __name__ == "__main__":
    main()
