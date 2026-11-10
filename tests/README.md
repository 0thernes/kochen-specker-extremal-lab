# tests

Unit and property tests for the Kochen-Specker Extremal Lab. Plain Python `unittest`, standard library
only (plus the project's own dependencies in `requirements.txt`).

```
python tests/test_pools.py                             # any file runs on its own, from the repository root
python -m unittest discover -s tests -p "test_*.py"    # everything (about one minute)
python scripts/run_all.py                              # tests + regenerated certificates + proofs, one line per stage
python scripts/run_all.py --lean --stack               # ... plus the Lean build/audit and the stack demonstration
```

## What is tested

| file | subject | independent oracle |
|---|---|---|
| `test_pools.py` | `src/pools.py`, `src/pools3d.py`: integer boxes, E8, stabilizer states, `build_box3` against `box_pool(3,H).ks_core()` | ray counts from closed formulas; orthogonality and all bases recomputed from the vectors with `itertools` and integer dot products |
| `test_cyclo.py` | `src/cyclo.py`: cyclotomic polynomials, `RootSums.is_zero`, root-of-unity pools | known polynomials, `prod_{d\|N} Phi_d = x^N - 1`; 150-digit evaluation with a rigorous separation bound; Gaussian- and Eisenstein-integer arithmetic |
| `test_colouring.py` | `Pool.coloring`, `is_ks`, `is_critical`, `shrink`; the 31-ray set of `results/ks31_box3_H2.json`; Lemmas 1 and 3 of `paper/PROOFS.md` | brute force over all 0/1 assignments (up to 2^18); an exhaustive backtracking search without a SAT solver |
| `test_search.py` | `ksdfs.KSDfs`, `gen_cert.CertDfs` / `check` / `check_pool`, `ksmaster.Master` (with and without symmetry breaking), `ksengine.minimum_ks` | every KS set an engine returns is re-checked by the backtracking search; every cut is recomputed from its witness |
| `test_cnf.py` | `ks_cnf.CNF.counter`, `ks_cnf.encode`, `verify_cuts`; Lemma 6 (normal form) | all input assignments of the counter; models decoded against the constraints as written in the paper; search over the 48 signed coordinate permutations |
| `test_verify_tools.py` | `verify/drup_check.c`, `tests/test_drup.py`, `verify/verify_cert.mjs`, `verify/test_verify.mjs`, `scripts/lemma7.py` and `results/lemma7_d5_axes.json` | a naive unit propagation; fresh certificates and proofs; integer re-check of the Lemma 7 file |
| `test_run_all.py` | `scripts/run_all.py` itself | failing and crashing stages must give FAIL and exit status 1 |
| `test_drup.py` | (pre-existing) positive and negative tests of the proof checker; a script with its own `main`, run by `test_verify_tools.py` as a subprocess | |

`_common.py` holds the oracles. It imports nothing from `src/`: orthogonality, bases, colorings and
cuts are recomputed there from the vectors.

Expected values written into the tests are either independent mathematical facts (numbers of rays,
orthogonal pairs and bases of the named pools) or the two minimum sizes that are proved in Lean
(31 for the 49-ray pool, 18 for the 40-ray pool; rows A1 and A8 of `results/RESULTS.md`). Nothing else
from the results register is hard-coded.

## Every test can fail

Each area contains deliberately corrupted inputs that must be rejected, for example

* pools: an added or removed orthogonal pair, a dropped or bogus basis, a changed coordinate, the wrong
  inner product;
* roots of unity: non-vanishing sums, every proper subsum of the weight-six relation, a wrong polynomial;
* colorings: a coloring with a basis left without a 1, with two orthogonal 1s, with a ray outside the set;
  the 31-ray set with one ray removed, added or replaced;
* certificates: `k` raised by one, each of the 254 single child deletions, a changed or dropped ray of an
  independent set, a dropped basis, a changed vector;
* cuts and CNF: a cut with a basis removed, a witness that is not independent, a counter with a clause
  deleted or a literal flipped, the formula without its cuts or without its cardinality clause, a model
  with one variable flipped; a too-strong "normal form";
* proofs: the real proof against the satisfiable formula for `k + 1`, the empty proof, a first lemma that
  does not follow by unit propagation;
* the runner: a stage that cannot succeed, a stage that raises.

A mutation check was run when the suite was written (2026-11-10): 21 single-line bugs were injected,
one at a time, into a scratch copy of `src/` (sign normalisation of rays, the E8 parity, the core
threshold, the zero test for root sums, the SAT clauses of the coloring model, the size bound of the
tree search, rules 1 and 2 of the certificate checker, the cardinality, (C2) and symmetry-breaking
constraints of both encodings, the counter, the cut verification, the hitting-set bound). 20 were
detected. The one that was not, `deg >= 4` instead of `deg >= 3` in `pools3d.build_box3`, changes
nothing for max-norm up to 6, where every ray of the core has at least four orthogonal partners; the
threshold itself is tested on random sub-pools through `Pool.ks_core`.

## Side effects

The tests and `scripts/run_all.py` do not write into the repository, with two exceptions: the report
`results/run_all.json` written by `run_all.py`, and the optional stage `--stack`, which runs
`scripts/run_stack.py` in place. Programs that write next to their sources (`ksmaster.py`, `ks_cnf.py`,
`lemma7.py`, `test_verify.mjs`) are run from byte-identical copies in a temporary directory with the same
layout, and the regenerated files are compared with the committed ones.

## Environment

| variable | meaning |
|---|---|
| `KS_TEST_WORKERS` | CP-SAT worker threads used by the tests (default 2) |
| `KS_SKIP_JS_SUITE=1` | skip the run of `verify/test_verify.mjs` inside `test_verify_tools.py` (`run_all.py` sets it and runs that suite as its own stage) |

External tools: `node` (22 or newer) for the JavaScript verifier, `gcc` or `cc` for the proof checker.
When `node` is missing the JavaScript tests are skipped with a message; when no up-to-date
`verify/drup_check` (`drup_check.exe` on Windows) is present it is compiled into a temporary directory,
and the proof-checker tests are skipped with a message if there is no C compiler either.
`scripts/run_all.py` is stricter: a missing tool makes the stage FAIL (use `--skip js,cert-verify` on a
machine without node).

## Not covered here

* The long runs behind the other rows of `results/RESULTS.md` (larger pools, dimension 5 cases); they are
  reproduced by the commands recorded in `logs/`, not by this suite.
* `src/kslocal.py`, `src/hunt.py` (randomised search), `src/ks_satcegar.py` and the exploratory scripts.
* The Lean development is checked by `scripts/run_all.py --lean` and by the `lean` job of
  `.github/workflows/ci.yml`, not by the unit tests.
* `pools.stabilizer_pool(3)` is not built (it would enumerate every 8-clique among 1080 rays); the test
  checks the 1080 rays returned by `pools.stabilizer_rays(3)`, which is what that pool is made from.

`test_cnf.KnownLimits` checks the encoder when `k` is at least the number of rays (the size bound is
then vacuous and is left out), and `test_cnf.FiveAxisControl` is the positive control for the
five-axis case of dimension five: a 31-ray KS set with all five coordinate axes is a model of its
cube's formula with bound 31 and is rejected with bound 30.
