"""ksdfs.py - exhaustive decision "does the pool contain a KS set with at most k rays?"

Search tree.  A node is (S, F): S is a union of bases (the rays chosen so
far) and F a set of bases that the final set must NOT contain.  Let
  Rel(S, F) = { bases b not in F with |S u b| <= k and S u b containing no basis of F }.
Any KS set T with S <= T, |T| <= k and no basis of F inside T has all of its
bases in Rel(S, F) (plus bases inside S).

At a node we look for a set I of pairwise non-orthogonal rays that hits every
basis inside S and as many bases of Rel as possible; let R be the bases of
Rel that I misses.
  * If no I hits all bases inside S, S itself is a KS set: report it.
  * Otherwise every admissible KS extension T must contain a basis of R
    (else I colors T).  Branch on which one: child i gets S u r_i and
    F u {r_1, ..., r_{i-1}}.
If R is empty the node is closed.  The root uses the symmetry group: once
"some KS set of size <= k contains basis b" is refuted with F empty of
unrelated restrictions, it is refuted for every image of b, so the whole
orbit of b is added to F.

Every leaf closure is justified by an explicit independent set, so the run
can emit a certificate tree that a separate checker replays.
"""
from __future__ import annotations

import sys
import time

from pysat.solvers import Solver

from ksengine import bits, mask, popcount


class KSDfs:
    def __init__(self, pool, k, sym=None, log=print, certificate=False, max_seconds=None):
        self.pool = pool
        self.k = k
        self.n = pool.n
        self.d = pool.d
        self.bases = pool.bases
        self.nb = len(self.bases)
        self.bm = [mask(b) for b in self.bases]
        self.log = log
        self.t0 = time.time()
        self.max_seconds = max_seconds
        self.nodes = 0
        self.sat_calls = 0
        self.found = None
        self.certificate = [] if certificate else None
        # SAT model: c_v = v+1 ; h_b = n+b+1 (basis b must be hit)
        self.sat = Solver(name="g4")
        for v in range(self.n):
            for w in bits(pool.adj[v] >> (v + 1) << (v + 1)):
                self.sat.add_clause([-(v + 1), -(w + 1)])
        for b, basis in enumerate(self.bases):
            self.sat.add_clause([-(self.n + b + 1)] + [x + 1 for x in basis])
        # orbits of bases under the symmetry group (for the root)
        self.orbit_of = None
        if sym is not None and sym.gens:
            index = {b: i for i, b in enumerate(self.bases)}
            bperms = [[index[tuple(sorted(g[v] for v in b))] for b in self.bases] for g in sym.gens]
            orb = [-1] * self.nb
            norb = 0
            for s in range(self.nb):
                if orb[s] >= 0:
                    continue
                orb[s] = norb
                stack = [s]
                while stack:
                    x = stack.pop()
                    for bp in bperms:
                        y = bp[x]
                        if orb[y] < 0:
                            orb[y] = norb
                            stack.append(y)
                norb += 1
            self.orbit_of = orb
            self.norbits = norb
            log(f"{pool.name}: {self.nb} bases in {norb} orbits under the symmetry group")

    def hvar(self, b):
        return self.n + b + 1

    def solve(self, required):
        self.sat_calls += 1
        ok = self.sat.solve(assumptions=[self.hvar(b) for b in required])
        if ok:
            model = self.sat.get_model()
            return True, mask(v for v in range(self.n) if model[v] > 0)
        core = self.sat.get_core() or []
        return False, [l - self.n - 1 for l in core]

    def relevant(self, Sm, F, Fm_list):
        """Bases outside F that fit in the budget and do not complete a forbidden basis."""
        k = self.k
        out = []
        for b in range(self.nb):
            if b in F:
                continue
            U = Sm | self.bm[b]
            if U == Sm:
                continue          # already inside S (handled as "inside")
            if popcount(U) > k:
                continue
            bad = False
            for fm in Fm_list:
                if fm & U == fm:
                    bad = True
                    break
            if not bad:
                out.append(b)
        return out

    def node(self, Sm, F, depth):
        """Returns True if a KS set was found below this node."""
        self.nodes += 1
        if self.max_seconds and time.time() - self.t0 > self.max_seconds:
            raise TimeoutError
        inside = [b for b in range(self.nb) if self.bm[b] & Sm == self.bm[b]]
        # a forbidden basis inside S cannot happen (children are filtered)
        Fm_list = [self.bm[f] for f in F]
        rel = self.relevant(Sm, F, Fm_list)
        removed = []
        relset = list(rel)
        while True:
            ok, res = self.solve(inside + relset)
            if ok:
                Im = res
                break
            core = res
            cand = [b for b in core if not (self.bm[b] & Sm == self.bm[b])]
            if not cand:
                # the bases inside S alone cannot be hit: S is a KS set
                self.found = Sm
                return True
            # drop the core basis that is most expensive to add
            cand.sort(key=lambda b: (-popcount(self.bm[b] & ~Sm), b))
            r = cand[0]
            removed.append(r)
            relset = [b for b in relset if b != r]
        # try to put removed bases back (keeps the branching set inclusion-minimal)
        kept = []
        for r in list(removed):
            trial = inside + relset + [r]
            ok, res = self.solve(trial)
            if ok:
                relset.append(r)
                Im = res
            else:
                kept.append(r)
        branch = sorted(kept, key=lambda b: (popcount(self.bm[b] & ~Sm), b))
        if self.certificate is not None:
            self.certificate.append((depth, Sm, sorted(F) if depth else None, Im, branch))
        if not branch:
            return False
        F2 = set(F)
        for i, r in enumerate(branch):
            if depth == 0 and self.orbit_of is not None:
                if r in F2:
                    continue      # its orbit was already refuted
            S2 = Sm | self.bm[r]
            # skip if S2 completes a forbidden basis (possible after F grew)
            if any((self.bm[f] & S2) == self.bm[f] for f in F2):
                continue
            if depth == 0:
                self.log(f"[{time.time()-self.t0:8.1f}s] root branch {i+1}/{len(branch)}: basis {r} "
                         f"(orbit {self.orbit_of[r] if self.orbit_of else '-'}), nodes so far {self.nodes}")
            if self.node(S2, F2, depth + 1):
                return True
            if depth == 0 and self.orbit_of is not None:
                o = self.orbit_of[r]
                F2 |= {b for b in range(self.nb) if self.orbit_of[b] == o}
            else:
                F2.add(r)
        return False

    def run(self):
        try:
            found = self.node(0, set(), 0)
        except TimeoutError:
            self.log(f"[{time.time()-self.t0:8.1f}s] TIMEOUT after {self.nodes} nodes")
            return {"status": "timeout", "nodes": self.nodes}
        dt = time.time() - self.t0
        if found:
            S = list(bits(self.found))
            self.log(f"[{dt:8.1f}s] FOUND a KS set with {len(S)} rays ({self.nodes} nodes): {self.pool.describe(S)}")
            return {"status": "found", "ks": frozenset(S), "nodes": self.nodes}
        self.log(f"[{dt:8.1f}s] EXHAUSTED: no KS set with at most {self.k} rays in {self.pool.name} "
                 f"({self.nodes} nodes, {self.sat_calls} SAT calls)")
        return {"status": "none", "nodes": self.nodes}


