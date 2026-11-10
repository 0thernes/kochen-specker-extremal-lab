"""scan_large_tokens.py - largest integer in the clauses of formula and proof files.

The build of verify/drup_check used before 10 November 2026, 02:00 read integers with scanf, so a token
of 2^31 or more could wrap around (docs/REVIEW.md, item 10). This script shows whether any file it was
used on contains such a token: for each file it reports the largest absolute value of an integer in a
clause line (the "p cnf" header and comment lines are skipped).

usage: python scripts/scan_large_tokens.py [--old-build-cubes] [files...]
  --old-build-cubes   the formula and proof files of the cubes that results/d5_cubes_certification.json
                      records as checked by the earlier build
Writes results/large_token_scan.json when --old-build-cubes is given.
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_BUILD = "e67f07b095c7781115462c57c1703ad894eeb2ae4f9e1ffa6874df847574755d"
NUM = re.compile(rb"\d+")


def largest(path):
    big = 0
    with open(path, "rb") as f:
        for line in f:
            if line[:1] in (b"p", b"c"):
                continue
            for m in NUM.findall(line):
                if len(m) >= len(str(big)):
                    v = int(m)
                    if v > big:
                        big = v
    return big


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    files = list(args)
    if "--old-build-cubes" in sys.argv:
        d = json.load(open(os.path.join(ROOT, "results", "d5_cubes_certification.json"), encoding="utf-8"))
        cubes = sorted(r["cube"] for r in d["records"] if r.get("checker_binary_sha256") == OLD_BUILD)
        for c in cubes:
            b = os.path.join(ROOT, "results", f"satcegar_box_5_1_k28_in01234_cube{c}_cuts")
            files += [b + ".cnf", b + ".drat"]
    out = []
    for p in files:
        v = largest(p)
        out.append({"file": os.path.basename(p), "bytes": os.path.getsize(p), "largest_integer": v})
        print(f"{os.path.basename(p)}: largest integer in a clause line {v}", flush=True)
    worst = max((r["largest_integer"] for r in out), default=0)
    print(f"{len(out)} files; largest integer overall {worst}; "
          f"{'far below' if worst < 2**31 else 'NOT below'} 2^31 = {2**31}")
    if "--old-build-cubes" in sys.argv:
        with open(os.path.join(ROOT, "results", "large_token_scan.json"), "w") as f:
            json.dump({"checker_build_sha256": OLD_BUILD, "files": out, "largest_integer": worst}, f, indent=1)
        print("wrote results/large_token_scan.json")


if __name__ == "__main__":
    main()
