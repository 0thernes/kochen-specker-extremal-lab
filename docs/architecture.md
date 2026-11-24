# Architecture

`kochen-specker-extremal-lab` intentionally preserves a **zero-Mathlib Lean 4.35.0 trust base** for exact ray-pool Kochen-Specker minimality proofs (`B(3,2) = 31` and `B(4,1) = 18`), paired with independent SAT/DRUP certificates for larger coordinate pools and an independent JavaScript certificate replayer (`docs/`).

- `lean/KS/`: Pure Lean 4.35.0 core (`Basic`, `Spec`, `Box3H2`, `Box4H1`, `Tests`, `Audit`), zero external Lake packages.
- `lean/Challenge.lean` & `lean/Solution.lean`: Isolated statement specification checked across six independent kernels by `lake comparator --config comparator.json --paranoid`.
- `src/`, `verify/`, `scripts/`, `tests/`: Exact integer & Gaussian-integer pool generators, CNF encoders, C11 DRUP checker (`verify/drup_check.c`), and test suite.
- `paper/` & `docs/`: Research preprint, lemma proofs, and interactive in-browser certificate replayer.