def build(kind, args, log=print):
    import pools
    if kind == "box":
        full = pools.box_pool(int(args[0]), int(args[1]), log=log)
        core = full.ks_core(log=log)
        return core, pools.signed_perm_symmetry(core)
    if kind == "boxfull":                 # the whole pool, without the reduction to the core
        full = pools.box_pool(int(args[0]), int(args[1]), log=log)
        return full, pools.signed_perm_symmetry(full)
    if kind == "box3":
        import pools3d
        core = pools3d.build_box3(int(args[0]), log=log)
        return core, pools3d.cube_symmetry(core)
    if kind == "roots":
        import cyclo
        full = cyclo.root_pool(int(args[0]), int(args[1]), log=log)
        core = full.ks_core(log=log)
        return core, cyclo.root_symmetry(core, int(args[1]))
    if kind == "e8":
        full = pools.e8_pool(log=log)
        core = full.ks_core(log=log)
        return core, pools.e8_symmetry(core)
    raise SystemExit("unknown kind")


if __name__ == "__main__":
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.setrecursionlimit(10000)
    k = int(sys.argv[1])
    secs = float(sys.argv[2]) if sys.argv[2] != "-" else None
    kind = sys.argv[3]
    args = sys.argv[4:]
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tag = "dfs_" + "_".join([kind] + args) + f"_k{k}"
    logf = open(os.path.join(ROOT, "logs", tag + ".log"), "a", encoding="utf-8")

    def log(msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    core, sym = build(kind, args, log)
    dfs = KSDfs(core, k, sym=sym, log=log, max_seconds=secs)
    res = dfs.run()
    if res.get("ks"):
        for v in sorted(res["ks"]):
            log(f"   ray {core.rays[v]}")
