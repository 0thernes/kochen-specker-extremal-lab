"""gen_cert.py - produce and independently re-check a tree certificate for
"every set of at most k rays of the pool is colorable".

Certificate (JSON):
  rays      list of integer vectors (the pool, in index order)
  d, k
  adj       list of neighbour-index lists (orthogonal partners)
  bases     list of d-tuples of ray indices (all bases of the pool)
  tree      nested node  [I, [[r_1, child_1], [r_2, child_2], ...]]
            I = list of ray indices (pairwise non-orthogonal),
            r_j = index of a basis, child_j = node

Checker rule at a node with state (S, F)  (S a set of rays, F a list of bases):
  0. if some basis of F lies inside S: accept (no admissible set contains S).
  1. I is pairwise non-orthogonal.
  2. every basis b that contains no ray of I satisfies one of
        (a) |S u b| > k,
        (b) some basis of F lies inside S u b,
        (c) b is one of r_1, ..., r_m.
  3. for each j the child_j is accepted in state (S u r_j, F + [r_1..r_{j-1}]).
Soundness: by induction, every set T with S <= T, |T| <= k that contains no
basis of F is colorable.  At the root S and F are empty.

usage: python gen_cert.py <k> <out.json> <kind> [args...]
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.setrecursionlimit(100000)

from ksdfs import KSDfs, build
from ksengine import bits, mask, popcount


class CertDfs(KSDfs):
    """KSDfs without symmetry that records the full tree."""

    def tree(self, Sm, F):
        """Return the certificate node for state (Sm, F) or raise if a KS set is found."""
        self.nodes += 1
        # rule 0: a forbidden basis already inside S
        for f in F:
            if self.bm[f] & Sm == self.bm[f]:
                return [[], []]
        Fm_list = [self.bm[f] for f in F]
        Fset = set(F)
        inside = [b for b in range(self.nb) if self.bm[b] & Sm == self.bm[b]]
        rel = self.relevant(Sm, Fset, Fm_list)
        removed = []
        relset = list(rel)
        while True:
            ok, res = self.solve(inside + relset)
            if ok:
                Im = res
                break
            cand = [b for b in res if not (self.bm[b] & Sm == self.bm[b])]
            if not cand:
                raise RuntimeError("KS set found: " + str(sorted(bits(Sm))))
            cand.sort(key=lambda b: (-popcount(self.bm[b] & ~Sm), b))
            removed.append(cand[0])
            relset = [b for b in relset if b != cand[0]]
        kept = []
        for r in list(removed):
            ok, res = self.solve(inside + relset + [r])
            if ok:
                relset.append(r)
                Im = res
            else:
                kept.append(r)
        branch = sorted(kept, key=lambda b: (popcount(self.bm[b] & ~Sm), b))
        children = []
        F2 = list(F)
        for r in branch:
            children.append([r, self.tree(Sm | self.bm[r], F2)])
            F2 = F2 + [r]
        return [sorted(bits(Im)), children]


def check(cert):
    """Independent re-check of the TREE of a certificate (shares no code with the search).

    It takes the orthogonality lists and the list of bases from the certificate as given.  That
    these lists are right for the listed vectors is a separate check, check_pool(); a certificate is
    accepted only if both pass (the command line below, scripts/run_all.py and the JavaScript
    verifier all require both)."""
    k = cert["k"]
    n = len(cert["rays"])
    adj = [set(a) for a in cert["adj"]]
    bases = [tuple(b) for b in cert["bases"]]
    count = 0

    def node(nd, S, F):
        nonlocal count
        count += 1
        I, children = nd
        # malformed references are a rejection, not a crash
        if any(not (0 <= v < n) for v in I) or any(not (0 <= c[0] < len(bases)) for c in children):
            return False
        for f in F:
            if set(bases[f]) <= S:
                return True
        Iset = set(I)
        for v in I:
            if adj[v] & Iset:
                return False
        child_bases = [c[0] for c in children]
        for bi, b in enumerate(bases):
            if Iset.intersection(b):
                continue
            U = S | set(b)
            if len(U) > k:
                continue
            if any(set(bases[f]) <= U for f in F):
                continue
            if bi in child_bases:
                continue
            return False
        F2 = list(F)
        for r, ch in children:
            if not node(ch, S | set(bases[r]), F2):
                return False
            F2 = F2 + [r]
        return True

    ok = node(cert["tree"], set(), [])
    return ok, count


def check_pool(cert):
    """Re-derive adjacency and bases from the integer vectors."""
    rays = [tuple(r) for r in cert["rays"]]
    d = cert["d"]
    n = len(rays)
    adj = [[j for j in range(n) if j != i and sum(a * b for a, b in zip(rays[i], rays[j])) == 0]
           for i in range(n)]
    if adj != [sorted(a) for a in cert["adj"]]:
        return False
    import itertools
    aset = [set(a) for a in adj]
    bases = []

    def rec(cl, cand):
        if len(cl) == d:
            bases.append(tuple(cl))
            return
        for v in cand:
            rec(cl + [v], [w for w in cand if w > v and w in aset[v]])

    rec([], list(range(n)))
    return sorted(bases) == sorted(tuple(b) for b in cert["bases"])


if __name__ == "__main__":
    k = int(sys.argv[1])
    out = sys.argv[2]
    kind = sys.argv[3]
    args = sys.argv[4:]
    core, sym = build(kind, args, log=lambda *a: None)
    t0 = time.time()
    dfs = CertDfs(core, k, sym=None, log=lambda *a: None)
    tree = dfs.tree(0, [])
    cert = {
        "pool": core.name, "d": core.d, "k": k,
        "rays": [list(r) for r in core.rays],
        "adj": [sorted(bits(a)) for a in core.adj],
        "bases": [list(b) for b in core.bases],
        "tree": tree,
    }
    with open(out, "w") as f:
        json.dump(cert, f)
    ok, count = check(cert)
    okp = check_pool(cert) if isinstance(core.rays[0][0], int) else None
    print(f"{core.name}: k={k}: tree with {dfs.nodes} nodes in {time.time()-t0:.1f}s; "
          f"re-check: tree ok={ok} ({count} nodes), pool ok={okp}; file {os.path.getsize(out)} bytes")
    if not ok or okp is False:
        sys.exit(1)
    if okp is None:
        print("warning: the pool lists were NOT re-checked (not an integer pool); "
              "this file is not a complete certificate")
        sys.exit(2)
