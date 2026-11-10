#!/usr/bin/env python3
"""
build_site_data.py - prepares docs/data/ for the static site (docs/index.html).

  python scripts/build_site_data.py

What it does
  1. writes docs/data/results.json from the hand-maintained tables below (RESULTS, STATUS_LEGEND,
     NOT_ACHIEVED, OPEN_PROBLEM). results/RESULTS.md is the register of record: when a row changes
     there, change it HERE and run this script again; the page reads only results.json.
  2. copies, byte for byte, the small JSON files the explorer needs from results/.
  3. writes docs/data/ks18_box4_H1.json: an 18-ray Kochen-Specker set inside the 40-ray pool of
     cert_box4_H1_k17.json. The candidate is the mask `ksSet` of lean/KS/Box4H1.lean; it is checked
     here with the project's SAT model (src/ksengine.py). If the Lean file is missing or the check
     fails, a set is searched for with Pool.shrink.
  4. writes docs/data/manifest.json with the SHA-256 and byte size of every data file. The page
     recomputes these hashes in the browser and refuses to report PASS for a file that differs.
"""
import hashlib, json, os, random, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results")
DATA = os.path.join(ROOT, "docs", "data")

# =============================================================================================
# HAND-MAINTAINED: the results shown on the site.  Keep in step with results/RESULTS.md.
#
#   status   list of status words (see STATUS_LEGEND); "in progress" marks a row that is not final
#   minimum  text shown in the "minimum KS set" column
#   final    False while any part of the row is pending; such rows are shown as provisional
# =============================================================================================
# Row A9 depends on the proof checks of the 81 sub-cases of the five-axis case: read their verdict
# from results/d5_cubes_certification.json, so that the row is final exactly when all 81 are VERIFIED.
def _cube_verdict():
    try:
        with open(os.path.join(RESULTS_DIR, "d5_cubes_certification.json"), encoding="utf-8") as f:
            d = json.load(f)
        n = sum(1 for r in d.get("records", []) if r.get("status") == "VERIFIED")
        return n, d.get("cubes", 81)
    except (OSError, ValueError):
        return 0, 81


_N_CUBES_VERIFIED, _N_CUBES = _cube_verdict()
SITE_A9_FINAL = _N_CUBES_VERIFIED == _N_CUBES
SITE_A9_STATUS = ["two engines", "proof-checked"] if SITE_A9_FINAL else ["two engines", "in progress"]
SITE_A9_CUBES = ("all %d proofs verified" % _N_CUBES if SITE_A9_FINAL
                 else "%d of %d proofs verified so far" % (_N_CUBES_VERIFIED, _N_CUBES))

RESULTS = [
    dict(id="A1", d=3, pool="integer coordinates, largest entry 2", rays=49, core=49, bases=26,
         minimum="31", status=["Lean", "tree", "two engines", "proof-checked"], final=True,
         note="Lean theorem KS.Box3H2.minimum_ks_size_vectors, stated for the integer vectors; tree certificate of "
              "255 nodes, replayable below. Exactly six sets of 31 rays, one orbit.",
         in_browser=True),
    dict(id="A2", d=3, pool="integer coordinates, largest entry 3", rays=145, core=97, bases=50,
         minimum="31", status=["tree", "two engines", "proof-checked"], final=True,
         note="Tree certificate of 11 330 nodes for the whole 145-ray pool. Exactly six sets of 31 rays, one orbit."),
    dict(id="A3", d=3, pool="integer coordinates, largest entry 4", rays=289, core=205, bases=110,
         minimum="31", status=["two engines", "proof-checked"], final=True,
         note="CP-SAT and Glucose agree; the Glucose proof (443 604 lemmas) was checked. "
              "Exactly six sets of 31 rays, one orbit."),
    dict(id="A4", d=3, pool="entries 0 or 6th roots of unity", rays=57, core=57, bases=22,
         minimum="33", status=["two engines", "proof-checked"], final=True,
         note="Exhaustive tree search in Python (1 456 nodes), CP-SAT, and a checked Glucose proof that the "
              "three sets of 33 rays (one orbit) are the only KS sets with at most 33 rays."),
    dict(id="A5", d=3, pool="entries 0 or 12th roots of unity", rays=183, core=183, bases=67,
         minimum="33", status=["two engines", "proof-checked"], final=True,
         note="Exactly twelve sets of 33 rays, one orbit."),
    dict(id="A6", d=3, pool="entries 0 or 18th roots of unity", rays=381, core=381, bases=136,
         minimum="33", status=["two engines", "proof-checked"], final=True,
         note="The Glucose proof (367 001 lemmas) was checked."),
    dict(id="A7", d=3, pool="entries 0 or 24th roots of unity", rays=651, core=651, bases=229,
         minimum="33", status=["two engines", "proof-checked"], final=True,
         note="CP-SAT, and CaDiCaL on the Boolean formula (Glucose ran out of memory on this pool); "
              "the CaDiCaL proof (1 464 683 lemmas) was checked."),
    dict(id="A8", d=4, pool="entries 0, +1, -1", rays=40, core=40, bases=32,
         minimum="18", status=["Lean", "tree", "two engines", "proof-checked"], final=True,
         note="Lean theorem KS.Box4H1.minimum_ks_size_vectors, stated for the integer vectors; tree certificate of "
              "509 nodes, replayable below. The 16 minimum sets are the 16 known sets inside the 24 rays of Peres.",
         in_browser=True),
    dict(id="A9", d=5, pool="entries 0, +1, -1", rays=121, core=105, bases=136,
         minimum="29", status=SITE_A9_STATUS, final=SITE_A9_FINAL,
         note="Three cases by the number of coordinate axes in the set. All three are closed by Glucose and, on "
              "the same formulas, by CaDiCaL; the proofs of the three-axis and four-axis cases were checked, and "
              "the five-axis case is split into 81 sub-cases with one proof each (" + SITE_A9_CUBES + "). "
              "Engine A (CP-SAT) closed only the three-axis case; 'two engines' here means the SAT solvers Glucose and "
              "CaDiCaL. The value 29 was reported before as the smallest set generated from these coordinates, "
              "without proof."),
]

