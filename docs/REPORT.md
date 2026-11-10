# Verification report

Kochen-Specker Extremal Lab, version 1.0.0, 10 November 2026.

This page says what was run, on what machine, with which versions, how long it took, what failed or
was stopped, and what has to be trusted. It adds no result: every number is taken from the register
[results/RESULTS.md](../results/RESULTS.md), from the machine-readable run report
[results/run_all.json](../results/run_all.json), or from a log named next to it. Where this page and
the register differ, the register is right. Per-claim commands and logs: [INDEX.md](INDEX.md).

## 1. Machine and versions

All runs were made on one desktop computer: Intel Core Ultra 9 275HX (24 cores), 47 GB of memory,
Windows 11 Pro. Nothing was run on a cluster or on rented machines.

| tool | version | source of this line |
|---|---|---|
| Python | 3.9.13 | `results/run_all.json` |
| python-sat (PySAT) | 1.9.dev21 | `results/run_all.json`, `requirements.txt` |
| Glucose (SAT solver of engine B), through PySAT | 4.1, bundled with python-sat | section C of the register |
| CaDiCaL (second SAT solver), through PySAT | 1.9.5, bundled with python-sat (solver name `cadical195`) | section C of the register, `results/second_solver_*.json` |
| OR-Tools (CP-SAT) | 9.15.6755 | `results/run_all.json`, `requirements.txt` |
| NumPy | 2.0.2 | `results/run_all.json`, `requirements.txt` |
| Node.js | v25.8.2 | `results/run_all.json` |
| C compiler | gcc 16.1.0 (MinGW-W64 x86_64, ucrt, posix, seh) | `results/run_all.json` |
| Lean | 4.35.0 (Lake 5.0.0), toolchain `leanprover/lean4:v4.35.0`, no Mathlib | `results/run_all.json`, `lean/lean-toolchain` |
| JavaScript verifier | `verify_cert.mjs` 1.0.0 | `results/run_all.json` |
| Eshkol (stack demonstration only) | Eshkol Compiler v1.3.6-evolve | `results/stack_demo.json` |
| Moonlab, QGTL, quantum_rng (stack demonstration only) | pinned commits, see `third_party/*/PROVENANCE.md` | `results/stack_demo.json` |

The continuous-integration workflow `.github/workflows/ci.yml` describes the same checks on Ubuntu
with Python 3.11 and Node 22. No run of that workflow is recorded in this repository, so nothing here
is claimed on its basis.

## 2. The one-command run

`python scripts/run_all.py --lean`, started 2026-11-10 11:34:09 UTC, after all 81 cube proofs had
been checked, 52.1 seconds in total, 8 stages passed, none failed, exit code 0. The optional stage
`stack` was not part of this run.

| stage | result | seconds | detail |
|---|---|---|---|
| `unit` | PASS | 21.9 | 115 tests, 1 skipped |
| `js` | PASS | 5.2 | 59 of 59 checks of `verify/test_verify.mjs` |
| `lemma7` | PASS | 0.2 | 121 rays, 136 bases, both facts hold; same facts and same coloring as the committed file |
| `cert-gen` | PASS | 0.6 | certificates for B(3, 2) (255 nodes) and B(4, 1) (509 nodes) regenerated; same content as the committed files |
| `cert-verify` | PASS | 0.1 | both regenerated certificates accepted by `verify_cert.mjs`; a copy with k raised by one rejected |
| `drup-49` | PASS | 2.2 | B(3, 2), k = 30: engine A infeasible after 5 iterations, 63 cuts; formula of 5 254 variables and 20 235 clauses unsatisfiable; proof VERIFIED, 183 lemmas; empty proof rejected |
| `drup-40` | PASS | 1.5 | B(4, 1), k = 17: engine A infeasible after 3 iterations, 84 cuts; 4 427 variables, 16 847 clauses; proof VERIFIED, 307 lemmas; empty proof rejected |
| `lean` | PASS | 20.3 | sources scanned for `sorry` and `native_decide` (none); `lake build` (all modules); axiom audit of the 26 theorems named in `lean/KS/Audit.lean`: only `propext`, `Classical.choice`, `Quot.sound` |

