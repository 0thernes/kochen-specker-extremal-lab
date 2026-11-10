"""hunt.py - randomised record hunt in a named pool.

usage: python -u hunt.py <seconds> <seed> <kind> [args...]
   kinds: box d H | e8 | stab n | stabreal n
Writes logs/hunt_<tag>_s<seed>.log and results/hunt_<tag>_s<seed>.json
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pools
from kslocal import local_search

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build(kind, args, log):
    if kind == "box":
        full = pools.box_pool(int(args[0]), int(args[1]), log=log)
    elif kind == "e8":
        full = pools.e8_pool(log=log)
    elif kind == "stab":
        full, _ = pools.stabilizer_pool(int(args[0]), log=log)
    elif kind == "stabreal":
        full, _ = pools.stabilizer_pool(int(args[0]), log=log, real_only=True)
    elif kind == "roots":
        import cyclo
        full = cyclo.root_pool(int(args[0]), int(args[1]), log=log)
    elif kind == "box3":
        import pools3d
        return pools3d.build_box3(int(args[0]), log=log)
    else:
        raise SystemExit("unknown kind")
    return full.ks_core(log=log)


def main():
    seconds = float(sys.argv[1])
    seed = int(sys.argv[2])
    kind = sys.argv[3]
    args = sys.argv[4:]
    tag = "_".join([kind] + args)
    logf = open(os.path.join(ROOT, "logs", f"hunt_{tag}_s{seed}.log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    t0 = time.time()
    core = build(kind, args, log)
    log(f"pool ready in {time.time()-t0:.1f}s")
    best = local_search(core, seconds=seconds, seed=seed, log=log)
    ok = core.is_critical(best)
    rays = [core.rays[v] for v in sorted(best)]
    out = {"pool": core.name, "seed": seed, "size": len(best), "description": core.describe(best),
           "critical": ok, "rays": rays}
    with open(os.path.join(ROOT, "results", f"hunt_{tag}_s{seed}.json"), "w") as f:
        json.dump(out, f, indent=1)
    log(f"HUNT RESULT {core.name} seed {seed}: {core.describe(best)} critical={ok}")


if __name__ == "__main__":
    main()
