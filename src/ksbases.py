"""ksbases.py - exact minimum KS sets by "coloring cuts" on bases.

Fact.  Let I be any set of pairwise non-orthogonal rays of the pool V and let
Miss(I) be the set of bases of V that contain no ray of I.  If a subset S of V
contains no basis of Miss(I), then S is colorable (give value 1 to the rays of
I that lie in S).  Hence every KS set S contains at least one basis of Miss(I),
for every such I.  Conversely, if S is colorable by f, then I = f^{-1}(1) is a
set of pairwise non-orthogonal rays and S contains no basis of Miss(I).

So  S is KS  <=>  for every independent set I, S contains a basis of Miss(I).

Master problem (CP-SAT): Boolean x_v (ray chosen), y_b (basis contained),
y_b -> x_v for v in b; one clause OR_{b in Miss(I)} y_b per collected I;
minimise sum x_v.  Separation: given the master optimum S, if S is colorable
take a coloring of S and extend it to an independent set of V that misses as
few bases as possible; its clause is violated by S.  If S is not colorable it
is a minimum KS set.
"""
from __future__ import annotations

import random
import time

from ortools.sat.python import cp_model

from ksengine import bits, mask, popcount


class BaseCuts:
    def __init__(self, pool, workers=8):
        self.pool = pool
        self.n = pool.n
        self.bases = pool.bases
        self.nb = len(self.bases)
        self.base_masks = [mask(b) for b in self.bases]
        self.workers = workers
        self.cuts = []          # list of frozensets of basis indices
        self.cutset = set()
        self.lower = 0
        self.last = None
        self.edges = []
        for v in range(self.n):
            for w in bits(pool.adj[v] >> (v + 1) << (v + 1)):
                self.edges.append((v, w))

    # ---- separation: best coloring extending a coloring of S ----
    def best_coloring(self, S=(), time_limit=None, forbid_missing=None):
        """Independent set I hitting every basis inside S and missing as few
        bases overall as possible.  Returns (I, missed basis indices) or None
        when S is not colorable."""
        pool = self.pool
        Sm = mask(S)
        m = cp_model.CpModel()
        c = [m.NewBoolVar(f"c{v}") for v in range(self.n)]
        for (v, w) in self.edges:
            m.AddBoolOr([c[v].Not(), c[w].Not()])
        miss = []
        for i, b in enumerate(self.bases):
            if self.base_masks[i] & Sm == self.base_masks[i]:
                m.AddBoolOr([c[x] for x in b])
            else:
                u = m.NewBoolVar(f"u{i}")
                m.AddBoolOr([c[x] for x in b] + [u])
                miss.append((i, u))
        m.Minimize(sum(u for _, u in miss))
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = self.workers
        if time_limit:
            s.parameters.max_time_in_seconds = time_limit
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            return None
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("separation: " + s.StatusName(st))
        I = frozenset(v for v in range(self.n) if s.Value(c[v]))
        # recompute the missed bases from I itself (do not trust u)
        Im = mask(I)
        missed = frozenset(i for i in range(self.nb) if not (self.base_masks[i] & Im))
        return I, missed

    def add_cut(self, missed):
        missed = frozenset(missed)
        if missed in self.cutset:
            return False
        self.cutset.add(missed)
        self.cuts.append(missed)
        return True

    # ---- master ----
    def feasible(self, k, time_limit=None, seed=None):
        """Some set of at most k rays containing a basis of every cut, or None
        if there is none.  Raises on a solver time-out."""
        m = cp_model.CpModel()
        x = [m.NewBoolVar(f"x{v}") for v in range(self.n)]
        used = set()
        for cut in self.cuts:
            used |= cut
        y = {}
        for i in used:
            y[i] = m.NewBoolVar(f"y{i}")
            for v in self.bases[i]:
                m.AddImplication(y[i], x[v])
        for cut in self.cuts:
            m.AddBoolOr([y[i] for i in cut])
        m.Add(sum(x) <= k)
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = self.workers
        if seed is not None:
            s.parameters.random_seed = seed
        if time_limit:
            s.parameters.max_time_in_seconds = time_limit
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            self.lower = max(self.lower, k + 1)
            return None
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("feasibility master: " + s.StatusName(st))
        # keep only rays that lie in a chosen basis (drops padding)
        S = set()
        for i in used:
            if s.Value(y[i]):
                S |= set(self.bases[i])
        return frozenset(S)

    def master(self, upper=None, time_limit=None):
        """Minimum set of rays containing a basis of every cut.  Returns the set
        or None if no such set has fewer than `upper` rays."""
        m = cp_model.CpModel()
        x = [m.NewBoolVar(f"x{v}") for v in range(self.n)]
        used = set()
        for cut in self.cuts:
            used |= cut
        y = {}
        for i in used:
            y[i] = m.NewBoolVar(f"y{i}")
            for v in self.bases[i]:
                m.AddImplication(y[i], x[v])
        for cut in self.cuts:
            m.AddBoolOr([y[i] for i in cut])
        total = sum(x)
        if self.lower:
            m.Add(total >= self.lower)
        if upper is not None:
            m.Add(total <= upper - 1)
        m.Minimize(total)
        if self.last is not None:
            for v in range(self.n):
                m.AddHint(x[v], 1 if v in self.last else 0)
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = self.workers
        if time_limit:
            s.parameters.max_time_in_seconds = time_limit
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            if upper is not None:
                self.lower = max(self.lower, upper)
            return None
        if st != cp_model.OPTIMAL:
            raise RuntimeError("master: " + s.StatusName(st))
        S = frozenset(v for v in range(self.n) if s.Value(x[v]))
        self.last = S
        self.lower = max(self.lower, len(S))
        return S


