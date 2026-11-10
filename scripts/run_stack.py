#!/usr/bin/env python3
"""run_stack.py -- one-command driver for the "stack" demonstration of the
31-ray Kochen-Specker (KS) set in results/ks31_box3_H2.json.

Usage:   python scripts/run_stack.py     (from the repository root)
Output:  one PASS/FAIL line per stage on stdout, logs in logs/stack_*.log,
         machine-readable summary in results/stack_demo.json.
Exit:    0 if every stage passed, 1 otherwise.

Stages
  vendor     vendored third-party files present, fingerprinted (SHA-256); the
             mixer block of stack/ks31_qrng.c is compared line by line with the
             vendored upstream source; the rays hard-coded in stack/ks31.esk are
             compared with the JSON file
  reference  exact integer recomputation in Python (this file): orthogonality
             table, bases, exhaustive classical searches
  moonlab    node stack/ks31_moonlab.cjs   (Moonlab WASM state-vector simulator)
  qgtl       gcc build + run of stack/ks31_qgtl.c (QGTL Fubini-Study distance)
  qrng       gcc build + run of stack/ks31_qrng.c (integer mixers, stream)
  eshkol     eshkol-run -r stack/ks31.esk  (exact-integer re-verification)
  cross      cross-language comparison of all key numbers

HONEST LABELLING.  Everything here is classical computation on this machine.
Moonlab is a classical state-vector simulator; the quantum_rng mixers are a
deterministic "quantum-inspired" integer mixer, not quantum randomness; QGTL is
used for one double-precision kernel only; nothing is an experiment on quantum
hardware, and nothing in this script is a formal proof (the formal statements
live in the Lean development, which this script does not touch).
"""
import datetime
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STACK = os.path.join(ROOT, "stack")
THIRD = os.path.join(ROOT, "third_party")
LOGS = os.path.join(ROOT, "logs")
RESULTS = os.path.join(ROOT, "results")
KS_JSON = os.path.join(RESULTS, "ks31_box3_H2.json")
OUT_JSON = os.path.join(RESULTS, "stack_demo.json")

EXPECT_PAIRS = 71
EXPECT_BASES = 17
STREAM_KAT = ["5df9ef9ba7cdcca2", "ddb5674ec90579d9", "e350bb351fce2beb",
              "20275c35a4eaee84", "2f7cdc01c2c0ba7d"]
# eshkol-run is looked up on PATH first; ESHKOL_RUN may name the executable explicitly.
ESHKOL_FALLBACK = os.environ.get("ESHKOL_RUN", "")

stages = []          # list of dicts, in order
summary_lines = []


def say(line):
    print(line, flush=True)
    summary_lines.append(line)


def record(name, ok, detail, data=None, seconds=None):
    entry = {"stage": name, "status": "PASS" if ok else "FAIL", "detail": detail}
    if seconds is not None:
        entry["seconds"] = round(seconds, 2)
    if data is not None:
        entry["data"] = data
    stages.append(entry)
    say("[run_stack] %s  %-9s %s" % ("PASS" if ok else "FAIL", name, detail))
    return ok


def write_log(name, text):
    os.makedirs(LOGS, exist_ok=True)
    path = os.path.join(LOGS, "stack_%s.log" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def run(cmd, logname, timeout, cwd=STACK):
    """Run a command, capture output, write logs/stack_<logname>.log."""
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout)
        rc = p.returncode
        out = p.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        err = p.stderr.decode("utf-8", "replace").replace("\r\n", "\n")
    except subprocess.TimeoutExpired as e:
        rc = -999
        out = (e.stdout or b"").decode("utf-8", "replace")
        err = (e.stderr or b"").decode("utf-8", "replace") + "\nTIMEOUT after %s s" % timeout
    except OSError as e:
        rc, out, err = -998, "", "could not start %r: %s" % (cmd[0], e)
    dt = time.time() - t0
    write_log(logname, "$ %s\n(cwd %s)\n--- stdout ---\n%s\n--- stderr ---\n%s\n--- exit code %d, %.1f s ---\n"
              % (" ".join(cmd), cwd, out, err, rc, dt))
    return rc, out, err, dt


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_tool(name, fallback=None):
    p = shutil.which(name)
    if p is None and fallback and os.path.exists(fallback):
        p = fallback
    return p


