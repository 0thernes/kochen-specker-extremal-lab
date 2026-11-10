"""pools.py - finite pools of rays with exact arithmetic, and their symmetries.

Integer pools use tuples of Python ints; complex pools use tuples of Gaussian
integers written as (re, im) pairs.  Orthogonality is decided exactly.
"""
from __future__ import annotations

import itertools
from math import gcd

from ksengine import Pool, Symmetry


# ----------------------------------------------------------------------------
# integer rays
# ----------------------------------------------------------------------------

def primitive(v):
    g = 0
    for x in v:
        g = gcd(g, abs(x))
    if g == 0:
        raise ValueError("zero vector")
    w = tuple(x // g for x in v)
    for x in w:
        if x != 0:
            if x < 0:
                w = tuple(-y for y in w)
            break
    return w


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def int_orth(u, v):
    return dot(u, v) == 0


def box_rays(d, H):
    """All rays of Z^d having a representative with max-norm at most H."""
    rays = set()
    for v in itertools.product(range(-H, H + 1), repeat=d):
        if any(v):
            rays.add(primitive(v))
    return sorted(rays)


def box_pool(d, H, log=print):
    return Pool.from_vectors(box_rays(d, H), d, int_orth, name=f"box(d={d},H={H})", log=log)


def linear_perm(rays, fn, canon):
    """Permutation of ray indices induced by the map fn, or None if the image
    of some ray is outside the pool."""
    index = {r: i for i, r in enumerate(rays)}
    img = []
    for r in rays:
        j = index.get(canon(fn(r)))
        if j is None:
            return None
        img.append(j)
    return tuple(img)


def signed_perm_symmetry(pool):
    """Signed coordinate permutations (generators) acting on an integer pool."""
    d = pool.d
    gens = []

    def swap(i, j):
        def f(r):
            r = list(r)
            r[i], r[j] = r[j], r[i]
            return tuple(r)
        return f

    def flip(i):
        def f(r):
            r = list(r)
            r[i] = -r[i]
            return tuple(r)
        return f

    for i in range(d - 1):
        gens.append(linear_perm(pool.rays, swap(i, i + 1), primitive))
    for i in range(d):
        gens.append(linear_perm(pool.rays, flip(i), primitive))
    gens = [g for g in gens if g is not None]
    return Symmetry(gens, pool.n)


# ----------------------------------------------------------------------------
# E8: the 120 rays through the 240 roots, coordinates scaled to integers
# ----------------------------------------------------------------------------

def e8_rays():
    rays = set()
    for i, j in itertools.combinations(range(8), 2):
        for s in (1, -1):
            v = [0] * 8
            v[i] = 1
            v[j] = s
            rays.add(primitive(v))
    for signs in itertools.product((1, -1), repeat=8):
        if sum(1 for s in signs if s < 0) % 2 == 0:
            rays.add(primitive(signs))
    return sorted(rays)


def e8_pool(log=print):
    return Pool.from_vectors(e8_rays(), 8, int_orth, name="E8(120 rays)", log=log)


def e8_symmetry(pool):
    """Reflections in the roots generate the Weyl group W(E8)."""
    gens = []
    roots = []
    for r in pool.rays:
        # roots of the first kind have norm 2, of the second kind norm 8 here
        roots.append(r)
    for root in roots[:]:
        nn = dot(root, root)

        def refl(v, root=root, nn=nn):
            # v - 2 (v.root)/(root.root) root, scaled by nn to stay integral
            k = 2 * dot(v, root)
            return tuple(nn * a - k * b for a, b in zip(v, root))

        g = linear_perm(pool.rays, refl, primitive)
        if g is not None:
            gens.append(g)
    return Symmetry(gens, pool.n)


# ----------------------------------------------------------------------------
# n-qubit stabilizer states with Gaussian-integer amplitudes
# ----------------------------------------------------------------------------

I_POW = [(1, 0), (0, 1), (-1, 0), (0, -1)]


def gmul(a, b):
    return (a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0])


def gconj(a):
    return (a[0], -a[1])


def gadd(a, b):
    return (a[0] + b[0], a[1] + b[1])


def herm(u, v):
    s = (0, 0)
    for a, b in zip(u, v):
        s = gadd(s, gmul(gconj(a), b))
    return s


def herm_orth(u, v):
    return herm(u, v) == (0, 0)


def gprimitive(v):
    """Canonical representative of a complex ray with Gaussian-integer entries:
    divide by the integer gcd of all real and imaginary parts, then multiply
    by a power of i so that the first non-zero entry is real positive or, if
    that is impossible, lies in the first quadrant with positive real part."""
    g = 0
    for a in v:
        g = gcd(g, gcd(abs(a[0]), abs(a[1])))
    if g == 0:
        raise ValueError("zero vector")
    v = tuple((a[0] // g, a[1] // g) for a in v)
    best = None
    for k in range(4):
        w = tuple(gmul(I_POW[k], a) for a in v)
        first = next(a for a in w if a != (0, 0))
        if first[0] > 0 and first[1] >= 0:
            best = w
            break
    return best


def stabilizer_rays(n):
    """All n-qubit stabilizer states, by closing |0...0> under H, S, CNOT.

    Amplitudes are kept as unnormalised Gaussian integers; rays are
    canonicalised with gprimitive (which also strips common factors such as
    1+i by reducing through the integer gcd after an exact division test)."""
    N = 1 << n

    def canon(v):
        # strip powers of (1+i): if every entry is divisible by 1+i, divide
        while True:
            if all((a[0] + a[1]) % 2 == 0 for a in v):
                # a / (1+i) = a (1-i) / 2
                v = tuple(((a[0] + a[1]) // 2, (a[1] - a[0]) // 2) for a in v)
            else:
                break
        return gprimitive(v)

    def apply_h(v, q):
        w = list(v)
        bit = 1 << q
        for x in range(N):
            if not x & bit:
                a, b = v[x], v[x | bit]
                w[x] = gadd(a, b)
                w[x | bit] = (a[0] - b[0], a[1] - b[1])
        return tuple(w)

    def apply_s(v, q):
        bit = 1 << q
        return tuple(gmul((0, 1), a) if x & bit else a for x, a in enumerate(v))

    def apply_cnot(v, c, t):
        cb, tb = 1 << c, 1 << t
        w = list(v)
        for x in range(N):
            if x & cb:
                w[x] = v[x ^ tb]
        return tuple(w)

    ops = []
    for q in range(n):
        ops.append(lambda v, q=q: apply_h(v, q))
        ops.append(lambda v, q=q: apply_s(v, q))
    for c in range(n):
        for t in range(n):
            if c != t:
                ops.append(lambda v, c=c, t=t: apply_cnot(v, c, t))

    start = canon(tuple((1, 0) if x == 0 else (0, 0) for x in range(N)))
    seen = {start}
    frontier = [start]
    while frontier:
        nxt = []
        for v in frontier:
            for op in ops:
                w = canon(op(v))
                if w not in seen:
                    seen.add(w)
                    nxt.append(w)
        frontier = nxt
    return sorted(seen), ops, canon


def stabilizer_pool(n, log=print, real_only=False):
    rays, ops, canon = stabilizer_rays(n)
    if real_only:
        rays = [r for r in rays if all(a[1] == 0 for a in r)]
    pool = Pool.from_vectors(rays, 1 << n, herm_orth,
                             name=f"stabilizer(n={n}{',real' if real_only else ''})", log=log)
    gens = [linear_perm(pool.rays, op, canon) for op in ops]
    sym = Symmetry([g for g in gens if g is not None], pool.n)
    return pool, sym