Three remarks. The `drup-49` stage finds its cuts afresh; in this run they gave 63 cuts, a formula of
20 235 clauses and a proof of 183 lemmas, while the register's run for row A1 gave 20 223 clauses and
191 lemmas; both proofs were accepted. The 20.3 seconds of the `lean` stage were measured with the
build products of an earlier build present (`lake build` itself took 0.2 seconds; the rest is the
axiom audit); the paper states that building everything from
scratch takes about one minute (53 seconds measured, `lean/README.md`). The same command in a fresh
clone of the repository, with an empty Lean build directory and none of the large proof files,
passed every stage as well (115 tests, 2 skipped; the `lean` stage took 49.4 seconds there).

The report also stores the SHA-256 of 64 input files (programs, tests, Lean sources, toolchain file,
requirements).

## 3. The longer runs

Engine A (CP-SAT), last run in each log, time to the answer "infeasible":

| row | pool, bound | iterations, cuts | seconds | log |
|---|---|---|---|---|
| A1 | B(3, 2), k = 30 | 4, 51 | 0.7 | `logs/master_box3_2_k30.log` |
| A2 | B(3, 3), k = 30 | 5, 54 | 0.6 | `logs/master_box3_3_k30.log` |
| A3 | B(3, 4), k = 30 | 7, 147 | 80.6 | `logs/master_box3_4_k30.log` |
| A5 | U(3, 12), k = 32 | 5, 4 860 | 9.0 | `logs/master_roots_3_12_k32.log` |
| A6 | U(3, 18), k = 32 | 6, 14 418 | 493.4 | `logs/master_roots_3_18_k32.log` |
| A7 | U(3, 24), k = 32 | 5, 12 307 | 621.5 | `logs/master_roots_3_24_k32.log` |
| A8 | B(4, 1), k = 17 | 3, 84 | 0.7 | `logs/master_box_4_1_k17.log` |

Engine B and the proof checker: the table of section C of the register, copied. The formula is
solved by Glucose 4.1 and, where the table says so, by a second solver, CaDiCaL 1.9.5, on the same
file. "Lemmas checked" is the number of proof steps that `verify/drup_check` verified before the empty
clause was reached.

| Run (bound) | variables / clauses | solver and time | lemmas checked | verdict |
|---|---|---|---|---|
| A1 (k = 30) | 5 254 / 20 223 | Glucose, under 1 s | 191 | VERIFIED |
| A8 (k = 17) | 4 427 / 16 847 | Glucose, under 1 s | 307 | VERIFIED |
| A2 (k = 30) | 17 374 / 67 890 | Glucose, 1.4 s | 2 447 | VERIFIED |
| A5 (k = 32) | 9 010 / 38 504 | Glucose, 14.3 s | 39 774 | VERIFIED |
| A6 (k = 32) | 19 699 / 88 136 | Glucose, 84.3 s | 367 001 | VERIFIED |
| A3 (k = 30) | 76 046 / 300 463 | Glucose, 736 s | 443 604 | VERIFIED |
| A7 (k = 32) | 34 372 / 141 027 | Glucose: stopped, out of its 32-bit clause memory. CaDiCaL: unsatisfiable, 338 s | 1 464 683 | VERIFIED |
| A9, exactly three axes (k = 28) | 29 500 / 114 428 | Glucose, 40 s | 94 680 | VERIFIED |
| A9, exactly four axes (k = 28) | 29 500 / 115 388 | CaDiCaL, 214 s | 1 614 075 | VERIFIED |
| the same formula | | Glucose, 1 446 s | 1 748 269 | VERIFIED |
| A9, five axes, 81 cubes (k = 28) | 33 790 / 132 361 to 133 321 | Glucose, 76 to 661 s per cube for the runs that wrote the proofs on file (first runs 84 to 751 s) | 101 525 to 1 064 942 per cube, 27 320 489 in total | VERIFIED (all 81; 18 of them with the earlier build of the checker, see register, section C.2) |

The logs are `logs/certify_*.log`, `logs/prove_*.log`, `logs/drup_H4.out` (row A3) and
`logs/check_cubes.out`. Since the review, the proof checks of rows A1 and A8 and of the three-axis
case have logs of their own (`logs/certify_master_box3_2_k30_cuts.log`,
`logs/certify_master_box_4_1_k17_cuts.log`, `logs/certify_master_box_5_1_k28_in012_out34_cuts.log`).

Second solver, answers without a proof (`results/second_solver_d5_k28.json`,
`results/second_solver_roots_3_24_k32.json`): CaDiCaL finds all 83 formulas of row A9 unsatisfiable
(three axes 28 s; four axes 235 s; the 81 cubes 57 to 449 s each, 2.85 hours in total) and the formula
of row A7 unsatisfiable (357 s). Both solvers read the same formula files, so this checks the solvers
against each other, not the encoding.

