"""ksengine.py - exact minimum Kochen-Specker (KS) sets inside finite pools of rays.

Definitions (standard, rank-1):
  * A pool is a finite set V of rays of a d-dimensional inner-product space,
    G = (V, E) its orthogonality graph, a BASIS a set of d mutually orthogonal
    rays of V (a d-clique of G).
  * S, a subset of V, is COLORABLE when there is f : S -> {0, 1} such that
      (i)  no two orthogonal rays of S both have value 1, and
      (ii) every basis contained in S has a ray of value 1.
    Otherwise S is a KS set.  Subsets of colorable sets are colorable.

Duality (implicit hitting sets):
  * If C is colorable then every KS set meets D = V \\ C ("correction set").
    Conversely a set that meets every correction set is KS.
  * So  min |KS set|  =  minimum hitting set of the family of correction sets.
    The family is generated lazily: a minimum hitting set H of the correction
    sets found so far is a lower bound; if H is colorable we extract new
    correction sets disjoint from H, otherwise H is a minimum KS set.

All decisions are exact (integer arithmetic and SAT); nothing is numerical.
"""
from __future__ import annotations

import random
import time

from pysat.examples.lbx import LBX
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF
from pysat.solvers import Solver


def popcount(x: int) -> int:
    return bin(x).count("1")


def bits(x: int):
    while x:
        low = x & -x
        yield low.bit_length() - 1
        x ^= low


def mask(it) -> int:
    m = 0
    for v in it:
        m |= 1 << v
    return m


