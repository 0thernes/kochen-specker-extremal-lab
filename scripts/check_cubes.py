"""check_cubes.py - certification of the "all five axes" case of the
{0,+1,-1}^5 pool (81 cubes, bound k = 28).

For every cube (states of the four pivot pairs, see src/cubes_d5.py) this
script
  1. re-verifies every cut of the cube from its witness (an independent set);
  2. re-encodes the candidate problem from scratch (ks_cnf.encode) and checks
     that the clause list written by the solver run is the same multiset of
     clauses;
  3. runs verify/drup_check on (formula, proof).
It also checks that the 81 cubes are exactly the 3^4 combinations.
Writes results/d5_cubes_certification.json; exit status 0 only if all pass.

usage: python -u scripts/check_cubes.py [parallel]
"""
from __future__ import annotations

import itertools
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import pools
from ks_cnf import encode, verify_cuts

K = 28
CASE_AXES = [0, 1, 2, 3, 4]
EXE = os.path.join(ROOT, "verify", "drup_check.exe" if os.name == "nt" else "drup_check")


def file_sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def cube_fixes(pool, states):
    index = {tuple(r): i for i, r in enumerate(pool.rays)}
    fin, fout = [], []
    for j, s in zip(range(1, 5), states):
        plus = [0] * 5
        plus[0] = 1
        plus[j] = 1
        minus = [0] * 5
        minus[0] = 1
        minus[j] = -1
        ip, im = index[tuple(plus)], index[tuple(minus)]
        if s == 0:
            fout += [ip, im]
        elif s == 1:
            fin.append(ip)
            fout.append(im)
        else:
            fin += [ip, im]
    return fin, fout


def read_cnf(path):
    """Clauses of a DIMACS file, read token by token exactly as the proof checker reads it: a clause
    ends at the token 0 wherever the line breaks are.  Raises ValueError if a token is not an
    integer, if the file ends inside a clause, or if the header disagrees with the content."""
    cls, cur, header = [], [], None
    with open(path) as f:
        for line in f:
            if line.startswith("c"):
                continue
            if line.startswith("p"):
                parts = line.split()
                header = (int(parts[2]), int(parts[3]))
                continue
            for t in line.split():
                lit = int(t)
                if lit == 0:
                    cls.append(tuple(sorted(cur)))
                    cur = []
                else:
                    cur.append(lit)
    if cur:
        raise ValueError(f"{path}: the file ends inside a clause")
    if header is not None:
        nv = max((abs(l) for c in cls for l in c), default=0)
        if len(cls) != header[1] or nv > header[0]:
            raise ValueError(f"{path}: header says {header}, file has {len(cls)} clauses and variable {nv}")
    return cls


def main():
    par = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    global CHECKER
    CHECKER = file_sha256(EXE)
    quiet = lambda *a: None
    pool = pools.box_pool(5, 1, log=quiet).ks_core(log=quiet)
    axis = {}
    for i, r in enumerate(pool.rays):
        nz = [j for j, c in enumerate(r) if c != 0]
        if len(nz) == 1:
            axis[nz[0]] = i
    axes_in = [axis[a] for a in CASE_AXES]
    groups = [CASE_AXES]
    tags = ["".join(map(str, s)) for s in itertools.product((0, 1, 2), repeat=4)]
    assert len(tags) == 81
    base = os.path.join(ROOT, "results", "satcegar_box_5_1_k28_in01234_cube{}_cuts")
    t0 = time.time()

    def one(tag):
        states = tuple(int(c) for c in tag)
        b = base.format(tag)
        rec = {"cube": tag}
        if not (os.path.exists(b + ".json") and os.path.exists(b + ".cnf") and os.path.exists(b + ".drat")):
            rec["status"] = "missing files"
            return rec
        data = json.load(open(b + ".json"))
        cw = [(c, I) for c, I in data["cuts"]]
        rec["cuts"] = len(cw)
        if not verify_cuts(pool, cw):
            rec["status"] = "cut verification failed"
            return rec
        fin, fout = cube_fixes(pool, states)
        F = encode(pool, K, [c for c, _ in cw], axes_in + fin, fout, groups, symbreak=True)
        mine = sorted(tuple(sorted(cl)) for cl in F.clauses)
        try:
            theirs = sorted(read_cnf(b + ".cnf"))
        except ValueError as exc:
            rec["status"] = f"formula file malformed: {exc}"
            return rec
        rec["clauses"] = len(mine)
        if mine != theirs:
            rec["status"] = "formula differs from the re-encoding"
            return rec
        # Exit status of verify/drup_check: 0 = proof accepted, 1 = proof rejected, 2 = input could not
        # be read or memory ran out (says nothing about the proof).  Anything else (no verdict line) means
        # the checker did not run to the end.  Cases 2 and "did not finish" are retried once.
        for attempt in (1, 2):
            r = subprocess.run([EXE, b + ".cnf", b + ".drat"], capture_output=True, text=True)
            rec["drup_check"] = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
            rec["exit_status"] = r.returncode
            rec["checker_binary_sha256"] = CHECKER
            rec["attempts"] = attempt
            for line in r.stdout.splitlines():
                if "lemmas checked" in line:
                    rec["lemmas"] = int(line.split("original clauses,")[1].split("lemmas")[0])
            if r.returncode == 0 and "s VERIFIED" in r.stdout:
                rec["status"] = "VERIFIED"
                return rec
            if r.returncode == 1 and "s NOT VERIFIED" in r.stdout:
                rec["status"] = "proof rejected"
                return rec
            if r.returncode == 2:
                rec["status"] = "checker error: " + " ".join(l for l in r.stdout.splitlines() if l.startswith("c "))[:200]
            else:
                rec["status"] = "checker did not finish"
                rec["stderr"] = (r.stderr or "")[-300:]
            time.sleep(30)
        return rec

    # Results are written after every cube, and cubes already VERIFIED in an existing result file
    # are kept, so an interrupted run loses nothing and a second run checks only what is missing.
    out_path = os.path.join(ROOT, "results", "d5_cubes_certification.json")
    done = {}
    if os.path.exists(out_path):
        for rec in json.load(open(out_path)).get("records", []):
            if rec.get("status") == "VERIFIED":
                done[rec["cube"]] = rec
    todo = [t for t in tags if t not in done]
    print(f"{len(done)} cubes already VERIFIED in {os.path.basename(out_path)}; checking {len(todo)}", flush=True)

    def save():
        recs = [done[t] for t in tags if t in done]
        ok = sum(1 for r in recs if r["status"] == "VERIFIED")
        out = {"k": K, "case": "all five axes", "cubes": len(tags), "verified": ok,
               "lemmas_checked_total": sum(r.get("lemmas", 0) for r in recs if r["status"] == "VERIFIED"),
               "records": recs}
        with open(out_path, "w") as f:
            json.dump(out, f, indent=1)
        return ok

    with ThreadPoolExecutor(max_workers=par) as ex:
        futs = [ex.submit(one, t) for t in todo]
        for fut in as_completed(futs):
            rec = fut.result()
            done[rec["cube"]] = rec
            save()
            print(f"[{time.time()-t0:7.0f}s] cube {rec['cube']}: {rec['status']}"
                  f" ({rec.get('cuts', '-')} cuts, {rec.get('lemmas', '-')} lemmas)", flush=True)
    ok = save()
    print(f"CUBES: {ok} of {len(tags)} verified")
    sys.exit(0 if ok == len(tags) else 1)


if __name__ == "__main__":
    main()
