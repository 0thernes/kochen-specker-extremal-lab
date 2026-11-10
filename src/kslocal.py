"""kslocal.py - randomised search for small critical KS sets inside a pool.

Walk on critical KS sets: add a few rays (or a whole basis) to the current
set, then delete rays in random order while the set stays KS.  Moves to a set
that is not much larger are accepted (annealing on the size).  Every reported
set is re-verified from scratch by the caller; this file only proposes.
"""
from __future__ import annotations

import math
import random
import time

from ksengine import mask, bits


def shrink_random(pool, S, rng, protect=()):
    """Critical KS subset of the KS set S; rays in `protect` are tried last."""
    core = pool.ks_core_of(S)
    if core is None:
        return None
    S = set(core)
    order = [v for v in S if v not in protect]
    rng.shuffle(order)
    tail = [v for v in S if v in protect]
    rng.shuffle(tail)
    for v in order + tail:
        if v not in S:
            continue
        core = pool.ks_core_of(S - {v})
        if core is not None:
            S = set(core)
    return frozenset(S)


def local_search(pool, seconds=60, seed=1, log=print, start=None, temp=1.2, add_basis_prob=0.5,
                 target=None):
    rng = random.Random(seed)
    t0 = time.time()
    everything = list(range(pool.n))
    S = start or shrink_random(pool, everything, rng)
    best = S
    log(f"[{time.time()-t0:7.1f}s] seed {seed}: start {len(S)} rays")
    steps = 0
    hist = {}
    while time.time() - t0 < seconds:
        steps += 1
        # destroy: forbid a few rays of the current set; repair: take a critical
        # KS subset of the rest of the pool that keeps as much of S as possible
        r = rng.choice((1, 1, 1, 2, 2, 3))
        R = set(rng.sample(sorted(S), min(r, len(S))))
        keep = S - R
        T = [v for v in everything if v not in R]
        U = shrink_random(pool, T, rng, protect=keep)
        if U is None:
            continue
        hist[len(U)] = hist.get(len(U), 0) + 1
        delta = len(U) - len(S)
        if delta <= 0 or rng.random() < math.exp(-delta / temp):
            S = U
        if len(U) < len(best):
            best = U
            log(f"[{time.time()-t0:7.1f}s] seed {seed}: new best {pool.describe(best)} (step {steps})")
            if target is not None and len(best) <= target:
                break
    log(f"[{time.time()-t0:7.1f}s] seed {seed}: done, {steps} steps, best {len(best)}, "
        f"sizes seen {sorted(hist.items())[:8]}")
    return best


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pools

    d = int(sys.argv[1])
    H = int(sys.argv[2])
    secs = float(sys.argv[3])
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    full = pools.box_pool(d, H)
    core = full.ks_core()
    best = local_search(core, seconds=secs, seed=seed)
    print("BEST", len(best), core.describe(best))
    for v in sorted(best):
        print("  ", core.rays[v])
