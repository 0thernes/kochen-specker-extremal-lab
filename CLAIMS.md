# Claims & Falsification Ledger (`CLAIMS.md`)

| ID | Claim | Evidence Tag | Verification Artifact | What Would Prove Us Wrong (Falsifier) |
|---|---|---|---|---|
| **KS-01** | Minimum KS set inside $B(3,2)$ (49 rays) has size **31** (31-ray uncolourable set exists; every $\le 30$-ray subset is colourable) | `kernel-checked` (zero Mathlib, 6 kernels) | `lean/KS/Box3H2.lean` (`minimum_ks_size_vectors`), `lean/Challenge.lean` Targets 1 & 3 | A $\le 30$-ray KS set inside $B(3,2)$ or a valid KS colouring of `ksSet`. |
| **KS-02** | Minimum KS set inside $B(4,1)$ (40 rays of $\{0,\pm 1\}^4$) has size **18** | `kernel-checked` (zero Mathlib, 6 kernels) | `lean/KS/Box4H1.lean` (`minimum_ks_size_vectors`), `lean/Challenge.lean` Targets 2 & 4 | A $\le 17$-ray KS set inside $B(4,1)$ or a valid KS colouring of `ksSet`. |
| **KS-03** | Exact pool minima 31/33 in 3D ($H=3,4$, roots of unity) and 29 in 5D | `certificate-checked` (SAT/DRUP + independent `drat-trim`/LRAT in CI for `B(3,2)`, `B(4,1)`, `B(3,3)`) | `verify/drup_check.c`, `scripts/verify_lrat.sh`, `results/RESULTS.md` | A smaller KS set inside any of those pools, or rejection of the CNF/DRUP/LRAT proof by `drat-trim`/`lrat-check`/`cake_lpr`. |
| **KS-04** | General minimal KS open problem ($24 \dots 31$ in $\mathbb{R}^3$) | `open` (NOT claimed) | `LIMITATIONS.md` | Explicitly out of scope; pool results say nothing about rays outside the stated pools. |
