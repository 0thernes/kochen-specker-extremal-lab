"""kscegar.py - decide "is there a KS set with at most k rays in this pool?"

Counterexample-guided search with one incremental SAT solver for candidates.

Soundness of a cut.  Let I be a set of pairwise non-orthogonal rays of the
pool and Miss(I) the bases containing no ray of I.  A set S that contains no
basis of Miss(I) is colorable (value 1 exactly on I).  So every KS set
contains a basis of Miss(I): the clause  OR_{b in Miss(I)} y_b  is valid,
where y_b means "all rays of basis b are chosen".

Candidate solver.  Variables x_v (ray chosen), y_b (basis chosen), clauses
y_b -> x_v, the cuts, and a totalizer for  sum x_v <= k.  If it is
unsatisfiable, no KS set with at most k rays exists in the pool.  If it
returns a set S (the union of the chosen bases), S is either a KS set or has
a coloring, which is extended to an independent set of the whole pool that
misses few bases and yields a new cut that S violates.
"""
from __future__ import annotations

import os
import random
import time

from pysat.card import ITotalizer
from pysat.solvers import Solver

from ksengine import bits, mask, popcount


class Cegar:
    def __init__(self, pool, sym=None, solver_name="g4", log=print, seed=1):
        self.pool = pool
        self.n = pool.n
        self.bases = pool.bases
        self.nb = len(self.bases)
        self.base_masks = [mask(b) for b in self.bases]
        self.log = log
        self.rng = random.Random(seed)
        self.cuts = []            # list of (frozenset of basis indices)
        self.cutset = set()
        self.witness = {}         # cut -> independent set I (frozenset of rays) certifying it
        # x_v = v+1, y_b = n+b+1
        self.xvar = lambda v: v + 1
        self.yvar = lambda b: self.n + b + 1
        self.top = self.n + self.nb
        self.solver_name = solver_name
        self.sat = Solver(name=solver_name)
        for b, basis in enumerate(self.bases):
            for v in basis:
                self.sat.add_clause([-self.yvar(b), self.xvar(v)])
        self.tot = ITotalizer(lits=[self.xvar(v) for v in range(self.n)], ubound=self.n, top_id=self.top)
        for cl in self.tot.cnf.clauses:
            self.sat.add_clause(cl)
        self.top = self.tot.top_id
        self.bperms = []
        if sym:
            index = {b: i for i, b in enumerate(self.bases)}
            for g in sym.gens:
                self.bperms.append(([index[tuple(sorted(g[v] for v in b))] for b in self.bases], g))
        # coloring solver: c_v = v+1, a_v = n+v+1 (shared with the pool object)
        self.stats = {"sat_calls": 0, "cuts": 0}

    # ---- cuts ----
    def missed(self, I):
        Im = mask(I)
        return frozenset(i for i in range(self.nb) if not (self.base_masks[i] & Im))

    def add_cut(self, cut, I):
        if cut in self.cutset:
            return False
        self.cutset.add(cut)
        self.cuts.append(cut)
        self.witness[cut] = I
        self.sat.add_clause([self.yvar(b) for b in cut])
        return True

    def add_cut_orbit(self, cut, I, cap=4000):
        fresh = 1 if self.add_cut(cut, I) else 0
        if not self.bperms:
            return fresh
        seen = {cut}
        frontier = [(cut, I)]
        while frontier and len(seen) < cap:
            nxt = []
            for (T, J) in frontier:
                for (bp, g) in self.bperms:
                    U = frozenset(bp[i] for i in T)
                    if U in seen:
                        continue
                    seen.add(U)
                    K = frozenset(g[v] for v in J)
                    nxt.append((U, K))
                    if self.add_cut(U, K):
                        fresh += 1
                    if len(seen) >= cap:
                        break
                if len(seen) >= cap:
                    break
            frontier = nxt
        return fresh

    # ---- coloring of a candidate, extended to the pool ----
    def extend_coloring(self, S, tries=6):
        """Independent set I of the pool that hits every basis inside S, chosen
        (heuristically) to miss few bases of the pool.  None if S is KS."""
        pool = self.pool
        ones = pool.coloring(S)
        if ones is None:
            return None
        best = None
        Sm = mask(S)
        for t in range(tries):
            I = set(ones)
            blocked = 0
            for v in I:
                blocked |= pool.adj[v]
            # greedily add rays that hit the most still-missed bases
            Im = mask(I)
            missed = [i for i in range(self.nb) if not (self.base_masks[i] & Im)]
            while True:
                score = {}
                for i in missed:
                    for v in self.bases[i]:
                        if not (blocked >> v) & 1:
                            score[v] = score.get(v, 0) + 1
                if not score:
                    break
                mx = max(score.values())
                if t == 0:
                    cand = [v for v, s in score.items() if s == mx]
                else:
                    cand = [v for v, s in score.items() if s >= mx * 0.7]
                v = self.rng.choice(cand)
                I.add(v)
                blocked |= pool.adj[v]
                Im |= 1 << v
                missed = [i for i in missed if not (self.base_masks[i] >> v) & 1]
            if best is None or len(missed) < best[1]:
                best = (frozenset(I), len(missed))
        return best[0]

    def best_coloring_exact(self, S, workers=8, time_limit=20):
        """Like extend_coloring but minimising the number of missed bases with
        CP-SAT (optimal or best found within the time limit)."""
        from ortools.sat.python import cp_model
        pool = self.pool
        Sm = mask(S)
        m = cp_model.CpModel()
        c = [m.NewBoolVar(f"c{v}") for v in range(self.n)]
        for v in range(self.n):
            for w in bits(pool.adj[v] >> (v + 1) << (v + 1)):
                m.AddBoolOr([c[v].Not(), c[w].Not()])
        us = []
        for i, b in enumerate(self.bases):
            if self.base_masks[i] & Sm == self.base_masks[i]:
                m.AddBoolOr([c[x] for x in b])
            else:
                u = m.NewBoolVar(f"u{i}")
                m.AddBoolOr([c[x] for x in b] + [u])
                us.append(u)
        m.Minimize(sum(us))
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = workers
        s.parameters.max_time_in_seconds = time_limit
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            return None
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return self.extend_coloring(S)
        return frozenset(v for v in range(self.n) if s.Value(c[v]))

    def check_cut(self, cut):
        """Re-verify a stored cut from its witness (independence + missed set)."""
        I = self.witness[cut]
        Im = mask(I)
        for v in I:
            if self.pool.adj[v] & Im:
                return False
        return self.missed(I) == cut

    # ---- main loop ----
    def candidate(self, k):
        """A union of bases with at most k rays satisfying all cuts, or None."""
        self.stats["sat_calls"] += 1
        assumptions = [-self.tot.rhs[k]] if k < self.n else []
        if not self.sat.solve(assumptions=assumptions):
            return None
        model = self.sat.get_model()
        S = set()
        for b in range(self.nb):
            if model[self.yvar(b) - 1] > 0:
                S |= set(self.bases[b])
        return frozenset(S)

    def search_below(self, k, max_seconds=None, exact_cuts=True, orbit_cap=4000, log_every=20,
                     workers=8):
        t0 = time.time()
        log = self.log
        if not self.cuts:
            I = self.best_coloring_exact((), workers=workers, time_limit=60) if exact_cuts else self.extend_coloring(())
            cut = self.missed(I)
            if not cut:
                log(f"{self.pool.name}: the whole pool is colorable; it contains no KS set")
                return {"status": "none", "ks": None, "colorable_pool": True}
            log(f"[{time.time()-t0:8.1f}s] a coloring of the whole pool misses {len(cut)} of {self.nb} bases")
            self.add_cut_orbit(cut, I, cap=orbit_cap)
        it = 0
        while True:
            it += 1
            S = self.candidate(k)
            if S is None:
                log(f"[{time.time()-t0:8.1f}s] it {it}: UNSAT - no KS set with at most {k} rays in "
                    f"{self.pool.name} ({len(self.cuts)} cuts)")
                return {"status": "none", "ks": None, "iterations": it}
            I = self.best_coloring_exact(S, workers=workers) if exact_cuts else self.extend_coloring(S)
            if I is None:
                log(f"[{time.time()-t0:8.1f}s] it {it}: FOUND a KS set: {self.pool.describe(S)}")
                return {"status": "found", "ks": S, "iterations": it}
            cut = self.missed(I)
            fresh = self.add_cut_orbit(cut, I, cap=orbit_cap)
            if fresh == 0:
                raise RuntimeError("no progress: cut already present")
            if it <= 10 or it % log_every == 0:
                log(f"[{time.time()-t0:8.1f}s] it {it}: candidate {len(S)} rays colorable; cut misses "
                    f"{len(cut)} bases, +{fresh} (total {len(self.cuts)})")
            if max_seconds and time.time() - t0 > max_seconds:
                log(f"[{time.time()-t0:8.1f}s] time limit after {it} iterations, {len(self.cuts)} cuts")
                return {"status": "timeout", "ks": None, "iterations": it}

    def dump_cnf(self, k, path):
        """Write the final candidate CNF (with the bound sum x <= k as a unit
        clause on the totalizer output) in DIMACS format."""
        clauses = []
        for b, basis in enumerate(self.bases):
            for v in basis:
                clauses.append([-self.yvar(b), self.xvar(v)])
        clauses.extend(self.tot.cnf.clauses)
        for cut in self.cuts:
            clauses.append([self.yvar(b) for b in sorted(cut)])
        clauses.append([-self.tot.rhs[k]])
        nv = max(abs(l) for cl in clauses for l in cl)
        with open(path, "w") as f:
            f.write(f"p cnf {nv} {len(clauses)}\n")
            for cl in clauses:
                f.write(" ".join(map(str, cl)) + " 0\n")
        return nv, len(clauses)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pools

    d = int(sys.argv[1])
    H = int(sys.argv[2])
    k = int(sys.argv[3])
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else None
    exact = (sys.argv[5] != "greedy") if len(sys.argv) > 5 else True
    full = pools.box_pool(d, H)
    core = full.ks_core()
    sym = pools.signed_perm_symmetry(core)
    cg = Cegar(core, sym=sym)
    res = cg.search_below(k, max_seconds=secs, exact_cuts=exact)
    print("status", res["status"], "iterations", res.get("iterations"), "cuts", len(cg.cuts))
    if res.get("ks"):
        for v in sorted(res["ks"]):
            print("  ", core.rays[v])