def basis_perm(pool, g):
    """Action of a ray permutation g on basis indices."""
    index = {b: i for i, b in enumerate(pool.bases)}
    return [index[tuple(sorted(g[v] for v in b))] for b in pool.bases]


def minimum_ks_bases(pool, sym=None, log=print, max_seconds=None, workers=8, orbit_cap=2000,
                     rng_seed=1, best=None):
    t0 = time.time()
    rng = random.Random(rng_seed)
    bc = BaseCuts(pool, workers=workers)
    everything = list(range(pool.n))
    if pool.coloring(everything) is not None:
        log(f"{pool.name}: the whole pool is colorable; it contains no KS set")
        return {"status": "colorable", "lower": None, "best": None, "cuts": []}
    if best is None:
        best = pool.shrink(everything, rng=rng)
    log(f"[{time.time()-t0:8.1f}s] starting KS set: {pool.describe(best)}")
    bperms = [basis_perm(pool, g) for g in sym.gens] if sym else []

    def add_with_images(missed):
        fresh = 0
        seen = {frozenset(missed)}
        frontier = [frozenset(missed)]
        if bc.add_cut(missed):
            fresh += 1
        while frontier and len(seen) < orbit_cap:
            nxt = []
            for T in frontier:
                for bp in bperms:
                    U = frozenset(bp[i] for i in T)
                    if U not in seen:
                        seen.add(U)
                        nxt.append(U)
                        if bc.add_cut(U):
                            fresh += 1
                        if len(seen) >= orbit_cap:
                            break
                if len(seen) >= orbit_cap:
                    break
            frontier = nxt
        return fresh

    I, missed = bc.best_coloring(())
    log(f"[{time.time()-t0:8.1f}s] best coloring of the whole pool misses {len(missed)} of {bc.nb} bases")
    add_with_images(missed)
    it = 0
    while True:
        it += 1
        S = bc.master(upper=len(best))
        if S is None:
            log(f"[{time.time()-t0:8.1f}s] it {it}: no candidate below {len(best)} rays; optimal "
                f"({len(bc.cuts)} cuts)")
            return {"status": "optimal", "lower": len(best), "best": best, "cuts": bc.cuts, "iterations": it}
        res = bc.best_coloring(S)
        if res is None:
            best = S
            log(f"[{time.time()-t0:8.1f}s] it {it}: candidate with {len(S)} rays is a KS set; optimal "
                f"({len(bc.cuts)} cuts)")
            return {"status": "optimal", "lower": len(S), "best": S, "cuts": bc.cuts, "iterations": it}
        I, missed = res
        fresh = add_with_images(missed)
        log(f"[{time.time()-t0:8.1f}s] it {it}: lower {bc.lower}, best {len(best)}, "
            f"cut misses {len(missed)} bases, +{fresh} cuts (total {len(bc.cuts)})")
        if max_seconds and time.time() - t0 > max_seconds:
            log(f"[{time.time()-t0:8.1f}s] time limit: lower {bc.lower}, best {len(best)}")
            return {"status": "timeout", "lower": bc.lower, "best": best, "cuts": bc.cuts, "iterations": it}


