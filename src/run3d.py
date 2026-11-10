"""run3d.py - decide whether integer rays of max-norm <= H in R^3 contain a KS
set with at most k rays.   usage: python -u run3d.py H k [seconds] [greedy]"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pools3d
from kscegar import Cegar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    H = int(sys.argv[1])
    k = int(sys.argv[2])
    secs = float(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    exact = not (len(sys.argv) > 4 and sys.argv[4] == "greedy")
    tag = f"box3_H{H}_k{k}"
    logf = open(os.path.join(ROOT, "logs", tag + ".log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    t0 = time.time()
    pool = pools3d.build_box3(H, log=log)
    sym = pools3d.cube_symmetry(pool)
    cg = Cegar(pool, sym=sym, log=log)
    res = cg.search_below(k, max_seconds=secs, exact_cuts=exact, log_every=10)
    out = {"H": H, "k": k, "status": res["status"], "iterations": res.get("iterations"),
           "cuts": len(cg.cuts), "core_rays": pool.n, "triples": len(pool.bases),
           "seconds": round(time.time() - t0, 1)}
    if res.get("ks"):
        out["ks"] = [list(pool.rays[v]) for v in sorted(res["ks"])]
    log("RESULT " + json.dumps(out))
    with open(os.path.join(ROOT, "results", tag + ".json"), "w") as f:
        json.dump(out, f, indent=1)
    return cg, res


if __name__ == "__main__":
    main()