def first_line(cmd, timeout=600):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        text = p.stdout.decode("utf-8", "replace").strip().splitlines()
        return text[0].strip() if text else "(no output)"
    except Exception as e:  # noqa: BLE001 - version probing must never abort the run
        return "unavailable (%s)" % type(e).__name__


def kv_lines(text):
    """Parse 'key=value' lines printed by the C programs."""
    d = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z0-9_]+)=(.*)$", line.strip())
        if m:
            d[m.group(1)] = m.group(2).strip()
    return d


# --------------------------------------------------------------------------
# exact integer reference (Python)
# --------------------------------------------------------------------------
def reference(rays):
    n = len(rays)
    dot = [[sum(a * b for a, b in zip(rays[i], rays[j])) for j in range(n)] for i in range(n)]
    orth = [[i != j and dot[i][j] == 0 for j in range(n)] for i in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n) if orth[i][j]]
    bases = [(i, j, k) for (i, j) in pairs for k in range(j + 1, n) if orth[i][k] and orth[j][k]]
    bases_of = [[b for b, t in enumerate(bases) if v in t] for v in range(n)]
    value = [0] * n
    hit = [0] * len(bases)

    def free(v):
        return not any(value[u] and orth[u][v] for u in range(v))

    # (i) every admissible assignment (no two orthogonal rays both 1), no pruning
    stats = {"admissible": 0, "best": -1, "best_count": 0}

    def plain(v, nhit):
        if v == n:
            stats["admissible"] += 1
            if nhit > stats["best"]:
                stats["best"], stats["best_count"] = nhit, 1
            elif nhit == stats["best"]:
                stats["best_count"] += 1
            return
        if free(v):
            value[v] = 1
            add = 0
            for b in bases_of[v]:
                if hit[b] == 0:
                    add += 1
                hit[b] += 1
            plain(v + 1, nhit + add)
            for b in bases_of[v]:
                hit[b] -= 1
            value[v] = 0
        plain(v + 1, nhit)

    plain(0, 0)

    # (ii) the KS search exactly as written in stack/ks31.esk (same node count)
    def ks_search(skip):
        counter = [0]

        def bases_ok(v):
            for b, (i, j, k) in enumerate(bases):
                if b != skip and k < v and value[i] + value[j] + value[k] == 0:
                    return False
            return True

        def search(v):
            counter[0] += 1
            if not bases_ok(v):
                return 0
            if v == n:
                return 1
            total = 0
            if free(v):
                value[v] = 1
                total += search(v + 1)
                value[v] = 0
            return total + search(v + 1)

        return search(0), counter[0]

    ks_solutions, ks_nodes = ks_search(-1)
    relaxed = sum(ks_search(s)[0] for s in range(len(bases)))

    # Fubini-Study distances arccos(|u.v| / (|u||v|)) of the non-orthogonal pairs
    non = [math.acos(abs(dot[i][j]) / math.sqrt(dot[i][i] * dot[j][j]))
           for i in range(n) for j in range(i + 1, n) if not orth[i][j]]
    return {
        "rays": n, "orthogonal_pairs": len(pairs), "bases": len(bases),
        "bases_list": [list(b) for b in bases],
        "classical_max": stats["best"], "admissible_assignments": stats["admissible"],
        "assignments_attaining_max": stats["best_count"],
        "ks_assignments": ks_solutions, "ks_search_nodes": ks_nodes,
        "relaxed_assignments": relaxed,
        "min_nonorthogonal_distance": min(non), "max_nonorthogonal_distance": max(non),
    }


