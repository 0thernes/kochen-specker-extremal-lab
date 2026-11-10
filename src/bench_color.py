"""Benchmark: best coloring (fewest missed bases) of a whole 3D integer pool, RC2 vs CP-SAT."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pools3d
from ksengine import bits, mask
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2, RC2Stratified


def rc2_best(pool, forced_bases=(), stratified=False):
    n = pool.n
    w = WCNF()
    for v in range(n):
        for u in bits(pool.adj[v] >> (v + 1) << (v + 1)):
            w.append([-(v + 1), -(u + 1)])
    fb = set(forced_bases)
    for i, b in enumerate(pool.bases):
        cl = [x + 1 for x in b]
        if i in fb:
            w.append(cl)
        else:
            w.append(cl, weight=1)
    cls = RC2Stratified if stratified else RC2
    with cls(w, solver="g4", adapt=True, exhaust=True, minz=True) as r:
        model = r.compute()
        if model is None:
            return None, None
        I = frozenset(v for v in range(n) if model[v] > 0)
        return I, r.cost


for H in map(int, sys.argv[1:]):
    pool = pools3d.build_box3(H, log=lambda *a: None)
    t = time.time()
    I, cost = rc2_best(pool)
    print(f"H={H}: {pool.n} rays, {len(pool.bases)} triples; RC2 min missed = {cost} in {time.time()-t:.2f}s", flush=True)