def search_below(pool, k, sym=None, log=print, max_seconds=None, workers=8, orbit_cap=4000,
                 bc=None, log_every=1):
    """Decide whether the pool contains a KS set with at most k rays.

    Counterexample-guided: ask for any set of at most k rays that contains a
    basis of every collected cut; if it is KS, return it; otherwise its best
    coloring gives a new cut (plus symmetric images).  When no candidate is
    left, no KS set with at most k rays exists.

    Returns dict(status='found'|'none'|'timeout', ks=set or None, cuts=list).
    """
    t0 = time.time()
    bc = bc or BaseCuts(pool, workers=workers)
    bperms = [basis_perm(pool, g) for g in sym.gens] if sym else []

    def add_with_images(missed):
        fresh = 0
        first = frozenset(missed)
        seen = {first}
        frontier = [first]
        if bc.add_cut(first):
            fresh += 1
        while frontier and len(seen) < orbit_cap:
            nxt = []
            for T in frontier:
                for bp in bperms:
                    U = frozenset(bp[i] for i in T)
                    if U not in seen:
                        seen.add(U)
                        nxt.append(U)
                        if bc.add_cut(U):
                            fresh += 1
                        if len(seen) >= orbit_cap:
                            break
                if len(seen) >= orbit_cap:
                    break
            frontier = nxt
        return fresh

    if not bc.cuts:
        res = bc.best_coloring(())
        if res is None:
            raise RuntimeError("empty set is not colorable?")
        I, missed = res
        if not missed:
            log(f"{pool.name}: the whole pool is colorable; it contains no KS set")
            return {"status": "none", "ks": None, "cuts": bc.cuts, "colorable_pool": True}
        log(f"[{time.time()-t0:8.1f}s] best coloring of the whole pool misses {len(missed)} of {bc.nb} bases")
        add_with_images(missed)
    it = 0
    while True:
        it += 1
        S = bc.feasible(k)
        if S is None:
            log(f"[{time.time()-t0:8.1f}s] it {it}: no candidate with at most {k} rays is left: "
                f"NO KS set with <= {k} rays in {pool.name} ({len(bc.cuts)} cuts)")
            return {"status": "none", "ks": None, "cuts": bc.cuts, "iterations": it}
        res = bc.best_coloring(S)
        if res is None:
            log(f"[{time.time()-t0:8.1f}s] it {it}: FOUND a KS set with {len(S)} rays: {pool.describe(S)}")
            return {"status": "found", "ks": S, "cuts": bc.cuts, "iterations": it}
        I, missed = res
        fresh = add_with_images(missed)
        if it <= 10 or it % log_every == 0:
            log(f"[{time.time()-t0:8.1f}s] it {it}: candidate {len(S)} rays colorable; cut misses "
                f"{len(missed)} bases, +{fresh} cuts (total {len(bc.cuts)})")
        if max_seconds and time.time() - t0 > max_seconds:
            log(f"[{time.time()-t0:8.1f}s] time limit after {it} iterations")
            return {"status": "timeout", "ks": None, "cuts": bc.cuts, "iterations": it}


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pools

    mode = sys.argv[1]
    d = int(sys.argv[2])
    H = int(sys.argv[3])
    full = pools.box_pool(d, H)
    core = full.ks_core()
    sym = pools.signed_perm_symmetry(core)
    if mode == "min":
        secs = float(sys.argv[4]) if len(sys.argv) > 4 else None
        res = minimum_ks_bases(core, sym=sym, max_seconds=secs)
        if res.get("best"):
            print("best:", core.describe(res["best"]), "status", res["status"], "lower", res["lower"])
            for v in sorted(res["best"]):
                print("  ", core.rays[v])
    else:
        k = int(sys.argv[4])
        secs = float(sys.argv[5]) if len(sys.argv) > 5 else None
        res = search_below(core, k, sym=sym, max_seconds=secs)
        print("status", res["status"], "iterations", res.get("iterations"), "cuts", len(res["cuts"]))
        if res.get("ks"):
            print("KS set:", core.describe(res["ks"]))
            for v in sorted(res["ks"]):
                print("  ", core.rays[v])
