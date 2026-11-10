"""cubes_d5.py - cube-and-conquer for one case of the {0,+1,-1}^5 pool.

The case is split on the four "pivot pairs" (e0+ej, e0-ej), j = 1..4.  By the
normal form (PROOFS.md, Lemma 6b) a pair is in one of three states:
  0: neither ray chosen   1: only e0+ej chosen   2: both chosen
which gives 3^4 = 81 cubes covering the case.  Each cube is an independent
run of ks_satcegar.py (plain CDCL candidate engine).

usage: python -u cubes_d5.py <k> <case> <parallel> <seconds-per-cube>
"""
from __future__ import annotations

import itertools
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def vec(j, sign):
    v = [0] * 5
    v[0] = 1
    v[j] = sign
    return ",".join(map(str, v))


def main():
    k = sys.argv[1]
    case = sys.argv[2]
    par = int(sys.argv[3])
    limit = float(sys.argv[4])
    only = sys.argv[5].split(",") if len(sys.argv) > 5 else None
    cubes = []
    for states in itertools.product((0, 1, 2), repeat=4):
        tag = "".join(map(str, states))
        if only and tag not in only:
            continue
        fin, fout = [], []
        for j, s in zip(range(1, 5), states):
            if s == 0:
                fout += [vec(j, 1), vec(j, -1)]
            elif s == 1:
                fin.append(vec(j, 1))
                fout.append(vec(j, -1))
            else:
                fin += [vec(j, 1), vec(j, -1)]
        cubes.append((tag, "|".join(fin), "|".join(fout)))
    casetag = case.replace(":", "").replace(";", "_").replace(",", "")
    summary = open(os.path.join(ROOT, "logs", f"cubes_d5_k{k}_{casetag}.log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        summary.write(line + "\n")
        summary.flush()

    log(f"=== {len(cubes)} cubes, k={k}, case={case}, {par} in parallel, {limit:.0f}s per cube")
    pending = list(cubes)
    running = []
    done = {}
    while pending or running:
        while pending and len(running) < par:
            tag, fin, fout = pending.pop(0)
            env = dict(os.environ, KS_FIX_IN=fin, KS_FIX_OUT=fout, KS_CUBE_TAG=tag)
            # KS_SOLVER chooses the candidate solver (default Glucose 4, which also writes a proof)
            p = subprocess.Popen([sys.executable, "-u", os.path.join(HERE, "ks_satcegar.py"), k, case,
                                  os.environ.get("KS_SOLVER", "g4"), "20",
                                  "box", "5", "1"], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True)
            running.append((tag, p, time.time()))
        time.sleep(2)
        still = []
        for tag, p, t0 in running:
            rc = p.poll()
            if rc is None:
                if time.time() - t0 > limit:
                    p.kill()
                    done[tag] = "timeout"
                    log(f"cube {tag}: TIMEOUT after {limit:.0f}s")
                else:
                    still.append((tag, p, t0))
                continue
            out = p.stdout.read()
            res = "error"
            for line in out.splitlines():
                if "SATCEGAR RESULT" in line:
                    res = "none" if ": none" in line else ("found" if ": found" in line else "error")
            done[tag] = res
            log(f"cube {tag}: {res} in {time.time()-t0:.0f}s ({len(done)}/{len(cubes)} done)")
            if res == "error":
                log("   last output: " + out[-300:].replace("\n", " | "))
        running = still
    counts = {}
    for r in done.values():
        counts[r] = counts.get(r, 0) + 1
    log(f"SUMMARY k={k} case={case}: {counts}")


if __name__ == "__main__":
    main()