# --------------------------------------------------------------------------
def stage_vendor(rays):
    t0 = time.time()
    problems = []
    needed = {
        "moonlab": ["LICENSE", "PROVENANCE.md", "moonlab.js", "moonlab.wasm"],
        "qgtl": ["LICENSE", "PROVENANCE.md",
                 "src/quantum_geometric/distributed/differential_geometry.c",
                 "include/quantum_geometric/distributed/differential_geometry.h",
                 "stub/cblas.h"],
        "quantum_rng": ["LICENSE", "PROVENANCE.md", "src/quantum_rng/quantum_rng.c",
                        "src/quantum_rng/quantum_rng.h", "src/common/secure_memory.h"],
    }
    fingerprints = {}
    for folder, files in needed.items():
        for rel in files:
            p = os.path.join(THIRD, folder, *rel.split("/"))
            if os.path.isfile(p):
                fingerprints["%s/%s" % (folder, rel)] = sha256(p)
            else:
                problems.append("missing third_party/%s/%s" % (folder, rel))
    own = {}
    for rel in ["ks31_moonlab.cjs", "ks31_qgtl.c", "ks31_qrng.c", "ks31.esk"]:
        p = os.path.join(STACK, rel)
        if os.path.isfile(p):
            own["stack/" + rel] = sha256(p)
        else:
            problems.append("missing stack/%s" % rel)

    # verbatim check: mixer block of ks31_qrng.c versus the vendored upstream lines
    verbatim = False
    try:
        up_path = os.path.join(THIRD, "quantum_rng", "src", "quantum_rng", "quantum_rng.c")
        with open(up_path, encoding="utf-8") as f:
            up = f.read().splitlines()
        wanted = []
        for a, b in [(12, 24), (61, 70), (73, 83), (113, 120)]:      # 1-based, inclusive
            wanted += up[a - 1:b]
        wanted = [x.rstrip() for x in wanted if x.strip()]
        with open(os.path.join(STACK, "ks31_qrng.c"), encoding="utf-8") as f:
            mine = f.read().splitlines()
        b = next(i for i, x in enumerate(mine) if x.startswith("/* ---- BEGIN UPSTREAM"))
        e = next(i for i, x in enumerate(mine) if x.startswith("/* ---- END UPSTREAM"))
        block = [x.rstrip() for x in mine[b + 1:e] if x.strip()]
        verbatim = block == wanted
        if not verbatim:
            problems.append("mixer block of ks31_qrng.c differs from upstream lines 12-24, 61-70, 73-83, 113-120")
    except Exception as ex:  # noqa: BLE001
        problems.append("verbatim check failed: %s" % ex)

    # rays hard-coded in ks31.esk versus the JSON file
    esk_ok = False
    try:
        with open(os.path.join(STACK, "ks31.esk"), encoding="utf-8") as f:
            esk = f.read()
        triples = [[int(a), int(b), int(c)] for a, b, c in
                   re.findall(r"\(vector\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\)", esk)]
        esk_ok = triples == rays
        if not esk_ok:
            problems.append("rays in ks31.esk differ from %s" % KS_JSON)
    except Exception as ex:  # noqa: BLE001
        problems.append("ks31.esk ray check failed: %s" % ex)

    ok = not problems
    detail = ("%d vendored files fingerprinted; mixer block identical to upstream lines; "
              "ks31.esk rays equal the JSON rays" % len(fingerprints)) if ok else "; ".join(problems)
    return record("vendor", ok, detail,
                  {"sha256_third_party": fingerprints, "sha256_stack": own,
                   "ks_json_sha256": sha256(KS_JSON),
                   "mixers_verbatim": verbatim, "esk_rays_match_json": esk_ok},
                  time.time() - t0)


def stage_reference(rays):
    t0 = time.time()
    ref = reference(rays)
    ok = (ref["rays"] == 31 and ref["orthogonal_pairs"] == EXPECT_PAIRS and ref["bases"] == EXPECT_BASES
          and ref["classical_max"] < EXPECT_BASES and ref["ks_assignments"] == 0)
    detail = ("exact integers: %d orthogonal pairs, %d bases, classical maximum M = %d "
              "(%d admissible assignments, %d attain M), KS assignments = %d"
              % (ref["orthogonal_pairs"], ref["bases"], ref["classical_max"],
                 ref["admissible_assignments"], ref["assignments_attaining_max"], ref["ks_assignments"]))
    record("reference", ok, detail, ref, time.time() - t0)
    return ref


def stage_moonlab(tools):
    if not tools["node"]:
        record("moonlab", False, "node not found on PATH")
        return None
    rc, out, err, dt = run([tools["node"], "ks31_moonlab.cjs"], "moonlab", 1800)
    res = None
    for line in out.splitlines():
        if line.startswith("RESULT_JSON "):
            try:
                res = json.loads(line[len("RESULT_JSON "):])
            except ValueError:
                res = None
    fails = [x for x in out.splitlines() if x.startswith("[moonlab] FAIL")]
    ok = rc == 0 and res is not None and res.get("ok") is True and not fails
    if ok:
        detail = ("classical simulator: %d orthogonal pairs, %d bases; %d states: every basis sums to 1 "
                  "(max dev %.1e), pair sums <= 1; quantum %d for every state versus classical at most %d"
                  % (res["orthogonal_pairs"], res["bases"], res["n_states"],
                     res["max_basis_sum_deviation"], res["quantum_value"], res["classical_max"]))
    else:
        detail = "exit code %d; %s" % (rc, (fails[0] if fails else (err.strip().splitlines() or ["no RESULT_JSON"])[-1]))
    record("moonlab", ok, detail, res, dt)
    return res if ok else None


