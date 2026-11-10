"""ksmin.py - exact minimum Kochen-Specker sets inside a finite pool of rays.

Definitions (standard):
  * A pool is a finite set V of rays (1-dim subspaces) of a d-dimensional
    inner-product space.  G = (V, E) is its orthogonality graph.
  * A basis is a set of d mutually orthogonal rays (a d-clique of G).
  * A subset S of V is COLORABLE when there is f : S -> {0, 1} with
      (i)  f(u) + f(v) <= 1 for orthogonal u, v in S, and
      (ii) every basis contained in S has a ray with f = 1.
    Otherwise S is a Kochen-Specker (KS) set.
  * Colorability is inherited by subsets, so KS sets are an up-closed family.

Duality used (implicit hitting sets):
  * If C is a colorable subset of V, every KS set meets D = V \\ C.
    D is a "correction set".  A set S is KS  iff  it meets every correction
    set (take C = S).
  * Hence  min |KS set in V|  =  min hitting set of all correction sets.
    We collect correction sets lazily: take a minimum hitting set H of the
    ones known so far; if H is colorable, a smallest correction set disjoint
    from H is a new constraint; if H is not colorable, H is a minimum KS set.

Everything here is exact integer / SAT reasoning; no floating point decides
anything.
"""
from __future__ import annotations

import itertools
import sys
import time
from math import gcd

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from pysat.solvers import Cadical153


# ----------------------------------------------------------------------------
# pools of integer rays
# ----------------------------------------------------------------------------

def primitive(v):
    """Canonical representative of the ray through a non-zero integer vector."""
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


def pool_box(d, H):
    """All rays of Z^d with a representative of max-norm <= H."""
    rays = set()
    for v in itertools.product(range(-H, H + 1), repeat=d):
        if any(v):
            w = primitive(v)
            rays.add(w)
    return sorted(rays)


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


class Pool:
    """Orthogonality structure of a list of rays (any hashable labels).

    adj[i] is the set of rays orthogonal to ray i; bases is the list of all
    d-cliques (as sorted tuples of indices).
    """

    def __init__(self, rays, d, orth=None, verbose=True):
        self.rays = list(rays)
        self.d = d
        n = len(self.rays)
        orth = orth or (lambda u, v: dot(u, v) == 0)
        adj = [set() for _ in range(n)]
        for i in range(n):
            ri = self.rays[i]
            for j in range(i + 1, n):
                if orth(ri, self.rays[j]):
                    adj[i].add(j)
                    adj[j].add(i)
        self.adj = adj
        self.bases = self._cliques(d)
        if verbose:
            m = sum(len(a) for a in adj) // 2
            print(f"pool: {n} rays, {m} orthogonal pairs, {len(self.bases)} bases", flush=True)

    def _cliques(self, d):
        adj = self.adj
        out = []

        def extend(clique, cand):
            if len(clique) == d:
                out.append(tuple(clique))
                return
            need = d - len(clique)
            cand = sorted(cand)
            for idx, v in enumerate(cand):
                if len(cand) - idx < need:
                    break
                extend(clique + [v], [w for w in cand[idx + 1:] if w in adj[v]])

        for v in range(len(self.rays)):
            extend([v], [w for w in adj[v] if w > v])
        return out

    def restrict(self, keep, verbose=True):
        """Sub-pool induced on the index set `keep` (order preserved)."""
        keep = sorted(keep)
        sub = Pool.__new__(Pool)
        sub.rays = [self.rays[i] for i in keep]
        sub.d = self.d
        pos = {v: k for k, v in enumerate(keep)}
        sub.adj = [set(pos[w] for w in self.adj[v] if w in pos) for v in keep]
        sub.bases = [tuple(pos[x] for x in b) for b in self.bases if all(x in pos for x in b)]
        if verbose:
            m = sum(len(a) for a in sub.adj) // 2
            print(f"sub-pool: {len(keep)} rays, {m} orthogonal pairs, {len(sub.bases)} bases", flush=True)
        return sub

    def ks_core(self, verbose=True):
        """Iteratively delete rays that cannot belong to a critical KS set.

        A ray of a critical KS set S lies in a basis inside S, and (for the
        argument used here) has at least d neighbours in S: if all its
        neighbours inside S formed, together with it, exactly one basis, any
        coloring of S minus the ray would extend to it.
        Deleting such rays never removes a critical (hence a minimum) KS set.
        """
        alive = set(range(len(self.rays)))
        changed = True
        while changed:
            changed = False
            in_basis = set()
            for b in self.bases:
                if all(x in alive for x in b):
                    in_basis.update(b)
            for v in list(alive):
                deg = sum(1 for w in self.adj[v] if w in alive)
                if v not in in_basis or deg < self.d:
                    alive.discard(v)
                    changed = True
        if verbose:
            print(f"KS core: {len(alive)} of {len(self.rays)} rays", flush=True)
        return self.restrict(alive, verbose=verbose)


# ----------------------------------------------------------------------------
# colorability and correction sets
# ----------------------------------------------------------------------------

def coloring(pool, S):
    """Return a valid coloring (set of rays with value 1) of S, or None."""
    S = set(S)
    cnf = []
    for v in S:
        for w in pool.adj[v]:
            if w > v and w in S:
                cnf.append([-(v + 1), -(w + 1)])
    for b in pool.bases:
        if all(x in S for x in b):
            cnf.append([x + 1 for x in b])
    with Cadical153(bootstrap_with=cnf) as s:
        if not s.solve():
            return None
        model = s.get_model()
    ones = set()
    if model:
        pos = set(l for l in model if l > 0)
        ones = set(v for v in S if (v + 1) in pos)
    return ones


