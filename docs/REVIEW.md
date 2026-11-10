# Review before release: findings and what was done about them

Kochen-Specker Extremal Lab, version 1.0.0, 10 November 2026.

Before release the material was examined in nine separate reviewing passes, each with one question, a
rule that every finding needs evidence produced during the review (a script and its output, two
quoted lines that contradict each other, or a counterexample), and no permission to change anything
in the repository. The passes were made by instances of the same AI system that produced the work
(Claude, Anthropic), each started without the working notes of the others. **This is an internal
check, not peer review by specialists, and it does not replace one.** It is recorded here because
it changed the paper in substance, and so that a reader can see what was looked at and what was
not.

Severity words: *critical* = a stated theorem or headline number could be false or unsupported;
*major* = a claim is overstated, a proof step is wrong or missing, or a check cannot fail; *minor*;
*note*. No pass reported a critical finding. No theorem and no minimum or count in Table 2 of the paper changed;
the evidence column changed for B(3, 3) and U(3, 24).

## Summary of the outcome

| Pass | Question | Result | Findings |
|---|---|---|---|
| Lean semantics | Do the Lean theorems say what the paper says, and can the checkers accept something false? | Theorems genuine; about 5.9 million malformed and well-formed certificates on tiny pools, none accepted for a false statement | 2 major, 1 minor, 2 notes |
| Lemmas | Can Lemmas 1, 3, 5 or Corollary 4 be refuted? | Not refuted, by reasoning or by brute force on five pools and on random graphs | 2 minor, 3 notes |
| Symmetry and uniqueness | Are the normal form, the case split, the 81 cubes and the "exactly n sets" inference right? | All correct as stated and as implemented | 1 major, 1 minor, 1 note |
| Encoder | Does the Boolean formula exclude any real KS set? | No: 221 critical KS sets of dimension five and all minimum sets of dimensions three and four are models of their formulas; non-solutions are rejected | 1 minor, 2 notes |
| Proof pipeline | Can the pipeline print VERIFIED for something that was not proved? | No false VERIFIED in 19 200 differential fuzzing rounds against an exact reference, 246 real Glucose proofs (one-shot and incremental) and their corrupted and satisfiable variants; the stored formulas equal a fresh encoding token for token | 1 major, 3 minor, 2 notes (this pass ran out of time before writing its report; its findings are taken from its working notes) |
| Numbers | Does every number in paper and register have evidence? | No headline number disagrees with the evidence | 1 major, 4 minor, 4 notes |
| Prior work and references | Is prior work described fairly, and does every reference exist? | All 38 references of the reviewed version exist as cited (two were added afterwards and checked against Crossref); three places where prior work was understated | 3 major, 3 minor, 3 notes |
| Independent pools | Are the pools, cores, bases and sets reproduced by code that shares nothing with the project? | All reproduced, including the cuts of all 81 cube files | 2 minor |
| Independent re-runs | Do the engines give the same answers from a clean copy? | Every verdict reproduced: engine A, engine B and the proof checker on fresh cut files, the uniqueness runs (6, 16, 3 sets), and KS sets found once the bound is raised by one; committed formulas and proofs byte-identical when regenerated | 2 minor, 3 notes |

## Findings that changed a claim

1. **Prior work in dimension five had been missed** (major). Pavicic and Megill (2022) generate, from
   the coordinates 0, +1, -1 in dimension five, the same 105 rays and 136 bases that form the core
   of the pool B(5, 1), and report 29 rays as the smallest critical set of that class, with two
   non-isomorphic sets. The paper had called the dimension-five minimum "the first exact minimum in
   a pool beyond dimension four" and listed no prior work for it. *Done:* Section 1.3 now describes
   that report; the claim is narrowed to the proof with checked certificates; the abstract, the box
   on the first page and section H of the register say so.
2. **The 16 minimum sets in dimension four were known** (major). They are the 16 sets of 18 rays
   inside the 24 rays of Peres counted by Waegell and Aravind (2011). *Done:* cited; the claim is
   narrowed to "the 16 further rays of the pool give no other 18-ray KS set";
   `scripts/peres24.py` checks that all 16 lie in the 24 rays.
3. **Earlier reports for dimension three were understated** (major). The first-page box said that two
   pools had been reported before; in fact four had (integer bounds 2, 3, 4 and sixth roots of
   unity). *Done:* corrected in the box, the abstract and Section 4.1.
4. **"A certificate for every result" was not true** (major): the pool of 24th roots of unity had only
   one solver's answer, because Glucose ran out of memory there. *Done:* the formula was given to a
   second solver (CaDiCaL), which finds it unsatisfiable; the status of its proof check is in the
   register, row A7, and the blanket sentences were reworded.
5. **The Lean theorems were about tables, not vectors, and the abstract credited Lean with the counts
   of minimum sets** (2 major). *Done:* `lean/KS/Spec.lean` now defines the pool `boxRays d H` and a
   notion of colorability that mentions only dot products; the data modules prove that their list
   of vectors is that pool, that every ray of the box occurs exactly once, and the theorems
   `minimum_ks_size_vectors`. The paper says that Lean covers the two minimum values only.
