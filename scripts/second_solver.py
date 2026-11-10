"""second_solver.py - solve existing CNF formulas again with a different SAT solver.

The formulas results/*.cnf are written by src/ks_cnf.py and src/ks_satcegar.py and were shown
unsatisfiable by Glucose 4, whose proofs are checked by verify/drup_check.  This script hands the
same files to another solver (default: CaDiCaL 1.9.5 through PySAT) and records the verdicts.  It is
a redundancy check of the solver answers only: the formula and its encoder are the same.

usage: python -u scripts/second_solver.py <solver> <parallel> <timeout seconds> <tag> <cnf files...>
       (internal) python scripts/second_solver.py --one <solver> <cnf file>

Writes results/second_solver_<tag>.json after every finished formula (so an interrupted run keeps
what it has) and logs/second_solver_<tag>.log.  Exit status 0 only if every formula is UNSAT.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def solve_one(solver_name, path):
    from pysat.formula import CNF
    from pysat.solvers import Solver

    t0 = time.time()
    cnf = CNF(from_file=path)
    s = Solver(name=solver_name, bootstrap_with=cnf.clauses)
    r = s.solve()
    out = {"file": os.path.basename(path), "solver": solver_name, "variables": cnf.nv,
           "clauses": len(cnf.clauses), "result": "SAT" if r else "UNSAT",
           "seconds": round(time.time() - t0, 1)}
    s.delete()
    print(json.dumps(out), flush=True)


def main():
    if sys.argv[1] == "--one":
        return solve_one(sys.argv[2], sys.argv[3])
    solver_name = sys.argv[1]
    par = int(sys.argv[2])
    timeout = int(sys.argv[3])
    tag = sys.argv[4]
    files = sys.argv[5:]
    out_path = os.path.join(ROOT, "results", f"second_solver_{tag}.json")
    log_path = os.path.join(ROOT, "logs", f"second_solver_{tag}.log")
    records = {}
    if os.path.exists(out_path):                 # resume: keep finished formulas
        for rec in json.load(open(out_path)).get("records", []):
            if rec.get("result") in ("UNSAT", "SAT") and rec.get("solver") == solver_name:
                records[rec["file"]] = rec
    t0 = time.time()

    def log(msg):
        line = f"[{time.time()-t0:7.0f}s] {msg}"
        print(line, flush=True)
        with open(log_path, "a") as f:
            f.write(time.strftime("%H:%M:%S ") + line + "\n")

    def save():
        recs = [records[k] for k in sorted(records)]
        summary = {"solver": solver_name, "formulas": len(files),
                   "unsat": sum(1 for r in recs if r["result"] == "UNSAT"),
                   "sat": sum(1 for r in recs if r["result"] == "SAT"),
                   "other": sum(1 for r in recs if r["result"] not in ("UNSAT", "SAT")),
                   "records": recs}
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=1)

    def one(path):
        name = os.path.basename(path)
        if name in records:
            return records[name]
        try:
            p = subprocess.run([sys.executable, os.path.abspath(__file__), "--one", solver_name, path],
                               capture_output=True, text=True, timeout=timeout)
            line = [ln for ln in p.stdout.splitlines() if ln.startswith("{")]
            rec = json.loads(line[-1]) if line else {"file": name, "solver": solver_name,
                                                     "result": "ERROR", "detail": p.stderr[-300:]}
        except subprocess.TimeoutExpired:
            rec = {"file": name, "solver": solver_name, "result": "TIMEOUT", "seconds": timeout}
        rec["sha256"] = sha256(path)
        return rec

    log(f"{len(files)} formulas, solver {solver_name}, {par} in parallel, timeout {timeout}s; "
        f"{len(records)} already done")
    with ThreadPoolExecutor(max_workers=par) as ex:
        futs = {ex.submit(one, p): p for p in files}
        for fut in as_completed(futs):
            rec = fut.result()
            fresh = rec["file"] not in records
            records[rec["file"]] = rec
            save()
            if fresh:
                log(f"{rec['file']}: {rec['result']} ({rec.get('seconds', '-')}s)")
    n_unsat = sum(1 for r in records.values() if r["result"] == "UNSAT")
    log(f"SECOND SOLVER {solver_name}: {n_unsat} of {len(files)} formulas UNSAT")
    sys.exit(0 if n_unsat == len(files) else 1)


if __name__ == "__main__":
    main()
