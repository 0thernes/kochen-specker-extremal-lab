"""ksmaster.py - counterexample-guided search for a CRITICAL KS set with at
most k rays, with a CP-SAT candidate problem strengthened by necessary
conditions for critical KS sets.

Candidate problem (Boolean x_v = ray chosen, y_b = basis chosen):
  (D)  y_b <-> AND_{v in b} x_v
  (C1) x_v -> OR_{b containing v} y_b          every ray of a critical KS set lies in a basis inside it
  (C2) x_v -> sum_{w orthogonal to v} x_w >= d  ... and has at least d orthogonal partners inside it
  (K)  sum_v x_v <= k
  cuts: OR_{b in Miss(I)} y_b for collected independent sets I (valid for every KS set)
  optional case constraints: rays fixed in / out.
Every KS set contains a critical KS set of no larger size, so if the
candidate problem becomes infeasible there is no KS set with at most k rays
(compatible with the case constraints only if these are closed under passing
to a critical subset; cases that fix rays OUT always are, and a case that
fixes rays IN must be justified separately by the caller).

(C1)/(C2) proof.  Let T be a critical KS set, v in T, c a coloring of T - v.
If v lies in no basis of T, extend c by c(v) = 0.  If v has fewer than d
neighbours in T, it lies in at most one basis b of T (two bases through v
share at most d-2 other rays, giving at least d neighbours) and all its
neighbours are in b; extend c by c(v) = 1 if the rest of b is all 0 and
c(v) = 0 otherwise.  Either way T is colorable, a contradiction.
"""
from __future__ import annotations

import json
import os
import sys
import time

from ortools.sat.python import cp_model

from ksengine import bits, mask, popcount


