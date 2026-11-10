"""Shared helpers for the test suite.

Everything in here is deliberately independent of the code under test: plain
Python, integer arithmetic, sets and itertools.  The project modules in src/
are only put on the import path; they are never used to compute an expected
value in this file.

The helpers that run external programs never write into the repository.  When
a program insists on writing next to its own sources (ksmaster.py, lemma7.py,
test_verify.mjs) it is run from a byte-identical copy in a temporary
"sandbox" directory with the same layout (src/, scripts/, verify/, results/,
logs/).
"""
from __future__ import annotations

import glob
import itertools
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
SCRIPTS = os.path.join(ROOT, "scripts")
VERIFY = os.path.join(ROOT, "verify")
RESULTS = os.path.join(ROOT, "results")
TESTS = os.path.join(ROOT, "tests")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# CP-SAT worker threads used by the tests (the machine may be busy)
WORKERS = int(os.environ.get("KS_TEST_WORKERS", "2"))
EXE_SUFFIX = ".exe" if os.name == "nt" else ""


def quiet(*args, **kwargs):
    """A log function that discards everything."""


# ----------------------------------------------------------------------------
# independent recomputation of the orthogonality structure of a list of vectors
# ----------------------------------------------------------------------------

def int_dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def int_orth(u, v):
    return int_dot(u, v) == 0


def gauss_orth(u, v):
    """Hermitian orthogonality for vectors of Gaussian integers (re, im)."""
    re = im = 0
    for (a, b), (c, d) in zip(u, v):
        # conj(a + bi) (c + di) = (ac + bd) + (ad - bc) i
        re += a * c + b * d
        im += a * d - b * c
    return re == 0 and im == 0


def orth_pairs(rays, orth):
    """All orthogonal pairs (i, j), i < j, by direct evaluation."""
    return {(i, j) for i, j in itertools.combinations(range(len(rays)), 2) if orth(rays[i], rays[j])}


def neighbour_sets(n, pairs):
    nb = [set() for _ in range(n)]
    for i, j in pairs:
        nb[i].add(j)
        nb[j].add(i)
    return nb


def cliques(nb, d):
    """All d-cliques of the graph given by neighbour sets, as sorted tuples."""
    out = []

    def grow(cl, cand):
        if len(cl) == d:
            out.append(tuple(cl))
            return
        for v in sorted(cand):
            grow(cl + [v], {w for w in cand if w > v and w in nb[v]})

    grow([], set(range(len(nb))))
    out.sort()
    return out


def pool_pairs(pool):
    """Orthogonal pairs (i, j), i < j, as stored in a ksengine.Pool (bit masks)."""
    out = set()
    for i, a in enumerate(pool.adj):
        j = 0
        while a:
            if a & 1:
                out.add((min(i, j), max(i, j)))
            a >>= 1
            j += 1
    return out


def pool_discrepancies(pool, orth):
    """Compare a ksengine.Pool with a from-scratch recomputation.

    Returns a list of human-readable differences (empty when the Pool object
    agrees with the vectors it carries)."""
    problems = []
    rays = [tuple(r) for r in pool.rays]
    if len(set(rays)) != len(rays):
        problems.append("duplicate rays")
    if pool.n != len(rays) or len(pool.adj) != len(rays):
        problems.append("n / adj length mismatch")
        return problems
    for i, a in enumerate(pool.adj):
        if a >> len(rays):
            problems.append(f"adj[{i}] has a bit beyond the last ray")
        if (a >> i) & 1:
            problems.append(f"ray {i} is listed as orthogonal to itself")
    mine = orth_pairs(rays, orth)
    theirs = pool_pairs(pool)
    if mine != theirs:
        problems.append(f"orthogonal pairs differ: {len(mine)} recomputed, {len(theirs)} stored, "
                        f"{len(mine ^ theirs)} in the symmetric difference")
    bases = cliques(neighbour_sets(len(rays), mine), pool.d)
    stored = sorted(tuple(sorted(b)) for b in pool.bases)
    if len(set(stored)) != len(stored):
        problems.append("a basis is listed twice")
    if bases != stored:
        problems.append(f"bases differ: {len(bases)} recomputed, {len(stored)} stored")
    return problems


# ----------------------------------------------------------------------------
# independent colorability deciders (no SAT solver)
# ----------------------------------------------------------------------------

def structure_of(pool):
    """(neighbour sets, list of bases as frozensets) read off a Pool object."""
    nb = neighbour_sets(pool.n, pool_pairs(pool))
    return nb, [frozenset(b) for b in pool.bases]


def valid_coloring(nb, bases, S, ones):
    """Is `ones` (the rays of value 1) a valid coloring of the set S?"""
    S = set(S)
    ones = set(ones)
    if not ones <= S:
        return False
    for v in ones:
        if nb[v] & ones:
            return False
    for b in bases:
        if b <= S and not (b & ones):
            return False
    return True