def stage_qgtl(tools):
    if not tools["gcc"]:
        record("qgtl", False, "gcc not found on PATH")
        return None
    inc = os.path.join("..", "third_party", "qgtl")
    build = [tools["gcc"], "-std=gnu11", "-O1",
             "-I", os.path.join(inc, "include"), "-I", os.path.join(inc, "stub"),
             os.path.join(inc, "src", "quantum_geometric", "distributed", "differential_geometry.c"),
             "ks31_qgtl.c", "-o", "ks31_qgtl.exe", "-lm"]
    rc, out, err, dt1 = run(build, "qgtl_build", 1800)
    if rc != 0:
        record("qgtl", False, "gcc build failed (exit code %d), see logs/stack_qgtl_build.log" % rc, None, dt1)
        return None
    rc, out, err, dt2 = run([os.path.join(STACK, "ks31_qgtl.exe"), KS_JSON], "qgtl", 600)
    kv = kv_lines(out)
    fails = [x for x in out.splitlines() if x.startswith("[qgtl] FAIL")]
    try:
        data = {"pairs_total": int(kv["pairs_total"]), "orthogonal_pairs": int(kv["orthogonal_pairs"]),
                "bases": int(kv["bases"]),
                "min_nonorthogonal_distance": float(kv["min_nonorthogonal_distance"]),
                "max_nonorthogonal_distance": float(kv["max_nonorthogonal_distance"]),
                "max_orthogonal_deviation": float(kv["max_orthogonal_deviation"])}
    except (KeyError, ValueError):
        data = None
    ok = rc == 0 and data is not None and not fails and "[qgtl] STAGE PASS" in out
    if ok:
        detail = ("Fubini-Study distance for %d pairs: pi/2 within 1e-12 exactly for %d orthogonal pairs, "
                  "non-orthogonal distances in [%.12f, %.12f]"
                  % (data["pairs_total"], data["orthogonal_pairs"],
                     data["min_nonorthogonal_distance"], data["max_nonorthogonal_distance"]))
    else:
        detail = "exit code %d; %s" % (rc, fails[0] if fails else "unexpected output, see logs/stack_qgtl.log")
    record("qgtl", ok, detail, data, dt1 + dt2)
    return data if ok else None


def stage_qrng(tools):
    if not tools["gcc"]:
        record("qrng", False, "gcc not found on PATH")
        return None
    build = [tools["gcc"], "-std=c11", "-O2", "-Wall", "-Wextra", "-o", "ks31_qrng.exe", "ks31_qrng.c"]
    rc, out, err, dt1 = run(build, "qrng_build", 1800)
    if rc != 0:
        record("qrng", False, "gcc build failed (exit code %d), see logs/stack_qrng_build.log" % rc, None, dt1)
        return None
    warnings = len([x for x in err.splitlines() if "warning" in x])
    rc, out, err, dt2 = run([os.path.join(STACK, "ks31_qrng.exe")], "qrng", 600)
    kv = kv_lines(out)
    data = None
    if "stream_first8" in kv:
        data = {"splitmix64_1": kv.get("splitmix64_1"), "hadamard_mix_1": kv.get("hadamard_mix_1"),
                "absorb_seed_le64_1": kv.get("absorb_seed_le64_1"),
                "stream_seed": int(kv.get("stream_seed", "-1")),
                "stream_first8": kv["stream_first8"].split(), "build_warnings": warnings}
    ok = (rc == 0 and data is not None and len(data["stream_first8"]) == 8
          and data["stream_first8"][:5] == STREAM_KAT and "[qrng] PASS" in out)
    detail = ("deterministic integer mixers (not quantum randomness): seed-1 known answers reproduced, "
              "stream[0..7] = %s" % " ".join(data["stream_first8"])) if ok else \
        "exit code %d, see logs/stack_qrng.log" % rc
    record("qrng", ok, detail, data, dt1 + dt2)
    return data if ok else None


