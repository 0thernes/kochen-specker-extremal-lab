"""pool_facts.py - recompute the pool statistics quoted in results/RESULTS.md and store them.

  * B(3, H) for H = 2, 3, 4, 5, 6, 8, 10: rays, orthogonal pairs, orthogonal triples (bases), and the
    core (rays and bases left after the iterated deletion of Corollary 4);
  * U(3, N) for N = 2, ..., 12: rays, bases, core, and whether the pool contains a KS set at all
    (the whole pool is a KS set exactly when it is not colorable; subsets of colorable sets are
    colorable, so a colorable pool contains no KS set);
  * B(4, 1), B(5, 1): rays, bases, core.

Writes results/pool_facts.json and prints one line per pool.
usage: python scripts/pool_facts.py
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import cyclo
import pools
import pools3d

quiet = lambda *a: None


def main():
    out = {"box3": [], "roots3": [], "box": []}
    for H in (2, 3, 4, 5, 6, 8, 10):
        t0 = time.time()
        rays, nbrs, tri = pools3d.box3_structure(H, log=quiet)
        core = pools3d.build_box3(H, log=quiet)
        rec = {"H": H, "rays": len(rays), "orthogonal_pairs": sum(len(x) for x in nbrs) // 2,
               "bases": len(tri), "core_rays": core.n, "core_bases": len(core.bases),
               "seconds": round(time.time() - t0, 1)}
        out["box3"].append(rec)
        print(f"B(3,{H}): {rec['rays']} rays, {rec['bases']} bases; core {rec['core_rays']} rays, "
              f"{rec['core_bases']} bases", flush=True)
    for N in range(2, 13):
        t0 = time.time()
        p = cyclo.root_pool(3, N, log=quiet)
        core = p.ks_core(log=quiet)
        has_ks = bool(core.n) and core.is_ks(list(range(core.n)))
        rec = {"N": N, "rays": p.n, "bases": len(p.bases), "core_rays": core.n, "core_bases": len(core.bases),
               "contains_ks_set": has_ks, "seconds": round(time.time() - t0, 1)}
        out["roots3"].append(rec)
        print(f"U(3,{N}): {rec['rays']} rays, {rec['bases']} bases; core {rec['core_rays']} rays; "
              f"contains a KS set: {has_ks}", flush=True)
    for d, H in ((4, 1), (5, 1)):
        p = pools.box_pool(d, H, log=quiet)
        core = p.ks_core(log=quiet)
        rec = {"d": d, "H": H, "rays": p.n, "bases": len(p.bases), "core_rays": core.n, "core_bases": len(core.bases)}
        out["box"].append(rec)
        print(f"B({d},{H}): {rec['rays']} rays, {rec['bases']} bases; core {rec['core_rays']} rays, "
              f"{rec['core_bases']} bases", flush=True)
    with open(os.path.join(ROOT, "results", "pool_facts.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote results/pool_facts.json")


if __name__ == "__main__":
    main()
