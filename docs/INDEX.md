# Index: where each claim is proved, regenerated and logged

Kochen-Specker Extremal Lab, version 1.0.0. The claims are those of the register
[results/RESULTS.md](../results/RESULTS.md), in its numbering. The status words are the register's;
where this page and the register differ, the register is right. Terms: [GLOSSARY.md](GLOSSARY.md).
Overview: [SUMMARY.md](SUMMARY.md). What was run and what failed: [REPORT.md](REPORT.md). What the
review before release found: [REVIEW.md](REVIEW.md).

## Documents

| document | what it is |
|---|---|
| [README.md](../README.md) | front page: plain-language account, results, how to check, prior work, limits |
| [paper/ks-minimum.md](../paper/ks-minimum.md) | the paper |
| [paper/PROOFS.md](../paper/PROOFS.md) | Lemmas 1 to 7 with their proofs |
| [results/RESULTS.md](../results/RESULTS.md) | the register: every result and its status |
| [SUMMARY.md](SUMMARY.md), [GLOSSARY.md](GLOSSARY.md) | plain-language summary; terms |
| [REPORT.md](REPORT.md) | verification report: runs, versions, timings, failures, trust base |
| [REVIEW.md](REVIEW.md) | the review before release: findings and what was changed |
| [TRIGGER-REGISTER.md](TRIGGER-REGISTER.md) | deferred items and the conditions that trigger them |
| [lean/README.md](../lean/README.md) | the Lean 4 development: statements, definitions, files, axiom audit |
| [verify/README.md](../verify/README.md) | the JavaScript verifier: rule, checks, tests, limits |
| [tests/README.md](../tests/README.md) | the unit tests |
| [third_party/README.md](../third_party/README.md) | vendored third-party files |
| [LEGAL.md](../LEGAL.md), [LICENSE](../LICENSE), [NOTICE](../NOTICE) | licence, third-party notices, authorship and AI disclosure |
| [CITATION.cff](../CITATION.cff), [CHANGELOG.md](../CHANGELOG.md), [VERSION](../VERSION) | citation, versions |
| [CONTRIBUTING.md](../CONTRIBUTING.md), [SECURITY.md](../SECURITY.md), [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) | reporting errors and contributing; security reports; conduct |
| [publication/README.md](../publication/README.md) | files prepared for the author's submissions |

## Command forms

All commands are run from the repository root. `<kind> <args>` names the pool: `box3 H` for B(3, H)
(built directly as its core), `box d H` for B(d, H), `boxfull d H` for the whole pool B(d, H) without
the reduction to the core, `roots d N` for U(d, N), `e8` for the E8 root rays. `<case>` is `-` for
none, or a quoted string such as `"in:0,1,2;out:3,4"` (coordinate axes that must be in the set and
that must be out). Unlike `scripts/run_all.py`, these programs write in place: they append to their
log in `logs/` and overwrite their result file in `results/`.

| form | command | writes |
|---|---|---|
| M (engine A) | `python -u src/ksmaster.py <k> <seconds or -> <workers> <case> <kind> <args>` | `logs/master_<pool>_k<k>[_<case>].log`, `results/master_<pool>_k<k>[_<case>]_cuts.json` |
| B (engine B) | `python -u src/ks_cnf.py results/<cuts>.json <k> <case> g4 <kind> <args>`, then `verify/drup_check results/<cuts>.cnf results/<cuts>.drat` | `results/<cuts>.cnf`, `results/<cuts>.drat`; the checker prints `s VERIFIED` |
| B' (both steps of B) | `bash scripts/certify.sh <cuts> <k> <case> <kind> <args>` | the same files and `logs/certify_<cuts>.log` |
| U (uniqueness run) | `bash scripts/certify_unique.sh <k> <kind> <args>` | repeats form E, then engine B on the candidate problem with the listed sets excluded, then the proof check: `results/enumerate_<pool>_k<k>.json`, `results/enumerate_<pool>_k<k>_cuts.json`, `.cnf`, `.drat`, `logs/unique_enumerate_<pool>_k<k>.log` |
| S (engine B, incremental) | `python -u src/ks_satcegar.py <k> <case> g4 <seedpairs> <kind> <args>` | `logs/satcegar_<pool>_k<k>[_<case>].log`, `results/satcegar_..._cuts.json`, and the final `.cnf` and `.drat` |
| S2 (second solver, answer only) | `python -u scripts/second_solver.py <solver> <parallel> <timeout> <tag> <cnf files...>` | `results/second_solver_<tag>.json`, `logs/second_solver_<tag>.log` |
| P (second solver, with proof) | `python -u scripts/prove_cnf.py <solver> <formula.cnf> <proof.drat> --check` | the proof file; prints the solver's answer and the verdict of `verify/drup_check` (the output of the runs of the register is kept in `logs/prove_*.log`) |
| T (tree certificate) | `python src/gen_cert.py <k> <out.json> <kind> <args>`, then `node verify/verify_cert.mjs <out.json>` | the certificate; the verifier prints a JSON summary with the verdict |
| D (tree search, no certificate) | `python -u src/ksdfs.py <k> <seconds or -> <kind> <args>` | `logs/dfs_<pool>_k<k>.log` |
| E (enumeration) | `python -u scripts/enumerate_min.py <k> <kind> <args>` | `results/enumerate_<pool>_k<k>.json` |
| H (randomised search) | `python -u src/hunt.py <seconds> <seed> <kind> <args>` | `logs/hunt_<pool>_s<seed>.log`, `results/hunt_<pool>_s<seed>.json` |