STATUS_LEGEND = [
    ["Lean", "the statement is proved in Lean 4 and checked by the Lean kernel"],
    ["proof-checked", "an unsatisfiability proof (DRUP) from a SAT solver was checked by the small C checker verify/drup_check"],
    ["two engines", "two independent solvers gave the same answer"],
    ["tree", "a search-tree certificate was replayed by the independent JavaScript verifier"],
    ["one engine", "one program gave the answer; no independent check yet"],
    ["in progress", "not finished; the number is not yet established"],
    ["search only", "randomised search; no proof that nothing smaller exists (not used in the table above)"],
]

NOT_ACHIEVED = [
    "No Kochen-Specker set smaller than a published one was found in any dimension.",
    "Integer coordinates up to 5 in dimension 3: the exact search did not finish; no claim.",
    "Coordinates 0 or 30th roots of unity in dimension 3: stopped unfinished; no claim.",
    "Lean proof for integer coordinates up to 3: the kernel check was stopped after 49 minutes; nothing claimed.",
    "Dimension 6 with cube roots of unity (is 21 optimal there?) and the E8 pool in dimension 8 (is 34 optimal there?): not decided.",
    "The general problem (any rays in dimension 3: between 24 and 31; dimensions 5 and above: between 18 and the smallest known sets) is untouched by results about pools.",
]

OPEN_PROBLEM = dict(dimension=3, lower_bound=24, upper_bound=31)

# files copied unchanged from results/ to docs/data/
COPIES = ["cert_box3_H2_k30.json", "cert_box4_H1_k17.json", "ks31_box3_H2.json", "stack_demo.json",
          "verify_summary.json"]
# =============================================================================================


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def write_json(path, obj, compact=False):
    text = json.dumps(obj, separators=(",", ":")) if compact else json.dumps(obj, indent=1, ensure_ascii=False)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def find_ks18():
    """An 18-ray KS set of the 40-ray pool, as (sorted list of pool indices, description of the source)."""
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from ksengine import Pool            # project code (needs python-sat)
    from pools import int_orth

    cert = json.load(open(os.path.join(RESULTS_DIR, "cert_box4_H1_k17.json"), encoding="utf-8"))
    rays = [tuple(r) for r in cert["rays"]]
    quiet = lambda *a, **k: None
    pool = Pool.from_vectors(rays, cert["d"], int_orth, name="box(d=4,H=1)", log=quiet)
    assert [sorted(a) for a in cert["adj"]] == [[j for j in range(pool.n) if (pool.adj[i] >> j) & 1] for i in range(pool.n)]
    assert sorted(tuple(sorted(b)) for b in cert["bases"]) == pool.bases
    want = cert["k"] + 1

    lean = os.path.join(ROOT, "lean", "KS", "Box4H1.lean")
    if os.path.exists(lean):
        src = open(lean, encoding="utf-8").read()
        m = re.search(r"def ksSet : Nat := (0x[0-9a-fA-F]+)", src)
        lean_rays = re.search(r"def rays : List \(List Int\) := \[(.*?)\]\]", src, flags=re.S)
        if m and lean_rays:
            listed = [tuple(int(x) for x in v.split(",")) for v in re.findall(r"\[([-0-9, ]+)\]", lean_rays.group(1) + "]")]
            mask = int(m.group(1), 16)
            S = [i for i in range(pool.n) if (mask >> i) & 1]
            if listed == rays and len(S) == want and pool.is_critical(S):
                return pool, S, "mask ksSet = %s of lean/KS/Box4H1.lean (same ray order as cert_box4_H1_k17.json)" % m.group(1)
            print("warning: the Lean mask did not pass the check here; searching instead")
    for seed in range(500):
        S = sorted(pool.shrink(range(pool.n), rng=random.Random(seed)))
        if len(S) == want and pool.is_critical(S):
            return pool, S, "found by Pool.shrink (src/ksengine.py), seed %d" % seed
    raise SystemExit("no %d-ray KS set found in the 40-ray pool" % want)