Uniqueness runs (section C.1 of the register): the candidate problem for k = minimum, plus one
clause per listed Kochen-Specker set that excludes it, solved by Glucose with a checked proof
(`scripts/certify_unique.sh`, logs `logs/unique_enumerate_*.log`), for the six pools B(3, 2),
B(3, 3), B(3, 4), U(3, 6), U(3, 12) and B(4, 1). For the integer pools the encoder first checks that
the list of sets is closed under the signed coordinate permutations (log line "the list is closed
... (checked)"). The sizes of the formulas, the solver times, the numbers of lemmas and the verdicts
are in the table of section C.1 of the register; they are not copied here, because some of these runs
were repeated with the scripts as they are now and the register is updated from the logs.

Solver times are elapsed times of single runs on a machine that was running other jobs; they vary
from run to run (the three-axis formula took Glucose 81 s in an earlier run and 40 s in the logged
one). The cuts are found afresh in every run of engine A, so a repeated run gives a formula of a
different size and a different proof; the verdict is what has to agree.

Other runs:

* Tree certificates (engine C): 255 nodes for B(3, 2), 509 for B(4, 1), and two for B(3, 3): 11 330
  nodes on the whole 145-ray pool and 11 247 on its 97-ray core. All four are replayed by
  `verify_cert.mjs` (`verify/README.md`, `results/verify_summary.json`). The exhaustive tree search
  for U(3, 6) with bound 32 closed after 1 456 nodes in 0.2 s (`logs/dfs_roots_3_6_k32.log`).
* Enumerations of all minimum sets by engine A (`results/enumerate_*.json`, as rewritten by the
  uniqueness runs): 1.7 s for B(3, 2), 1.9 s for B(3, 3), 67.6 s for B(3, 4), 1.9 s for U(3, 6), 4.1 s
  for U(3, 12), 1.5 s for B(4, 1).
* Dimension five, bound 28 (section D of the register). Three axes: engine A infeasible in two runs
  (57 s and 9 s); Glucose unsatisfiable in 40 s, and in 58 s in the incremental variant; CaDiCaL
  unsatisfiable in 28 s. Four axes: engine A was stopped by hand without an answer; Glucose
  unsatisfiable in 24 minutes, CaDiCaL in 4 minutes. Five axes: engine A was stopped by hand without
  an answer; Glucose closed all 81 cubes, each in 84 to 751 seconds, median 222 seconds; CaDiCaL
  closed the same 81 formulas, median 112 seconds. For 21 of the 81 cubes the formula and proof on
  file come from a later run of the cube, made to write the proof (the second run for 20 cubes, the
  third for cube 0110).
* Controls for dimension five. With bound 29 the three-axis case and the four-axis case each find a
  29-ray Kochen-Specker set; with bound 31 the five-axis case, run in cube 2211, finds a 31-ray
  Kochen-Specker set with all five axes (`logs/satcegar_box_5_1_k31_in01234_cube2211.log`). Plain
  random deletion with the axes deleted last (`scripts/axes_sanity.py`,
  `results/d5_axes_sanity.json`): 3828 samples, 4 with three axes, 90 with four, 3734 with five.
* Randomised searches (section E of the register): 10 to 15 minutes per pool; the three small pools
  B(3, 2), B(4, 1), B(5, 1) were run again for 10 minutes on 10 November to have a log.
* Small computations behind single statements of the register, each with a result file:
  `scripts/pool_facts.py` (pool sizes for H up to 10; empty cores of U(3, N) for N = 2 to 5 and 7 to
  11; `logs/pool_facts.log`), `scripts/min_missed.py` (fewest bases missed, exact MaxSAT;
  `logs/min_missed.log`), `scripts/peres24.py` (the 16 minimum sets of B(4, 1) lie in the 24 rays of
  Peres), `scripts/d5_sections.py` (which sections of the recorded dimension-five sets by a coordinate
  hyperplane are Kochen-Specker sets), `scripts/ablate_c1c2.py` (effect of the two necessary
  conditions; `logs/ablate_c1c2_box3_4_k30.log`).
* Stack demonstration (`results/stack_demo.json`, generated 2026-11-10 08:06:14 UTC): all seven
  stages PASS. It is a simulation on an ordinary computer and is not part of any proof.

## 4. What failed, was stopped, was wrong, or was not achieved

From section G of the register, from the logs and from the review before release
([REVIEW.md](REVIEW.md)):

* **No record was broken.** No Kochen-Specker set smaller than a published one was found in any
  dimension.
* **A7, Glucose.** For U(3, 24) the cuts were re-verified and the formula was written (34 372
  variables, 141 027 clauses), then Glucose stopped with an out-of-memory error at its 32-bit clause
  memory (`logs/certify_master_roots_3_24_k32_cuts.log`). Glucose gave no answer for this pool. The
  same formula was then solved by CaDiCaL 1.9.5: unsatisfiable, twice (357 s without a proof, 338 s
  with a proof; `logs/second_solver_roots_3_24_k32.log`,
  `logs/prove_master_roots_3_24_k32_cuts_cadical195.log`). The CaDiCaL proof was accepted by
  `verify/drup_check`: 1 464 683 lemmas checked, VERIFIED. The row therefore rests on engine A and
  on a checked proof of the second solver, not on Glucose.
* **Lean, B(3, 3).** A Lean module for all 145 rays (certificate of 11 330 nodes) was generated, but
  its kernel check was stopped after 49 minutes without a verdict (`logs/lean_box3h3.out`). Nothing is
  claimed and the module is not in the repository. B(3, 3) is covered by the two tree certificates,
  by engine A and by checked proofs of engine B.
* **Dimension five, engine A.** Engine A closed only the three-axis case. Its runs for the four-axis
  and the five-axis case were stopped by hand without an answer; the logs do not record the stop, and
  section D of the register words what is known about their duration. These two cases rest on engine B with two
  solvers and on the proof checks listed in section 3.
* **B(3, 5).** The exact search did not finish; it was stopped by hand after more than an hour (the
  log ends at round 10 and does not record the stop). No claim.
* **U(3, 30).** Stopped unfinished. No claim.
* **U(6, 3) and the E8 pool.** Whether 21 and 34 are the minima there was not decided; both exact
  searches were stopped unfinished.
* **The general problem.** Dimension three between 24 and 31, and dimensions five and above between
  18 and the records, are not settled by pool results.
* **Randomised search in U(3, 24).** The walk stopped at 36 rays although the pool contains 33-ray
  sets. An earlier table left this row out.
* **A3, first checker call.** In `logs/certify_master_box3_4_k30_cuts.log` the solver step ended with
  "unsatisfiable" and the checker step ended with exit status 127 without checking anything. The
  proof was checked in a separate call (`logs/drup_H4.out`: 443 604 lemmas, VERIFIED), and checked
  again on 10 November with the release build of the checker, with the same counts and exit status 0
  (end of `logs/certify_master_box3_4_k30_cuts.log`).
* **A wrong remark about dimension five, withdrawn.** Earlier versions of the register and the paper
  said that no critical Kochen-Specker set with all five coordinate axes had been met in a large
  number of random samples and that the case might be empty. Two reviewers found such sets within
  seconds. The sampler was biased: it replaced the set by the solver's unsatisfiable core after every
  deletion. With plain deletion 3734 of 3828 samples end with five axes. The remark and the open
  question were rewritten, and the five-axis case received a positive control. No theorem depended on
  the remark ([REVIEW.md](REVIEW.md), finding 6).
* **Two published reports were missed by the first literature search.** Pavičić and Megill (2022)
  report 29 rays as the smallest critical set generated from the coordinates 0, +1, -1 in dimension
  five, and Waegell and Aravind (2011) count the 16 sets of 18 rays inside the 24 rays of Peres, which
  are the 16 minimum sets of B(4, 1). The paper had called the dimension-five value new and had not
  credited the 16 sets. Both were found by the review, and the claims were narrowed
  ([REVIEW.md](REVIEW.md), findings 1 and 2). The same review found that earlier reports for dimension
  three had been understated (four pools, not two; finding 3).
* **Other findings of the review that changed a claim** ([REVIEW.md](REVIEW.md), findings 4, 5, 7 and
  8): "a certificate for every result" was not true while row A7 had one solver's answer only; the
  Lean theorems were about tables, not vectors, and the abstract credited Lean with the counts of
  minimum sets; the counts rested on an unchecked closure property; and a comparison of rounds with
  and without the conditions (C1), (C2) compared two different programs and was replaced by a
  controlled run.
* **Defects found and corrected during the work.** While the soundness theorems were being proved in
  Lean, the first versions of both certificate checkers turned out to accept malformed certificates;
  the definitions were corrected and the counterexamples are now rejected (paper, Section 5;
  `lean/KS/Tests.lean`). A mutation check of the unit tests detected 20 of 21 injected single-line
  bugs; the one not detected changes nothing for the pools that are used (`tests/README.md`). The
  review found that `scripts/certify.sh` could have checked a proof left by an earlier run and that
  cube fixes could leak from the environment into a run without cubes; both were fixed
  (`scripts/certify.sh` and `scripts/certify_unique.sh` now delete an older proof first, clear the
  variables that restrict a run to one cube, and end with exit status 0 only if the proof of that run
  was VERIFIED). After the review a reviewer showed that the old reader of the proof checker let a
  token such as 4294967296 wrap around to 0. The project's formulas cannot trigger this (their largest
  variable is 76 220), but the reader was rewritten: `verify/drup_check.c` now accepts only decimal
  integers of absolute value at most 10^8, requires a "p cnf" line, refuses a formula whose clause
  count or largest variable differs from that line, and reports running out of memory instead of
  crashing (exit status 0 accepted, 1 rejected, 2 unreadable input or out of memory). The new cases
  are in `tests/test_drup.py`.