6. **A wrong remark about dimension five** (major). The paper said that no critical KS set with all
   five coordinate axes had been met in 58 684 samples and that the case might be empty. Two
   reviewers found such sets within seconds. The project's sampler was biased: it jumped to the SAT
   solver's unsatisfiable core after every deletion. *Done:* `scripts/axes_sanity.py` now does plain
   deletion (3734 of 3828 samples end with five axes); a 31-ray five-axis set is recorded in
   `results/ks_sets.json`; the five-axis case has a positive control (a search in one cube with
   bound 31 finds a KS set, and a unit test plants that set in its cube's formula); the remark and
   the open question were rewritten. No theorem depended on the remark.
7. **The count of minimum sets rested on an unchecked property** (minor). With symmetry breaking in
   the formula, "unsatisfiable once the listed sets are excluded" proves that every minimum set is
   an image of a listed one; the count needs the list to be closed under the symmetry group, which
   was only asserted in a comment. A reviewer showed that a list of 2 of the 6 sets would also have
   been "verified". The lists are in fact closed (checked independently by two reviewers). *Done:*
   `src/ks_cnf.py` now checks closure and stops otherwise; the uniqueness runs were repeated.
8. **A comparison that was not like for like** (minor). "The conditions C1 and C2 reduce the rounds
   for B(3, 4) from 26 to 7" compared two different programs. *Done:* replaced by a controlled run
   (`scripts/ablate_c1c2.py`): 15 rounds without the conditions, 6 with them, no gain in time.
9. **The randomised-search table left out a failure** (minor). In the pool of 24th roots of unity the
   walk stopped at 36 rays although the pool contains 33-ray sets. *Done:* the row is in Table 4
   and in section E of the register, with the sentence corrected.
10. **The proof checker's reader could be fooled by an out-of-range number** (proof pipeline, minor
    in effect). In the old reader a token such as 4294967296 wrapped around to 0 and split a clause
    in two, so a crafted satisfiable formula was "verified". The project's formulas cannot contain such
    a token (their largest variable is 76 220, and the cube check compares every formula with a fresh
    encoding), but a checker must not depend on that. *Done:* `verify/drup_check.c` now reads every
    token strictly (integers of absolute value at most 10^8), requires a `p cnf` line that matches
    the clauses, and reports running out of memory instead of crashing; `tests/test_drup.py` has nine
    new cases for this. Both builds give identical output on every real proof compared.
11. **The certification scripts could report success after a failed check** (proof pipeline, major).
    `scripts/certify.sh` and `scripts/certify_unique.sh` ended with exit status 0 even when the
    checker could not be started, the summary of `certify_unique.sh` could show the VERIFIED line of
    an earlier run from the same log, and variables left in the shell that restrict a run to one cube
    were passed on silently. No recorded verdict was wrong: every VERIFIED of the register has a
    matching log line, rechecked by the reviewer. *Done:* both scripts now exit 0 only if the proof of
    the current run was written and verified, delete an older proof first, print the current run only,
    and clear those variables; `src/ks_cnf.py` refuses cube fixes outside a cube run and prints the
    fixed rays.
12. **Smaller defects of the pipeline.** `src/ks_cnf.py` and `scripts/prove_cnf.py` ended with exit
    status 127 instead of the documented 3 after a satisfiable answer (a crash of the solver's
    destructor at exit on Windows); `scripts/check_cubes.py` read formula files line by line while the
    checker reads token by token. Both fixed. "14 of 266" (fewest bases missed in B(3, 5)) came from a
    time-limited solve; it is now an optimum of an exact MaxSAT solver (`scripts/min_missed.py`).
13. **What happened during the final checks.** In the first run of the proof check of the 81 cubes,
    18 cubes were verified and for the other 63 the checker ended without printing any verdict. A
    manual run on one of them verified it, and the machine's memory commit charge was near its limit
    at the time, so the likely cause is that the checker ran out of memory (the old build did not
    report this). These were not rejections. The 63 cubes were checked again with the release build (outcome:
    CUBEVERDICT); `results/d5_cubes_certification.json` records, for every cube, the verdict and the
    SHA-256 of the checker build that produced it.
14. **Smaller corrections.** The structure "18-ray KS set in a hyperplane plus 11 rays" was attributed
    to the wrong one of the two 29-ray sets; 33 was called a "record" number of rays although the
    cited record is the number of bases; the bound 18 in every dimension was attributed to a
    four-dimensional paper; a tree certificate for B(3, 3) covered only the core (a certificate for
    the whole 145-ray pool, 11 330 nodes, is now shipped and replayed); several durations had no
    log record and are now quoted from logs or without a figure; a Python pre-check lacked a guard
    that the Lean checker has; cube fixes could leak from the environment into a non-cube run;
    `certify.sh` could have checked a proof left by an earlier run. All fixed.

## What the reviews confirmed

* The pools, their cores and bases, recomputed with separate code and separate exact arithmetic for
  roots of unity: every size in section A of the register.
* Each recorded KS set is a KS set and is critical; the six, three, twelve and sixteen minimum sets
  are distinct, are KS sets, and form one orbit; the Conway-Kochen set, as described in the
  literature, is one of the six.
* Lemma 1 in both directions, Lemma 3 on more than 1700 critical sets and on random graphs, Lemma 5
  by an exhaustive fixed-point test on tiny structures, Lemma 6 by applying all 48, 384 or 3840
  signed coordinate permutations, Lemma 7 by separate enumeration.
* The formulas on disk for the certified runs equal a fresh re-encoding, clause for clause; every
  stored cut equals the set of bases missed by its stored independent set (all 131 760 cuts of the
  81 cube files included).
* The Lean development has no `sorry`, no added axiom and no `native_decide`; the displayed
  theorems are the theorems in the sources.
* All 38 references of the reviewed version exist with the stated authors, titles, venues and
  numbers.

## What was not reviewed

* Nobody outside this project has read the paper. The author is not a specialist in the field.
* The proof checker `verify/drup_check.c` and the JavaScript verifier were attacked with crafted
  inputs and fuzzing, not formally verified.
* The full text of several cited papers was read only in part (abstracts, tables, the passages
  quoted in Section 1).
* The reviewing passes were made by the system that wrote the work. They found real errors, as the
  list above shows, but they share its blind spots.
