#!/usr/bin/env python3
"""run_all.py - one command that re-runs the checks of the Kochen-Specker Extremal Lab.

usage:  python scripts/run_all.py [--lean] [--stack] [--only a,b] [--skip a,b]
                                  [--workers N] [--work DIR] [--keep-work]
                                  [--json PATH] [--list]

Stages, in order (one PASS/FAIL line each, then a summary; exit status 0 only
if no stage failed):

  unit         python -m unittest discover -s tests -p "test_*.py"
  js           node verify/test_verify.mjs (tests of the JavaScript verifier)
  lemma7       scripts/lemma7.py, compared with results/lemma7_d5_axes.json
  cert-gen     src/gen_cert.py: search-tree certificates for the 49-ray pool
               (k = 30) and the 40-ray pool (k = 17), regenerated from scratch
  cert-verify  node verify/verify_cert.mjs on the regenerated certificates
               (and a corrupted copy, which must be rejected)
  drup-49      49-ray pool, k = 30: src/ksmaster.py (cuts) -> src/ks_cnf.py
               (CNF, Glucose 4, DRUP proof) -> verify/drup_check
  drup-40      40-ray pool, k = 17: the same route
  lean         (--lean)  lake build (all modules), axiom audit of the theorems
               named in lean/KS/Audit.lean, scan of the Lean sources for
               sorry / native_decide
  stack        (--stack) python scripts/run_stack.py

Nothing in the repository is overwritten except the report results/run_all.json
(--json to change) - with one exception: the optional stage `stack` runs
scripts/run_stack.py in place, which rewrites its own outputs.  Programs that
write next to their sources (ksmaster.py, ks_cnf.py, lemma7.py,
test_verify.mjs) are run from byte-identical copies in a scratch directory
with the same layout, so the committed result files stay as they are; the
regenerated files are compared with the committed ones and the outcome is
recorded in the report.  The proof checker is compiled from
verify/drup_check.c into the scratch directory when a C compiler is available.

Standard library only; the stages call the project's programs as subprocesses.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
EXE = ".exe" if os.name == "nt" else ""
AXIOM_ALLOWLIST = ("propext", "Classical.choice", "Quot.sound")
TAIL_LINES = 25

STAGES = [          # (name, optional flag or None, title)
    ("unit", None, "unit tests (tests/test_*.py)"),
    ("js", None, "JavaScript verifier tests (verify/test_verify.mjs)"),
    ("lemma7", None, "Lemma 7 facts (scripts/lemma7.py)"),
    ("cert-gen", None, "search-tree certificates regenerated (src/gen_cert.py)"),
    ("cert-verify", None, "regenerated certificates checked by verify/verify_cert.mjs"),
    ("drup-49", None, "49-ray pool, k=30: ksmaster -> ks_cnf (g4) -> drup_check"),
    ("drup-40", None, "40-ray pool, k=17: ksmaster -> ks_cnf (g4) -> drup_check"),
    ("lean", "lean", "Lean 4: lake build, axiom audit, source scan"),
    ("stack", "stack", "stack demonstration (scripts/run_stack.py)"),
]


class Failure(Exception):
    """A stage failed; the message is the one-line reason."""


class Missing(Failure):
    """A required external tool is not installed."""


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tail(text, lines=TAIL_LINES):
    return "\n".join(text.rstrip().splitlines()[-lines:])


class Runner:
    def __init__(self, args):
        self.args = args
        self.work = None
        self.report_stages = []
        self.current = None
        self.drup = None
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("KS_")}
        self.env["PYTHONIOENCODING"] = "utf-8"
        elan = os.path.join(os.path.expanduser("~"), ".elan", "bin")
        if os.path.isdir(elan) and elan not in self.env.get("PATH", ""):
            self.env["PATH"] = elan + os.pathsep + self.env.get("PATH", "")

    # ---- plumbing ----
    def which(self, name):
        return shutil.which(name, path=self.env.get("PATH"))

    def cmd(self, argv, cwd=None, timeout=1800, env=None, expect=0):
        """Run a command, record it in the current stage, return (exit code, output)."""
        e = dict(self.env)
        if env:
            e.update(env)
        t0 = time.time()
        try:
            p = subprocess.run(argv, cwd=cwd or ROOT, env=e, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, timeout=timeout)
            code, out = p.returncode, p.stdout.decode("utf-8", "replace")
        except subprocess.TimeoutExpired as exc:
            code, out = 124, (exc.stdout or b"").decode("utf-8", "replace") + f"\nTIMEOUT after {timeout}s"
        except OSError as exc:
            code, out = 127, f"cannot run {argv[0]}: {exc}"
        shown = [self.rel(a) for a in argv]
        if os.path.isabs(shown[0]):          # an installed program: its name is enough for the report
            shown[0] = re.sub(r"\.exe$", "", os.path.basename(shown[0]), flags=re.I)
        self.current["commands"].append({
            "argv": shown, "cwd": self.rel(cwd or ROOT), "exit_code": code,
            "seconds": round(time.time() - t0, 2), "output_tail": self.scrub(tail(out)),
        })
        if expect is not None and code != expect:
            raise Failure(f"`{' '.join(shown[:4])} ...` exited with {code} (expected {expect})")
        return code, out

    def scrub(self, text):
        """Machine-specific directories (scratch directory, home directory) out of recorded output."""
        home = os.path.expanduser("~")
        for base, label in ((self.work, "<work>"), (home, "~")):
            if base and len(base) > 3:
                for variant in {base, base.replace("\\", "/"), base.replace("\\", "\\\\")}:
                    text = text.replace(variant, label)
        return text

    def rel(self, path):
        """Paths inside the repository or the scratch directory, shortened for the report."""
        s = str(path)
        for base, label in ((self.work, "<work>"), (ROOT, "<repo>")):
            if not base:
                continue
            b = base.rstrip("\\/")
            if s == b or s == base:
                return label
            if s.startswith(b + "\\") or s.startswith(b + "/"):
                return label + "/" + s[len(b):].lstrip("\\/").replace("\\", "/")
        return s

    def sandbox(self):
        """Scratch copy of the programs that write next to their own sources."""
        if self.work:
            return self.work
        if self.args.work:
            os.makedirs(self.args.work, exist_ok=True)
            self.work = tempfile.mkdtemp(prefix="run_all_", dir=self.args.work)
        else:
            self.work = tempfile.mkdtemp(prefix="ks_run_all_")
        for sub in ("src", "scripts", "verify", "results", "logs"):
            os.makedirs(os.path.join(self.work, sub))
        for pattern, sub in (("src/*.py", "src"), ("scripts/*.py", "scripts"),
                             ("verify/*.mjs", "verify"), ("verify/*.c", "verify")):
            for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
                shutil.copy2(path, os.path.join(self.work, sub, os.path.basename(path)))
        return self.work

    def in_work(self, *parts):
        return os.path.join(self.sandbox(), *parts)

    def need(self, tool):
        path = self.which(tool)
        if path is None:
            raise Missing(f"{tool} is not installed (not found on PATH)")
        return path

    def drup_check(self):
        """The proof checker: compiled from the current source when possible."""
        if self.drup:
            return self.drup
        src = os.path.join(ROOT, "verify", "drup_check.c")
        repo_exe = os.path.join(ROOT, "verify", "drup_check" + EXE)
        cc = self.which("gcc") or self.which("cc")
        if cc:
            exe = self.in_work("verify", "drup_check" + EXE)
            self.cmd([cc, "-O2", "-o", exe, src], timeout=600)
            if not os.path.isfile(exe):
                raise Failure("the C compiler produced no drup_check binary")
            self.current["data"]["drup_check"] = "compiled from verify/drup_check.c for this run"
            self.drup = exe
        elif os.path.isfile(repo_exe) and os.path.getmtime(repo_exe) >= os.path.getmtime(src):
            self.current["data"]["drup_check"] = "existing binary verify/drup_check" + EXE + " (no C compiler found)"
            self.drup = repo_exe
        else:
            raise Missing("no C compiler (gcc / cc) and no up-to-date verify/drup_check" + EXE)
        self.current["data"]["drup_check_c_sha256"] = sha256_file(src)
        return self.drup

    # ---- stages ----
    def stage_unit(self):
        code, out = self.cmd([PY, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
                             env={"KS_SKIP_JS_SUITE": "1", "KS_TEST_WORKERS": str(self.args.workers)},
                             expect=None, timeout=3600)
        m = re.search(r"Ran (\d+) tests? in ([\d.]+)s", out)
        ran = int(m.group(1)) if m else 0
        skipped = re.search(r"skipped=(\d+)", out)
        skipped = int(skipped.group(1)) if skipped else 0
        self.current["data"].update(tests_run=ran, tests_skipped=skipped)
        if code != 0 or not re.search(r"^OK\b", out, re.M) or ran == 0:
            raise Failure(f"unittest exited with {code}; {ran} tests run")
        return f"{ran} tests, {skipped} skipped"

    def stage_js(self):
        node = self.need("node")
        # the test suite reads ../results/<name> and writes ../results/verify_summary.json:
        # give it the committed certificates in a results directory next to a copy of verify/
        # (separate from <work>/results, which holds the files regenerated by later stages)
        jsbox = os.path.join(self.sandbox(), "js")
        os.makedirs(os.path.join(jsbox, "verify"))
        os.makedirs(os.path.join(jsbox, "results"))
        for path in glob.glob(os.path.join(ROOT, "verify", "*.mjs")):
            shutil.copy2(path, os.path.join(jsbox, "verify", os.path.basename(path)))
        for pattern in ("cert_*.json", "ks31_box3_H2.json"):
            for path in glob.glob(os.path.join(ROOT, "results", pattern)):
                shutil.copy2(path, os.path.join(jsbox, "results", os.path.basename(path)))
        code, out = self.cmd([node, os.path.join(jsbox, "verify", "test_verify.mjs")], cwd=jsbox,
                             timeout=1800)
        summary_path = os.path.join(jsbox, "results", "verify_summary.json")
        if not os.path.isfile(summary_path):
            raise Failure("test_verify.mjs wrote no verify_summary.json")
        with open(summary_path) as f:
            summary = json.load(f)
        failures = summary.get("failures")
        self.current["data"].update(verdict=summary.get("verdict"), failures=failures,
                                    verifier=summary.get("verifier"), node=summary.get("node"))
        if failures != []:
            raise Failure(f"{len(failures or [])} failed checks in test_verify.mjs")
        last = out.strip().splitlines()[-1] if out.strip() else ""
        m = re.search(r"(\d+)/(\d+) checks passed", last)
        return f"{m.group(1)}/{m.group(2)} checks passed" if m else "all checks passed"

    def stage_lemma7(self):
        self.cmd([PY, self.in_work("scripts", "lemma7.py")], cwd=self.sandbox(), timeout=900)
        fresh_path = self.in_work("results", "lemma7_d5_axes.json")
        if not os.path.isfile(fresh_path):
            raise Failure("lemma7.py wrote no results/lemma7_d5_axes.json")
        with open(fresh_path) as f:
            fresh = json.load(f)
        if not (fresh.get("fact1_every_basis_contains_an_axis") is True
                and fresh.get("fact2_colorable_without_three_axes") is True):
            raise Failure("lemma7.py does not confirm the two facts")
        data = self.current["data"]
        data.update(n_rays=fresh.get("n_rays"), n_bases=fresh.get("n_bases"))
        committed_path = os.path.join(ROOT, "results", "lemma7_d5_axes.json")
        if os.path.isfile(committed_path):
            with open(committed_path) as f:
                committed = json.load(f)
            differing = sorted(k for k in set(fresh) | set(committed)
                               if k != "ones" and fresh.get(k) != committed.get(k))
            data["committed_file_same_facts"] = not differing
            data["committed_file_same_coloring"] = fresh.get("ones") == committed.get("ones")
            if differing:
                raise Failure("results/lemma7_d5_axes.json differs from the recomputation in: "
                              + ", ".join(differing))
            note = "matches results/lemma7_d5_axes.json"
        else:
            data["committed_file_same_facts"] = None
            note = "no committed file to compare with"
        return f"{fresh.get('n_rays')} rays, {fresh.get('n_bases')} bases, both facts hold; {note}"

    CERTS = [    # (file name, k, kind, args)
        ("cert_box3_H2_k30.json", 30, "box3", ["2"]),
        ("cert_box4_H1_k17.json", 17, "box", ["4", "1"]),
    ]

    def stage_cert_gen(self):
        notes = []
        self.current["data"]["certificates"] = []
        for name, k, kind, kargs in self.CERTS:
            out_path = self.in_work("results", name)
            code, out = self.cmd([PY, self.in_work("src", "gen_cert.py"), str(k), out_path, kind] + kargs,
                                 cwd=self.sandbox(), timeout=1800)
            if not os.path.isfile(out_path):
                raise Failure(f"gen_cert.py wrote no {name}")
            m = re.search(r"tree with (\d+) nodes.*tree ok=(\w+) \((\d+) nodes\), pool ok=(\w+)", out)
            if not m:
                raise Failure(f"unexpected output of gen_cert.py for {name}")
            nodes, tree_ok, replayed, pool_ok = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4)
            if tree_ok != "True" or pool_ok != "True" or replayed != nodes:
                raise Failure(f"{name}: Python re-check failed (tree ok={tree_ok}, pool ok={pool_ok})")
            committed = os.path.join(ROOT, "results", name)
            same = None
            if os.path.isfile(committed):
                with open(committed) as f1, open(out_path) as f2:
                    same = json.load(f1) == json.load(f2)
            self.current["data"]["certificates"].append({
                "file": name, "k": k, "pool": kind + " " + " ".join(kargs), "nodes": nodes,
                "sha256": sha256_file(out_path), "same_content_as_committed_file": same})
            notes.append(f"{name}: {nodes} nodes" + ("" if same is None else
                                                      (", same as committed" if same else ", differs from committed")))
        return "; ".join(notes)

    def stage_cert_verify(self):
        node = self.need("node")
        paths = [self.in_work("results", name) for name, _, _, _ in self.CERTS]
        missing = [os.path.basename(p) for p in paths if not os.path.isfile(p)]
        if missing:
            raise Failure("no regenerated certificate (stage cert-gen did not run or failed): "
                          + ", ".join(missing))
        verifier = os.path.join(ROOT, "verify", "verify_cert.mjs")
        summary_path = self.in_work("results", "verify_fresh.json")
        code, out = self.cmd([node, verifier] + paths + ["--out", summary_path], timeout=1800)
        # negative control: the same certificate with k raised by one states something false
        with open(paths[0]) as f:
            cert = json.load(f)
        cert["k"] += 1
        bad = self.in_work("results", "corrupted_k_plus_1.json")
        with open(bad, "w") as f:
            json.dump(cert, f)
        self.cmd([node, verifier, bad], expect=1, timeout=600)
        self.current["data"]["negative_control"] = "certificate with k raised by one was rejected"
        return f"{len(paths)} certificates PASS; corrupted copy rejected"

    def drup_route(self, k, kind, kargs):
        box = self.sandbox()
        drup = self.drup_check()
        tag = "master_" + "_".join([kind] + kargs) + f"_k{k}_cuts"
        cuts = self.in_work("results", tag + ".json")
        cnf = self.in_work("results", tag + ".cnf")
        drat = self.in_work("results", tag + ".drat")
        data = self.current["data"]
        # 1. counterexample-guided search (CP-SAT): must end with "none" and write the cuts
        code, out = self.cmd([PY, "-u", self.in_work("src", "ksmaster.py"), str(k), "900",
                              str(self.args.workers), "-", kind] + kargs, cwd=box, timeout=1800)
        m = re.search(r"MASTER RESULT .*: (\w+) after (\d+) iterations, (\d+) cuts", out)
        if not m:
            raise Failure("ksmaster.py printed no MASTER RESULT line")
        if m.group(1) != "none":
            raise Failure(f"ksmaster.py ended with status {m.group(1)!r}, expected 'none'")
        if not os.path.isfile(cuts):
            raise Failure(f"ksmaster.py wrote no {tag}.json")
        data.update(engine_a="CP-SAT: infeasible", iterations=int(m.group(2)), cuts=int(m.group(3)))
        # 2. CNF re-encoding, Glucose 4 with a DRUP proof
        code, out = self.cmd([PY, "-u", self.in_work("src", "ks_cnf.py"), cuts, str(k), "-", "g4", kind] + kargs,
                             cwd=box, timeout=1800)
        if not re.search(r"cuts re-verified from their witnesses: True", out):
            raise Failure("ks_cnf.py did not re-verify the cuts")
        if not re.search(r"^g4: UNSAT", out, re.M):
            raise Failure("Glucose 4 did not report UNSAT")
        m = re.search(r"CNF: (\d+) variables, (\d+) clauses", out)
        if m:
            data.update(variables=int(m.group(1)), clauses=int(m.group(2)))
        if not (os.path.isfile(cnf) and os.path.isfile(drat)):
            raise Failure("ks_cnf.py wrote no .cnf / .drat pair")
        # 3. the proof checker
        code, out = self.cmd([drup, cnf, drat], timeout=1800)
        if "s VERIFIED" not in out:
            raise Failure("drup_check exited 0 without the line 's VERIFIED'")
        m = re.search(r"(\d+) lemmas checked", out)
        if m:
            data["lemmas_checked"] = int(m.group(1))
        # 4. negative control: the empty proof must not be accepted for the same formula
        empty = self.in_work("results", tag + ".empty.drat")
        open(empty, "w").close()
        code, out = self.cmd([drup, cnf, empty], expect=None, timeout=600)
        if code == 0 or "s VERIFIED" in out:
            raise Failure("drup_check accepted an empty proof")
        data["negative_control"] = "empty proof rejected"
        data["cnf_sha256"] = sha256_file(cnf)
        return (f"{data.get('cuts')} cuts, CNF {data.get('variables')} vars / {data.get('clauses')} clauses, "
                f"UNSAT, proof VERIFIED ({data.get('lemmas_checked')} lemmas)")

    def stage_drup_49(self):
        return self.drup_route(30, "box3", ["2"])

    def stage_drup_40(self):
        return self.drup_route(17, "box", ["4", "1"])

    def stage_lean(self):
        lake = self.need("lake")
        lean_dir = os.path.join(ROOT, "lean")
        with open(os.path.join(lean_dir, "lean-toolchain")) as f:
            self.current["data"]["toolchain"] = f.read().strip()
        # 1. no sorry / native_decide in the sources
        hits = []
        sources = sorted(glob.glob(os.path.join(lean_dir, "KS", "*.lean")) + [os.path.join(lean_dir, "KS.lean")])
        for path in sources:
            with open(path, encoding="utf-8") as f:
                for no, line in enumerate(f, 1):
                    if re.search(r"\b(sorry|native_decide)\b", line):
                        hits.append(f"{os.path.relpath(path, ROOT)}:{no}")
        self.current["data"]["sources_scanned"] = [os.path.relpath(p, ROOT).replace("\\", "/") for p in sources]
        if hits:
            raise Failure("sorry / native_decide found in: " + ", ".join(hits[:10]))
        # 2. build
        # plain `lake build` checks KS.lean and all it imports: Basic, Spec, Box3H2, Box4H1, Tests
        self.cmd([lake, "build"], cwd=lean_dir, timeout=4 * 3600)
        # 3. axiom audit
        code, out = self.cmd([lake, "env", "lean", "KS/Audit.lean"], cwd=lean_dir, timeout=3600)
        with open(os.path.join(lean_dir, "KS", "Audit.lean"), encoding="utf-8") as f:
            wanted = re.findall(r"^#print axioms\s+(\S+)", f.read(), re.M)
        audit = parse_axiom_report(out)
        self.current["data"]["axioms"] = audit
        if not wanted:
            raise Failure("KS/Audit.lean contains no '#print axioms' command")
        problems = []
        for name in wanted:
            if name not in audit:
                problems.append(f"no axiom report for {name}")
                continue
            extra = [a for a in audit[name] if a not in AXIOM_ALLOWLIST]
            if extra:
                problems.append(f"{name} depends on {', '.join(extra)}")
        if re.search(r"\bsorry", out):
            problems.append("the audit output mentions sorry")
        if problems:
            raise Failure("; ".join(problems))
        used = sorted({a for name in wanted for a in audit[name]})
        return f"{len(wanted)} theorems audited, axioms used: {', '.join(used) if used else 'none'}; no sorry"

    def stage_stack(self):
        # run_stack.py runs in place: it rewrites results/stack_demo.json and logs/stack_*.log
        code, out = self.cmd([PY, os.path.join(ROOT, "scripts", "run_stack.py")], expect=None, timeout=3600)
        verdicts = re.findall(r"^(?:\[run_stack\]\s+)?(PASS|FAIL)\b", out, re.M)
        passes, fails = verdicts.count("PASS"), verdicts.count("FAIL")
        self.current["data"].update(pass_lines=passes, fail_lines=fails, exit_code=code)
        if code != 0 or fails:
            raise Failure(f"run_stack.py exited with {code}; {fails} FAIL lines")
        if passes == 0:
            raise Failure("run_stack.py printed no PASS line")
        return f"{passes} PASS lines, no FAIL"

    # ---- driver ----
    def run_stage(self, name, title):
        self.current = {"name": name, "title": title, "status": None, "seconds": None,
                        "detail": "", "commands": [], "data": {}}
        t0 = time.time()
        try:
            detail = getattr(self, "stage_" + name.replace("-", "_"))()
            status = "PASS"
        except Failure as exc:
            status, detail = "FAIL", str(exc)
        except Exception as exc:                               # a bug in this script is a failure too
            status, detail = "FAIL", f"{type(exc).__name__}: {exc}"
        self.current.update(status=status, seconds=round(time.time() - t0, 1), detail=detail)
        self.report_stages.append(self.current)
        print(f"{status:<4}  {name:<12} {self.current['seconds']:>7.1f}s  {detail}", flush=True)
        if status == "FAIL" and self.current["commands"]:
            last = self.current["commands"][-1]
            print("      last command: " + " ".join(last["argv"]), flush=True)
            for line in last["output_tail"].splitlines()[-12:]:
                print("      | " + line, flush=True)
        return status


def parse_axiom_report(text):
    """{theorem: [axioms]} from the output of '#print axioms' (robust to line wrapping)."""
    flat = " ".join(text.split())
    report = {}
    for m in re.finditer(r"'([^']+)' depends on axioms: \[([^\]]*)\]", flat):
        report[m.group(1)] = [a.strip() for a in m.group(2).split(",") if a.strip()]
    for m in re.finditer(r"'([^']+)' does not depend on any axioms", flat):
        report[m.group(1)] = []
    return report


def tool_version(runner, argv):
    exe = runner.which(argv[0])
    if exe is None:
        return None
    try:
        p = subprocess.run([exe] + argv[1:], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=60, env=runner.env)
        lines = p.stdout.decode("utf-8", "replace").strip().splitlines()
        return lines[0].strip() if lines else ""
    except (OSError, subprocess.TimeoutExpired):
        return None


def python_packages(runner):
    code = ("import json\n"
            "out = {}\n"
            "for mod, dist in (('pysat', 'python-sat'), ('ortools', 'ortools'), ('numpy', 'numpy')):\n"
            "    try:\n"
            "        m = __import__(mod)\n"
            "        out[dist] = getattr(m, '__version__', 'unknown')\n"
            "    except Exception as e:\n"
            "        out[dist] = None\n"
            "print(json.dumps(out))\n")
    try:
        p = subprocess.run([PY, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                           timeout=120, env=runner.env)
        return json.loads(p.stdout.decode("utf-8", "replace").strip().splitlines()[-1])
    except Exception:
        return {}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Re-run the checks of the Kochen-Specker Extremal Lab.")
    ap.add_argument("--lean", action="store_true", help="also build and audit the Lean development")
    ap.add_argument("--stack", action="store_true", help="also run scripts/run_stack.py")
    ap.add_argument("--only", default="", help="comma-separated stage names to run (implies their flags)")
    ap.add_argument("--skip", default="", help="comma-separated stage names to leave out")
    ap.add_argument("--workers", type=int, default=2, help="CP-SAT worker threads (default 2)")
    ap.add_argument("--work", default="", help="parent directory for the scratch directory")
    ap.add_argument("--keep-work", action="store_true", help="do not delete the scratch directory")
    ap.add_argument("--json", default=os.path.join(ROOT, "results", "run_all.json"),
                    help="where to write the machine-readable report")
    ap.add_argument("--list", action="store_true", help="list the stages and exit")
    args = ap.parse_args(argv)

    names = [s[0] for s in STAGES]
    if args.list:
        for name, flag, title in STAGES:
            print(f"{name:<12} {'(--' + flag + ')' if flag else '':<10} {title}")
        return 0
    only = [x for x in args.only.split(",") if x]
    skip = [x for x in args.skip.split(",") if x]
    unknown = [x for x in only + skip if x not in names]
    if unknown:
        ap.error("unknown stage(s): " + ", ".join(unknown) + "; known: " + ", ".join(names))

    runner = Runner(args)
    started = datetime.datetime.now(datetime.timezone.utc)
    t0 = time.time()
    print(f"run_all: repository {ROOT}", flush=True)
    not_run = []
    try:
        for name, flag, title in STAGES:
            if only:
                selected = name in only
                reason = "not in --only"
            else:
                selected = flag is None or getattr(args, flag)
                reason = f"optional, enable with --{flag}"
            if name in skip:
                selected, reason = False, "--skip"
            if not selected:
                not_run.append({"name": name, "title": title, "status": "SKIP", "detail": reason})
                print(f"SKIP  {name:<12} {'':>8}  {reason}", flush=True)
                continue
            runner.run_stage(name, title)
    finally:
        work = runner.work
        if work and not args.keep_work:
            shutil.rmtree(work, ignore_errors=True)
    passed = sum(1 for s in runner.report_stages if s["status"] == "PASS")
    failed = sum(1 for s in runner.report_stages if s["status"] == "FAIL")
    exit_code = 0 if failed == 0 and passed > 0 else 1
    seconds = round(time.time() - t0, 1)

    inputs = {}
    for pattern in ("src/*.py", "scripts/*.py", "verify/*.mjs", "verify/*.c", "tests/*.py",
                    "lean/KS/*.lean", "lean/lean-toolchain", "requirements.txt"):
        for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
            inputs[os.path.relpath(path, ROOT).replace("\\", "/")] = sha256_file(path)
    report = {
        "tool": "scripts/run_all.py",
        "started_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seconds": seconds,
        "argv": [runner.scrub(a) for a in (sys.argv[1:] if argv is None else list(argv))],
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "packages": python_packages(runner),
            "node": tool_version(runner, ["node", "--version"]),
            "c_compiler": tool_version(runner, ["gcc", "--version"]) or tool_version(runner, ["cc", "--version"]),
            "lake": tool_version(runner, ["lake", "--version"]) if (args.lean or "lean" in only) else None,
            "cpsat_workers": args.workers,
        },
        "stages": runner.report_stages,
        "not_run": not_run,
        "passed": passed,
        "failed": failed,
        "ok": exit_code == 0,
        "exit_code": exit_code,
        "scratch_directory": work if (work and args.keep_work) else None,
        "inputs_sha256": inputs,
    }
    text = json.dumps(report, indent=1)
    os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
    with open(args.json, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    shown = os.path.abspath(args.json)
    if shown.startswith(ROOT):
        shown = os.path.relpath(shown, ROOT).replace("\\", "/")
    print(f"SUMMARY: {passed} passed, {failed} failed, {len(not_run)} not run, {seconds}s; report: {shown}",
          flush=True)
    if work and args.keep_work:
        print(f"scratch directory kept: {work}", flush=True)
    print(f"exit code {exit_code}", flush=True)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