class Pool:
    """Orthogonality structure: adj[i] is a bitmask of rays orthogonal to ray i."""

    def __init__(self, rays, d, adj, bases=None, name="pool", log=print):
        self.rays = list(rays)
        self.d = d
        self.n = len(self.rays)
        self.adj = list(adj)
        self.name = name
        self.bases = list(bases) if bases is not None else self.find_bases()
        self._solver = None
        m = sum(popcount(a) for a in self.adj) // 2
        log(f"{name}: {self.n} rays, {m} orthogonal pairs, {len(self.bases)} bases (d={d})")

    @classmethod
    def from_vectors(cls, rays, d, orth, name="pool", log=print):
        rays = list(rays)
        n = len(rays)
        adj = [0] * n
        for i in range(n):
            ri = rays[i]
            for j in range(i + 1, n):
                if orth(ri, rays[j]):
                    adj[i] |= 1 << j
                    adj[j] |= 1 << i
        return cls(rays, d, adj, name=name, log=log)

    def find_bases(self):
        adj, d = self.adj, self.d
        out = []

        def rec(clique, cand, need):
            if need == 0:
                out.append(tuple(sorted(clique)))
                return
            while cand:
                if popcount(cand) < need:
                    return
                v = cand.bit_length() - 1
                cand ^= 1 << v
                rec(clique + [v], cand & adj[v], need - 1)

        for v in range(self.n):
            rec([v], adj[v] & ((1 << v) - 1), d - 1)
        out.sort()
        return out

    def restrict(self, keep, name=None, log=print):
        keep = sorted(keep)
        pos = {v: k for k, v in enumerate(keep)}
        km = mask(keep)
        adj = [mask(pos[w] for w in bits(self.adj[v] & km)) for v in keep]
        bases = [tuple(pos[x] for x in b) for b in self.bases if all(x in pos for x in b)]
        sub = Pool([self.rays[v] for v in keep], self.d, adj, bases=bases,
                   name=name or (self.name + "/sub"), log=log)
        sub.parent_index = keep
        return sub

    def ks_core(self, log=print):
        """Delete, repeatedly, rays that lie in no basis or have fewer than d
        neighbours.  Such a ray is in no critical KS set, so minimum KS sets
        are unaffected.  (Proof: let S be a critical KS set and v in S.  A
        coloring of S minus v exists.  If v lies in no basis of S, give v the
        value 0.  If all neighbours of v in S lie in one basis b with v, give v
        the value 1 when the rest of b is all 0 and the value 0 otherwise.
        Either way S would be colorable.)"""
        alive = (1 << self.n) - 1
        while True:
            in_basis = 0
            for b in self.bases:
                bm = mask(b)
                if bm & alive == bm:
                    in_basis |= bm
            new = 0
            for v in bits(alive):
                if (in_basis >> v) & 1 and popcount(self.adj[v] & alive) >= self.d:
                    new |= 1 << v
            if new == alive:
                break
            alive = new
        log(f"{self.name}: KS core keeps {popcount(alive)} of {self.n} rays")
        if popcount(alive) == self.n:
            self.parent_index = list(range(self.n))
            return self
        return self.restrict(list(bits(alive)), name=self.name + "/core", log=log)

    # ---- SAT model: c_v (value of ray v) = v+1, a_v (ray v present) = n+v+1 ----
    def cvar(self, v):
        return v + 1

    def avar(self, v):
        return self.n + v + 1

    def hard_clauses(self):
        cl = []
        for v in range(self.n):
            for w in bits(self.adj[v] >> (v + 1) << (v + 1)):
                cl.append([-self.cvar(v), -self.cvar(w)])
        for b in self.bases:
            cl.append([self.cvar(x) for x in b] + [-self.avar(x) for x in b])
        return cl

    def solver(self):
        if self._solver is None:
            self._solver = Solver(name="g4", bootstrap_with=self.hard_clauses())
        return self._solver

    def coloring(self, S):
        """Set of value-1 rays of a valid coloring of S, or None if S is KS."""
        s = self.solver()
        S = list(S)
        if s.solve(assumptions=[self.avar(v) for v in S]):
            model = s.get_model()
            inS = set(S)
            return frozenset(v for v in inS if model[self.cvar(v) - 1] > 0)
        return None

    def is_ks(self, S):
        return self.coloring(S) is None

    def ks_core_of(self, S):
        """A KS subset of the KS set S taken from the solver's final conflict."""
        s = self.solver()
        S = list(S)
        if s.solve(assumptions=[self.avar(v) for v in S]):
            return None
        core = s.get_core() or []
        return frozenset(l - self.n - 1 for l in core)

    def shrink(self, S, rng=None, keep_first=()):
        """Deletion-based reduction of a KS set S to a critical KS set.

        Rays in keep_first are tried for deletion last."""
        rng = rng or random.Random(0)
        S = set(self.ks_core_of(S))
        order = [v for v in S if v not in keep_first]
        rng.shuffle(order)
        tail = [v for v in S if v in keep_first]
        rng.shuffle(tail)
        for v in order + tail:
            if v not in S:
                continue
            T = S - {v}
            core = self.ks_core_of(T)
            if core is not None:
                S = set(core)
        return frozenset(S)

    def is_critical(self, S):
        S = set(S)
        if not self.is_ks(S):
            return False
        return all(not self.is_ks(S - {v}) for v in S)

    # ---- correction sets ----
    def wcnf(self, forced_in=()):
        w = WCNF()
        for c in self.hard_clauses():
            w.append(c)
        forced = set(forced_in)
        for v in range(self.n):
            if v in forced:
                w.append([self.avar(v)])
            else:
                w.append([self.avar(v)], weight=1)
        return w

    def minimal_correction_set(self, forced_in=(), rng=None):
        """An inclusion-minimal correction set disjoint from forced_in
        (None if forced_in is itself KS)."""
        w = self.wcnf(forced_in)
        if rng is not None:
            idx = list(range(len(w.soft)))
            rng.shuffle(idx)
            w.soft = [w.soft[i] for i in idx]
            w.wght = [w.wght[i] for i in idx]
        with LBX(w, use_cld=True, solver_name="g4") as lbx:
            mcs = lbx.compute()
            if mcs is None:
                return None
            D = frozenset(w.soft[i - 1][0] - self.n - 1 for i in mcs)
        return D

    def minimum_correction_set(self, forced_in=()):
        """A minimum-cardinality correction set disjoint from forced_in."""
        w = self.wcnf(forced_in)
        with RC2(w, solver="g4", adapt=True, exhaust=True, minz=True) as rc2:
            model = rc2.compute()
            if model is None:
                return None
            D = frozenset(v for v in range(self.n) if model[self.avar(v) - 1] < 0)
        return D

    def check_correction_set(self, D):
        """True iff V minus D is colorable."""
        return self.coloring([v for v in range(self.n) if v not in D]) is not None

    def describe(self, S):
        S = set(S)
        sm = mask(S)
        nb = sum(1 for b in self.bases if all(x in S for x in b))
        ne = sum(popcount(self.adj[v] & sm) for v in S) // 2
        return f"{len(S)} rays, {ne} orthogonal pairs, {nb} bases"


