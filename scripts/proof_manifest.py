"""proof_manifest.py - list every formula (.cnf) and proof (.drat) in results/
with its size and SHA-256, so that the large files, which are not kept in the
repository, can be identified when they are regenerated or requested.
Writes results/proof_manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    out = []
    total = 0
    for name in sorted(os.listdir(RES)):
        if name.endswith(".cnf") or name.endswith(".drat"):
            p = os.path.join(RES, name)
            size = os.path.getsize(p)
            total += size
            out.append({"file": name, "bytes": size, "sha256": sha256(p)})
    with open(os.path.join(RES, "proof_manifest.json"), "w") as f:
        json.dump({"files": out, "total_bytes": total}, f, indent=1)
    print(f"{len(out)} files, {total/1e9:.2f} GB; wrote results/proof_manifest.json")


if __name__ == "__main__":
    main()