class Master:
    def __init__(self, pool, k, sym=None, log=print, workers=8, fix_in=(), fix_out=(), use_c1=True,
                 use_c2=True, color_time=15.0):
        self.pool = pool
        self.k = k
        self.n = pool.n
        self.d = pool.d
        self.bases = pool.bases
        self.nb = len(self.bases)
        self.bm = [mask(b) for b in self.bases]
        self.log = log
        self.workers = workers
        self.fix_in = set(fix_in)
        self.fix_out = set(fix_out)
        self.use_c1 = use_c1
        self.use_c2 = use_c2
        self.color_time = color_time
        self.symbreak = None
        self.cuts = []
        self.cutset = set()
        self.witness = {}
        self.edges = []
        for v in range(self.n):
            for w in bits(pool.adj[v] >> (v + 1) << (v + 1)):
                self.edges.append((v, w))
        self.bases_of = [[] for _ in range(self.n)]
        for b, basis in enumerate(self.bases):
            for v in basis:
                self.bases_of[v].append(b)
        self.bperms = []
        if sym:
            index = {b: i for i, b in enumerate(self.bases)}
            for g in sym.gens:
                self.bperms.append(([index[tuple(sorted(g[v] for v in b))] for b in self.bases], g))

    # ---- cuts ----
    def missed(self, I):
        Im = mask(I)
        return frozenset(i for i in range(self.nb) if not (self.bm[i] & Im))

    def add_cut(self, cut, I):
        if cut in self.cutset:
            return False
        self.cutset.add(cut)
        self.cuts.append(cut)
        self.witness[cut] = I
        return True

    def add_cut_orbit(self, cut, I, cap=5000):
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

    # ---- separation ----
    def best_coloring(self, S):
        """Independent set hitting all bases inside S, missing few bases overall.
        None if S is a KS set."""
        Sm = mask(S)
        m = cp_model.CpModel()
        c = [m.NewBoolVar(f"c{v}") for v in range(self.n)]
        for (v, w) in self.edges:
            m.AddBoolOr([c[v].Not(), c[w].Not()])
        us = []
        for i, b in enumerate(self.bases):
            if self.bm[i] & Sm == self.bm[i]:
                m.AddBoolOr([c[x] for x in b])
            else:
                u = m.NewBoolVar(f"u{i}")
                m.AddBoolOr([c[x] for x in b] + [u])
                us.append(u)
        m.Minimize(sum(us))
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = self.workers
        s.parameters.max_time_in_seconds = self.color_time
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            return None
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            ones = self.pool.coloring(S)
            return ones
        return frozenset(v for v in range(self.n) if s.Value(c[v]))

    # ---- candidate ----
    def candidate(self, time_limit=None, seed=0):
        m = cp_model.CpModel()
        x = [m.NewBoolVar(f"x{v}") for v in range(self.n)]
        y = [m.NewBoolVar(f"y{b}") for b in range(self.nb)]
        for b, basis in enumerate(self.bases):
            for v in basis:
                m.AddImplication(y[b], x[v])
            m.AddBoolOr([y[b]] + [x[v].Not() for v in basis])
        if self.use_c1:
            for v in range(self.n):
                m.AddBoolOr([x[v].Not()] + [y[b] for b in self.bases_of[v]])
        if self.use_c2:
            for v in range(self.n):
                nb = list(bits(self.pool.adj[v]))
                m.Add(sum(x[w] for w in nb) >= self.d).OnlyEnforceIf(x[v])
        for v in self.fix_in:
            m.Add(x[v] == 1)
        for v in self.fix_out:
            m.Add(x[v] == 0)
        if self.symbreak:
            self.symbreak(m, x)
        for cut in self.cuts:
            m.AddBoolOr([y[b] for b in cut])
        m.Add(sum(x) <= self.k)
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = self.workers
        s.parameters.random_seed = seed
        if time_limit:
            s.parameters.max_time_in_seconds = time_limit
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            return "infeasible"
        if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return frozenset(v for v in range(self.n) if s.Value(x[v]))
        return "unknown"

    def coloring_with(self, forced):
        """Independent set containing the rays `forced` (assumed pairwise
        non-orthogonal) that misses as few bases as possible."""
        m = cp_model.CpModel()
        c = [m.NewBoolVar(f"c{v}") for v in range(self.n)]
        for (v, w) in self.edges:
            m.AddBoolOr([c[v].Not(), c[w].Not()])
        for v in forced:
            m.Add(c[v] == 1)
        us = []
        for i, b in enumerate(self.bases):
            u = m.NewBoolVar(f"u{i}")
            m.AddBoolOr([c[x] for x in b] + [u])
            us.append(u)
        m.Minimize(sum(us))
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = self.workers
        s.parameters.max_time_in_seconds = self.color_time
        st = s.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None
        return frozenset(v for v in range(self.n) if s.Value(c[v]))

    def seed_cuts(self, orbit_cap=5000, pairs=True, max_pairs=40):
        """Add cuts from the best colorings that contain a prescribed ray (one
        ray per symmetry orbit) or a prescribed pair of non-orthogonal rays."""
        t0 = time.time()
        gens = [g for (_, g) in self.bperms]
        orb = list(range(self.n))

        def find(a):
            while orb[a] != a:
                orb[a] = orb[orb[a]]
                a = orb[a]
            return a

        for g in gens:
            for v in range(self.n):
                a, b = find(v), find(g[v])
                if a != b:
                    orb[a] = b
        reps = sorted({find(v) for v in range(self.n)})
        added = 0
        for v in reps:
            I = self.coloring_with([v])
            if I is not None:
                added += self.add_cut_orbit(self.missed(I), I, cap=orbit_cap)
        npairs = 0
        if pairs:
            import random
            rng = random.Random(5)
            seen = set()
            cand = [(v, w) for v in reps for w in range(self.n)
                    if w != v and not (self.pool.adj[v] >> w) & 1]
            rng.shuffle(cand)
            for (v, w) in cand[:max_pairs]:
                I = self.coloring_with([v, w])
                if I is not None:
                    added += self.add_cut_orbit(self.missed(I), I, cap=orbit_cap)
                    npairs += 1
        self.log(f"[{time.time()-t0:8.1f}s] seeded cuts from {len(reps)} ray orbits and {npairs} pairs: "
                 f"+{added} (total {len(self.cuts)})")

    def run(self, max_seconds=None, cand_time=None, log_every=1, orbit_cap=5000):
        t0 = time.time()
        log = self.log
        if not self.cuts:
            I = self.best_coloring(())
            cut = self.missed(I)
            if not cut:
                log(f"{self.pool.name}: the pool is colorable")
                return {"status": "none"}
            log(f"[{time.time()-t0:8.1f}s] a coloring of the whole pool misses {len(cut)} of {self.nb} bases")
            self.add_cut_orbit(cut, I, cap=orbit_cap)
        it = 0
        while True:
            it += 1
            tc = time.time()
            S = self.candidate(time_limit=cand_time, seed=it)
            tc = time.time() - tc
            if S == "infeasible":
                log(f"[{time.time()-t0:8.1f}s] it {it}: INFEASIBLE ({tc:.1f}s) - no critical KS set with at most "
                    f"{self.k} rays in {self.pool.name} under the case constraints ({len(self.cuts)} cuts)")
                return {"status": "none", "iterations": it}
            if S == "unknown":
                log(f"[{time.time()-t0:8.1f}s] it {it}: candidate problem not solved within {cand_time}s")
                return {"status": "timeout", "iterations": it}
            I = self.best_coloring(S)
            if I is None:
                log(f"[{time.time()-t0:8.1f}s] it {it}: FOUND a KS set: {self.pool.describe(S)}")
                return {"status": "found", "ks": S, "iterations": it}
            cut = self.missed(I)
            fresh = self.add_cut_orbit(cut, I, cap=orbit_cap)
            if fresh == 0:
                raise RuntimeError("no progress")
            if it <= 10 or it % log_every == 0:
                log(f"[{time.time()-t0:8.1f}s] it {it}: candidate {len(S)} rays ({tc:.1f}s) colorable; cut misses "
                    f"{len(cut)} bases, +{fresh} (total {len(self.cuts)})")
            if max_seconds and time.time() - t0 > max_seconds:
                log(f"[{time.time()-t0:8.1f}s] time limit after {it} iterations")
                return {"status": "timeout", "iterations": it}

    def save_cuts(self, path):
        data = {"pool": self.pool.name, "k": self.k, "n": self.n,
                "cuts": [[sorted(c), sorted(self.witness[c])] for c in self.cuts]}
        with open(path, "w") as f:
            json.dump(data, f)