def register_rows():
    """Section A of results/RESULTS.md: row id -> (rays, core, bases, minimum)."""
    rows = {}
    with open(os.path.join(RESULTS_DIR, "RESULTS.md"), encoding="utf-8") as f:
        for line in f:
            m = re.match(r"\|\s*(A\d+)\s*\|[^|]*\|\s*(\d+)\s*\((\d+)\)\s*\|\s*(\d+)\s*\|\s*\*\*(\d+)\*\*\s*\|", line)
            if m:
                rows[m.group(1)] = tuple(int(x) for x in m.groups()[1:])
    return rows


def check_against_register():
    """The hand-maintained list must agree with the register on every number it repeats."""
    reg = register_rows()
    problems = []
    if sorted(reg) != sorted(r["id"] for r in RESULTS):
        problems.append("row ids differ: register %s, site %s" % (sorted(reg), sorted(r["id"] for r in RESULTS)))
    for r in RESULTS:
        want = reg.get(r["id"])
        if want is None:
            continue
        have = (r["rays"], r["core"], r["bases"])
        if have != want[:3]:
            problems.append("%s: rays/core/bases %s here, %s in the register" % (r["id"], have, want[:3]))
        if not re.match(r"%d\b" % want[3], r["minimum"]):
            problems.append("%s: minimum %r here, %d in the register" % (r["id"], r["minimum"], want[3]))
    if problems:
        raise SystemExit("site data disagree with results/RESULTS.md:\n  " + "\n  ".join(problems))
    print("site rows agree with section A of results/RESULTS.md (%d rows)" % len(reg))


def main():
    os.makedirs(DATA, exist_ok=True)
    produced = {}

    # 1. results table
    check_against_register()
    for r in RESULTS:
        r.setdefault("in_browser", False)
    write_json(os.path.join(DATA, "results.json"), dict(
        source="results/RESULTS.md (register of record); edited by hand in scripts/build_site_data.py",
        open_problem=OPEN_PROBLEM, status_legend=STATUS_LEGEND, rows=RESULTS, not_achieved=NOT_ACHIEVED))
    produced["results.json"] = "scripts/build_site_data.py (hand-maintained list)"

    # 2. copies
    for name in COPIES:
        src = os.path.join(RESULTS_DIR, name)
        if not os.path.exists(src):
            raise SystemExit("missing input: " + src)
        shutil.copyfile(src, os.path.join(DATA, name))
        produced[name] = "results/" + name

    # 3. the 18-ray set
    pool, S, how = find_ks18()
    write_json(os.path.join(DATA, "ks18_box4_H1.json"), dict(
        name="18-ray Kochen-Specker set inside the 40-ray pool (d = 4, entries 0, +1, -1)",
        d=4, rays=[list(pool.rays[i]) for i in S], pool_indices=S, source=how), compact=True)
    produced["ks18_box4_H1.json"] = "scripts/build_site_data.py: " + how
    print("ks18:", pool.describe(S), "|", how)

    # 4. manifest
    files = {}
    for name in sorted(produced):
        path = os.path.join(DATA, name)
        raw = open(path, "rb").read()
        if b"\r" in raw:
            print("warning: %s contains carriage returns; a git end-of-line conversion would change its hash" % name)
        files[name] = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), source=produced[name])
    write_json(os.path.join(DATA, "manifest.json"), dict(algorithm="SHA-256", files=files))
    for name, info in files.items():
        print("%s  %8d  %s" % (info["sha256"], info["bytes"], name))
    print("wrote", os.path.join(DATA, "manifest.json"))


if __name__ == "__main__":
    main()
