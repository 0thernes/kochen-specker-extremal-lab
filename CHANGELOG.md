# Changelog

## After 1.0.0 (not released)

* The release and its archiving are recorded: `docs/REPORT.md`, section 8, and
  `results/release_archiving.json` (CI run, release assets, GitHub Pages, Software Heritage snapshot,
  Internet Archive captures, each compared byte for byte with the files at the tag v1.0.0);
  `publication/README.md` says which venues are done. No result, proof or paper text changed.

## 1.0.0 (10 November 2026)

First public release.

### Results (see `results/RESULTS.md`, the register, for the status of each)

* Exact minimum size of a Kochen-Specker set inside nine pools of rays: 31 for integer coordinates up
  to 2, 3 and 4 in dimension three; 33 for coordinates 0 or N-th roots of unity, N = 6, 12, 18, 24, in
  dimension three; 18 for coordinates 0, +1, -1 in dimension four; 29 for coordinates 0, +1, -1 in
  dimension five.
* All Kochen-Specker sets of minimum size in six of these pools: 6, 6, 6, 3, 12 and 16 sets, one orbit
  under the symmetries of the pool in each case.
* Several of these values had been reported before without proof (31 for integer bounds 2, 3 and 4;
  33 for sixth roots of unity; 29 as the smallest set generated from 0, +1, -1 in dimension five), and
  the 16 minimum sets of dimension four are the known sets inside the 24 rays of Peres (Waegell and
  Aravind 2011). What is new is mainly the proofs; see the paper, Section 1.3.
* No Kochen-Specker set smaller than a published one was found. The general minimal-set problem is
  not settled by pool results.

### Evidence

* Lean 4 (no Mathlib): soundness of two certificate checkers, and kernel-checked theorems for the
  49-ray pool of dimension three and the 40-ray pool of dimension four, stated both for the tables of
  bit masks and for the integer vectors themselves (`boxRays d H`, `VColorable`).
* Search-tree certificates replayed by an independent JavaScript verifier, three of them covering
  whole pools.
* Unsatisfiability proofs (DRUP) of the candidate problems, checked by `verify/drup_check.c`, for the
  minimum values and for the counts of minimum sets. The formulas of the 24th-root pool and of
  dimension five were also solved by a second SAT solver (CaDiCaL); for the 24th-root pool, where
  Glucose ran out of memory, and for the four-axis case of dimension five the CaDiCaL proofs were
  checked as well.
* The lemmas the programs rely on, with proofs: `paper/PROOFS.md`.

### Contents

* `paper/` the paper and the proofs of the lemmas; `publication/` the files prepared for the author's
  submissions (nothing has been submitted by the build process).
* `src/`, `scripts/`, `verify/`, `tests/` the programs, the checkers and their tests; one command,
  `python scripts/run_all.py`, repeats the small checks.
* `lean/` the Lean development; `results/`, `logs/` certificates, cut files with their witnesses,
  explicit sets, enumerations and the logs of the runs.
* `docs/` the site with an in-browser verifier, the built paper, and the documents: summary, index of
  claims and evidence, glossary, verification report, review before release, trigger register.
* `stack/`, `third_party/` a demonstration of the 31-ray set on Moonlab, QGTL, quantum_rng and Eshkol
  (classical computation; not part of any proof).

### Review before release

* Nine reviewing passes (the Lean development, the lemmas, symmetry breaking and uniqueness, the
  encoder, the proof pipeline, the numbers, prior work and references, independent reconstructions of
  the pools, independent re-runs). No theorem and no headline number changed. What changed: two
  missed prior reports are now credited and the novelty claims were narrowed; the Lean theorems are
  stated for integer vectors; a wrong remark about dimension five (five-axis sets "may not exist")
  was withdrawn; the proof checker reads its input strictly; the certification scripts report failure
  correctly; several durations and counts were corrected. Details: `docs/REVIEW.md`.

### Known limits

* Not peer reviewed. Produced by an AI system under human direction (see `LEGAL.md`).
* The proof checker and the JavaScript verifier are tested, not formally verified.
* Runs that did not finish, and work that is deliberately deferred, are listed in section G of the
  register and in `docs/TRIGGER-REGISTER.md`.