def stage_eshkol(tools):
    if not tools["eshkol-run"]:
        record("eshkol", False, "eshkol-run not found on PATH")
        return None
    say("[run_stack] ....  eshkol    running eshkol-run -r ks31.esk (this stage can take several minutes)")
    rc, out, err, dt = run([tools["eshkol-run"], "-r", "ks31.esk"], "eshkol", 7200)
    data = {}
    for line in out.splitlines():
        m = re.match(r"^ESHKOL ([a-z-]+) (-?\d+)\s*$", line.strip())
        if m:
            data[m.group(1)] = int(m.group(2))
    lines = [x.strip() for x in out.splitlines()]
    ok = (rc == 0 and "ESHKOL-PASS" in lines and "ESHKOL-FAIL" not in lines
          and data.get("orthogonal-pairs") == EXPECT_PAIRS and data.get("bases") == EXPECT_BASES
          and data.get("ks-assignments") == 0 and data.get("relaxed-assignments", 0) > 0)
    if ok:
        detail = ("ESHKOL-PASS: %d orthogonal pairs, %d bases, 0 assignments satisfy the KS rules "
                  "(exhaustive backtracking, %d nodes); positive control finds %d assignments"
                  % (data["orthogonal-pairs"], data["bases"], data.get("search-nodes", -1),
                     data["relaxed-assignments"]))
    else:
        detail = "exit code %d, parsed %s, see logs/stack_eshkol.log" % (rc, data)
    record("eshkol", ok, detail, data, dt)
    return data if ok else None


def stage_cross(ref, moon, qgtl, qrng, esk):
    t0 = time.time()
    if not all([ref, moon, qgtl, qrng, esk]):
        return record("cross", False, "skipped: an earlier stage failed, nothing to compare")
    checks = []

    def chk(name, cond):
        checks.append({"check": name, "ok": bool(cond)})

    chk("orthogonal pairs = 71 in Python, Moonlab/JS, QGTL/C, Eshkol",
        ref["orthogonal_pairs"] == moon["orthogonal_pairs"] == qgtl["orthogonal_pairs"]
        == esk["orthogonal-pairs"] == EXPECT_PAIRS)
    chk("bases = 17 in Python, Moonlab/JS, QGTL/C, Eshkol",
        ref["bases"] == moon["bases"] == qgtl["bases"] == esk["bases"] == EXPECT_BASES)
    chk("list of the 17 bases identical in Python and Moonlab/JS",
        ref["bases_list"] == moon["bases_list"])
    chk("classical maximum M identical in Python and JS and below 17",
        ref["classical_max"] == moon["classical_max"] < EXPECT_BASES)
    chk("number of admissible assignments identical in Python and JS",
        ref["admissible_assignments"] == moon["admissible_assignments"])
    chk("number of assignments attaining M identical in Python and JS",
        ref["assignments_attaining_max"] == moon["assignments_attaining_max"])
    chk("KS assignments = 0 in Eshkol and Python (consistent with M < 17)",
        esk["ks-assignments"] == ref["ks_assignments"] == 0)
    chk("KS search node count identical in Eshkol and Python",
        esk.get("search-nodes") == ref["ks_search_nodes"])
    chk("positive-control count identical in Eshkol and Python",
        esk["relaxed-assignments"] == ref["relaxed_assignments"])
    chk("stream first 8 outputs identical in JS (BigInt) and C",
        moon["stream_first8"] == qrng["stream_first8"])
    chk("stream first 5 outputs equal the recorded seed-1 known answers",
        moon["stream_first8"][:5] == STREAM_KAT and qrng["stream_first8"][:5] == STREAM_KAT)
    chk("mixer known answers identical in JS and C",
        all(moon["mixer_kat"][k] == qrng[k] for k in ("splitmix64_1", "hadamard_mix_1", "absorb_seed_le64_1")))
    chk("QGTL min/max non-orthogonal distances agree with Python arccos within 1e-12",
        abs(qgtl["min_nonorthogonal_distance"] - ref["min_nonorthogonal_distance"]) < 1e-12
        and abs(qgtl["max_nonorthogonal_distance"] - ref["max_nonorthogonal_distance"]) < 1e-12)
    chk("simulator sum over the 17 bases equals 17 within tolerance for every state",
        moon["max_total_deviation"] <= 17 * moon["tolerance"] and moon["quantum_value"] == EXPECT_BASES)
    bad = [c["check"] for c in checks if not c["ok"]]
    ok = not bad
    detail = ("%d cross-language comparisons agree: pairs 71, bases 17, M = %d, stream values, node counts"
              % (len(checks), ref["classical_max"])) if ok else "MISMATCH: " + "; ".join(bad)
    return record("cross", ok, detail, {"checks": checks}, time.time() - t0)


