"""fill_cube_verdict.py - write the verdict of the proof checks of the 81 cubes into the documents.

Reads results/d5_cubes_certification.json (written by scripts/check_cubes.py). If and only if all 81
cubes are VERIFIED, it replaces the placeholders CUBELEMMAS and CUBEVERDICT that the documents carry
while the checks run, and removes the explanatory note about placeholders from docs/INDEX.md.
Otherwise it changes nothing and lists the cubes that are not verified.

usage: python scripts/fill_cube_verdict.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def fmt(n):
    return f"{n:,}".replace(",", " ")


def main():
    dry = "--dry-run" in sys.argv
    d = json.load(open(os.path.join(ROOT, "results", "d5_cubes_certification.json"), encoding="utf-8"))
    recs = d.get("records", [])
    ok = [r for r in recs if r.get("status") == "VERIFIED"]
    if len(ok) != 81 or d.get("cubes") != 81:
        bad = sorted(set(f"{a}{b}{c}{e}" for a in "012" for b in "012" for c in "012" for e in "012")
                     - {r["cube"] for r in ok})
        print(f"{len(ok)} of 81 cubes VERIFIED; not verified yet: {' '.join(bad)}")
        sys.exit(1)
    lem = [r["lemmas"] for r in ok]
    total, lo, hi = sum(lem), min(lem), max(lem)
    builds = sorted({r.get("checker_binary_sha256", "?")[:12] for r in ok})
    n_old = sum(1 for r in ok if r.get("checker_binary_sha256", "").startswith("e67f07b0"))
    lemmas_cell = f"{fmt(lo)} to {fmt(hi)} per cube, {fmt(total)} in total"
    print(f"all 81 VERIFIED; lemmas {lemmas_cell}; checker builds {builds}; {n_old} by the earlier build")
    verdict = (f"VERIFIED (all 81; {n_old} of them with the earlier build of the checker, see section C.2)"
               if n_old else "VERIFIED (all 81)")
    repl = {
        "results/RESULTS.md": [("| CUBELEMMAS | CUBEVERDICT |", f"| {lemmas_cell} | {verdict} |"),
                               ("81 Glucose proofs: CUBEVERDICT", "81 Glucose proofs, all VERIFIED")],
        "README.md": [("81 Glucose proofs: CUBEVERDICT", "81 Glucose proofs, all VERIFIED")],
        "paper/ks-minimum.md": [("81 Glucose proofs: CUBEVERDICT",
                                 f"81 Glucose proofs, all VERIFIED, {fmt(total)} lemmas in total")],
        "docs/REPORT.md": [("| CUBELEMMAS | CUBEVERDICT |", f"| {lemmas_cell} | {verdict.replace('section C.2', 'register, section C.2')} |")],
        "docs/INDEX.md": [("lemmas checked: CUBELEMMAS | CUBEVERDICT |",
                           f"lemmas checked: {lemmas_cell} | {verdict.replace('section C.2', 'register, section C.2')} |"),
                          ("Cells that hold one of the words CUBELEMMAS, CUBEVERDICT repeat the cell of the same name in\n"
                           "sections C and D of the register.\n\n", "")],
        "docs/REVIEW.md": [("(outcome:\n    CUBEVERDICT)", "(outcome:\n    all 63 VERIFIED)")],
    }
    for rel, pairs in repl.items():
        p = os.path.join(ROOT, rel)
        s = open(p, encoding="utf-8").read()
        for a, b in pairs:
            if a not in s:
                print(f"  {rel}: placeholder text not found (already filled?): {a[:50]!r}")
                continue
            s = s.replace(a, b)
        if "CUBELEMMAS" in s or "CUBEVERDICT" in s:
            print(f"  {rel}: a placeholder is left after replacement; check by hand")
        if not dry:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(s)
        print(("would write " if dry else "wrote ") + rel)


if __name__ == "__main__":
    main()
