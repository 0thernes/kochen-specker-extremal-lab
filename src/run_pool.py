"""run_pool.py - run the exact minimum-KS search on a named pool and save the result.

usage: python -u run_pool.py <kind> [args...] [--seconds N] [--tag NAME] [--nosym]
  kinds:  box d H        integer rays of max-norm <= H in Z^d
          e8             the 120 rays of the E8 root system (d = 8)
          stab n         all n-qubit stabilizer states
          stabreal n     the real n-qubit stabilizer states
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pools
from ksengine import minimum_ks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = {}
    it = iter(argv)
    for a in it:
        if a == "--seconds":
            opts["seconds"] = float(next(it))
        elif a == "--tag":
            opts["tag"] = next(it)
        elif a == "--nosym":
            opts["nosym"] = True
        elif a == "--cuts":
            opts["cuts"] = int(next(it))
        elif a == "--orbit":
            opts["orbit"] = int(next(it))
        elif a == "--mincuts":
            opts["mincuts"] = int(next(it))
        elif a == "--workers":
            opts["workers"] = int(next(it))
        elif a == "--backend":
            opts["backend"] = next(it)
    # drop option values from positional args
    pos = []
    skip = False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in ("--seconds", "--tag", "--cuts", "--orbit", "--mincuts", "--workers", "--backend"):
            skip = True
            continue
        if a.startswith("--"):
            continue
        pos.append(a)
    kind = pos[0]
    tag = opts.get("tag") or "_".join(pos)
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
    logf = open(os.path.join(ROOT, "logs", f"{tag}.log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    log(f"=== run {' '.join(argv)} ===")
    t0 = time.time()
    if kind == "box":
        d, H = int(pos[1]), int(pos[2])
        full = pools.box_pool(d, H, log=log)
        core = full.ks_core(log=log)
        sym = pools.signed_perm_symmetry(core)
    elif kind == "e8":
        full = pools.e8_pool(log=log)
        core = full.ks_core(log=log)
        sym = pools.e8_symmetry(core)
    elif kind in ("stab", "stabreal"):
        n = int(pos[1])
        full, sym_full = pools.stabilizer_pool(n, log=log, real_only=(kind == "stabreal"))
        core = full.ks_core(log=log)
        sym = sym_full if core is full else None
    else:
        raise SystemExit("unknown pool kind")
    log(f"pool built in {time.time()-t0:.1f}s; symmetry generators: {len(sym.gens) if sym else 0}")
    if opts.get("nosym"):
        sym = None
    res = minimum_ks(core, sym=sym, log=log, max_seconds=opts.get("seconds"),
                     cuts_per_round=opts.get("cuts", 8), min_cuts_per_round=opts.get("mincuts", 1),
                     orbit_cap=opts.get("orbit", 4000), backend=opts.get("backend", "cpsat"),
                     workers=opts.get("workers", 8))
    out = {
        "pool": core.name,
        "args": argv,
        "d": core.d,
        "n_rays": core.n,
        "n_bases": len(core.bases),
        "status": res["status"],
        "lower": res["lower"],
        "best_size": len(res["best"]) if res.get("best") else None,
        "best_rays": [list(map(list, core.rays[v])) if isinstance(core.rays[v][0], tuple) else list(core.rays[v])
                      for v in sorted(res["best"])] if res.get("best") else None,
        "best_description": core.describe(res["best"]) if res.get("best") else None,
        "iterations": res.get("iterations"),
        "n_corrections": len(res["corrections"]),
        "seconds": round(time.time() - t0, 1),
    }
    with open(os.path.join(ROOT, "results", f"{tag}.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    log(f"RESULT {core.name}: status={out['status']} lower={out['lower']} best={out['best_size']} "
        f"({out['best_description']}) cuts={out['n_corrections']} time={out['seconds']}s")
    if res.get("best"):
        for v in sorted(res["best"]):
            log(f"   ray {core.rays[v]}")


if __name__ == "__main__":
    main(sys.argv[1:])
