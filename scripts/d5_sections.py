"""d5_sections.py - structure of the two 29-ray KS sets of B(5, 1) recorded in results/ks_sets.json.

For each set and each coordinate j, the section x_j = 0 is the subset of rays whose j-th entry is 0.
It lies in a four-dimensional coordinate hyperplane; its bases are its sets of four mutually
orthogonal rays.  The script decides by exhaustive enumeration of all 0/1 assignments whether the
section is a Kochen-Specker set of that four-dimensional space, and writes results/d5_sections.json.

This backs the remark of Section 4.4 of the paper: the four-axis set consists of an 18-ray KS set in a
coordinate hyperplane plus 11 further rays (the shape of the recursive construction of Cabello,
Estebaranz and Garcia-Alcaine), while no coordinate hyperplane section of the three-axis set is a KS
set.

usage: python scripts/d5_sections.py
"""
from __future__ import annotations

import itertools
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def section_report(rays, j):
    sec = [r for r in rays if r[j] == 0]
    n = len(sec)
    adj = [0] * n
    for a in range(n):
        for b in range(n):
            if a != b and dot(sec[a], sec[b]) == 0:
                adj[a] |= 1 << b
    bases = [c for c in itertools.combinations(range(n), 4)
             if all(adj[x] >> y & 1 for x, y in itertools.combinations(c, 2))]
    bmask = [sum(1 << x for x in c) for c in bases]
    colourings = None
    if n <= 22:
        colourings = 0
        for m in range(1 << n):
            ok = True
            x = m
            while x:
                low = x & -x
                if adj[low.bit_length() - 1] & m:
                    ok = False
                    break
                x ^= low
            if ok and all(b & m for b in bmask):
                colourings += 1
    return {"coordinate": j, "rays": n, "bases": len(bases),
            "orthogonal_pairs": sum(bin(a).count("1") for a in adj) // 2,
            "colourings": colourings,
            "is_ks_set": (colourings == 0) if colourings is not None else None}


def main():
    sets = json.load(open(os.path.join(ROOT, "results", "ks_sets.json")))
    out = []
    for e in sets:
        if e["d"] != 5:
            continue
        rays = [tuple(r) for r in e["rays"]]
        secs = [section_report(rays, j) for j in range(5)]
        rec = {"name": e["name"], "size": e["size"], "orthogonal_pairs": e["orthogonal_pairs"],
               "axes": e.get("axes"), "sections": secs,
               "ks_sections": [s["coordinate"] for s in secs if s["is_ks_set"]]}
        out.append(rec)
        print(f"{e['name']}: {e['size']} rays, {e['orthogonal_pairs']} orthogonal pairs, axes {e.get('axes')}")
        for s in secs:
            print(f"   section x{s['coordinate']} = 0: {s['rays']} rays, {s['bases']} bases, "
                  f"{s['colourings']} colourings -> {'KS set' if s['is_ks_set'] else 'colourable'}")
    with open(os.path.join(ROOT, "results", "d5_sections.json"), "w") as f:
        json.dump(out, f, indent=1)
    print("wrote results/d5_sections.json")


if __name__ == "__main__":
    main()