def colorings_bruteforce(nb, bases, S):
    """Number of valid colorings of S, by enumerating all 2^|S| assignments.

    Local bit masks; ok[f] is filled by dynamic programming over the lowest
    set bit, so every one of the 2^|S| assignments is visited exactly once."""
    S = sorted(S)
    m = len(S)
    if m > 20:
        raise ValueError("brute force is limited to 20 rays")
    pos = {v: i for i, v in enumerate(S)}
    ladj = [0] * m
    for v in S:
        for w in nb[v]:
            if w in pos:
                ladj[pos[v]] |= 1 << pos[w]
    inside = []
    for b in bases:
        if all(x in pos for x in b):
            bmask = 0
            for x in b:
                bmask |= 1 << pos[x]
            inside.append(bmask)
    indep = bytearray(1 << m)
    indep[0] = 1
    count = 0
    for f in range(1 << m):
        if f:
            low = f & -f
            i = low.bit_length() - 1
            indep[f] = 1 if (indep[f ^ low] and not (ladj[i] & f)) else 0
        if indep[f]:
            for bmask in inside:
                if not (bmask & f):
                    break
            else:
                count += 1
    return count


def decide_colorable(nb, bases, S):
    """Exhaustive backtracking: a set of value-1 rays that colors S, or None.

    Branch on a basis inside S that has no ray of value 1 yet: one of its
    still-free rays gets value 1 (its neighbours get value 0)."""
    S = set(S)
    inside = [b for b in bases if b <= S]

    def rec(ones, zeros):
        pick = None
        for b in inside:
            if b & ones:
                continue
            free = b - zeros
            if not free:
                return None
            if pick is None or len(free) < len(pick):
                pick = free
        if pick is None:
            return ones
        z = set(zeros)
        for v in sorted(pick):
            r = rec(ones | {v}, z | (nb[v] & S))
            if r is not None:
                return r
            z.add(v)          # v = 1 is exhausted: v = 0 in the remaining branches
        return None

    return rec(frozenset(), frozenset())


def is_independent(nb, I):
    I = set(I)
    return all(not (nb[v] & I) for v in I)


def missed_bases(bases, I):
    I = set(I)
    return [i for i, b in enumerate(bases) if not (b & I)]


# ----------------------------------------------------------------------------
# data files
# ----------------------------------------------------------------------------

def load_ks31_indices(pool):
    """Indices, in `pool`, of the rays of results/ks31_box3_H2.json."""
    with open(os.path.join(RESULTS, "ks31_box3_H2.json")) as f:
        data = json.load(f)
    index = {tuple(r): i for i, r in enumerate(pool.rays)}
    return [index[tuple(r)] for r in data["rays"]]


# ----------------------------------------------------------------------------
# external tools
# ----------------------------------------------------------------------------

def run(cmd, cwd=None, timeout=600, env=None):
    """Run a command; returns (exit code, combined stdout + stderr)."""
    e = dict(os.environ)
    e.setdefault("PYTHONIOENCODING", "utf-8")
    if env:
        e.update(env)
    try:
        p = subprocess.run(cmd, cwd=cwd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return 124, (exc.stdout or b"").decode("utf-8", "replace") + f"\nTIMEOUT after {timeout}s"
    except OSError as exc:
        return 127, f"cannot run {cmd[0]}: {exc}"
    return p.returncode, p.stdout.decode("utf-8", "replace")


def which(name):
    return shutil.which(name)


def make_sandbox(prefix="ks_sandbox_", with_results=()):
    """A temporary directory with copies of src/, scripts/, verify/ sources and
    tests/test_drup.py, empty results/ and logs/, plus the result files whose
    glob patterns are listed in `with_results`.  The caller removes it."""
    box = tempfile.mkdtemp(prefix=prefix)
    for sub in ("src", "scripts", "verify", "tests", "results", "logs"):
        os.makedirs(os.path.join(box, sub))
    for pattern, sub in (("src/*.py", "src"), ("scripts/*.py", "scripts"), ("verify/*.mjs", "verify"),
                         ("verify/*.c", "verify"), ("tests/test_drup.py", "tests")):
        for path in glob.glob(os.path.join(ROOT, pattern)):
            shutil.copy2(path, os.path.join(box, sub, os.path.basename(path)))
    for pattern in with_results:
        for path in glob.glob(os.path.join(RESULTS, pattern)):
            shutil.copy2(path, os.path.join(box, "results", os.path.basename(path)))
    return box


def drup_binary_in_repo():
    """Path of verify/drup_check[.exe] if it exists and is not older than its source."""
    exe = os.path.join(VERIFY, "drup_check" + EXE_SUFFIX)
    src = os.path.join(VERIFY, "drup_check.c")
    if os.path.isfile(exe) and os.path.getmtime(exe) >= os.path.getmtime(src):
        return exe
    return None


def build_drup(dest_dir):
    """Compile verify/drup_check.c into dest_dir.  Returns (path or None, message)."""
    gcc = which("gcc") or which("cc")
    if gcc is None:
        return None, "no C compiler (gcc / cc) on PATH"
    exe = os.path.join(dest_dir, "drup_check" + EXE_SUFFIX)
    code, out = run([gcc, "-O2", "-o", exe, os.path.join(VERIFY, "drup_check.c")], timeout=300)
    if code != 0 or not os.path.isfile(exe):
        return None, "compilation of verify/drup_check.c failed:\n" + out
    return exe, "built " + exe


def write_cnf(path, nvars, clauses):
    with open(path, "w") as f:
        f.write(f"p cnf {nvars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")


def drup_verified(exe, cnf_path, proof_path):
    code, out = run([exe, cnf_path, proof_path], timeout=300)
    return code == 0 and "s VERIFIED" in out, out
