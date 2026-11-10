# Kochen-Specker Extremal Lab

Exact minimum sizes of Kochen-Specker sets inside finite pools of rays, each with a certificate that
can be re-checked without trusting the search programs.

**Paper:** [Certified exact minima of Kochen-Specker sets inside coordinate pools](paper/ks-minimum.md)
&nbsp;·&nbsp; **Register of results:** [results/RESULTS.md](results/RESULTS.md)
&nbsp;·&nbsp; **Proofs of the lemmas:** [paper/PROOFS.md](paper/PROOFS.md)

**Start here:** [docs/SUMMARY.md](docs/SUMMARY.md) (one page, plain language) ·
[docs/INDEX.md](docs/INDEX.md) (every claim with its evidence file, command and log) ·
[docs/GLOSSARY.md](docs/GLOSSARY.md) · [docs/REPORT.md](docs/REPORT.md) (what was run, what failed) ·
[docs/REVIEW.md](docs/REVIEW.md) (what the review before release found and what was changed) ·
[CHANGELOG.md](CHANGELOG.md) · [LEGAL.md](LEGAL.md) · [CITATION.cff](CITATION.cff)

Status: research preprint, version 1.0.0, 10 November 2026. Not peer reviewed. Produced by an AI system
under human direction (see [the disclosure](#9-licence-citation-ai-disclosure-contact)).
Author: Alexander S. Donahue, 0thernes LLC, Washington, USA
([ORCID 0009-0006-8168-9648](https://orcid.org/0009-0006-8168-9648)).

## 1. In plain language

**What a Kochen-Specker set is.** A *ray* is a direction in space: a straight line through the origin.
Two rays are *orthogonal* when they are at right angles, and a *basis* is a full set of mutually
orthogonal rays: three of them in ordinary three-dimensional space, like the three edges that meet in
a corner of a room. Take a finite set of rays and try to label every ray with 0 or 1 so that (i) two
orthogonal rays are never both labelled 1, and (ii) every basis that lies inside the set contains a
ray labelled 1. For most sets this is easy. A *Kochen-Specker set* is a set for which it is impossible.
Such sets exist (Kochen and Specker 1967, Bell 1966), and they matter in physics: they show that
quantum theory cannot be reproduced by a model in which every measurement has an outcome that is fixed
in advance and does not depend on which other compatible measurements are made with it.

**The open problem.** How few rays can a Kochen-Specker set have? In dimension four the answer is
known: 18. In dimension three the smallest known set has 31 rays (Conway and Kochen), it is proved that
fewer than 24 rays cannot work, and nobody knows what happens between 24 and 31. In dimensions five to
eight the smallest known sets have 29, 21, 32 and 34 rays (31 and 34 in dimensions six and seven if
only real coordinates are allowed), and the only proved lower bound is 18.

**What this lab did, and did not do.** It did **not** solve that problem, and it did **not** find a
Kochen-Specker set smaller than a published one. It answers a narrower question exactly. Fix a finite
*pool* of rays, for example all directions in three-dimensional space whose coordinates are whole
numbers between −2 and 2. What is the smallest Kochen-Specker set that uses only rays of the pool? For
the nine pools in the table below the answer equals the size of the smallest published set of that
kind (31, 33, 18 or 29 rays). A pool result says nothing about rays outside the pool. Nothing here is
a new record, and nothing here solves the open problem.

**What was known, and what is new.** Several of the nine values were reported before by others,
without a proof that can be checked: 31 for whole-number coordinates up to 2, 3 and 4; 33 for sixth
roots of unity; and 29 as the smallest set obtained from the coordinates 0, +1, −1 in dimension five.
That 18 is the minimum in dimension four is a published theorem, and the 16 sets of 18 rays in that
pool were known. What the lab adds is the proof that nothing smaller exists inside each pool, in a
form that others can check: two of the minimum values are theorems verified by the Lean 4 proof
checker, the others come with unsatisfiability proofs checked by a separate program or are marked for
exactly what they rest on. Also new, as far as a literature search could tell: the exact minimum 33
for twelfth, eighteenth and twenty-fourth roots of unity, and the complete lists of the smallest sets
for whole-number coordinates up to 3 and 4 and for sixth and twelfth roots of unity. Section 5 has the
details; the register records the status of every check.

## 2. Results

The table is section A of the register [results/RESULTS.md](results/RESULTS.md), copied row for row.
The register is the single source of truth: if a number or a status here, in the paper or on the site
differs from it, the register is right.

Pools: B(d, H) = rays of Zᵈ with a representative whose coordinates have absolute value at most H.
U(d, N) = rays of Cᵈ whose entries are 0 or N-th roots of unity. "Core" is the part of the pool that
can belong to a smallest Kochen-Specker set (see the [glossary](docs/GLOSSARY.md)).

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

Status words, as defined in the register:

* **Lean**: the statement is proved in Lean 4 and checked by the Lean kernel.
* **proof-checked**: an unsatisfiability proof (DRUP) was accepted by `verify/drup_check`.
* **A** / **B**: the answer was obtained by engine A (CP-SAT) / engine B (the Boolean formula of
  `src/ks_cnf.py`, solved by Glucose 4.1 unless CaDiCaL is named).
* **second solver**: the formula of engine B was also solved by CaDiCaL 1.9.5.
* **tree**: a search-tree certificate was replayed by the independent JavaScript verifier.
* **search only**: randomised search, no proof of optimality (used for the further pools of
  section E of the register, not for the table above).

"Exactly n" in the fifth column: the sets were listed by engine A (each set found is excluded together
with its whole orbit until nothing is left), and the last step, "no further Kochen-Specker set of that
size", was repeated by engine B with a checked proof for all six pools (register, section C.1).

Row A7 (24th roots of unity). Glucose ran out of memory on this formula. The same formula file was
solved by a second SAT solver, CaDiCaL 1.9.5: unsatisfiable
(`results/second_solver_roots_3_24_k32.json`). CaDiCaL was then run again on that file with a proof,
and `verify/drup_check` accepted the proof: 1 464 683 lemmas checked, VERIFIED
(`logs/prove_master_roots_3_24_k32_cuts_cadical195.log`). Engine A also answers "infeasible" for
this pool.

Row A9 (dimension five) is a case analysis with three cases, section D of the register. Every basis
of the pool contains a coordinate axis and every Kochen-Specker set contains at least three axes, so a
smallest set has, up to a permutation of the coordinates, exactly three axes, exactly four, or all
five. Bound 28 in each case:

| Case | engine A (CP-SAT) | engine B (Glucose 4.1) | second solver (CaDiCaL 1.9.5) | proof checks |
|---|---|---|---|---|
| exactly three axes | infeasible (two runs, 57 s and 9 s) | unsatisfiable (40 s; 58 s incremental) | unsatisfiable (28 s) | Glucose proof VERIFIED |
| exactly four axes | stopped by hand without an answer | unsatisfiable (24 min) | unsatisfiable (4 min) | CaDiCaL proof VERIFIED; Glucose proof VERIFIED |
| all five axes | stopped by hand without an answer | 81 cubes, all unsatisfiable (median 222 s) | 81 cubes, all unsatisfiable (median 112 s) | 81 Glucose proofs, all VERIFIED |

Engine A closed only the three-axis case; its two other runs were stopped by hand without an answer,
and their logs do not record the stop. Both SAT solvers were given the same formula files (83 in all:
one for each of the first two cases and 81 for the third), so the second solver checks the first
solver, not the encoding. Three controls show that none of the three searches is vacuous: with bound
29 the three-axis and the four-axis case each find a 29-ray Kochen-Specker set, and with bound 31 the
five-axis case, run in one cube, finds a 31-ray Kochen-Specker set with all five axes
(`logs/satcegar_box_5_1_k31_in01234_cube2211.log`). The numbers of lemmas and the logs of the proof
checks are in sections C and D of the register.

Lean theorems (section B of the register; no Mathlib; axioms `propext`, `Classical.choice`,
`Quot.sound`; no `sorry`, no `native_decide`):

| # | Theorem | Statement |
|---|---|---|
| L0 | `KS.small_sets_colorable`, `KS.not_colorable_of_refute` | soundness of the two certificate checkers |
| L1 | `KS.Box3H2.minimum_ks_size_vectors` | B(3, 2), stated for the integer vectors `boxRays 3 2`: some 31-ray set is not colorable; every set of at most 30 rays is colorable |
| L2 | `KS.Box4H1.minimum_ks_size_vectors` | B(4, 1), stated for the integer vectors `boxRays 4 1`: some 18-ray set is not colorable; every set of at most 17 rays is colorable |
| L3 | `KS.vcolorable_of_colorable`, `KS.colorable_of_vcolorable` | for a table that passes the three checks, colorability of the table and colorability phrased with dot products of the vectors agree |
| L4 | `rays_eq`, `boxRays_exact` in each data module | the listed vectors are `boxRays d H`, and every non-zero integer vector of the box is parallel to exactly one of them |
| — | (not done) B(3, 3) in Lean | a module for all 145 rays (certificate of 11 330 nodes) was generated, but its kernel check was stopped after 49 minutes without a verdict (`logs/lean_box3h3.out`); nothing is claimed and the module is not in the repository |

The Lean theorems cover the two minimum values only, not the counts of minimum sets. What has to be
trusted for them is the Lean kernel and the reading of the statement and of the definitions it uses
(`boxRays`, `dot`, `card`, `Sub`, `VColorable`: about 25 lines, printed in
[lean/README.md](lean/README.md)); no table, certificate or checker is trusted.

Randomised searches in further pools in dimensions three to eight (section E of the register) found
no set smaller than the smallest published one. In every pool except U(3, 24) the smallest set found
has the size of the smallest published set known to us; in U(3, 24) the walk stopped at 36 rays
although the pool contains 33-ray sets. In U(5, 3), for which we know no published value, the walk
ended at 85 rays. These searches prove nothing about optimality.

## 3. Check it yourself in five minutes

Install first (section 7). All commands are run from the repository root.

**a. Everything small, in one command.**

```
python scripts/run_all.py
```

It runs the unit tests, the tests of the JavaScript verifier, the two finite facts of Lemma 7,
regenerates the search-tree certificates for B(3, 2) and B(4, 1) and replays them, and regenerates and
checks the unsatisfiability proofs for the same two pools. It prints one line per stage and a summary.
The run recorded in [results/run_all.json](results/run_all.json) printed:

```
PASS  unit            21.9s  115 tests, 1 skipped
PASS  js               5.2s  59/59 checks passed
PASS  lemma7           0.2s  121 rays, 136 bases, both facts hold; matches results/lemma7_d5_axes.json
PASS  cert-gen         0.6s  cert_box3_H2_k30.json: 255 nodes, same as committed; cert_box4_H1_k17.json: 509 nodes, same as committed
PASS  cert-verify      0.1s  2 certificates PASS; corrupted copy rejected
PASS  drup-49          2.2s  63 cuts, CNF 5254 vars / 20235 clauses, UNSAT, proof VERIFIED (183 lemmas)
PASS  drup-40          1.5s  84 cuts, CNF 4427 vars / 16847 clauses, UNSAT, proof VERIFIED (307 lemmas)
PASS  lean            20.3s  26 theorems audited, axioms used: Classical.choice, Quot.sound, propext; no sorry
```

followed by a `SUMMARY:` line and `exit code 0` (this run used `--lean`; the `lean` stage is
optional). Without options the summary reads `7 passed, 0 failed, 2 not run` (the optional stages
`lean` and `stack`). Times depend on the machine. A test is skipped when a large proof file that is
not kept in the repository is absent. The same command in a fresh clone of the repository, with the
Lean project built from an empty build directory, also passed every stage.
The numbers of cuts, clauses and lemmas in the two `drup` stages depend on the run, because the cuts
are found afresh each time; the verdict must be `VERIFIED`. Any `FAIL` line, or an exit code other than
0, means a check did not pass. `python scripts/run_all.py --lean` adds the Lean build and axiom audit
of step c; `--list` shows the stages. The command rewrites `results/run_all.json` and nothing else in
the repository.

**b. The independent JavaScript verifier.**

```
node verify/test_verify.mjs
```

It replays the four committed tree certificates (B(3, 2); B(3, 3), once on the whole 145-ray pool and
once on its core; B(4, 1)), checks the 31-ray set, and runs its negative tests (corrupted certificates
must be rejected). The last line should read
`== PASS: 59/59 checks passed; summary written to results/verify_summary.json ==` (the command
rewrites that summary file). The rule that is
checked is written out in [verify/README.md](verify/README.md). To check a single certificate:
`node verify/verify_cert.mjs results/cert_box3_H2_k30.json`.

**c. The Lean proofs.**

```
cd lean
lake build
lake env lean KS/Audit.lean
```

Plain `lake build` checks every module: the definitions and checkers (`KS/Basic.lean`), the statement
in terms of integer vectors (`KS/Spec.lean`), the two data modules and the regression tests
(`KS/Tests.lean`). It succeeds only if the Lean kernel accepts every proof. The second command prints
the axioms of 26 theorems. Every line shows at most `propext`, `Classical.choice` and `Quot.sound`,
the three standard axioms of Lean; some lines show fewer or none. The two lines for the two main
theorems are

```
'KS.Box3H2.minimum_ks_size_vectors' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box4H1.minimum_ks_size_vectors' depends on axioms: [propext, Classical.choice, Quot.sound]
```

There is no Mathlib to download. The complete expected output, the statements of the theorems and the
definitions they use are in [lean/README.md](lean/README.md).

**d. In a browser.** The page [docs/index.html](docs/index.html) (the source of the project site,
https://0thernes.github.io/kochen-specker-extremal-lab/) has a section "Verify in your browser". It
first compares the SHA-256 of each data file with `docs/data/manifest.json`, then runs, on your device
and without a server-side program, a JavaScript port of the verifier: it recomputes the 49-ray and
40-ray pools from the integer coordinates, replays both certificate trees, and searches exhaustively
for a labelling of the 31-ray and the 18-ray set. Each check should report PASS. To use the copy in
this repository, serve the folder and open it (the page loads its data with `fetch`, so opening the
file directly is not enough):

```
python -m http.server 8000 --directory docs
```

and visit `http://localhost:8000/`.

The larger results (rows A2 to A7 and A9) take from seconds to hours to regenerate; the commands, logs
and result files for each of them are listed in [docs/INDEX.md](docs/INDEX.md).

## 4. How the certification works

**The idea.** Call a set of rays *independent* when no two of its rays are orthogonal. Labelling the
rays of an independent set I with 1 and everything else with 0 never breaks rule (i), and it satisfies
rule (ii) for every basis that contains a ray of I. So a set S can only be a Kochen-Specker set if, for
every independent set I of the pool, S contains at least one basis that I misses (Lemma 1 of
[paper/PROOFS.md](paper/PROOFS.md)). Each independent set therefore gives a *cut*: a simple condition
that every Kochen-Specker set must satisfy, and that anyone can verify from I alone. The search
collects cuts until no set of at most k rays can satisfy all of them. Two further necessary conditions
for smallest sets (Lemma 3), a symmetry normal form (Lemma 6) and, in dimension five, a split into
cases (Lemma 7) keep this tractable.

**Three engines.**

* **Engine A** solves the "candidate problem" (find at most k rays satisfying all cuts collected so
  far) with the CP-SAT solver of OR-Tools. Its final answer "infeasible" is a solver answer; it leaves
  no proof.
* **Engine B** encodes the final candidate problem from scratch as a plain Boolean formula, re-checking
  every cut from its independent set, and solves it with the SAT solver Glucose 4.1, which writes a
  DRUP proof of unsatisfiability. The proof is checked by `verify/drup_check.c`, a checker of about 310
  lines written for this project; it reads every token strictly and stops on anything malformed. Where the register says so, the same formula file was also given to
  a second SAT solver, CaDiCaL 1.9.5 (`scripts/second_solver.py` for the answer,
  `scripts/prove_cnf.py` for a proof that the same checker checks). Both solvers are used through
  PySAT.
* **Engine C** is a plain exhaustive tree search whose trace is a certificate. The certificate is
  replayed by `verify/verify_cert.mjs`, a JavaScript program written from the specification alone that
  also recomputes orthogonality and all bases from the integer vectors, and, for two pools, by a
  checker whose soundness is proved in Lean 4.

**What has to be trusted.**

* For a result marked **Lean**: the Lean kernel, and the reading of the theorem statement and of the
  definitions it uses (`boxRays`, `dot`, `card`, `Sub`, `VColorable`, about 25 lines in
  [lean/KS/Spec.lean](lean/KS/Spec.lean) and [lean/KS/Basic.lean](lean/KS/Basic.lean), printed in
  full in [lean/README.md](lean/README.md)). The statement speaks of the integer vectors of the pool
  and of dot products only. The tables of bit masks, the certificates and the checkers are not
  trusted: Lean proves that the tables agree with the vectors and that the checkers are sound.
* For a result marked **proof-checked**: the construction of the pool, the encoder, the verification of
  the cuts, the proof checker, and Lemmas 1, 3, 6 and 7. The SAT and CP-SAT solvers are not trusted.
  For the four-axis case of dimension five the proofs of two different solvers (CaDiCaL and Glucose)
  were both checked.
* For a count "exactly n": the same as for "proof-checked" (the uniqueness runs of section C.1 of the
  register), together with the encoder's check that the list of sets is closed under the symmetries of
  the pool.
* For a result marked **tree**: the JavaScript verifier and the Node runtime, and that the rays listed
  in the certificate file are the pool the paper describes.
* For a result marked only **A** or **B**, or "second solver" without a checked proof: the solvers that
  gave the answer, in addition to the above.

## 5. Prior work, and what is new

The values 31, 33, 18 and 29 are the sizes of published sets and are not claimed here: 31 is the set
of Conway and Kochen (in Peres 1993), 33 the complex set of Cabello (2025) and Pavičić (2025), 18 the
set of Cabello, Estebaranz and García-Alcaine (1996), 29 their set of 2005. The question "what is the
exact minimum inside a pool" has also been asked before:

* **Kernaghan**, arXiv:2603.16988, a preprint whose computations and text were, by its own statement,
  generated by a language model, surveys coordinate alphabets in dimension three. It reports as exact,
  by a SAT procedure for which no certificate is given, the minimum 31 for the 49 rays with coordinates
  in {0, ±1, ±2} and the minimum 33 for the 57-ray pool of sixth roots of unity, and it lists 31 also
  for coordinates up to 3. By randomised minimisation it finds six distinct 31-ray sets in the 49-ray
  pool (one remark there speaks instead of 162 distinct sets, six up to automorphism). It proves that
  the pool of N-th roots of unity contains a Kochen-Specker set if and only if 6 divides N. For
  N = 12, 18, 24 it gives only upper bounds, and it has no dimension above three.
* A note on the forum **ProblemHive** (post p/xfkay, October 2026, posted by an AI agent) reports the
  minimum 31 for integer coordinates up to 2, 3 and 4, obtained with CP-SAT and the same kind of
  coloring cut as here. It states itself that its solver logs are not a certificate.
* In **dimension four** the bound 18 holds for all Kochen-Specker sets (Pavičić, Merlet, McKay and
  Megill 2005), and in every dimension (Xu, Chen and Gühne 2020), not only inside a pool. The 18-ray
  sets inside the 24 rays of Peres are known: there are 16 of them (Waegell and Aravind, Found.
  Phys. 41 (2011) 1786).
* In **dimension five**, Pavičić and Megill (Phys. Rev. A 106, L060203, 2022) generate from the
  components 0, ±1 a "master" set with 105 rays and 136 bases, which is the core of the pool B(5, 1),
  and report that the smallest critical set of its class has 29 rays and 16 bases, with two
  non-isomorphic sets of that size (also Pavičić and Waegell 2024). No proof that nothing smaller
  exists is given there.
* Formal proofs exist for other statements: non-colorability of Peres's 33 rays in HOL Light
  (Harrison), the Kochen-Specker paradox in Lean (Gupta), case-tree certificates of non-embeddability
  replayed in Lean for the geometric half of the bound 24 (Siddique and Mian), and a contextuality
  degree in Lean (Li, Gupta and Ganesh). We found no formal proof of a minimality statement for
  Kochen-Specker sets, and none for the Conway-Kochen or the 18-ray set.

So these are **not new**: the minimum 31 for B(3, 2), B(3, 3) and B(3, 4) and the minimum 33 for
U(3, 6), which were reported before without certificates (four values in dimension three); 29 as the
smallest set generated from the coordinates 0, ±1 in dimension five, reported without a proof that
nothing smaller exists; the minimum 18 in dimension four; and the count of 16 minimum sets in B(4, 1),
which are the 16 known sets inside the 24 rays of Peres (`results/peres24_check.json`). The first
literature search of this project missed the last two reports (dimension five, and the 16 sets). They
were found in the review before release and the claims were narrowed
([docs/REVIEW.md](docs/REVIEW.md)).

Claimed as new, to our knowledge and within a literature search made on 9 and 10 November 2026:

1. proofs with certificates for the results: Lean 4 kernel proofs for the 49-ray pool and for the
   40-ray pool of dimension four, replayable search trees, and unsatisfiability proofs checked by a
   separate checker, at the level recorded for each row in the register;
2. complete lists of the minimum sets: exactly six for integer coordinates up to 3 and up to 4 (the
   same six as for 2), exactly 3 and 12 for sixth and twelfth roots of unity, each list a single orbit
   under the symmetries of the pool; and the fact that the 40-ray pool of dimension four contains no
   18-ray Kochen-Specker set besides the 16 known ones;
3. the exact minimum 33 for twelfth, eighteenth and twenty-fourth roots of unity;
4. the proof that 29 is the minimum for coordinates 0, ±1 in dimension five, where 29 had been
   reported as the smallest set obtained, and the fact that every Kochen-Specker set in that pool
   contains at least three coordinate axes;
5. the method beyond the coloring cut itself: necessary conditions for critical sets as constraints, a
   symmetry normal form, an encoding whose unsatisfiability proofs are checked independently, and tree
   certificates with a checker proved sound in Lean.

The coloring-cut idea is not claimed; it also appears in the ProblemHive note and, in the form of an
unsatisfiable-subset loop, in Kernaghan's preprint. Preprints in this area appear weekly, several of
them produced with AI systems, and a further overlap we did not find is possible. Full references are
in the [paper](paper/ks-minimum.md), Section 1.3 and the reference list.

## 6. Repository map

| path | what |
|---|---|
| `paper/ks-minimum.md` | the paper |
| `paper/PROOFS.md` | every lemma the programs rely on, with its proof |
| `results/RESULTS.md` | the register of results and their status (single source of truth) |
| `results/` | tree certificates (`cert_*.json`), cut files with their witnesses (`master_*_cuts.json`, `satcegar_*_cuts.json`, `enumerate_*_cuts.json`), the explicit sets (`ks_sets.json`, seven sets; `ks31_box3_H2.json`), the lists of minimum sets (`enumerate_*.json`), the answers of the second solver (`second_solver_*.json`), `lemma7_d5_axes.json`, `d5_axes_sanity.json`, `d5_sections.json`, `peres24_check.json`, `pool_facts.json`, `min_missed.json`, `ablate_c1c2_box3_4_k30.json`, the results of the randomised searches (`hunt_*.json`), the run report `run_all.json` |
| `logs/` | the logs written by the runs |
| `src/` | the programs: `ksengine.py` (the Pool class), `pools.py`, `pools3d.py`, `cyclo.py` (pools), `ksmaster.py` (engine A), `ks_cnf.py` and `ks_satcegar.py` (engine B), `cubes_d5.py` (the 81 cubes of the five-axis case), `ksdfs.py` and `gen_cert.py` (engine C and its certificates), `kslocal.py` and `hunt.py` (randomised search) |
| `scripts/` | `run_all.py` (one command for the small checks); `certify.sh` and `certify_unique.sh` (engine B with proof check, for a minimum and for a count of minimum sets); `second_solver.py` and `prove_cnf.py` (a second SAT solver on an existing formula, without and with a proof); `check_cubes.py` (proof checks of the 81 cubes); `enumerate_min.py`, `lemma7.py`, `axes_sanity.py`, `d5_sections.py`, `peres24.py`, `pool_facts.py`, `min_missed.py`, `ablate_c1c2.py` (the computations behind single statements of the register); `gen_lean.py`, `collect_sets.py`, `run_stack.py`; `check_docs.py` (consistency of the documents with the register); and the site and paper builders |
| `verify/` | `verify_cert.mjs` (independent JavaScript verifier) with its tests, `drup_check.c` (proof checker) |
| `lean/` | the Lean 4 development ([lean/README.md](lean/README.md)): `KS/Basic.lean` (tables, checkers, soundness theorems), `KS/Spec.lean` (the pool `boxRays` and colorability in terms of integer vectors; agreement with the tables), `KS/Box3H2.lean` and `KS/Box4H1.lean` (generated data modules with the main theorems), `KS/Tests.lean` (regression tests), `KS/Audit.lean` (axiom audit) |
| `tests/` | unit and property tests ([tests/README.md](tests/README.md)) |
| `stack/`, `third_party/` | the demonstration of the 31-ray set on Moonlab, QGTL, quantum_rng and Eshkol (paper, Section 6), and the vendored third-party files it uses ([third_party/README.md](third_party/README.md)) |
| `docs/` | the site (`index.html`, `assets/`, `data/`), the built paper, and the documents listed at the top of this page, among them the review record [docs/REVIEW.md](docs/REVIEW.md) and the list of deferred work [docs/TRIGGER-REGISTER.md](docs/TRIGGER-REGISTER.md) |
| `publication/` | files prepared for the author's submissions ([publication/README.md](publication/README.md)); nothing in it is submitted by the build process |
| `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` | versions; how to report an error or contribute; how to report a security problem; conduct |

## 7. Install

* **Python 3.9 or newer** (developed on 3.9.13). `python -m pip install -r requirements.txt` installs
  the pinned versions of python-sat, OR-Tools and NumPy. Two scripts need one more package each and are
  not needed for the checks of section 3: `scripts/enumerate_min.py` imports `networkx`, and
  `scripts/build_paper.py` imports `commonmark`.
* **Node 22 or newer** for the JavaScript verifier (it has no dependencies; developed on Node 25).
* **A C compiler** (`gcc` or `cc`) for the proof checker: `scripts/run_all.py` compiles
  `verify/drup_check.c` itself; by hand, `gcc -O2 -o verify/drup_check verify/drup_check.c`.
* **Lean** through [elan](https://github.com/leanprover/elan), only for step c. The toolchain is fixed
  in `lean/lean-toolchain` (Lean 4.35.0) and is downloaded by elan on first use.

The demonstration `python scripts/run_all.py --stack` additionally uses the Eshkol compiler
(`eshkol-run`); it is optional and is not part of any proof (see section 8).

## 8. Limits and open questions

* **Scope.** A pool result excludes smaller Kochen-Specker sets only inside the pool. The general
  problem in dimension three (between 24 and 31) and in dimensions five and above (between 18 and the
  records) is not settled by any of this.
* **No record was broken.** No Kochen-Specker set smaller than a published one was found in any
  dimension.
* **Not everything is certified to the same level.** Only rows A1 and A8 have a Lean proof, and the
  Lean theorems cover the minimum value, not the count of minimum sets. Only rows A1, A2 and A8 have a
  tree certificate replayed by the JavaScript verifier. For row A7 Glucose ran out of memory; the
  formula of engine B was solved by CaDiCaL instead, and its proof was checked. In row A9 engine A
  closed only one of the three cases; the proof checks of the 81 cubes of the five-axis case are
  recorded in the register. The register and
  [docs/INDEX.md](docs/INDEX.md) give the level for every row and the status of every proof check.
* **Stopped runs.** B(3, 5): the exact search did not finish; it was stopped by hand after more than
  an hour, and no claim is made. U(3, 30): stopped unfinished. Whether 21 is the minimum in U(6, 3)
  and 34 in the pool of E8 root rays was not decided. The Lean check for B(3, 3) was stopped after 49
  minutes without a verdict.
* **A withdrawn remark.** An earlier version of the register and the paper said that no critical
  Kochen-Specker set of B(5, 1) with all five coordinate axes had been met in random samples and that
  this case might be empty. That was wrong: the sampler was biased. With plain random deletion 3734 of
  3828 samples end with five axes; the smallest such sets found have 31 rays
  (`results/d5_axes_sanity.json`). No theorem depended on the remark.
* **Weak evidence stays weak.** In U(3, 24) the randomised walk stopped at 36 rays although the pool
  contains 33-ray sets. A randomised search that finds nothing smaller is not a proof.
* **Not peer reviewed.** No specialist has refereed the paper or the programs. Before release the
  material was examined in nine reviewing passes made by the same AI system that produced it; that is
  an internal check, not peer review, and it changed several claims
  ([docs/REVIEW.md](docs/REVIEW.md)).
* **The proof checker and the JavaScript verifier are tested, not formally verified.** Only the Lean
  results have a machine-verified checker.
* **The stack demonstration is a simulation.** Moonlab is a classical state-vector simulator, the
  quantum_rng mixers are a classical pseudo-random stream, and nothing here is an experiment on quantum
  hardware.
* **Open questions** (paper, Section 7): Is 31 the minimum in B(3, H) for all H? Is 33 the minimum in
  U(3, N) for every multiple N of 6? Is 21 the minimum in U(6, 3), and 34 in the E8 pool? Is 29 the
  minimum in dimension five without restriction on the coordinates? Does B(5, 1) contain a critical
  Kochen-Specker set with 29 or 30 rays and all five coordinate axes?

Deferred work, each item with the condition that would trigger it, is listed in
[docs/TRIGGER-REGISTER.md](docs/TRIGGER-REGISTER.md).

## 9. Licence, citation, AI disclosure, contact

**Licence.** Copyright © 2026 0thernes LLC (Alexander S. Donahue). The repository is released under
the verification licence in [LICENSE](LICENSE): anyone may download, build, run and study it to check,
reproduce or referee the results, and quote from it with attribution; redistribution of modified
versions and commercial use need written permission. Third-party components keep their MIT licences
([NOTICE](NOTICE), [third_party/README.md](third_party/README.md)). Plain-language notes are in
[LEGAL.md](LEGAL.md).

**Citation.** See [CITATION.cff](CITATION.cff). Please also cite the prior work credited in section 5.

**AI disclosure.** The research, programs, Lean proofs and text were produced by an AI system, Claude
(Anthropic), working as an agent at the request and under the direction of the author, who is
responsible for the release. An AI system is not an author. The work was funded by the author through
0thernes LLC; there was no external funding and there are no competing interests.

**Contact and corrections.** If you find an error in a statement, a proof or a count, or know of
earlier work that already contains one of the results, please open an issue on
https://github.com/0thernes/kochen-specker-extremal-lab or write to 0_0@0thernes.art. See also
[CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
