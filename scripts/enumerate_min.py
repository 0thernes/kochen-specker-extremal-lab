"""enumerate_min.py - list ALL KS sets with exactly k rays in a pool (k = the
minimum), then sort them into orbits under the pool's symmetries and into
isomorphism classes of orthogonality graphs.

Uses the candidate problem of ksmaster.py without symmetry breaking; every KS
set found is excluded by a clause and the search continues until the problem
is infeasible.  The count is therefore exhaustive for critical KS sets with at
most k rays, which for k = minimum means all KS sets of that size.

usage: python -u scripts/enumerate_min.py <k> <kind> [args...]
"""
from __future__ import annotations

import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from ortools.sat.python import cp_model

from ksdfs import build
from ksengine import bits, mask
from ksmaster import Master


def main():
    k = int(sys.argv[1])
    kind = sys.argv[2]
    args = sys.argv[3:]
    quiet = lambda *a: None
    pool, sym = build(kind, args, log=quiet)
    ms = Master(pool, k, sym=sym, log=quiet, workers=6)
    I = ms.best_coloring(())
    ms.add_cut_orbit(ms.missed(I), I)
    found = []
    blocked = []
    t0 = time.time()

    def candidate():
        m = cp_model.CpModel()
        x = [m.NewBoolVar(f"x{v}") for v in range(ms.n)]
        y = [m.NewBoolVar(f"y{b}") for b in range(ms.nb)]
        for b, basis in enumerate(ms.bases):
            for v in basis:
                m.AddImplication(y[b], x[v])
            m.AddBoolOr([y[b]] + [x[v].Not() for v in basis])
        for v in range(ms.n):
            m.AddBoolOr([x[v].Not()] + [y[b] for b in ms.bases_of[v]])
            m.Add(sum(x[w] for w in bits(pool.adj[v])) >= pool.d).OnlyEnforceIf(x[v])
        for cut in ms.cuts:
            m.AddBoolOr([y[b] for b in cut])
        for B in blocked:
            m.AddBoolOr([x[v].Not() for v in B])
        m.Add(sum(x) <= k)
        s = cp_model.CpSolver()
        s.parameters.num_search_workers = 6
        st = s.Solve(m)
        if st == cp_model.INFEASIBLE:
            return None
        assert st in (cp_model.OPTIMAL, cp_model.FEASIBLE)
        return frozenset(v for v in range(ms.n) if s.Value(x[v]))

    while True:
        S = candidate()
        if S is None:
            break
        I = ms.best_coloring(S)
        if I is None:
            # S is KS; it may contain a smaller critical set only if k is not the minimum
            assert len(S) == k, "found a KS candidate with fewer than k rays: k is not the minimum"
            # add the whole orbit at once
            orb = sym.orbit(S, cap=100000) if sym else {S}
            new = [T for T in orb if T not in set(found)]
            found.extend(new)
            blocked.extend(new)
            print(f"[{time.time()-t0:6.1f}s] KS set found; orbit of {len(orb)} sets; total {len(found)}", flush=True)
        else:
            ms.add_cut_orbit(ms.missed(I), I)
    # orbits
    orbits = []
    seen = set()
    for S in found:
        if S in seen:
            continue
        orb = sym.orbit(S, cap=100000) if sym else {S}
        seen |= orb
        orbits.append(sorted(orb, key=lambda T: sorted(T))[0])
    # isomorphism classes of orthogonality graphs
    import networkx as nx
    graphs = []
    for S in orbits:
        G = nx.Graph()
        G.add_nodes_from(S)
        for v in S:
            for w in bits(pool.adj[v]):
                if w in S and w > v:
                    G.add_edge(v, w)
        graphs.append(G)
    classes = []
    for i, G in enumerate(graphs):
        for cl in classes:
            if nx.is_isomorphic(G, graphs[cl[0]]):
                cl.append(i)
                break
        else:
            classes.append([i])
    out = {
        "pool": pool.name, "k": k, "n_sets": len(found), "n_orbits": len(orbits),
        "n_graph_classes": len(classes),
        "orbit_representatives": [[list(pool.rays[v]) for v in sorted(S)] for S in orbits],
        "sets_as_indices": [sorted(S) for S in found],
        "orbit_sizes": [len(sym.orbit(S, cap=100000)) if sym else 1 for S in orbits],
        "edges_per_class": [graphs[cl[0]].number_of_edges() for cl in classes],
        "seconds": round(time.time() - t0, 1),
    }
    tag = "enumerate_" + "_".join([kind] + args) + f"_k{k}"
    with open(os.path.join(ROOT, "results", tag + ".json"), "w") as f:
        json.dump(out, f, indent=1)
    # the cuts (with witnesses) used by the final infeasible problem, for the proof-checked
    # confirmation by engine B:  KS_BLOCKED=results/<tag>.json python src/ks_cnf.py <tag>_cuts.json ...
    ms.save_cuts(os.path.join(ROOT, "results", tag + "_cuts.json"))
    print(f"ENUMERATION {pool.name} k={k}: {len(found)} KS sets, {len(orbits)} orbits under the symmetry group "
          f"(sizes {out['orbit_sizes']}), {len(classes)} isomorphism classes of orthogonality graphs; "
          f"{out['seconds']}s")


if __name__ == "__main__":
    main()