def main():
    t_start = time.time()
    os.makedirs(LOGS, exist_ok=True)
    say("[run_stack] 31-ray KS set, operational demonstration on the vendored Tsotchke stack")
    say("[run_stack] note: all stages are classical computations (state-vector simulator, deterministic")
    say("[run_stack]       integer mixers, double-precision geometry kernel); no quantum hardware is used")

    with open(KS_JSON, encoding="utf-8") as f:
        ks = json.load(f)
    rays = ks["rays"]

    tools = {"gcc": find_tool("gcc"), "node": find_tool("node"),
             "eshkol-run": find_tool("eshkol-run", ESHKOL_FALLBACK)}

    stage_vendor(rays)
    ref = stage_reference(rays)
    moon = stage_moonlab(tools)
    qgtl = stage_qgtl(tools)
    qrng = stage_qrng(tools)
    esk = stage_eshkol(tools)
    stage_cross(ref, moon, qgtl, qrng, esk)

    all_ok = all(s["status"] == "PASS" for s in stages)
    versions = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "gcc": first_line([tools["gcc"], "--version"]) if tools["gcc"] else "not found",
        "node": first_line([tools["node"], "--version"]) if tools["node"] else "not found",
        "eshkol": first_line([tools["eshkol-run"], "--version"]) if tools["eshkol-run"] else "not found",
        "moonlab": ("core %s (prebuilt WASM, pinned commit cd3b234)" % (moon.get("glue_version") or {}).get("core"))
        if moon else "see third_party/moonlab/PROVENANCE.md",
        "qgtl": "v0.777 beta, pinned commit 770994a (differential_geometry.c only)",
        "quantum_rng": "pinned commit 1a77e77 (three integer mixers only)",
    }
    key = {}
    if ref:
        key.update({"rays": ref["rays"], "orthogonal_pairs": ref["orthogonal_pairs"], "bases": ref["bases"],
                    "classical_max_M": ref["classical_max"],
                    "admissible_assignments": ref["admissible_assignments"],
                    "assignments_attaining_M": ref["assignments_attaining_max"],
                    "ks_assignments": ref["ks_assignments"]})
    if moon:
        key.update({"quantum_value_every_state": moon["quantum_value"], "n_states": moon["n_states"],
                    "max_basis_sum_deviation": moon["max_basis_sum_deviation"],
                    "max_pair_sum": moon["max_pair_sum"], "stream_first8": moon["stream_first8"]})
    if qgtl:
        key.update({"fs_min_nonorthogonal_distance": qgtl["min_nonorthogonal_distance"],
                    "fs_max_nonorthogonal_distance": qgtl["max_nonorthogonal_distance"]})
    gap = None
    if ref and moon:
        gap = "quantum %d for every state versus classical at most %d" % (moon["quantum_value"], ref["classical_max"])
        say("[run_stack] state-independent gap: %s" % gap)
    say("[run_stack] %s  overall   %d/%d stages passed in %.0f s"
        % ("PASS" if all_ok else "FAIL", sum(s["status"] == "PASS" for s in stages), len(stages),
           time.time() - t_start))

    doc = {
        "title": "Stack demonstration of the 31-ray Kochen-Specker set",
        "generated_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall": "PASS" if all_ok else "FAIL",
        "state_independent_gap": gap,
        "key_numbers": key,
        "stages": stages,
        "tool_versions": versions,
        "inputs": {"ks_set": "results/ks31_box3_H2.json", "ks_set_name": ks.get("name")},
        "honest_labels": [
            "Moonlab is a classical state-vector simulator (prebuilt WASM run on the CPU under Node).",
            "The quantum_rng mixers are a deterministic 'quantum-inspired' integer mixer, not quantum randomness; "
            "the counter-mode stream built on them is this project's own construction.",
            "QGTL is used for one double-precision kernel (Fubini-Study distance); the rest of that library is not exercised.",
            "Nothing here is an experiment on quantum hardware.",
            "Floating-point stages are numerical checks with tolerance 1e-12; exact statements are integer "
            "recomputations (Python, Eshkol, JavaScript); none of this is a formal proof.",
        ],
        "logs": sorted({x for x in os.listdir(LOGS) if x.startswith("stack_") and x.endswith(".log")} | {"stack_run.log"}),
    }
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    say("[run_stack] wrote %s" % OUT_JSON)
    write_log("run", "\n".join(summary_lines) + "\n")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
