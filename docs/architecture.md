# Architecture

`kochen-specker-extremal-lab` intentionally preserves a **zero-Mathlib Lean 4.35.0 trust base** for exact ray-pool Kochen-Specker minimality proofs (`B(3,2) = 31` and `B(4,1) = 18`), paired with SAT/DRUP certificates for the seven larger coordinate pools (checked by the project's own `verify/drup_check.c`; third-party `drat-trim`/LRAT cross-check in CI for `B(3,3)` only among them) and an independent JavaScript certificate replayer (`docs/`).

- `lean/KS/`: Pure Lean 4.35.0 core (`Basic`, `Spec`, `Box3H2`, `Box4H1`, `Tests`, `Audit`), zero external Lake packages.
- `lean/Challenge.lean` & `lean/Solution.lean`: Isolated statement specification accepted by `lake comparator --config comparator.json --paranoid` with the official Lean kernel (default and paranoid mode) and lean4lean, nanoda, con-leche, con-ron.
- `src/`, `verify/`, `scripts/`, `tests/`: Exact integer & Gaussian-integer pool generators, CNF encoders, C11 DRUP checker (`verify/drup_check.c`), and test suite.
- `paper/` & `docs/`: Research preprint, lemma proofs, and interactive in-browser certificate replayer.
