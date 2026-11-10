"""pools3d.py - large pools of integer rays in R^3 (max-norm at most H), built
with exact integer arithmetic (numpy int64 only for enumeration; all values
stay far below 2^53).

build_box3(H) returns the KS core as a ksengine.Pool: rays that survive the
iterated deletion of rays lying in no orthogonal triple or having fewer than
three orthogonal partners.
"""
from __future__ import annotations

import time
from math import gcd

import numpy as np

from ksengine import Pool, Symmetry, mask


def primitive3(a, b, c):
    g = gcd(gcd(abs(a), abs(b)), abs(c))
    a, b, c = a // g, b // g, c // g
    if a < 0 or (a == 0 and (b < 0 or (b == 0 and c < 0))):
        a, b, c = -a, -b, -c
    return (a, b, c)


def box3_rays(H):
    rays = []
    for a in range(0, H + 1):
        for b in range(-H, H + 1):
            for c in range(-H, H + 1):
                if a == 0 and (b < 0 or (b == 0 and c <= 0)):
                    continue
                if gcd(gcd(a, abs(b)), abs(c)) == 1:
                    rays.append((a, b, c))
    return rays


def box3_structure(H, log=print):
    """Rays, orthogonality lists and orthogonal triples of the height-H box."""
    t0 = time.time()
    rays = box3_rays(H)
    n = len(rays)
    index = {r: i for i, r in enumerate(rays)}
    R = np.array(rays, dtype=np.int64)
    nbrs = [None] * n
    # for each ray, orthogonal partners with larger index, by one matrix product per block
    block = 2048
    m = 0
    for s in range(0, n, block):
        P = R[s:s + block] @ R.T          # dot products, exact in int64
        for k in range(P.shape[0]):
            i = s + k
            js = np.nonzero(P[k] == 0)[0]
            nbrs[i] = js
            m += len(js)
    m //= 2
    log(f"box3(H={H}): {n} rays, {m} orthogonal pairs ({time.time()-t0:.1f}s)")
    tri = set()
    for i in range(n):
        a = rays[i]
        for j in nbrs[i]:
            if j <= i:
                continue
            b = rays[j]
            w = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
            k = index.get(primitive3(*w))
            if k is not None:
                tri.add(tuple(sorted((i, int(j), k))))
    tri = sorted(tri)
    log(f"box3(H={H}): {len(tri)} orthogonal triples ({time.time()-t0:.1f}s)")
    return rays, nbrs, tri


def build_box3(H, log=print):
    rays, nbrs, tri = box3_structure(H, log=log)
    n = len(rays)
    alive = np.ones(n, dtype=bool)
    tri_arr = np.array(tri, dtype=np.int64) if tri else np.zeros((0, 3), dtype=np.int64)
    while True:
        ok_tri = alive[tri_arr[:, 0]] & alive[tri_arr[:, 1]] & alive[tri_arr[:, 2]]
        in_tri = np.zeros(n, dtype=bool)
        for col in range(3):
            in_tri[tri_arr[ok_tri, col]] = True
        deg = np.array([int(alive[nbrs[i]].sum()) if alive[i] else 0 for i in range(n)])
        new = alive & in_tri & (deg >= 3)
        if (new == alive).all():
            break
        alive = new
    keep = [i for i in range(n) if alive[i]]
    pos = {v: k for k, v in enumerate(keep)}
    log(f"box3(H={H}): KS core keeps {len(keep)} of {n} rays")
    adj = [0] * len(keep)
    for v in keep:
        mk = 0
        for w in nbrs[v]:
            w = int(w)
            if w in pos:
                mk |= 1 << pos[w]
        adj[pos[v]] = mk
    bases = [tuple(pos[x] for x in t) for t in tri if all(x in pos for x in t)]
    core_rays = [rays[v] for v in keep]
    pool = Pool(core_rays, 3, adj, bases=bases, name=f"box3(H={H})/core", log=log)
    return pool


def cube_symmetry(pool):
    index = {r: i for i, r in enumerate(pool.rays)}
    gens = []

    def perm_of(fn):
        img = []
        for r in pool.rays:
            j = index.get(primitive3(*fn(r)))
            if j is None:
                return None
            img.append(j)
        return tuple(img)

    for fn in (lambda r: (r[1], r[0], r[2]), lambda r: (r[0], r[2], r[1]),
               lambda r: (-r[0], r[1], r[2]), lambda r: (r[0], -r[1], r[2]),
               lambda r: (r[0], r[1], -r[2])):
        g = perm_of(fn)
        if g is not None:
            gens.append(g)
    return Symmetry(gens, pool.n)


if __name__ == "__main__":
    import sys
    for H in map(int, sys.argv[1:]):
        t = time.time()
        p = build_box3(H)
        print(f"H={H}: core {p.n} rays, {len(p.bases)} triples, total {time.time()-t:.1f}s", flush=True)
