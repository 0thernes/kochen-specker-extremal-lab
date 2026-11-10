"""Exploration of the {0,+1,-1}^5 pool: correction-set structure and timings."""
import sys, os, time, itertools, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pools
from ksengine import Pool, Symmetry, HittingSets, mask, bits, popcount
from ortools.sat.python import cp_model


def min_correction_cpsat(pool, forced_in=(), forbid=(), workers=8, limit=None, time_limit=60):
    m = cp_model.CpModel()
    c = [m.NewBoolVar(f"c{v}") for v in range(pool.n)]
    a = [m.NewBoolVar(f"a{v}") for v in range(pool.n)]
    for v in range(pool.n):
        for w in bits(pool.adj[v] >> (v + 1) << (v + 1)):
            m.AddBoolOr([c[v].Not(), c[w].Not()])
    for b in pool.bases:
        m.AddBoolOr([c[x] for x in b] + [a[x].Not() for x in b])
    for v in forced_in:
        m.Add(a[v] == 1)
    removed = sum(1 - a[v] for v in range(pool.n))
    if limit is not None:
        m.Add(removed <= limit)
    for D in forbid:
        # exclude this exact correction set and its supersets
        m.AddBoolOr([a[v] for v in D])
    m.Minimize(removed)
    s = cp_model.CpSolver()
    s.parameters.num_search_workers = workers
    s.parameters.max_time_in_seconds = time_limit
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, s.StatusName(st)
    D = frozenset(v for v in range(pool.n) if not s.Value(a[v]))
    return D, s.StatusName(st)


if __name__ == "__main__":
    d = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    H = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    full = pools.box_pool(d, H)
    core = full.ks_core()
    sym = pools.signed_perm_symmetry(core)
    t = time.time()
    D, st = min_correction_cpsat(core)
    print("min correction set", len(D), st, f"{time.time()-t:.2f}s", [core.rays[v] for v in sorted(D)])
    orb = sym.orbit(D, cap=100000)
    print("orbit size", len(orb))
    # enumerate all minimum correction sets up to symmetry
    reps = [D]
    known = set(orb)
    while True:
        t = time.time()
        D2, st = min_correction_cpsat(core, forbid=known, limit=len(D))
        if D2 is None:
            print("no further correction set of size <=", len(D), st, f"{time.time()-t:.2f}s")
            break
        o = sym.orbit(D2, cap=100000)
        known |= o
        reps.append(D2)
        print("another class, size", len(D2), "orbit", len(o), [core.rays[v] for v in sorted(D2)], f"{time.time()-t:.2f}s")
    hs = HittingSets(core.n, backend="cpsat")
    for T in known:
        hs.add(T)
    t = time.time()
    Hs = hs.minimum()
    print("hitting set of all minimum correction sets:", len(Hs), f"{time.time()-t:.2f}s", "KS?", core.is_ks(Hs))
    # iterate a few rounds of minimum cuts disjoint from H
    for rnd in range(40):
        t = time.time()
        D3, st = min_correction_cpsat(core, forced_in=Hs)
        t1 = time.time() - t
        if D3 is None:
            print("H is KS", st)
            break
        o = sym.orbit(D3, cap=100000)
        for T in o:
            if T not in known:
                known.add(T)
                hs.add(T)
        t = time.time()
        Hs = hs.minimum()
        print(f"round {rnd}: cut size {len(D3)} ({t1:.2f}s), orbit {len(o)}, total {len(known)}, hitting set {len(Hs)} ({time.time()-t:.2f}s)", flush=True)
        if core.is_ks(Hs):
            print("KS set of size", len(Hs), core.describe(Hs))
            for v in sorted(Hs):
                print("  ", core.rays[v])
            break