# ----------------------------------------------------------------------------
# symmetry
# ----------------------------------------------------------------------------

class Symmetry:
    """A set of generator permutations of the ray indices of a pool."""

    def __init__(self, gens, n):
        ident = tuple(range(n))
        self.n = n
        self.gens = [g for g in dict.fromkeys(tuple(g) for g in gens) if g != ident]

    def orbit(self, S, cap=20000):
        """Orbit of a set under the generated group (breadth first, capped)."""
        S = frozenset(S)
        seen = {S}
        frontier = [S]
        while frontier and len(seen) < cap:
            nxt = []
            for T in frontier:
                for g in self.gens:
                    U = frozenset(g[v] for v in T)
                    if U not in seen:
                        seen.add(U)
                        nxt.append(U)
                        if len(seen) >= cap:
                            break
                if len(seen) >= cap:
                    break
            frontier = nxt
        return seen

    def canonical(self, S, cap=200000):
        return min(tuple(sorted(T)) for T in self.orbit(S, cap=cap))


# ----------------------------------------------------------------------------
# implicit hitting set search
# ----------------------------------------------------------------------------

class HittingSets:
    """Minimum hitting set.  backend 'rc2' is incremental core-guided MaxSAT
    (good when the sets are small); backend 'cpsat' rebuilds a CP-SAT model
    each time (good when there are many overlapping sets)."""

    def __init__(self, n, backend="cpsat", workers=8):
        self.n = n
        self.sets = []
        self.backend = backend
        self.workers = workers
        self.last = None
        self.lower = 0
        if backend == "rc2":
            w = WCNF()
            for v in range(n):
                w.append([-(v + 1)], weight=1)
            self.rc2 = RC2(w, solver="g4", adapt=True, exhaust=True, minz=True)

    def add(self, D):
        self.sets.append(frozenset(D))
        if self.backend == "rc2":
            self.rc2.add_clause([v + 1 for v in D])

    def minimum(self, upper=None):
        """A minimum hitting set.  If `upper` is given and every hitting set has
        at least `upper` elements, returns None (the caller's incumbent is
        optimal)."""
        if self.backend == "rc2":
            model = self.rc2.compute()
            if model is None:
                return None
            H = frozenset(v for v in range(self.n) if model[v] > 0)
            self.lower = max(self.lower, len(H))
            return H
        from ortools.sat.python import cp_model

        m = cp_model.CpModel()
        x = [m.NewBoolVar(f"x{v}") for v in range(self.n)]
        for s in self.sets:
            m.AddBoolOr([x[v] for v in s])
        total = sum(x)
        if self.lower:
            m.Add(total >= self.lower)
        if upper is not None:
            m.Add(total <= upper - 1)
        m.Minimize(total)
        if self.last is not None:
            for v in range(self.n):
                m.AddHint(x[v], 1 if v in self.last else 0)
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = self.workers
        st = solver.Solve(m)
        if st == cp_model.INFEASIBLE:
            if upper is not None:
                self.lower = max(self.lower, upper)
            return None
        if st != cp_model.OPTIMAL:
            raise RuntimeError(f"hitting set solver status {solver.StatusName(st)}")
        H = frozenset(v for v in range(self.n) if solver.Value(x[v]))
        self.last = H
        self.lower = max(self.lower, len(H))
        return H