def is_ks(pool, S):
    return coloring(pool, S) is None


def min_correction_set(pool, forced_in=(), solver="g3"):
    """Smallest D disjoint from `forced_in` such that V \\ D is colorable.

    Variables: I_v (ray has value 1) and D_v (ray deleted).
    Returns (D, I).
    """
    n = len(pool.rays)
    I = lambda v: v + 1
    Dv = lambda v: n + v + 1
    w = WCNF()
    for v in range(n):
        for u in pool.adj[v]:
            if u > v:
                w.append([-I(v), -I(u)])
    for b in pool.bases:
        w.append([I(x) for x in b] + [Dv(x) for x in b])
    forced = set(forced_in)
    for v in range(n):
        if v in forced:
            w.append([-Dv(v)])
        else:
            w.append([-Dv(v)], weight=1)
    with RC2(w, solver=solver) as rc2:
        model = rc2.compute()
        if model is None:
            return None, None
        pos = set(l for l in model if l > 0)
    D = frozenset(v for v in range(n) if Dv(v) in pos)
    ones = frozenset(v for v in range(n) if I(v) in pos and v not in D)
    return D, ones


# ----------------------------------------------------------------------------
# symmetry of integer pools: signed coordinate permutations
# ----------------------------------------------------------------------------

def signed_perm_group(pool):
    """Permutations of ray indices induced by signed coordinate permutations
    that map the pool to itself (deduplicated)."""
    index = {r: i for i, r in enumerate(pool.rays)}
    d = pool.d
    perms = set()
    for p in itertools.permutations(range(d)):
        for signs in itertools.product((1, -1), repeat=d):
            img = []
            ok = True
            for r in pool.rays:
                w = primitive(tuple(signs[i] * r[p[i]] for i in range(d)))
                j = index.get(w)
                if j is None:
                    ok = False
                    break
                img.append(j)
            if ok:
                perms.add(tuple(img))
    return sorted(perms)


def orbit(sets_or_set, group):
    s = frozenset(sets_or_set)
    return {frozenset(g[v] for v in s) for g in group}


# ----------------------------------------------------------------------------
# minimum hitting set (CP-SAT) and the implicit-hitting-set loop
# ----------------------------------------------------------------------------

def min_hitting_set(n, sets, time_limit=None, hint=None, workers=8, lower=0):
    from ortools.sat.python import cp_model

    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{v}") for v in range(n)]
    for s in sets:
        m.AddBoolOr([x[v] for v in s])
    if lower:
        m.Add(sum(x) >= lower)
    m.Minimize(sum(x))
    if hint:
        for v in range(n):
            m.AddHint(x[v], 1 if v in hint else 0)
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = workers
    if time_limit:
        solver.parameters.max_time_in_seconds = time_limit
    st = solver.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, None, False
    H = frozenset(v for v in range(n) if solver.Value(x[v]))
    return H, int(round(solver.BestObjectiveBound())), st == cp_model.OPTIMAL


def minimum_ks(pool, group=None, verbose=True, max_iter=100000, workers=8, log=None):
    """Exact minimum KS set of the pool by implicit hitting sets.

    Returns (H, corrections) where H is a minimum KS set (frozenset of ray
    indices) or None when the pool is colorable, and corrections is the list
    of correction sets that certifies the lower bound.
    """
    n = len(pool.rays)
    group = group or [tuple(range(n))]
    t0 = time.time()
    D0, _ = min_correction_set(pool)
    if D0 is not None and len(D0) == 0:
        if verbose:
            print("pool is colorable: no KS set", flush=True)
        return None, []
    corrections = set()
    corrections |= orbit(D0, group)
    lower = 0
    H = None
    for it in range(1, max_iter + 1):
        H, bound, optimal = min_hitting_set(n, corrections, hint=H, workers=workers, lower=lower)
        if not optimal:
            raise RuntimeError("hitting set not solved to optimality")
        lower = max(lower, len(H))
        ones = coloring(pool, H)
        if ones is None:
            if verbose:
                print(f"[{time.time()-t0:8.1f}s] it {it}: |H|={len(H)} is a KS set; "
                      f"{len(corrections)} correction sets", flush=True)
            return H, sorted(corrections, key=lambda s: (len(s), sorted(s)))
        D, _ = min_correction_set(pool, forced_in=H)
        new = orbit(D, group) - corrections
        corrections |= new
        if verbose and (it <= 20 or it % 10 == 0):
            msg = (f"[{time.time()-t0:8.1f}s] it {it}: |H|={len(H)} colorable; new correction set "
                   f"size {len(D)} (+{len(new)} with symmetry, total {len(corrections)})")
            print(msg, flush=True)
            if log:
                log.write(msg + "\n")
                log.flush()
    raise RuntimeError("iteration limit reached")


def describe(pool, S):
    S = sorted(S)
    nb = sum(1 for b in pool.bases if all(x in S for x in b))
    ne = sum(1 for v in S for w in pool.adj[v] if w > v and w in S)
    return f"{len(S)} rays, {ne} orthogonal pairs, {nb} bases"


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    Hmax = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    full = Pool(pool_box(d, Hmax), d)
    core = full.ks_core()
    grp = signed_perm_group(core)
    print(f"symmetry group acting on core: {len(grp)} permutations", flush=True)
    H, corr = minimum_ks(core, grp)
    if H is not None:
        print("minimum KS set:", describe(core, H))
        for v in sorted(H):
            print("  ", core.rays[v])
        sizes = {}
        for c in corr:
            sizes[len(c)] = sizes.get(len(c), 0) + 1
        print("correction-set sizes:", dict(sorted(sizes.items())))