* **Records that do not exist.** The times at which the three runs stopped by hand were stopped
  (engine A on the four-axis and the five-axis case, and on B(3, 5)) are not in any log. No engine-A
  log with bound 32 is kept for U(3, 6); that row has the exhaustive tree search, the enumeration run
  and the checked uniqueness proof instead.

## 5. Trust base

For a result marked **Lean** (rows A1 and A8, theorems L0 to L4): the Lean kernel, and the reading of
the statement of the two main theorems and of the definitions they use: `boxRays`, `dot`, `card`,
`Sub` and `VColorable`, about 25 lines, printed in full in `lean/README.md`. The statement is about
the integer vectors of the pool: `boxRays d H` is defined in Lean as the list of primitive integer
vectors of the box with positive first non-zero entry, and `VColorable` speaks of dot products only.
Proved inside Lean, and therefore not trusted: that the table notion and the vector notion of
colorability agree (L3); that the list of vectors of each data module is `boxRays d H` and that every
non-zero integer vector of the box is parallel to exactly one listed ray (L4); that the orthogonality
table is "dot product zero" and the list of bases is the set of all d-cliques; and that the two
certificate checkers are sound (L0). Tables, certificates, the Python generator and the Lean compiler
are not trusted. The axioms used are `propext`, `Classical.choice` and `Quot.sound`. The Lean
theorems cover the two minimum values only, not the counts of minimum sets.

