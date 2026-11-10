"""collect_sets.py - gather the explicit Kochen-Specker sets that witness the
upper bounds of results/RESULTS.md, re-verify each one (KS and critical) inside
its pool, and write results/ks_sets.json.

Sets: 31 rays (d=3, integers <= 2), 33 rays (d=3, 12th roots of unity),
18 rays (d=4, entries 0,+-1), 29 rays (d=5, entries 0,+-1).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import cyclo
import pools
from ksdfs import KSDfs
from kslocal import local_search

quiet = lambda *a: None


def entry(name, pool, S, note, extra=None):
    S = sorted(S)
    assert pool.is_ks(S), name + ": not a KS set"
    crit = pool.is_critical(S)
    sm = set(S)
    nb = sum(1 for b in pool.bases if all(x in sm for x in b))
    ne = sum(1 for v in S for w in S if v < w and (pool.adj[v] >> w) & 1)
    e = {"name": name, "pool": pool.name, "d": pool.d, "size": len(S), "orthogonal_pairs": ne, "bases": nb,
         "critical": crit, "note": note, "rays": [list(pool.rays[v]) for v in S]}
    if extra:
        e.update(extra)
    print(f"{name}: {len(S)} rays, {ne} orthogonal pairs, {nb} bases, critical={crit}")
    return e


# The 29-ray KS set with four coordinate axes found by engine B in the four-axis case with bound 29
# (logs/satcegar_box_5_1_k29_in0123_out4_cubesanityk29.log); it is re-verified by entry().
FOUR_AXIS_29 = [
    (0, 0, 0, 1, -1), (0, 0, 0, 1, 0), (0, 0, 0, 1, 1), (0, 0, 1, 0, -1), (0, 0, 1, 0, 0), (0, 0, 1, 0, 1),
    (0, 1, 0, 0, -1), (0, 1, 0, 0, 0), (0, 1, 0, 0, 1), (0, 1, 0, 1, 0), (0, 1, 1, 0, 0),
    (1, -1, -1, 0, -1), (1, -1, -1, 0, 1), (1, -1, 0, -1, -1), (1, -1, 0, -1, 1), (1, -1, 0, 1, -1),
    (1, -1, 0, 1, 1), (1, -1, 1, 0, -1), (1, -1, 1, 0, 1), (1, 0, 0, 0, -1), (1, 0, 0, 0, 0), (1, 0, 0, 0, 1),
    (1, 0, 0, 1, 0), (1, 0, 1, 0, 0), (1, 1, -1, 0, -1), (1, 1, -1, 0, 1), (1, 1, 0, -1, -1), (1, 1, 0, -1, 1),
    (1, 1, 0, 0, 0),
]
FOUR_AXIS_NAME = "KS-29 with four axes (dimension 5)"

# A 31-ray KS set containing all five coordinate axes, found by engine B in one cube of the
# five-axis case with bound 31 (logs/satcegar_box_5_1_k31_in01234_cube2211.log).  It is critical; it
# is NOT claimed to be the smallest KS set with five axes (29 and 30 rays are not excluded).
FIVE_AXIS_31 = [
    (0, 0, 0, 0, 1), (0, 0, 0, 1, 0), (0, 0, 1, 0, -1), (0, 0, 1, 0, 0), (0, 0, 1, 1, 0), (0, 1, -1, 0, 0),
    (0, 1, 0, 0, -1), (0, 1, 0, 0, 0), (0, 1, 0, 1, 0), (0, 1, 1, 0, 0), (1, -1, -1, -1, 0), (1, -1, -1, 0, -1),
    (1, -1, -1, 1, 0), (1, -1, 0, 0, 0), (1, -1, 1, -1, 0), (1, -1, 1, 0, -1), (1, -1, 1, 0, 1), (1, -1, 1, 1, 0),
    (1, 0, -1, 0, 0), (1, 0, 0, 0, 0), (1, 0, 0, 0, 1), (1, 0, 0, 1, 0), (1, 0, 1, 0, 0), (1, 1, -1, -1, 0),
    (1, 1, -1, 0, -1), (1, 1, -1, 0, 1), (1, 1, -1, 1, 0), (1, 1, 0, 0, 0), (1, 1, 1, -1, 0), (1, 1, 1, 0, -1),
    (1, 1, 1, 0, 1),
]
FIVE_AXIS_NAME = "KS-31 with five axes (dimension 5)"


def count_axes(pool, S):
    return sum(1 for v in S if sum(1 for c in pool.rays[v] if c) == 1)


def explicit_entry(pool, name, rays, axes, note):
    index = {tuple(r): i for i, r in enumerate(pool.rays)}
    S = [index[r] for r in rays]
    assert len(set(S)) == len(rays) and count_axes(pool, S) == axes
    return entry(name, pool, S, note, {"axes": axes})


def four_axis_entry(pool):
    return explicit_entry(pool, FOUR_AXIS_NAME, FOUR_AXIS_29, 4,
                          "found by engine B in the four-axis case with bound 29 "
                          "(logs/satcegar_box_5_1_k29_in0123_out4_cubesanityk29.log)")


def five_axis_entry(pool):
    return explicit_entry(pool, FIVE_AXIS_NAME, FIVE_AXIS_31, 5,
                          "found by engine B in cube 2211 of the five-axis case with bound 31 "
                          "(logs/satcegar_box_5_1_k31_in01234_cube2211.log); not claimed to be the "
                          "smallest KS set with five axes")


def add_explicit():
    """Add the explicit dimension-five sets to an existing results/ks_sets.json without touching the
    other entries."""
    path = os.path.join(ROOT, "results", "ks_sets.json")
    out = json.load(open(path))
    p = pools.box_pool(5, 1, log=quiet).ks_core(log=quiet)
    index = {tuple(r): i for i, r in enumerate(p.rays)}
    for e in out:
        if e["name"] == "KS-29 (dimension 5)":
            e["axes"] = count_axes(p, [index[tuple(r)] for r in e["rays"]])
    for name, make in ((FOUR_AXIS_NAME, four_axis_entry), (FIVE_AXIS_NAME, five_axis_entry)):
        if not any(e["name"] == name for e in out):
            pos = max(i for i, e in enumerate(out) if e["d"] == 5) + 1
            out.insert(pos, make(p))
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print("updated results/ks_sets.json:", [e["name"] for e in out])


def main():
    if "--add-explicit" in sys.argv:
        return add_explicit()
    out = []
    # 31 rays, d = 3
    p = pools.box_pool(3, 2, log=quiet)
    res = KSDfs(p, 31, sym=None, log=quiet).run()
    out.append(entry("KS-31 (Conway-Kochen type)", p, res["ks"], "found by exhaustive search with k = 31"))
    # 18 rays, d = 4
    p = pools.box_pool(4, 1, log=quiet)
    res = KSDfs(p, 18, sym=None, log=quiet).run()
    out.append(entry("KS-18 (Cabello-Estebaranz-Garcia-Alcaine type)", p, res["ks"],
                     "found by exhaustive search with k = 18"))
    # 29 rays, d = 5
    p = pools.box_pool(5, 1, log=quiet).ks_core(log=quiet)
    best = local_search(p, seconds=20, seed=1, log=quiet, target=29)
    assert len(best) == 29
    out.append(entry("KS-29 (dimension 5)", p, best, "found by randomised search (seed 1)"))
    # a second 29-ray set in the same pool, with four coordinate axes (the first has three)
    out[-1]["axes"] = count_axes(p, best)
    out.append(four_axis_entry(p))
    out.append(five_axis_entry(p))
    # 33 rays, d = 3, 12th roots of unity
    p = cyclo.root_pool(3, 12, log=quiet)
    best = local_search(p, seconds=30, seed=1, log=quiet, target=33)
    assert len(best) == 33
    out.append(entry("KS-33 (12th roots of unity)", p, best,
                     "found by randomised search (seed 1); entries are exponents k of exp(2 pi i k / 12), -1 = zero entry",
                     {"N": 12}))
    # 33 rays in the 6th-root pool (57 rays)
    p = cyclo.root_pool(3, 6, log=quiet)
    best = local_search(p, seconds=30, seed=1, log=quiet, target=33)
    assert len(best) == 33
    out.append(entry("KS-33 (6th roots of unity)", p, best,
                     "found by randomised search (seed 1); entries are exponents k of exp(2 pi i k / 6), -1 = zero entry",
                     {"N": 6}))
    with open(os.path.join(ROOT, "results", "ks_sets.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote results/ks_sets.json")


if __name__ == "__main__":
    main()
