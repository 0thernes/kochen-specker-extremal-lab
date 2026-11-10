# Summary in plain language

Kochen-Specker Extremal Lab, version 1.0.0, 10 November 2026. Research preprint, not peer reviewed.
Produced by an AI system (Claude, Anthropic) at the request and under the direction of Alexander S.
Donahue, 0thernes LLC, who is responsible for the release.

## The question

Quantum mechanics predicts the results of measurements. It does not say that the measured quantity had
that value before it was measured. The opposite idea is that every measurement outcome is fixed in
advance, whatever else is measured alongside it. In 1967 Kochen and Specker showed, with a finite
geometric puzzle, that this idea cannot be reconciled with quantum theory.

The puzzle goes like this. A *ray* is a direction in space. Two rays are *orthogonal* when they are at
right angles; a *basis* is a full set of mutually orthogonal rays (three in ordinary space). Given a
finite set of rays, try to label each ray 0 or 1 so that

1. two orthogonal rays are never both 1, and
2. every basis inside the set has a ray labelled 1.

A set of rays for which no such labelling exists is a **Kochen-Specker set**. The first one had 117
rays. Ever since, people have asked how small such a set can be.

That question is open. In dimension three the smallest known set has 31 rays, and it has been proved
that at least 24 are needed; the truth lies somewhere from 24 to 31. Only in dimension four is the
answer known (18).

## What this lab did

It did not solve the open question, and it found no set smaller than the published ones. Nothing here
is a new record.

It answered a restricted question. Choose a finite *pool* of rays, for instance all directions whose
coordinates are whole numbers from −2 to 2 (49 rays). What is the smallest Kochen-Specker set made
only of rays from that pool? For nine pools the lab determined the answer:

| Pool | number of rays | smallest Kochen-Specker set |
|---|---|---|
| dimension 3, whole-number coordinates up to 2, up to 3, up to 4 | 49, 145, 289 | 31 |
| dimension 3, coordinates 0 or 6th, 12th, 18th, 24th roots of unity | 57, 183, 381, 651 | 33 |
| dimension 4, coordinates 0, +1, −1 | 40 | 18 |
| dimension 5, coordinates 0, +1, −1 | 121 | 29 |

In every pool the answer is the size of the smallest set of that kind already published. So the known
sets cannot be improved in the places where they live, and making the pool larger (from 49 to 289
rays, say) did not help. For six of the pools the lab also listed all the smallest sets: exactly 6 in
each of the three whole-number pools of dimension three, 3 for sixth roots of unity, 12 for twelfth
roots of unity, and 16 in the four-dimensional pool. In each of these pools the smallest sets are all
copies of one another under the symmetries of the pool.

## What was known before, and what is new

Reported before by others, without a proof that a reader can check:

* 31 for whole-number coordinates up to 2, 3 and 4 (a preprint by Kernaghan and a note on the forum
  ProblemHive), and six smallest sets for coordinates up to 2 (found by Kernaghan with a randomised
  method);
* 33 for sixth roots of unity (Kernaghan);
* 29 as the smallest set obtained from the coordinates 0, +1, −1 in dimension five (Pavičić and
  Megill 2022), with no proof that nothing smaller exists.

Known and proved before:

* 18 is the minimum for all Kochen-Specker sets, in dimension four and in every dimension, not only
  inside a pool;
* the 16 sets of 18 rays: they are the 16 known sets inside a classical family of 24 rays due to Peres
  (Waegell and Aravind 2011).

New here, as far as a search of the literature on 9 and 10 November 2026 could tell:

* the proofs: for each of the nine pools, evidence that nothing smaller exists that can be checked
  without trusting the search program (next section). For dimension five this is the proof that 29 is
  the minimum, where 29 had been reported as the smallest set found;
* the value 33 for 12th, 18th and 24th roots of unity (only upper bounds were known);
* the complete lists of smallest sets for whole-number coordinates up to 3 and 4 and for sixth and
  twelfth roots of unity, and the fact that the 40-ray pool of dimension four contains no set of 18
  rays besides the 16 known ones.

The first literature search of this project missed two of the earlier reports (the one for dimension
five and the 16 sets). A review before release found them, and the claims were narrowed; the record
is in [REVIEW.md](REVIEW.md).

## Why "there is nothing smaller" can be checked

A small set is easy to verify once someone shows it. Showing that *no* smaller set exists is the hard
part, because a computer search could simply be wrong. The lab therefore attaches evidence that does
not depend on trusting the search:

* **Proved in Lean** (two pools: 49 rays in dimension three, 40 rays in dimension four). Lean is a
  proof checker; its kernel verified the statement "some set of 31 rays cannot be labelled, and every
  set of at most 30 rays can" (18 and 17 for the other pool), using only its three standard axioms.
  The statement is written directly for the whole-number vectors of the pool, so a reader has to
  trust the Lean kernel and about 25 lines of definitions, and nothing else. Lean covers these two
  minimum values only, not the lists of smallest sets.
* **Proof-checked.** A solver's claim "impossible" comes with a long proof file, and a separate small
  program checks that file step by step. The lists of smallest sets ("exactly 6", "exactly 16" and so
  on) are confirmed in this way for all six pools.
* **Second solver.** The same formula is given to a second, different solver (CaDiCaL next to
  Glucose). Agreement checks the solvers against each other; it does not check that the formula was
  written correctly.
* **Tree certificate.** A record of an exhaustive search, replayed by an independently written
  program.
* **Solver answer only.** Some of the evidence is a solver's answer and nothing more (for example
  every answer of the method called engine A); the register marks it as such and does not count it
  as a proof.

Which result has which kind of evidence, and the status of every proof check, is listed row by row in
the register, [results/RESULTS.md](../results/RESULTS.md). The weaker points are stated there too. For
the pool of 24th roots of unity the first SAT solver ran out of memory; the formula was solved by a
second one, CaDiCaL, and its proof passed the check. The result for dimension five is an argument in
three cases with 83 formulas in all; engine A could finish only one of the three cases, and the other
two rest on the SAT solvers and the checks of their proofs, which the register lists case by case.

## What this is not

* Not a solution of the minimal Kochen-Specker problem in any dimension. A result about a pool says
  nothing about rays outside it.
* Not a new record. No smaller set was found anywhere, including in randomised searches in further
  pools in dimensions three to eight. In one of those pools the randomised search even stopped above
  the known size, which shows how little such a search proves.
* Not peer reviewed. The review before release was made by the same AI system that produced the work.
* Not an experiment. The demonstration on the Tsotchke software (Moonlab and others) is a calculation
  on an ordinary computer.
* Not a claim to the values 31, 33, 18, 29 themselves, which belong to the authors cited in the paper,
  nor to the pool results reported earlier by Kernaghan, on the ProblemHive forum, and by Pavičić and
  Megill, nor to the count of 16 sets in dimension four.

## Check it yourself

```
python -m pip install -r requirements.txt
python scripts/run_all.py
node verify/test_verify.mjs
cd lean && lake build && lake env lean KS/Audit.lean
```

What each command should print is described in the [README](../README.md), section 3. Where each claim
is proved, tested and logged: [INDEX.md](INDEX.md). The terms: [GLOSSARY.md](GLOSSARY.md). What was
run and what failed: [REPORT.md](REPORT.md). What the review found: [REVIEW.md](REVIEW.md). The full
text: [the paper](../paper/ks-minimum.md).
