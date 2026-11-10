"""Experiment: how hard is the d=5 candidate problem for different solvers / encodings?"""
import sys, os, time, random, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pools
from kscegar import Cegar
from ksengine import mask, bits, popcount
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType


def run_with_timeout(solver, assumptions, seconds):
    timer = threading.Timer(seconds, lambda: solver.interrupt())
    timer.start()
    r = solver.solve_limited(assumptions=assumptions, expect_interrupt=True)
    timer.cancel()
    return r


k = int(sys.argv[1]) if len(sys.argv) > 1 else 28
rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 3
limit = float(sys.argv[3]) if len(sys.argv) > 3 else 60
full = pools.box_pool(5, 1)
core = full.ks_core()
sym = pools.signed_perm_symmetry(core)
cg = Cegar(core, sym=sym, log=lambda *a: None)
n, nb = core.n, len(core.bases)

# seed cuts: a few optimal colorings + orbits
I = cg.best_coloring_exact((), time_limit=20)
cg.add_cut_orbit(cg.missed(I), I)
print("initial cuts", len(cg.cuts), "missed", len(cg.missed(I)), flush=True)

for rnd in range(rounds):
    # build fresh solvers with the current cuts and test them
    clauses = []
    for b, basis in enumerate(core.bases):
        for v in basis:
            clauses.append([-(n + b + 1), v + 1])
        clauses.append([n + b + 1] + [-(v + 1) for v in basis])      # y <-> AND x
    for v in range(n):
        clauses.append([-(v + 1)] + [n + b + 1 for b in range(nb) if v in core.bases[b]])   # x -> some chosen basis
    for cut in cg.cuts:
        clauses.append([n + b + 1 for b in sorted(cut)])
    results = {}
    S = None
    for enc_name, enc in (("totalizer", EncType.totalizer), ("seqcounter", EncType.seqcounter),
                          ("kmtotalizer", EncType.kmtotalizer), ("cardnetwrk", EncType.cardnetwrk)):
        card = CardEnc.atmost(lits=[v + 1 for v in range(n)], bound=k, top_id=n + nb, encoding=enc)
        for sname in ("g4", "cd15", "mcb"):
            try:
                s = Solver(name=sname, bootstrap_with=clauses + card.clauses)
            except Exception as e:
                results[(enc_name, sname)] = "n/a"
                continue
            t = time.time()
            try:
                r = run_with_timeout(s, [], limit)
            except Exception as e:
                r = "err"
            dt = time.time() - t
            results[(enc_name, sname)] = (r, round(dt, 1))
            if r is True and S is None:
                model = s.get_model()
                S = frozenset(v for v in range(n) if model[v] > 0)
            s.delete()
    print(f"round {rnd}: cuts {len(cg.cuts)}:", results, flush=True)
    if S is None:
        print("no solver produced a candidate; stop")
        break
    I = cg.best_coloring_exact(S, time_limit=20)
    if I is None:
        print("KS set found!", len(S), core.describe(S))
        break
    cut = cg.missed(I)
    fresh = cg.add_cut_orbit(cut, I)
    print(f"   candidate {len(S)} rays colorable; new cut misses {len(cut)} bases, +{fresh}", flush=True)