In forms S2 and P the solver name used for the register is `cadical195` (CaDiCaL 1.9.5 through
PySAT); `g4` is Glucose 4.1. Both forms read a formula file written by form B or S; they do not build
the formula.

The proof checker is compiled with `gcc -O2 -o verify/drup_check verify/drup_check.c`. The scripts
`scripts/certify.sh` and `scripts/certify_unique.sh` use `verify/drup_check.exe` if it exists and
`verify/drup_check` otherwise. Both delete a proof file left by an earlier run before they start, and
both end with exit status 0 only if the proof of that run was written and VERIFIED.
`src/ks_cnf.py` ends with exit status 3 if its formula is satisfiable. The `.cnf` and `.drat` files
are not kept in the Git repository (they are regenerated by forms B, U, S and P; see
[TRIGGER-REGISTER.md](TRIGGER-REGISTER.md), item T1). The cut files `results/*_cuts.json`, from which
form B rebuilds the formula, are kept.

## Claims and their evidence

Cells that hold one of the words CUBELEMMAS, CUBEVERDICT repeat the cell of the same name in
sections C and D of the register.

| claim | evidence file | command that regenerates it | log or record | status |
|---|---|---|---|---|
| **A1** B(3, 2), 49 rays: minimum 31. Lean | `lean/KS/Box3H2.lean`, theorem `KS.Box3H2.minimum_ks_size_vectors` | `cd lean && lake build`; or `python scripts/run_all.py --lean` | `results/run_all.json` (stage `lean`) | Lean |
| A1, tree certificate (255 nodes) | `results/cert_box3_H2_k30.json` | T: `python src/gen_cert.py 30 results/cert_box3_H2_k30.json box3 2`, `node verify/verify_cert.mjs results/cert_box3_H2_k30.json`; also stages `cert-gen`, `cert-verify` of `run_all.py` | `results/verify_summary.json`, `results/run_all.json` | tree |
| A1, engine A (k = 30) | `results/master_box3_2_k30_cuts.json` | M: k = 30, `box3 2` | `logs/master_box3_2_k30.log` | A |
| A1, engine B (k = 30) | `results/master_box3_2_k30_cuts.cnf`, `.drat` (regenerated) | B': `bash scripts/certify.sh master_box3_2_k30_cuts 30 - box3 2`; stage `drup-49` of `run_all.py` repeats the whole route with fresh cuts | `logs/certify_master_box3_2_k30_cuts.log` (191 lemmas, `s VERIFIED`); `results/run_all.json` (stage `drup-49`) | B proof-checked |
| A1, a 31-ray KS set exists (71 orthogonal pairs, 17 bases, critical) | `results/ks31_box3_H2.json`, `results/ks_sets.json` | `node verify/verify_cert.mjs --ks results/ks31_box3_H2.json --require-critical`; `python scripts/collect_sets.py` | `results/verify_summary.json` | re-verified as a critical KS set |
| **A2** B(3, 3), 145 rays (core 97): minimum 31. Tree certificate on the whole pool (11 330 nodes) | `results/cert_box3_H3full_k30.json` | T: `python src/gen_cert.py 30 results/cert_box3_H3full_k30.json boxfull 3 3`, `node verify/verify_cert.mjs results/cert_box3_H3full_k30.json` | `results/verify_summary.json` | tree |
| A2, tree certificate on the core (11 247 nodes) | `results/cert_box3_H3_k30.json` | T: `python src/gen_cert.py 30 results/cert_box3_H3_k30.json box3 3`, `node verify/verify_cert.mjs results/cert_box3_H3_k30.json` | `results/verify_summary.json` | tree |
| A2, engine A (k = 30) | `results/master_box3_3_k30_cuts.json` | M: k = 30, `box3 3` | `logs/master_box3_3_k30.log` | A |
| A2, engine B (k = 30) | `results/master_box3_3_k30_cuts.cnf`, `.drat` (regenerated) | B': `bash scripts/certify.sh master_box3_3_k30_cuts 30 - box3 3` | `logs/certify_master_box3_3_k30_cuts.log` (2 447 lemmas, `s VERIFIED`) | B proof-checked |
| **A3** B(3, 4), 289 rays (core 205): minimum 31. Engine A (k = 30) | `results/master_box3_4_k30_cuts.json` | M: k = 30, `box3 4` | `logs/master_box3_4_k30.log` | A |
| A3, engine B (k = 30) | `results/master_box3_4_k30_cuts.cnf`, `.drat` (regenerated) | B': `bash scripts/certify.sh master_box3_4_k30_cuts 30 - box3 4` | `logs/certify_master_box3_4_k30_cuts.log` (solver: unsatisfiable in 736 s; the checker step of that script call ended with exit status 127), `logs/drup_H4.out` (the check of that proof, made by a separate call: 443 604 lemmas, `s VERIFIED`) | B proof-checked |
| **A4** U(3, 6), 57 rays: minimum 33. Exhaustive tree search (1 456 nodes, k = 32) | none stored (no certificate file) | D: `python -u src/ksdfs.py 32 - roots 3 6` | `logs/dfs_roots_3_6_k32.log` | exhaustive tree search |
| A4, engine A | `results/enumerate_roots_3_6_k33.json` (the candidate problem with bound 33, run until infeasible, finds only 33-ray sets) | E: k = 33, `roots 3 6` | `logs/enumerate_batch.out`, `logs/unique_enumerate_roots_3_6_k33.log`; no engine-A log with bound 32 is kept | A (enumeration run) |
| A4, engine B | `results/enumerate_roots_3_6_k33_cuts.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 33 roots 3 6` (see C.1 below; this run also re-proves the minimum) | `logs/unique_enumerate_roots_3_6_k33.log` (`s VERIFIED`; figures in section C.1 of the register) | B proof-checked (uniqueness run) |
| **A5** U(3, 12), 183 rays: minimum 33. Engine A (k = 32) | `results/master_roots_3_12_k32_cuts.json` | M: k = 32, `roots 3 12` | `logs/master_roots_3_12_k32.log` | A |
| A5, engine B (k = 32) | `results/master_roots_3_12_k32_cuts.cnf`, `.drat` (regenerated) | B': `bash scripts/certify.sh master_roots_3_12_k32_cuts 32 - roots 3 12` | `logs/certify_master_roots_3_12_k32_cuts.log` (39 774 lemmas, `s VERIFIED`) | B proof-checked |
| **A6** U(3, 18), 381 rays: minimum 33. Engine A (k = 32) | `results/master_roots_3_18_k32_cuts.json` | M: k = 32, `roots 3 18` | `logs/master_roots_3_18_k32.log` | A |
| A6, engine B (k = 32) | `results/master_roots_3_18_k32_cuts.cnf`, `.drat` (regenerated) | B': `bash scripts/certify.sh master_roots_3_18_k32_cuts 32 - roots 3 18` | `logs/certify_master_roots_3_18_k32_cuts.log` (367 001 lemmas, `s VERIFIED`) | B proof-checked |
| **A7** U(3, 24), 651 rays: minimum 33. Engine A (k = 32) | `results/master_roots_3_24_k32_cuts.json` | M: k = 32, `roots 3 24` | `logs/master_roots_3_24_k32.log` | A |
| A7, engine B with Glucose | `results/master_roots_3_24_k32_cuts.cnf` (the formula, 34 372 variables and 141 027 clauses; regenerated); no answer | B': `bash scripts/certify.sh master_roots_3_24_k32_cuts 32 - roots 3 24` | `logs/certify_master_roots_3_24_k32_cuts.log` (cuts re-verified, formula written, then Glucose ran out of its 32-bit clause memory) | no answer from Glucose |
| A7, engine B with CaDiCaL, answer | `results/second_solver_roots_3_24_k32.json` (unsatisfiable, 357 s) | S2: `python -u scripts/second_solver.py cadical195 1 14400 roots_3_24_k32 results/master_roots_3_24_k32_cuts.cnf` | `logs/second_solver_roots_3_24_k32.log` | second solver |
| A7, engine B with CaDiCaL, proof | `results/master_roots_3_24_k32_cuts.cadical195.drat` (regenerated) | P: `python -u scripts/prove_cnf.py cadical195 results/master_roots_3_24_k32_cuts.cnf results/master_roots_3_24_k32_cuts.cadical195.drat --check` | `logs/prove_master_roots_3_24_k32_cuts_cadical195.log` (unsatisfiable in 338 s; 1 464 683 lemmas, `s VERIFIED`) | B with CaDiCaL, proof-checked |
| **A8** B(4, 1), 40 rays: minimum 18. Lean | `lean/KS/Box4H1.lean`, theorem `KS.Box4H1.minimum_ks_size_vectors` | `cd lean && lake build`; or `python scripts/run_all.py --lean` | `results/run_all.json` (stage `lean`) | Lean |
| A8, tree certificate (509 nodes) | `results/cert_box4_H1_k17.json` | T: `python src/gen_cert.py 17 results/cert_box4_H1_k17.json box 4 1`, `node verify/verify_cert.mjs results/cert_box4_H1_k17.json`; also `run_all.py` | `results/verify_summary.json`, `results/run_all.json` | tree |
| A8, engine A (k = 17) | `results/master_box_4_1_k17_cuts.json` | M: k = 17, `box 4 1` | `logs/master_box_4_1_k17.log` | A |
| A8, engine B (k = 17) | `results/master_box_4_1_k17_cuts.cnf`, `.drat` (regenerated) | B': `bash scripts/certify.sh master_box_4_1_k17_cuts 17 - box 4 1`; stage `drup-40` of `run_all.py` | `logs/certify_master_box_4_1_k17_cuts.log` (307 lemmas, `s VERIFIED`); `results/run_all.json` (stage `drup-40`) | B proof-checked |
| A8, the 16 minimum sets are the 16 known 18-ray sets inside the 24 rays of Peres | `results/peres24_check.json` (all 16 sets use only rays with one, two or four non-zero coordinates) | `python scripts/peres24.py` | the JSON file | computed |
| **A9** B(5, 1), 121 rays (core 105): minimum 29 | the three cases of section D below | see D1 to D3 | see D1 to D3 | B and a second solver, with case analysis; proof checks as in D1 to D3 |
| A9, a 29-ray KS set exists; at least two non-isomorphic ones | `results/ks_sets.json`: one with three axes (151 orthogonal pairs, 16 bases) and one with four axes (150 orthogonal pairs, 16 bases); `results/d5_sections.json` (which sections by a coordinate hyperplane are KS sets) | `python scripts/collect_sets.py`; `python scripts/d5_sections.py`; M: k = 29, case `"in:0,1,2;out:3,4"`, `box 5 1`; S: k = 29, case `"in:0,1,2,3;out:4"`, `box 5 1` | `logs/master_box_5_1_k29_in012_out34.log`, `logs/satcegar_box_5_1_k29_in0123_out4_cubesanityk29.log` | found; both sets are re-verified as critical KS sets |
| **Counts (engine A).** B(3, 2): exactly 6 sets of 31 rays, one orbit | `results/enumerate_box3_2_k31.json` | E: k = 31, `box3 2` | `logs/unique_enumerate_box3_2_k31.log` | A (enumeration) |
| B(3, 3): exactly 6, one orbit | `results/enumerate_box3_3_k31.json` | E: k = 31, `box3 3` | `logs/enumerate_batch.out`, `logs/unique_enumerate_box3_3_k31.log` | A (enumeration) |
| B(3, 4): exactly 6, one orbit | `results/enumerate_box3_4_k31.json` | E: k = 31, `box3 4` | `logs/enumerate_batch.out`, `logs/unique_enumerate_box3_4_k31.log` | A (enumeration) |
| U(3, 6): exactly 3, one orbit | `results/enumerate_roots_3_6_k33.json` | E: k = 33, `roots 3 6` | `logs/enumerate_batch.out`, `logs/unique_enumerate_roots_3_6_k33.log` | A (enumeration) |
| U(3, 12): exactly 12, one orbit | `results/enumerate_roots_3_12_k33.json` | E: k = 33, `roots 3 12` | `logs/enumerate_batch.out`, `logs/unique_enumerate_roots_3_12_k33.log` | A (enumeration) |
| B(4, 1): exactly 16 sets of 18 rays, one orbit | `results/enumerate_box_4_1_k18.json` | E: k = 18, `box 4 1` | `logs/unique_enumerate_box_4_1_k18.log` | A (enumeration) |
| **C.1 Uniqueness runs (engine B, proof-checked).** B(3, 2): no KS set with at most 31 rays besides the 6 listed | `results/enumerate_box3_2_k31_cuts.json`; `.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 31 box3 2` | `logs/unique_enumerate_box3_2_k31.log` (line "the list is closed ... (checked)", then the verdict of the proof check) | VERIFIED (sizes, times and lemma counts: register, section C.1) |
| C.1, B(3, 3), 6 sets excluded | `results/enumerate_box3_3_k31_cuts.json`; `.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 31 box3 3` | `logs/unique_enumerate_box3_3_k31.log` | VERIFIED (register, section C.1) |
| C.1, B(3, 4), 6 sets excluded | `results/enumerate_box3_4_k31_cuts.json`; `.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 31 box3 4` | `logs/unique_enumerate_box3_4_k31.log` | VERIFIED (register, section C.1) |
| C.1, U(3, 6), 3 sets excluded | `results/enumerate_roots_3_6_k33_cuts.json`; `.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 33 roots 3 6` | `logs/unique_enumerate_roots_3_6_k33.log` | VERIFIED (register, section C.1) |
| C.1, U(3, 12), 12 sets excluded | `results/enumerate_roots_3_12_k33_cuts.json`; `.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 33 roots 3 12` | `logs/unique_enumerate_roots_3_12_k33.log` | VERIFIED (register, section C.1) |
| C.1, B(4, 1), 16 sets excluded | `results/enumerate_box_4_1_k18_cuts.json`; `.cnf`, `.drat` (regenerated) | U: `bash scripts/certify_unique.sh 18 box 4 1` | `logs/unique_enumerate_box_4_1_k18.log` | VERIFIED (register, section C.1) |
| **Upper bounds.** Seven explicit KS sets: 31 rays (dimension three), 18 rays (dimension four), 29 rays with three axes, 29 rays with four axes and 31 rays with five axes (dimension five), 33 rays for twelfth and for sixth roots of unity; each a critical KS set | `results/ks_sets.json` | `python scripts/collect_sets.py` (`--add-explicit` adds the four-axis and the five-axis set to an existing file) | none | re-verified by the script |
| Pools without any KS set: U(3, N) for N = 2, 3, 4, 5, 7, 8, 9, 10, 11 (the core is empty) | `results/pool_facts.json` | `python scripts/pool_facts.py` | `logs/pool_facts.log` | computed |
| **L0** soundness of the two certificate checkers | `lean/KS/Basic.lean`: `KS.small_sets_colorable`, `KS.not_colorable_of_refute` | `cd lean && lake build && lake env lean KS/Audit.lean` | `results/run_all.json` (stage `lean`, axioms of each theorem) | Lean |
| **L1** `KS.Box3H2.minimum_ks_size_vectors` (the statement for the integer vectors `boxRays 3 2`) | `lean/KS/Box3H2.lean` (generated by `python scripts/gen_lean.py Box3H2 31 boxfull 3 2`) | `cd lean && lake build && lake env lean KS/Audit.lean` | `results/run_all.json` (stage `lean`); expected audit output in `lean/README.md` | Lean |
| **L2** `KS.Box4H1.minimum_ks_size_vectors` (the statement for the integer vectors `boxRays 4 1`) | `lean/KS/Box4H1.lean` (generated by `python scripts/gen_lean.py Box4H1 18 boxfull 4 1`) | `cd lean && lake build && lake env lean KS/Audit.lean` | `results/run_all.json` (stage `lean`); expected audit output in `lean/README.md` | Lean |
| **L3** `KS.vcolorable_of_colorable`, `KS.colorable_of_vcolorable`: for a table that passes the three checks, colorability of the table and colorability phrased with dot products agree | `lean/KS/Spec.lean` | `cd lean && lake build && lake env lean KS/Audit.lean` | `results/run_all.json` (stage `lean`) | Lean |
| **L4** `rays_eq`, `boxRays_exact` in each data module: the listed vectors are `boxRays d H`, and every non-zero integer vector of the box is parallel to exactly one of them | `lean/KS/Box3H2.lean`, `lean/KS/Box4H1.lean` | `cd lean && lake build && lake env lean KS/Audit.lean` | `results/run_all.json` (stage `lean`) | Lean |
| Lean regression tests (malformed certificates and wrong tables are rejected) | `lean/KS/Tests.lean` | `cd lean && lake build` | `results/run_all.json` (stage `lean`) | Lean (tests) |
| (not done) B(3, 3) in Lean, all 145 rays | none: the generated module is not in the repository | `python scripts/gen_lean.py Box3H3 31 boxfull 3 3` would regenerate the module | `logs/lean_box3h3.out` (the kernel check was stopped after 49 minutes without a verdict) | not done; nothing claimed |
| **D0** Lemma 7: every basis of B(5, 1) contains a coordinate axis; the pool without three axes is colorable | `results/lemma7_d5_axes.json` | `python scripts/lemma7.py`; stage `lemma7` of `run_all.py` | `results/run_all.json` (stage `lemma7`) | recomputed with integer arithmetic |
| **D1** exactly three axes, k = 28: engine A infeasible (two runs) | `results/master_box_5_1_k28_in012_out34_cuts.json` | M: k = 28, case `"in:0,1,2;out:3,4"`, `box 5 1` | `logs/master_box_5_1_k28_in012_out34.log` | A |
| D1, engine B with Glucose: unsatisfiable (29 500 variables, 114 428 clauses), proof checked | `results/master_box_5_1_k28_in012_out34_cuts.cnf`, `.drat` (regenerated); incremental run: `results/satcegar_box_5_1_k28_in012_out34_cuts.json` | B': `bash scripts/certify.sh master_box_5_1_k28_in012_out34_cuts 28 "in:0,1,2;out:3,4" box 5 1`; S: k = 28, same case | `logs/certify_master_box_5_1_k28_in012_out34_cuts.log` (unsatisfiable in 40 s; 94 680 lemmas, `s VERIFIED`); `logs/satcegar_box_5_1_k28_in012_out34.log` (incremental run) | Glucose proof VERIFIED |
| D1, second solver: unsatisfiable (28 s) | `results/second_solver_d5_k28.json` | S2, see the last row of D3 | `logs/second_solver_d5_k28.log` | second solver |
| **D2** exactly four axes, k = 28: engine A | none | M: k = 28, case `"in:0,1,2,3;out:4"`, `box 5 1` | `logs/master_box_5_1_k28_in0123_out4.log` (the log does not record the stop) | stopped by hand without an answer |
| D2, engine B with Glucose: unsatisfiable (29 500 variables, 115 388 clauses; 24 minutes) | `results/satcegar_box_5_1_k28_in0123_out4_cuts.json`; `.cnf`, `.drat` (regenerated) | S: k = 28, case `"in:0,1,2,3;out:4"`, `box 5 1`; then B': `bash scripts/certify.sh satcegar_box_5_1_k28_in0123_out4_cuts 28 "in:0,1,2,3;out:4" box 5 1` | `logs/satcegar_box_5_1_k28_in0123_out4.log`, `logs/certify_satcegar_box_5_1_k28_in0123_out4_cuts.log` (Glucose 1 446 s on the formula; 1 748 269 lemmas, `s VERIFIED`) | Glucose proof VERIFIED |
| D2, the same formula with CaDiCaL: unsatisfiable (214 s), proof checked | `results/satcegar_box_5_1_k28_in0123_out4_cuts.cadical195.drat` (regenerated) | P: `python -u scripts/prove_cnf.py cadical195 results/satcegar_box_5_1_k28_in0123_out4_cuts.cnf results/satcegar_box_5_1_k28_in0123_out4_cuts.cadical195.drat --check` | `logs/prove_satcegar_box_5_1_k28_in0123_out4_cuts_cadical195.log` (1 614 075 lemmas, `s VERIFIED`) | CaDiCaL proof VERIFIED |
| **D3** all five axes, k = 28: engine A | none | M: k = 28, case `"in:0,1,2,3,4"`, `box 5 1` | `logs/master_box_5_1_k28_in01234.log` (the log does not record the stop) | stopped by hand without an answer |
| D3, engine B with Glucose: 81 cubes, all unsatisfiable | `results/satcegar_box_5_1_k28_in01234_cube*_cuts.json`; `.cnf`, `.drat` (regenerated) | `python -u src/cubes_d5.py 28 "in:0,1,2,3,4" <parallel> <seconds per cube>` | `logs/cubes_d5_k28_in01234.log`, `logs/satcegar_box_5_1_k28_in01234_cube*.log` (all 81 end with "none") | B |
| D3, proof check of the 81 Glucose proofs | `results/d5_cubes_certification.json` (written by the command at the right after every cube, with the verdict and the SHA-256 of the checker binary for each cube; the script also re-verifies the cuts and compares each formula file with a fresh encoding) | `python -u scripts/check_cubes.py [parallel]` | `logs/check_cubes.out`; lemmas checked: CUBELEMMAS | CUBEVERDICT |
| D3 (and D1, D2), second solver: all 83 formulas of row A9 unsatisfiable with CaDiCaL | `results/second_solver_d5_k28.json` | S2: `python -u scripts/second_solver.py cadical195 6 14400 d5_k28 results/master_box_5_1_k28_in012_out34_cuts.cnf results/satcegar_box_5_1_k28_in0123_out4_cuts.cnf results/satcegar_box_5_1_k28_in01234_cube*_cuts.cnf` | `logs/second_solver_d5_k28.log` (last line: 83 of 83 formulas UNSAT) | second solver |
| **D4** controls: with bound 29 the three-axis and the four-axis case each find a 29-ray KS set | the sets printed in the logs; both are in `results/ks_sets.json` | M: k = 29, case `"in:0,1,2;out:3,4"`, `box 5 1`; S: k = 29, case `"in:0,1,2,3;out:4"`, `box 5 1` | `logs/master_box_5_1_k29_in012_out34.log`, `logs/satcegar_box_5_1_k29_in0123_out4_cubesanityk29.log` | found (the searches are not vacuous) |
| D4, control of the five-axis case: with bound 31, cube 2211 finds a 31-ray KS set with all five axes (18 bases, 165 orthogonal pairs) | the set printed in the log; it is in `results/ks_sets.json` | `python -u src/cubes_d5.py 31 "in:0,1,2,3,4" 1 10800 2211` | `logs/satcegar_box_5_1_k31_in01234_cube2211.log`, `logs/cubes_d5_k31_control.out` | found (the search is not vacuous) |
| D4, five-axis case with bound 30: unsatisfiable in 80 of 81 cubes; cube 2222 finds a 30-ray KS set with five axes that is not critical (without e0 a 29-ray KS set with four axes) | `results/satcegar_box_5_1_k30_in01234_cube*_cuts.json` (cuts of each cube) | `KS_SOLVER=cadical195 python -u src/cubes_d5.py 30 "in:0,1,2,3,4" 8 7200` | `logs/cubes_d5_k30_cadical.out`, `logs/satcegar_box_5_1_k30_in01234_cube*.log` | solver answers (CaDiCaL), no proof check |
| D4, the same set is a model of the formula of cube 2211 with bound 31 and not with bound 30 | `tests/test_cnf.py`, class `FiveAxisControl` | `python tests/test_cnf.py FiveAxisControl`; stage `unit` of `run_all.py` | `results/run_all.json` (stage `unit`) | unit test |
| D4, critical KS sets by number of axes, plain random deletion with the axes deleted last: 3828 samples, 4 with three axes, 90 with four, 3734 with five (smallest 29, 29 and 31 rays) | `results/d5_axes_sanity.json` | `python scripts/axes_sanity.py` | `logs/axes_sanity.log` | search only; whether a KS set with 29 or 30 rays and five axes exists is not decided |
| **E** randomised searches: U(3, 12), U(3, 18): 33; U(3, 24): 36 (the pool contains 33-ray sets); U(4, 6): 18; B(5, 2), U(5, 4), U(5, 6): 29; U(5, 3): 85 (no published value known to us); B(6, 1): 31; U(6, 3): 21; B(7, 1): 34; U(7, 3): 32; E8: 34 | `results/hunt_*.json` | H, for example `python -u src/hunt.py 600 1 roots 6 3` | `logs/hunt_*.log` (line `HUNT RESULT`) | search only |
| E, B(3, 2): 31; B(4, 1): 18; B(5, 1): 29 | `results/hunt_box_3_2_s1.json`, `results/hunt_box_4_1_s1.json`, `results/hunt_box_5_1_s1.json` | H: `python -u src/hunt.py 600 1 box 3 2`, the same with `box 4 1` and `box 5 1` | `logs/hunt_box_3_2_s1.log`, `logs/hunt_box_4_1_s1.log`, `logs/hunt_box_5_1_s1.log` (runs of 10 November) | search only (the minimum itself is A1, A8, A9) |
| E, cores agree with the master hypergraphs of Pavičić and Megill (105-136, 1185-3596, 332-1408, 805-9936, 834-1609) | first lines of the logs at the right; for B(5, 1) also `results/pool_facts.json` | H or M on `box 5 1`, `box 5 2`, `box 6 1`, `box 7 1`, `roots 6 3` | `logs/hunt_box_5_2_s1.log`, `logs/hunt_box_6_1_s1.log`, `logs/hunt_box_7_1_s1.log`, `logs/hunt_roots_6_3_s1.log`, `logs/master_box_5_1_k28_in012_out34.log` | computed |
| **F** fewest bases missed by an independent set: 1 of 26, 2 of 50, 7 of 110, 14 of 266, 24 of 136 (optima of an exact MaxSAT solver) | `results/min_missed.json` | `python -u scripts/min_missed.py` | `logs/min_missed.log` | computed (exact) |
| F, the 31-ray set: 71 orthogonal pairs, 17 bases; at most 16 of 17 bases under rule (i); basis sums of probabilities equal 1 | `results/stack_demo.json` | `python scripts/run_stack.py`; or `python scripts/run_all.py --stack` | `logs/stack_run.log` and the other `logs/stack_*.log` | computed; simulation, not a proof |
| F, effect of the conditions (C1), (C2) of Lemma 3, engine A on B(3, 4) with bound 30: 6 rounds and 123 cuts with both, 15 rounds and 307 cuts with neither; no gain in time | `results/ablate_c1c2_box3_4_k30.json` | `python -u scripts/ablate_c1c2.py 30 600 4 box3 4` | `logs/ablate_c1c2_box3_4_k30.log` | computed (one controlled run of four variants) |
| F, integer pools (rays / core / bases) for H = 5, 6, 8, 10 | `results/pool_facts.json` | `python scripts/pool_facts.py` | `logs/pool_facts.log` | computed |
| **G** B(3, 5): exact search stopped by hand after more than an hour | none | M: k = 30, `box3 5` | `logs/master_box3_5_k30.log` (ends at round 10 and does not record the stop), `logs/stdout_30_-_6_-_box3_5.txt` | not achieved; no claim |
| G, U(3, 30): stopped unfinished | none | M: k = 32, `roots 3 30` | `logs/master_roots_3_30_k32.log` | not achieved; no claim |
| G, U(6, 3) and E8: optimality of 21 and 34 not decided | none | M: k = 20, `roots 6 3`; D: k = 20, `roots 6 3`; M: k = 33, `e8` | `logs/master_roots_6_3_k20.log`, `logs/dfs_roots_6_3_k20.log`, `logs/master_e8_k33.log` | not achieved; no claim |

## Notes on reading the table

* "Regenerated" files (`.cnf`, `.drat`) exist after the command has been run; they are not part of
  the Git repository.
* Sections C and C.1 of the register give, for each engine-B run, the numbers of variables, clauses
  and lemmas and the solver time. A fresh run of form M or U may collect different cuts, so the
  formula of a fresh run and its proof can have different sizes; the verdict is what has to agree.
* Forms S2 and P give the same formula file to a second solver. They check the solvers against each
  other, not the encoding.
* The time stamps in the logs are local clock times of 9 and 10 November 2026; several logs contain
  more than one run, appended one after the other. Solver times are elapsed times of single runs on a
  machine that was running other jobs.
* The durations of the runs that were stopped by hand (rows D2, D3 with engine A, and B(3, 5)) are not
  in the logs; the register words what is known about them.