For a result marked **proof-checked**: the construction of the pool; the encoder `src/ks_cnf.py`
(that the formula says what the paper says); the verification of each cut from its independent set;
the proof checker `verify/drup_check.c`; Lemmas 1, 3, 6 and 7 of `paper/PROOFS.md`, which are proved
on paper and not formalised. The solvers are not trusted. The proof checker is a program of about 310
lines written for this project; it reads its input strictly, it is tested on correct proofs, corrupted
proofs, malformed files and satisfiable formulas, and it is not formally verified. It has not been
cross-checked against another proof checker (see [TRIGGER-REGISTER.md](TRIGGER-REGISTER.md), item
T2). For the four-axis case of row A9 the same formula was proved unsatisfiable by two different
solvers and both proofs were checked: the CaDiCaL proof (1 614 075 lemmas) and the Glucose proof
(1 748 269 lemmas) were both VERIFIED. For row A7 the checked proof is CaDiCaL's.

For a result that has a **second solver** but no checked proof for that solver: both solvers read the
same formula file, so their agreement says something about the solvers and nothing about the encoder.

For a result marked **tree**: the JavaScript verifier `verify/verify_cert.mjs` and the Node runtime.
The verifier recomputes orthogonality and all bases from the integer vectors in the certificate file
and its replay is duplicated by a second implementation in its test file; neither is machine-verified.
It does not check that the rays in the file are the pool the paper describes.

For a result marked **A** or **B** without a checked proof: additionally the solver that gave the
answer (CP-SAT of OR-Tools, or Glucose 4.1 or CaDiCaL 1.9.5 through PySAT).

For the uniqueness counts ("exactly n"): the lists are produced by engine A and the symmetry and
graph-isomorphism code of `scripts/enumerate_min.py`, but the statement no longer rests on them alone.
For all six pools engine B proves, with a checked proof, that no Kochen-Specker set of at most the
minimum size exists besides the listed ones (section C.1 of the register). Where the formula contains
symmetry breaking, that proof shows that every minimum set is an image of a listed set, and the
encoder checks that the list is closed under the signed coordinate permutations and stops otherwise.
The trust base is that of "proof-checked", together with this closure check.