def minimum_ks(pool, sym=None, log=print, rng_seed=1, max_seconds=None, cuts_per_round=8,
               min_cuts_per_round=1, orbit_cap=4000, backend="cpsat", workers=8, log_every=1):
    """Exact minimum KS set of `pool`.

    Returns a dict with keys: status ('optimal', 'colorable', 'timeout'),
    lower (proved lower bound), best (smallest KS set found), corrections
    (list of correction sets, each certified by a coloring of its complement).
    """
    t0 = time.time()
    rng = random.Random(rng_seed)
    n = pool.n
    everything = list(range(n))
    if pool.coloring(everything) is not None:
        log(f"{pool.name}: the whole pool is colorable; it contains no KS set")
        return {"status": "colorable", "lower": None, "best": None, "corrections": []}

    hs = HittingSets(n, backend=backend, workers=workers)
    known = set()
    best = pool.shrink(everything, rng=rng)
    log(f"[{time.time()-t0:8.1f}s] first critical KS set: {pool.describe(best)}")

    def add_cut(D):
        fresh = 0
        images = sym.orbit(D, cap=orbit_cap) if sym else {frozenset(D)}
        for T in images:
            if T not in known:
                known.add(T)
                hs.add(T)
                fresh += 1
        return fresh

    def finish(status, it):
        return {"status": status, "lower": hs.lower, "best": best,
                "corrections": sorted(known, key=lambda s: (len(s), sorted(s))), "iterations": it}

    D0 = pool.minimum_correction_set()
    log(f"[{time.time()-t0:8.1f}s] minimum correction set of the whole pool has {len(D0)} rays")
    add_cut(D0)

    it = 0
    while True:
        it += 1
        H = hs.minimum(upper=len(best))
        if H is None:
            log(f"[{time.time()-t0:8.1f}s] it {it}: no hitting set below {len(best)}; "
                f"the best KS set is optimal ({len(known)} cuts)")
            return finish("optimal", it)
        if pool.is_ks(H):
            best = H
            hs.lower = len(H)
            log(f"[{time.time()-t0:8.1f}s] it {it}: hitting set of size {len(H)} is a KS set; optimal "
                f"({len(known)} cuts)")
            return finish("optimal", it)
        # H is colorable: harvest pairwise disjoint correction sets disjoint from H
        forced = set(H)
        fresh = 0
        sizes = []
        for k in range(cuts_per_round):
            if k < min_cuts_per_round:
                D = pool.minimum_correction_set(forced_in=forced)
            else:
                D = pool.minimal_correction_set(forced_in=forced, rng=rng)
            if D is None:
                # forced is a KS set: an upper bound candidate
                cand = pool.shrink(forced, rng=rng, keep_first=H)
                if len(cand) < len(best):
                    best = cand
                    log(f"[{time.time()-t0:8.1f}s] it {it}: new best KS set: {pool.describe(best)}")
                break
            sizes.append(len(D))
            fresh += add_cut(D)
            forced |= D
        if it <= 10 or it % log_every == 0:
            log(f"[{time.time()-t0:8.1f}s] it {it}: lower {hs.lower}, best {len(best)}, |H|={len(H)}, "
                f"cut sizes {sizes}, +{fresh} cuts (total {len(known)})")
        if max_seconds and time.time() - t0 > max_seconds:
            log(f"[{time.time()-t0:8.1f}s] time limit: lower {hs.lower}, best {len(best)}")
            return finish("timeout", it)