def box_symmetry_breaking(pool, groups):
    """Symmetry breaking for integer box pools (signed coordinate permutations).

    Every set of rays can be moved, by a coordinate permutation that preserves
    each group in `groups` (lists of interchangeable coordinates) followed by
    sign changes of coordinates 1..d-1, to a set with
      * n_a >= n_b for consecutive coordinates a, b of a group, where n_j is the
        number of chosen rays with a non-zero j-th entry (sort each group);
      * x[e_0 + e_j] >= x[e_0 - e_j] for j = 1..d-1 (flipping the sign of
        coordinate j swaps these two rays and fixes e_0 +- e_i for i != j; it
        changes no n_i).
    Both maps are symmetries of the pool and fix every coordinate axis ray up
    to the permutation, so they preserve the case constraints used with them
    and map critical KS sets to critical KS sets.
    """
    d = pool.d
    index = {r: i for i, r in enumerate(pool.rays)}
    supp = [[i for i, r in enumerate(pool.rays) if r[j] != 0] for j in range(d)]
    pairs = []
    for j in range(1, d):
        a = [0] * d
        a[0] = 1
        a[j] = 1
        b = [0] * d
        b[0] = 1
        b[j] = -1
        ia, ib = index.get(tuple(a)), index.get(tuple(b))
        if ia is not None and ib is not None:
            pairs.append((ia, ib))

    def add(m, x):
        for g in groups:
            for a, b in zip(g, g[1:]):
                m.Add(sum(x[i] for i in supp[a]) >= sum(x[i] for i in supp[b]))
        for ia, ib in pairs:
            m.Add(x[ia] >= x[ib])

    return add


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ksdfs import build

    # usage: python -u ksmaster.py k seconds workers case kind args...
    #   case: "-" or comma list like in:0,1,2;out:3,4 (ray labels resolved for box pools as axis indices)
    k = int(sys.argv[1])
    secs = float(sys.argv[2]) if sys.argv[2] != "-" else None
    workers = int(sys.argv[3])
    case = sys.argv[4]
    kind = sys.argv[5]
    args = sys.argv[6:]
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tag = "master_" + "_".join([kind] + args) + f"_k{k}" + ("" if case == "-" else "_" + case.replace(":", "").replace(";", "_").replace(",", ""))
    logf = open(os.path.join(ROOT, "logs", tag + ".log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    core, sym = build(kind, args, log)
    fix_in, fix_out = [], []
    if case != "-":
        d = core.d
        axis = {}
        for i, r in enumerate(core.rays):
            nz = [j for j, c in enumerate(r) if c != 0]
            if len(nz) == 1:
                axis[nz[0]] = i
        for part in case.split(";"):
            name, vals = part.split(":")
            idx = [axis[int(c)] for c in vals.split(",") if c != ""]
            (fix_in if name == "in" else fix_out).extend(idx)
    # optional extra fixed rays (cube-and-conquer), same convention as ks_cnf.parse_case
    _index = {tuple(r): i for i, r in enumerate(core.rays)}
    for _var, _target in (("KS_FIX_IN", fix_in), ("KS_FIX_OUT", fix_out)):
        for _part in [p for p in os.environ.get(_var, "").split("|") if p]:
            _vec = tuple(int(c) for c in _part.split(","))
            if _vec not in _index:
                raise SystemExit(f"{_var}: ray {_vec} is not in the pool")
            _target.append(_index[_vec])
    if os.environ.get("KS_CUBE_TAG"):
        tag += "_cube" + os.environ["KS_CUBE_TAG"]
        logf.close()
        logf = open(os.path.join(ROOT, "logs", tag + ".log"), "a", encoding="utf-8")
    log(f"=== ksmaster k={k} case={case} workers={workers} fix_in={fix_in} fix_out={fix_out}")
    ms = Master(core, k, sym=sym, log=log, workers=workers, fix_in=fix_in, fix_out=fix_out)
    if kind in ("box", "box3") and os.environ.get("KS_SYMBREAK", "1") == "1":
        d = core.d
        if case == "-":
            groups = [list(range(d))]
        else:
            ins, outs = [], []
            for part in case.split(";"):
                nm, vals = part.split(":")
                (ins if nm == "in" else outs).extend(int(c) for c in vals.split(",") if c != "")
            rest = [j for j in range(d) if j not in ins and j not in outs]
            groups = [g for g in (ins, outs, rest) if len(g) > 1]
            # the sign rule uses coordinate 0 as pivot, which is fine for any grouping
        ms.symbreak = box_symmetry_breaking(core, groups)
        log(f"symmetry breaking on coordinate groups {groups}")
    if os.environ.get("KS_SEED", "0") != "0":
        ms.seed_cuts(max_pairs=int(os.environ.get("KS_SEED", "0")))
    res = ms.run(max_seconds=secs)
    ms.save_cuts(os.path.join(ROOT, "results", tag + "_cuts.json"))
    log(f"MASTER RESULT {core.name} k={k} case={case}: {res['status']} after {res.get('iterations')} iterations, "
        f"{len(ms.cuts)} cuts")
    if res.get("ks"):
        for v in sorted(res["ks"]):
            log(f"   ray {core.rays[v]}")
