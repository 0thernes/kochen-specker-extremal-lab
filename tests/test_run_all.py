"""test_run_all.py - the one-command runner scripts/run_all.py itself.

The runner must report failures as failures: a stage that cannot succeed gives
a FAIL line, "ok": false in the JSON report and exit status 1.  Only cheap
stages are exercised here (the full run is `python scripts/run_all.py`).

Run alone:  python tests/test_run_all.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C  # noqa: E402

if C.SCRIPTS not in sys.path:
    sys.path.insert(0, C.SCRIPTS)
import run_all  # noqa: E402

RUN_ALL = os.path.join(C.SCRIPTS, "run_all.py")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class AxiomReportParser(unittest.TestCase):
    GOOD = ("'KS.small_sets_colorable' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
            "'KS.not_colorable_of_refute' depends on axioms: [propext, Quot.sound]\n")

    def test_plain_output(self):
        rep = run_all.parse_axiom_report(self.GOOD)
        self.assertEqual(rep, {"KS.small_sets_colorable": ["propext", "Classical.choice", "Quot.sound"],
                               "KS.not_colorable_of_refute": ["propext", "Quot.sound"]})
        for axioms in rep.values():
            self.assertTrue(all(a in run_all.AXIOM_ALLOWLIST for a in axioms))

    def test_wrapped_lines_and_no_axioms(self):
        text = ("'A.b' depends on axioms: [propext,\n Classical.choice,\n Quot.sound]\n"
                "'C.d' does not depend on any axioms\n")
        self.assertEqual(run_all.parse_axiom_report(text),
                         {"A.b": ["propext", "Classical.choice", "Quot.sound"], "C.d": []})

    def test_forbidden_axioms_are_visible(self):
        text = ("'A.b' depends on axioms: [propext, sorryAx, Quot.sound]\n"
                "'C.d' depends on axioms: [Lean.ofReduceBool,\n propext]\n")
        rep = run_all.parse_axiom_report(text)
        extra = {name: [a for a in axioms if a not in run_all.AXIOM_ALLOWLIST] for name, axioms in rep.items()}
        self.assertEqual(extra, {"A.b": ["sorryAx"], "C.d": ["Lean.ofReduceBool"]})

    def test_allowlist(self):
        self.assertEqual(sorted(run_all.AXIOM_ALLOWLIST), ["Classical.choice", "Quot.sound", "propext"])


class RunnerUnit(unittest.TestCase):
    def make(self):
        args = argparse.Namespace(lean=False, stack=False, only="", skip="", workers=1, work="",
                                  keep_work=False, json="", list=False)
        return run_all.Runner(args)

    def test_failing_stage_is_reported_as_fail(self):
        r = self.make()

        def boom():
            raise run_all.Failure("deliberate failure")

        r.stage_unit = boom
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            status = r.run_stage("unit", "title")
        self.assertEqual(status, "FAIL")
        self.assertEqual(r.report_stages[-1]["status"], "FAIL")
        self.assertEqual(r.report_stages[-1]["detail"], "deliberate failure")
        self.assertTrue(buf.getvalue().startswith("FAIL"))

    def test_crashing_stage_is_a_failure_not_a_pass(self):
        r = self.make()
        r.stage_unit = lambda: 1 // 0
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(r.run_stage("unit", "title"), "FAIL")
        self.assertIn("ZeroDivisionError", r.report_stages[-1]["detail"])

    def test_command_with_unexpected_exit_status(self):
        r = self.make()
        r.current = {"commands": [], "data": {}}
        code, out = r.cmd([sys.executable, "-c", "print('hello')"])
        self.assertEqual((code, out.strip()), (0, "hello"))
        with self.assertRaises(run_all.Failure):
            r.cmd([sys.executable, "-c", "import sys; sys.exit(3)"])
        code, _ = r.cmd([sys.executable, "-c", "import sys; sys.exit(3)"], expect=3)
        self.assertEqual(code, 3)
        code, out = r.cmd(["this-program-does-not-exist-ks"], expect=None)
        self.assertEqual(code, 127)
        self.assertEqual([c["exit_code"] for c in r.current["commands"]], [0, 3, 3, 127])

    def test_environment_is_cleaned_of_ks_variables(self):
        os.environ["KS_FIX_OUT"] = "1,0,0"
        try:
            r = self.make()
        finally:
            del os.environ["KS_FIX_OUT"]
        self.assertNotIn("KS_FIX_OUT", r.env)

    def test_stage_table_matches_methods(self):
        for name, flag, title in run_all.STAGES:
            self.assertTrue(callable(getattr(run_all.Runner, "stage_" + name.replace("-", "_"))), name)
            self.assertIn(flag, (None, "lean", "stack"))


class CommandLine(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ks_runall_")
        self.report = os.path.join(self.tmp, "report.json")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_all(self, *args):
        return C.run([sys.executable, RUN_ALL, "--json", self.report, "--work", self.tmp] + list(args),
                     cwd=C.ROOT, timeout=600)

    def test_list(self):
        code, out = C.run([sys.executable, RUN_ALL, "--list"], cwd=C.ROOT)
        self.assertEqual(code, 0, out)
        for name, _, _ in run_all.STAGES:
            self.assertIn(name, out)

    def test_unknown_stage_is_an_error(self):
        code, out = self.run_all("--only", "no-such-stage")
        self.assertEqual(code, 2, out)
        self.assertFalse(os.path.exists(self.report))

    def test_a_stage_that_cannot_succeed_gives_exit_status_1(self):
        # cert-verify without cert-gen: there is nothing to verify
        code, out = self.run_all("--only", "cert-verify")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL  cert-verify", out)
        self.assertIn("exit code 1", out)
        with open(self.report) as f:
            rep = json.load(f)
        self.assertFalse(rep["ok"])
        self.assertEqual((rep["passed"], rep["failed"], rep["exit_code"]), (0, 1, 1))
        self.assertEqual(rep["stages"][0]["status"], "FAIL")

    def test_lemma7_stage_passes_and_leaves_the_repository_alone(self):
        committed = os.path.join(C.RESULTS, "lemma7_d5_axes.json")
        default_report = os.path.join(C.RESULTS, "run_all.json")
        before = sha(committed)
        before_report = sha(default_report) if os.path.exists(default_report) else None
        code, out = self.run_all("--only", "lemma7")
        self.assertEqual(code, 0, out)
        self.assertIn("PASS  lemma7", out)
        with open(self.report) as f:
            rep = json.load(f)
        self.assertTrue(rep["ok"])
        self.assertEqual([s["name"] for s in rep["stages"]], ["lemma7"])
        self.assertEqual(rep["stages"][0]["data"]["committed_file_same_facts"], True)
        self.assertEqual(len(rep["not_run"]), len(run_all.STAGES) - 1)
        self.assertEqual(sha(committed), before)
        self.assertEqual(sha(default_report) if os.path.exists(default_report) else None, before_report)
        # the scratch directory was removed again
        self.assertEqual([x for x in os.listdir(self.tmp) if x.startswith("run_all_")], [])

    def test_skipping_everything_is_not_a_success(self):
        names = ",".join(name for name, _, _ in run_all.STAGES)
        code, out = self.run_all("--skip", names)
        self.assertEqual(code, 1, out)       # nothing ran: not "all checks passed"


if __name__ == "__main__":
    unittest.main(verbosity=2)
