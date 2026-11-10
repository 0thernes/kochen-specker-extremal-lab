"""prove_cnf.py - prove an existing CNF formula unsatisfiable with a proof-producing SAT solver and
write the proof as DRUP text, without holding the proof in memory.

usage: python -u scripts/prove_cnf.py <solver> <formula.cnf> <proof.drat> [--check]

  solver   a PySAT solver name with proof support: g4 (Glucose 4.1), cadical153, cadical195, ...
  --check  afterwards run verify/drup_check on (formula, proof) and print its verdict

The formula is NOT built here: it is a file written by src/ks_cnf.py (which re-verifies every cut
and encodes the candidate problem).  This script only replaces the solver, for formulas on which
Glucose is too slow or runs out of memory.  CaDiCaL writes its proof in the binary DRAT format; it is
converted to text line by line.  Every added clause of a CaDiCaL proof is checked by verify/drup_check
as a reverse-unit-propagation step, like any other lemma.

Exit status: 0 unsatisfiable (and, with --check, proof VERIFIED); 3 satisfiable; 1 otherwise.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_text_proof(inner, path):
    """Copy a text proof (Glucose and relatives) from PySAT's temporary file."""
    n_add = n_del = 0
    inner.prfile.seek(0)
    with open(path, "wb") as out:
        for line in inner.prfile:
            line = line.rstrip()
            if not line:
                continue
            if line.startswith(b"d"):
                n_del += 1
            else:
                n_add += 1
            out.write(line + b"\n")
    return n_add, n_del


def write_binary_proof(inner, path):
    """Convert a binary DRAT proof (CaDiCaL) from PySAT's temporary file to DRUP text.

    Record: one byte 'a' (0x61, clause added) or 'd' (0x64, clause deleted); then each literal l as
    the number 2*|l| + (1 if l < 0 else 0) in 7-bit groups, least significant first, high bit set on
    all but the last group; then a zero byte."""
    n_add = n_del = 0
    inner.prfile.seek(0)
    with open(path, "w") as out:
        new = True
        lits = []
        lit = shift = 0
        deleting = False
        while True:
            chunk = inner.prfile.read(1 << 20)
            if not chunk:
                break
            for byte in chunk:
                if new:
                    if byte == 100:
                        deleting = True
                    elif byte == 97:
                        deleting = False
                    else:
                        raise ValueError("binary proof: a record must start with 'a' or 'd'")
                    new = False
                elif byte:
                    lit |= (byte & 0x7F) << shift
                    shift += 7
                    if byte < 128:
                        lits.append(str(lit >> 1) if lit % 2 == 0 else "-" + str(lit >> 1))
                        lit = shift = 0
                else:
                    if shift:
                        raise ValueError("binary proof: literal cut off by the end of a clause")
                    out.write(("d " if deleting else "") + " ".join(lits + ["0"]) + "\n")
                    if deleting:
                        n_del += 1
                    else:
                        n_add += 1
                    lits = []
                    new = True
        if not new:
            raise ValueError("binary proof: file ends inside a record")
    return n_add, n_del


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    solver_name, cnf_path, proof_path = args
    from pysat.formula import CNF
    from pysat import solvers as ps

    t0 = time.time()
    if os.path.exists(proof_path):
        os.remove(proof_path)                       # never leave an older proof next to a new run
    cnf = CNF(from_file=cnf_path)
    print(f"{os.path.basename(cnf_path)}: {cnf.nv} variables, {len(cnf.clauses)} clauses", flush=True)
    s = ps.Solver(name=solver_name, bootstrap_with=cnf.clauses, with_proof=True)
    r = s.solve()
    print(f"{solver_name}: {'SAT' if r else 'UNSAT'} in {time.time()-t0:.1f}s", flush=True)
    if r:
        # os._exit: on Windows the destructor of a proof-logging solver object can end the process
        # with another status after a satisfiable answer, which would hide the documented status 3
        sys.stdout.flush()
        os._exit(3)
    inner = s.solver
    ps.pysolvers.flushpr(inner.prfp)
    t1 = time.time()
    binary = solver_name.startswith("cadical")
    n_add, n_del = (write_binary_proof if binary else write_text_proof)(inner, proof_path)
    print(f"proof: {n_add} added clauses, {n_del} deletions, {os.path.getsize(proof_path)} bytes of text "
          f"-> {os.path.basename(proof_path)} ({time.time()-t1:.1f}s)", flush=True)
    s.delete()
    if not check:
        return
    exe = os.path.join(ROOT, "verify", "drup_check.exe" if os.name == "nt" else "drup_check")
    t2 = time.time()
    p = subprocess.run([exe, cnf_path, proof_path], capture_output=True, text=True)
    print(p.stdout.strip(), flush=True)
    print(f"drup_check exit={p.returncode} ({time.time()-t2:.1f}s)", flush=True)
    sys.exit(0 if (p.returncode == 0 and "s VERIFIED" in p.stdout) else 1)


if __name__ == "__main__":
    main()
