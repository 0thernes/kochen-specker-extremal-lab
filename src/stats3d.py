import sys, os, time, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pools3d
from ksengine import popcount

for H in map(int, sys.argv[1:]):
    p = pools3d.build_box3(H, log=lambda *a: None)
    deg = [popcount(a) for a in p.adj]
    tcount = [0] * p.n
    for b in p.bases:
        for v in b:
            tcount[v] += 1
    m = sum(deg) // 2
    dd = collections.Counter(min(d, 12) for d in deg)
    td = collections.Counter(min(t, 6) for t in tcount)
    norms = collections.Counter()
    print(f"H={H}: core {p.n} rays, {m} edges, {len(p.bases)} triples; avg deg {2*m/p.n:.2f}; "
          f"deg hist {sorted(dd.items())}; triples-per-ray hist {sorted(td.items())}", flush=True)