The randomised searches and the stack demonstration carry no claim of optimality or proof.

The review before release ([REVIEW.md](REVIEW.md)) was made by instances of the AI system that
produced the work. It is an internal check, not peer review.

## 6. Spot checks made while writing this report

On 10 November 2026, on the same machine:

* `verify/drup_check` on the stored formula and proof of row A1
  (`results/master_box3_2_k30_cuts.cnf`, `.drat`): 20 223 original clauses, 191 lemmas checked,
  `s VERIFIED`, 0.2 s. The same for row A8 (`results/master_box_4_1_k17_cuts.cnf`, `.drat`): 16 847
  original clauses, 307 lemmas checked, `s VERIFIED`, 0.2 s. These agree with section C of the
  register. Both checks now also have logs of their own (section 3).
* `python src/gen_cert.py 30 <file> box3 3` regenerated the certificate of the 97-ray core of
  B(3, 3): 11 247 nodes in 2.6 s, tree and pool re-check passed, content equal to
  `results/cert_box3_H3_k30.json`.
* An earlier spot check started a re-check of the stored proof of the three-axis case with a time
  limit of 170 seconds; it did not finish within the limit, which was neither a pass nor a fail. It is
  superseded by the full check that is now logged: 94 680 lemmas checked, VERIFIED
  (`logs/certify_master_box_5_1_k28_in012_out34_cuts.log`).
* The axiom audit was extended after the review: `lean/KS/Audit.lean` now prints the axioms of 26
  theorems. The expected output is in `lean/README.md`; the `lean` stage of `scripts/run_all.py` runs
  the audit and fails if a theorem named there depends on anything other than `propext`,
  `Classical.choice` and `Quot.sound`.

## 7. Reproducing

```
python -m pip install -r requirements.txt
python scripts/run_all.py --lean
node verify/test_verify.mjs
```

The longer runs are reproduced with the commands of [INDEX.md](INDEX.md). Expect minutes for rows A3,
A6 and A7 with engine A, minutes for the four-axis case with CaDiCaL and about half an hour with
Glucose, and several hours of solver time for the 81 cubes (the paper gives about 6 hours summed over
the cubes for Glucose and about 3 hours for CaDiCaL). The proof checks take additional time.

## 8. Release and archiving

Done on 10 November 2026 (times UTC), after the CI run 42808925275 (workflow `ci`) had passed on
commit `06e4c13`. The full record, with every request and answer, is
[results/release_archiving.json](../results/release_archiving.json).

| step | outcome |
|---|---|
| repository | made public: https://github.com/0thernes/kochen-specker-extremal-lab |
| release v1.0.0 | published 11:41:03, tag at commit `06e4c13`; assets `ks-minimum.pdf` (119 381 bytes, SHA-256 `8063949e478c41b9...f5ae967`) and `arxiv-source.zip` (17 802 bytes, SHA-256 `1e6d40ab2533ef8a...0d90907`), the files of `publication/ks-minimum/` at that commit |
| GitHub Pages | built from `main`, folder `/docs`: https://0thernes.github.io/kochen-specker-extremal-lab/ ; all 19 files the site serves were fetched and are byte-identical to the repository's `docs/` |
| Software Heritage | save request 2636249, visit 11:41:55, status full; snapshot `swh:1:snp:fdc362b2aca1a4a3c32cda671d8033bcaea0901f`, whose branches `main` and `v1.0.0` both point to `06e4c13` |
| Internet Archive | captures 11:44:45 (site), 11:45:13 (`paper.html`), 11:45:39 (`ks-minimum.pdf`), 11:51:35 and 11:52:07 (the register and the paper source at the tag, as raw files from `raw.githubusercontent.com`); each capture was downloaded again and is byte-identical to the file at the tag. The save service answered HTTP 523 twice for the four github.com pages (repository, release, register and paper source); those pages have no capture, and the repository itself is preserved by Software Heritage |

Not done by the release process, and left to the author: arXiv, Journal of Physics A and ORCID, and
Zenodo only after its ruling (see `publication/README.md`); Google Scholar and OpenAIRE index on their
own. The search of register section G (B(3, 5) with CaDiCaL) was still running when the release was
made; the register reports it as not answered, and a later answer would be recorded in a new version.
