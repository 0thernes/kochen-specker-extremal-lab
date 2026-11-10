"""peres24.py - where do the 16 minimum KS sets of B(4, 1) live?

The 40 rays of B(4, 1) are the 24 rays of Peres (4 rays with one non-zero coordinate, 12 with two,
8 with four) and 16 rays with three non-zero coordinates.  The 24 rays of Peres are known to contain
exactly 16 KS sets of 18 rays and 9 bases (M. Waegell, P. K. Aravind, Found. Phys. 41 (2011) 1786).
This script checks that each of the 16 sets of results/enumerate_box_4_1_k18.json uses only rays of
Peres, so that they are those 16 known sets, and writes results/peres24_check.json.

usage: python scripts/peres24.py
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import pools

quiet = lambda *a: None


def main():
    pool = pools.box_pool(4, 1, log=quiet)
    weight = [sum(1 for c in r if c) for r in pool.rays]
    by_weight = {w: weight.count(w) for w in sorted(set(weight))}
    enum = json.load(open(os.path.join(ROOT, "results", "enumerate_box_4_1_k18.json")))
    sets = enum["sets_as_indices"]
    rows = []
    for S in sets:
        ws = sorted(weight[v] for v in S)
        bases = sum(1 for b in pool.bases if all(v in S for v in b))
        rows.append({"rays": len(S), "bases": bases, "is_ks": pool.is_ks(S),
                     "weights": {str(w): ws.count(w) for w in sorted(set(ws))},
                     "inside_peres_24": all(w != 3 for w in ws)})
    inside = sum(1 for r in rows if r["inside_peres_24"])
    out = {"pool_rays": pool.n, "rays_by_number_of_nonzero_coordinates": {str(k): v for k, v in by_weight.items()},
           "minimum_sets": len(sets), "inside_peres_24": inside, "sets": rows}
    with open(os.path.join(ROOT, "results", "peres24_check.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(f"B(4,1): {pool.n} rays, by number of non-zero coordinates {by_weight}")
    print(f"{len(sets)} minimum sets; {inside} of them use only the 24 rays of Peres; "
          f"all KS: {all(r['is_ks'] for r in rows)}; bases per set: {sorted(set(r['bases'] for r in rows))}")
    print("wrote results/peres24_check.json")


if __name__ == "__main__":
    main()
