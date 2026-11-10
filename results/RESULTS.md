# Results register (single source of truth)

Every number quoted in the README, the paper and the site must agree with this file.

Status words. **Lean**: statement proved in Lean 4 and checked by the Lean kernel. **proof-checked**:
unsatisfiability proof (DRUP) accepted by `verify/drup_check`. **A** / **B**: answer obtained by
engine A (CP-SAT) / engine B (the Boolean formula of `src/ks_cnf.py`, solved by Glucose 4.1 unless
CaDiCaL is named). **second solver**: the formula of engine B was also solved by CaDiCaL 1.9.5. **tree**: search-tree certificate replayed by the independent
JavaScript verifier. **search only**: randomised search, no proof of optimality.

Definition used everywhere: a set S of rays is *colorable* if some f : S → {0,1} has no two orthogonal
rays both 1 and a 1 in every basis (d mutually orthogonal rays) contained in S; otherwise S is a
Kochen-Specker (KS) set. Only the rays of S are counted.

Pools: B(d, H) = rays of Zᵈ with a representative of max-norm at most H. U(d, N) = rays of Cᵈ with
entries 0 or N-th roots of unity.

## A. Exact minima inside pools

| # | Pool | rays (core) | bases | minimum | KS sets of minimum size | evidence |
|---|---|---|---|---|---|---|
| A1 | B(3, 2) | 49 (49) | 26 | **31** | exactly 6, one orbit | Lean; tree (255 nodes); A; B proof-checked |
| A2 | B(3, 3) | 145 (97) | 50 | **31** | exactly 6, one orbit | tree (11 330 nodes on the whole pool; 11 247 on the core); A; B proof-checked |
| A3 | B(3, 4) | 289 (205) | 110 | **31** | exactly 6, one orbit | A; B proof-checked |
| A4 | U(3, 6) | 57 (57) | 22 | **33** | exactly 3, one orbit | exhaustive tree search (1 456 nodes); A (enumeration run); B proof-checked (uniqueness run, section C.1) |
| A5 | U(3, 12) | 183 (183) | 67 | **33** | exactly 12, one orbit | A; B proof-checked |
| A6 | U(3, 18) | 381 (381) | 136 | **33** | not enumerated | A; B proof-checked |
| A7 | U(3, 24) | 651 (651) | 229 | **33** | not enumerated | A; B with CaDiCaL (Glucose ran out of memory), proof-checked |
| A8 | B(4, 1) | 40 (40) | 32 | **18** | exactly 16, one orbit (the known sets inside Peres's 24 rays) | Lean; tree (509 nodes); A; B proof-checked |
| A9 | B(5, 1) | 121 (105) | 136 | **29** | at least two non-isomorphic | B and a second solver, with case analysis (section D); proof-checked |

"Exactly n" counts come from `scripts/enumerate_min.py` (engine A: each KS set found is excluded
together with its whole orbit, and the run continues until the candidate problem is infeasible):
`results/enumerate_*.json`. The last step, "no further KS set of that size", is repeated by engine B
with a checked proof where section C.1 says so. Orbits are under signed coordinate permutations for
B(d, H), and under coordinate permutations, multiplication of single coordinates by N-th roots of
unity and complex conjugation for U(3, N).

Upper bounds: explicit sets in `results/ks_sets.json`, each re-verified as a critical KS set. The
31-ray set of A1 lies in the pools A2 and A3; the 33-ray set of A4 lies in A5, A6 and A7.

Pools without any KS set (the core is empty): U(3, N) for N = 2, 3, 4, 5, 7, 8, 9, 10, 11
(`scripts/pool_facts.py`, `results/pool_facts.json`), agreeing with Kernaghan's theorem that U(3, N)
has a KS set iff 6 divides N.

## B. Lean 4 (kernel-checked; no Mathlib; axioms propext, Classical.choice, Quot.sound)

| # | Theorem | Statement |
|---|---|---|
| L0 | `KS.small_sets_colorable`, `KS.not_colorable_of_refute` | soundness of the two certificate checkers |
| L1 | `KS.Box3H2.minimum_ks_size_vectors` | B(3, 2), stated for the integer vectors `boxRays 3 2`: some 31-ray set is not colorable; every set of at most 30 rays is colorable |
| L2 | `KS.Box4H1.minimum_ks_size_vectors` | B(4, 1), stated for the integer vectors `boxRays 4 1`: some 18-ray set is not colorable; every set of at most 17 rays is colorable |
| L3 | `KS.vcolorable_of_colorable`, `KS.colorable_of_vcolorable` | for a table that passes the three checks, colorability of the table and colorability phrased with dot products of the vectors agree |
| L4 | `rays_eq`, `boxRays_exact` in each data module | the listed vectors are `boxRays d H`, and every non-zero integer vector of the box is parallel to exactly one of them |
| — | (not done) B(3, 3) in Lean | a module for all 145 rays (certificate of 11 330 nodes) was generated, but its kernel check was stopped after 49 minutes without a verdict (`logs/lean_box3h3.out`); nothing is claimed and the module is not in the repository |

L1 and L2 are derived from the table versions `KS.Box3H2.minimum_ks_size` and
`KS.Box4H1.minimum_ks_size` (kernel evaluation of the certificates), from the three checks of each
data module (`adj_spec`, `bases_sound`, `bases_complete`: the orthogonality table equals "dot product
zero" on the listed vectors and the list of bases is exactly the set of all d-cliques), and from L3
and L4. The Lean theorems cover the two minimum values only, not the counts of minimum sets.
`lake build` checks every module; `lake env lean KS/Audit.lean` prints the axioms of 26 theorems.

## C. Engine B: unsatisfiability proofs and their checks

Engine B writes the candidate problem as a Boolean formula (`src/ks_cnf.py`). The formula is solved
by Glucose 4.1 and, where the table says so, by a second solver, CaDiCaL 1.9.5, on the same file
(`scripts/second_solver.py` for the answer only, `scripts/prove_cnf.py` with a proof). Both solvers
are used through PySAT. "Lemmas checked" is the number of proof steps that `verify/drup_check`
verified by reverse unit propagation before the empty clause was reached.

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
| A9, five axes, 81 cubes (k = 28) | 33 790 / 132 361 to 133 321 | Glucose, 84 to 751 s per cube | CUBELEMMAS | CUBEVERDICT |
| cube 0001 of the same case, the same formula | 33 790 / 132 361 | CaDiCaL, 168 s | 1 726 879 | VERIFIED |

Second solver, answers without a proof (`results/second_solver_d5_k28.json`,
`results/second_solver_roots_3_24_k32.json`): CaDiCaL finds all 83 formulas of row A9 unsatisfiable
(three axes 28 s; four axes 235 s; the 81 cubes 57 to 449 s each, 2.85 hours in total) and the
formula of row A7 unsatisfiable (357 s). Both solvers read the same formula files, so this checks
the solvers against each other, not the encoding.

Solver times are elapsed times of single runs on a machine that was running other jobs; they vary
from run to run (the three-axis formula took Glucose 81 s in an earlier run and 40 s in the logged
one). The logs are `logs/certify_*.log`, `logs/prove_*.log`, `logs/drup_H4.out` (row A3) and
`logs/check_cubes.out`.

### C.1 Uniqueness runs: no KS set of the minimum size besides the listed ones

The formula is the candidate problem for k = minimum, plus one clause per listed KS set that excludes
it (`scripts/certify_unique.sh`, logs `logs/unique_enumerate_*.log`). Unsatisfiable means: every KS set
with at most k rays is one of the listed sets. For B(d, H), where the formula contains symmetry
breaking, it means that every such set is an image of a listed set under a signed coordinate
permutation; the encoder checks that the list is closed under these permutations and stops
otherwise (log line "the list is closed ... (checked)"). This also re-proves the minimum.

| Pool (k, sets excluded) | variables / clauses | solver time | lemmas checked | verdict |
|---|---|---|---|---|
| B(3, 2) (31, 6 sets) | 5 272 / 20 336 | under 0.1 s | 174 | VERIFIED |
| B(3, 3) (31, 6 sets) | 17 440 / 68 204 | 0.5 s | 4 082 | VERIFIED |
| B(3, 4) (31, 6 sets) | 76 220 / 301 248 | 765 s | 636 157 | VERIFIED |
| U(3, 6) (33, 3 sets) | 2 329 / 8 983 | under 0.1 s | 221 | VERIFIED |
| U(3, 12) (33, 12 sets) | 9 160 / 37 099 | 7.2 s | 79 626 | VERIFIED |
| B(4, 1) (18, 16 sets) | 4 449 / 16 950 | under 0.1 s | 571 | VERIFIED |

The figures are those of the last run in each log. The cuts are found afresh in every run, so a
repeated run gives a formula of a different size and a different proof; the verdict is what has to
agree. The same holds for the runs of section C.

## D. Dimension 5, pool B(5, 1): no KS set with 28 or fewer rays

Every basis of the pool contains a coordinate axis and every KS set contains at least three axes
(`scripts/lemma7.py`, `results/lemma7_d5_axes.json`). Up to coordinate permutations a critical KS set
contains exactly the axes {e0,e1,e2}, or {e0,e1,e2,e3}, or all five.

| Case | engine A (CP-SAT) | engine B (Glucose 4.1) | second solver (CaDiCaL 1.9.5) | proof checks |
|---|---|---|---|---|
| exactly three axes | infeasible (two runs, 57 s and 9 s) | unsatisfiable (40 s; 58 s incremental) | unsatisfiable (28 s) | Glucose proof VERIFIED |
| exactly four axes | stopped by hand without an answer | unsatisfiable (24 min) | unsatisfiable (4 min) | CaDiCaL proof VERIFIED; Glucose proof VERIFIED |
| all five axes | stopped by hand without an answer | 81 cubes, all unsatisfiable (median 222 s) | 81 cubes, all unsatisfiable (median 112 s) | 81 Glucose proofs: CUBEVERDICT |

The two engine-A runs without an answer were stopped after roughly 50 and 60 minutes; their logs do
not record the stop. For 21 of the 81 cubes the formula and proof on file come from a second run of
the cube, made to write the proof; all 81 cube logs end with "none".

Sanity checks of the case machinery: with bound 29 the three-axis case finds a 29-ray KS set
(16 bases, 151 orthogonal pairs) and the four-axis case finds a 29-ray KS set (16 bases, 150
orthogonal pairs); with bound 31 the five-axis case, run in cube 2211, finds a 31-ray KS set with all
five axes (18 bases, 165 orthogonal pairs; `logs/satcegar_box_5_1_k31_in01234_cube2211.log`). So none
of the three searches is vacuous.

Critical KS sets by number of axes, plain random deletion with the axes deleted last
(`scripts/axes_sanity.py`, `results/d5_axes_sanity.json`): 3828 samples, of which 4 with three axes
(smallest 29 rays), 90 with four (smallest 29) and 3734 with five (smallest 31). Whether a critical
KS set with 29 or 30 rays and five axes exists is not decided. With bound 30 the five-axis case is unsatisfiable
for CaDiCaL in 80 of the 81 cubes (answers only, no proof check; `logs/cubes_d5_k30_cadical.out`);
in cube 2222 it finds a 30-ray KS set with five axes, 159 orthogonal pairs and 17 bases that is not
critical (without e0 it is a 29-ray KS set with four axes;
`logs/satcegar_box_5_1_k30_in01234_cube2222.log`). So a critical five-axis KS set with at most 30
rays, if one exists, lies in cube 2222. *Correction:* an earlier version of the register
said that no critical KS set with five axes had been met in 58 684 samples and that the case might be
empty. That sampler replaced the set by the solver's unsatisfiable core after every deletion and was
biased; two reviewers found five-axis sets within seconds by plain deletion (`docs/REVIEW.md`).

## E. Randomised searches (search only)

Destroy-and-repair walk on critical KS sets (`src/kslocal.py`, `src/hunt.py`), 10 to 15 minutes per
pool (10 minutes for the three small pools of the first, third and fourth rows, run again on
10 November to have a log). No search found a set smaller than the smallest published one. In every
pool except U(3, 24) the smallest set found has the size of the smallest published set known to us;
in U(3, 24) the walk stopped at 36 rays although the pool contains 33-ray sets.

| Pool | rays in core | smallest KS set found | smallest published |
|---|---|---|---|
| B(3, 2) | 49 | 31 | 31 (Conway-Kochen) |
| U(3, 12), U(3, 18) | 183, 381 | 33 (14 bases) | 33 complex (Cabello 2025; Pavicic 2025) |
| U(3, 24) | 651 | 36 (15 bases) | 33 (the 33-ray sets of U(3, 6) lie in this pool) |
| U(5, 3) | 230 | 85 (27 bases) | none known to us |
| B(4, 1), U(4, 6) | 40, 400 | 18 | 18 |
| B(5, 1), B(5, 2) | 105, 1185 | 29 | 29 (Cabello, Estebaranz, Garcia-Alcaine 2005) |
| U(5, 4), U(5, 6) | 525, 1505 | 29 | 29 |
| B(6, 1) | 332 | 31 | 31 (real) |
| U(6, 3) | 834 | 21 (7 bases) | 21 (Lisonek et al. 2014) |
| B(7, 1) | 805 | 34 | 34 (real) |
| U(7, 3) | 2968 | 32 (12 bases) | 32 (Waegell-Aravind 2017) |
| E8 root rays, d = 8 | 120 | 34 (9 bases) | 34 (Waegell-Aravind 2015) |

Core sizes and basis counts agree with the "master" hypergraphs of Pavicic and Megill where both
exist: 105-136 for B(5, 1), 1185-3596 for B(5, 2), 332-1408 for B(6, 1), 805-9936 for B(7, 1),
834-1609 for U(6, 3).

## F. Other computed quantities

* Fewest bases missed by an independent set of the whole pool: 1 of 26 (A1), 2 of 50 (A2),
  7 of 110 (A3), 14 of 266 (B(3, 5)), 24 of 136 (A9). These are optima of an exact MaxSAT solver
  (`scripts/min_missed.py`, `results/min_missed.json`), not the best values found within a time limit.
* The 31-ray set: 71 orthogonal pairs, 17 bases. At most 16 of the 17 bases can receive a 1 under
  rule (i); for every quantum state the 17 basis sums of probabilities equal 1
  (`results/stack_demo.json`).
* Effect of the two necessary conditions of Lemma 3, engine A on B(3, 4) with bound 30, 4 workers,
  everything else equal (`scripts/ablate_c1c2.py`, `results/ablate_c1c2_box3_4_k30.json`): both
  conditions 6 rounds, 123 cuts, 9.3 s; (C1) only 15 rounds, 327 cuts, 7.4 s; (C2) only 9 rounds, 183
  cuts, 16.9 s; neither 15 rounds, 307 cuts, 9.2 s. The answer is "infeasible" in all four runs.
* Integer pools (rays / rays of the core / bases of the core): H = 5: 577 / 421 / 266;
  H = 6: 865 / 625 / 382; H = 8: 2017 / 1249 / 778; H = 10: 3745 / 2185 / 1408. Up to H = 8 every
  basis of the pool lies in the core; for H = 10 the pool has 1414 bases, six of them outside the core
  (`scripts/pool_facts.py`, `results/pool_facts.json`).

## G. Not achieved

* No KS set smaller than a published record was found in any dimension.
* B(3, 5): the exact search with engine A did not finish; it was stopped by hand after more than an
  hour (the log `logs/master_box3_5_k30.log` ends at round 10 and does not record the stop). A second
  attempt with the incremental SAT version and CaDiCaL (`logs/satcegar_box3_5_k30.log`) had not
  answered when this version was released.
  U(3, 30): stopped unfinished.
* U(6, 3) (is 21 optimal there?) and the E8 pool (is 34 optimal there?): not decided.
* The general problems (any rays: dimension 3 between 24 and 31; dimensions 5 and above between 18
  and the records) are not settled by pool results.

## H. Prior art for the values (see paper, Section 1.3)

* A1: minimum 31 reported as exact, and six 31-ray sets found by randomised minimisation, by Kernaghan
  arXiv:2603.16988 (no certificate; one remark there speaks of 162 distinct sets, six up to
  automorphism); six equivalent versions of the Conway-Kochen set are noted by Trandafir and Cabello
  (2025). A2: 31 is listed in Kernaghan's Table 2. A1 to A3: minimum 31, ProblemHive thread p/xfkay,
  October 2026 (CP-SAT with coloring cuts, no certificate).
* A4: minimum 33, Kernaghan (no certificate). Existence of KS sets in U(3, N) iff 6 | N: Kernaghan,
  Theorem 11. A5 to A7: only "best found" or "at most 33" there.
* A8: 18 is the minimum for KS sets in dimension four (Pavicic et al. 2005) and in any dimension (Xu,
  Chen, Guehne 2020). The 16 sets are the 16 known 18-ray sets inside the 24 rays of Peres (Waegell
  and Aravind 2011, Table 2); `results/peres24_check.json` confirms that all 16 lie in those 24 rays.
  New here: the 16 further rays of the pool give no other 18-ray KS set.
* A9: Pavicic and Megill (2022) generate from the components 0, +1, -1 the master set 105-136, which
  is the core of B(5, 1), and report 29-16 as the smallest critical set of its class, with two
  non-isomorphic sets of that size (also Pavicic and Waegell 2024, who call it likely that the
  smallest sets in dimensions 4 to 8 are known). No proof that nothing smaller exists is given there.
  New here: the proof, with checked certificates.
* These two items (A8, A9) were missed by the first literature search and found by the review before
  release (`docs/REVIEW.md`).
