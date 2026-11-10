"""axes_sanity.py - how many coordinate axes do critical KS sets of the pool B(5, 1) contain?

Sanity check for the case analysis of dimension five: critical KS sets with three, four and five
axes all exist, so none of the three cases is empty, and a search in any of them with a large enough
bound must find a KS set.

Each sample is a PLAIN random deletion: start from the whole core, go through the rays in random
order (the axes last, or in a fully random order with --mixed), and delete a ray whenever the rest is
still a KS set.  The result is a critical KS set.  (An earlier version of this script jumped to the
SAT solver's unsatisfiable core after every deletion; that sampler is biased and returned four axes
in every one of 58 684 runs, which led to the wrong remark that five-axis critical sets might not
exist.  They are in fact the most common outcome of plain deletion with the axes last.)

usage: python scripts/axes_sanity.py [seconds] [--mixed]
Writes results/d5_axes_sanity.json.
"""
from __future__ import annotations

import json
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import pools

quiet = lambda *a: None


def plain_deletion(pool, order):
    S = set(range(pool.n))
    for v in order:
        if pool.is_ks(S - {v}):
            S.discard(v)
    return frozenset(S)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    seconds = float(args[0]) if args else 60
    mixed = "--mixed" in sys.argv
    pool = pools.box_pool(5, 1, log=quiet).ks_core(log=quiet)
    axes = [i for i, r in enumerate(pool.rays) if sum(1 for c in r if c) == 1]
    others = [v for v in range(pool.n) if v not in axes]
    best, count, sizes = {}, {}, {}
    t0 = time.time()
    seed = 0
    while time.time() - t0 < seconds:
        seed += 1
        rng = random.Random(seed)
        if mixed:
            order = list(range(pool.n))
            rng.shuffle(order)
        else:
            head, tail = others[:], axes[:]
            rng.shuffle(head)
            rng.shuffle(tail)
            order = head + tail
        S = plain_deletion(pool, order)
        na = sum(1 for v in S if v in axes)
        count[na] = count.get(na, 0) + 1
        sizes.setdefault(na, {})
        sizes[na][len(S)] = sizes[na].get(len(S), 0) + 1
        if na not in best or len(S) < len(best[na][0]):
            best[na] = (S, seed)
    print(f"{seed} samples ({'fully random order' if mixed else 'axes last'}); "
          f"critical KS sets by number of axes: {dict(sorted(count.items()))}")
    out = {}
    for na, (S, sd) in sorted(best.items()):
        crit = pool.is_critical(S)
        print(f"  {na} axes: smallest found has {len(S)} rays (seed {sd}); {pool.describe(S)}; critical={crit}")
        out[str(na)] = {"size": len(S), "seed": sd, "critical": crit,
                        "sizes_seen": {str(k): v for k, v in sorted(sizes[na].items())},
                        "rays": [list(pool.rays[v]) for v in sorted(S)]}
    with open(os.path.join(ROOT, "results", "d5_axes_sanity.json"), "w") as f:
        json.dump({"sampler": "plain random deletion, " + ("fully random order" if mixed else "axes last"),
                   "samples": sum(count.values()), "by_axes": {str(k): v for k, v in sorted(count.items())},
                   "smallest_by_axes": out}, f, indent=1)
    print("wrote results/d5_axes_sanity.json")


if __name__ == "__main__":
    main()
