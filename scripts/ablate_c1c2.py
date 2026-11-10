"""ablate_c1c2.py - what do the two necessary conditions for critical KS sets (Lemma 3) buy?

Runs engine A (src/ksmaster.py, class Master) on one pool and bound four times: with both conditions
(C1: every chosen ray lies in a chosen basis; C2: every chosen ray has at least d chosen orthogonal
partners), with only one of them, and with neither.  Everything else is the same: same pool, same
symmetry breaking, same number of workers, same time limit.  Writes results/ablate_c1c2_<pool>.json
and logs/ablate_c1c2_<pool>.log.

usage: python -u scripts/ablate_c1c2.py <k> <seconds per run> <workers> <kind> <args...>
example: python -u scripts/ablate_c1c2.py 30 600 4 box3 4
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ksdfs import build
from ksmaster import Master, box_symmetry_breaking


def main():
    k = int(sys.argv[1])
    seconds = float(sys.argv[2])
    workers = int(sys.argv[3])
    kind = sys.argv[4]
    args = sys.argv[5:]
    tag = "ablate_c1c2_" + "_".join([kind] + args) + f"_k{k}"
    logf = open(os.path.join(ROOT, "logs", tag + ".log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    out = []
    for use_c1, use_c2 in ((True, True), (True, False), (False, True), (False, False)):
        pool, sym = build(kind, args, log=lambda *a: None)
        log(f"=== {pool.name} k={k}: C1={'on' if use_c1 else 'off'}, C2={'on' if use_c2 else 'off'}, "
            f"{workers} workers, limit {seconds:.0f}s")
        ms = Master(pool, k, sym=sym, log=log, workers=workers, use_c1=use_c1, use_c2=use_c2)
        if kind in ("box", "box3"):
            ms.symbreak = box_symmetry_breaking(pool, [list(range(pool.d))])
        t0 = time.time()
        res = ms.run(max_seconds=seconds, cand_time=seconds)
        dt = time.time() - t0
        rec = {"C1": use_c1, "C2": use_c2, "status": res["status"], "rounds": res.get("iterations"),
               "cuts": len(ms.cuts), "seconds": round(dt, 1)}
        out.append(rec)
        log(f"ABLATION RESULT C1={use_c1} C2={use_c2}: {res['status']} after {res.get('iterations')} rounds, "
            f"{len(ms.cuts)} cuts, {dt:.1f}s")
    with open(os.path.join(ROOT, "results", tag + ".json"), "w") as f:
        json.dump({"pool": pool.name, "k": k, "workers": workers, "limit_seconds": seconds, "runs": out}, f, indent=1)
    log("wrote results/" + tag + ".json")


if __name__ == "__main__":
    main()
