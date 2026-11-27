# Claims & Falsification Ledger (`CLAIMS.md`)

| ID | Claim | Evidence Tag | Verification Artifact | What Would Prove Us Wrong (Falsifier) |
|---|---|---|---|---|
| **KS-01** | Minimum KS set inside $B(3,2)$ (49 rays) has size **31** (31-ray uncolourable set exists; every $\le 30$-ray subset is colourable) | `kernel-checked` (zero Mathlib; accepted by the official Lean kernel in default and paranoid mode and by lean4lean, nanoda, con-leche, con-ron) | `lean/KS/Box3H2.lean` (`minimum_ks_size_vectors`), `lean/Challenge.lean` Targets 1, 3, 5 (min, independent basis-bearing 30-ray colouring witness, kernel refutation of false bound 30) | A $\le 30$-ray KS set inside $B(3,2)$ or a valid KS colouring of `ksSet`. |
| **KS-02** | Minimum KS set inside $B(4,1)$ (40 rays of $\{0,\pm 1\}^4$) has size **18** | `kernel-checked` (same checkers as KS-01) | `lean/KS/Box4H1.lean` (`minimum_ks_size_vectors`), `lean/Challenge.lean` Targets 2, 4, 6 (min, independent basis-bearing 17-ray colouring witness, kernel refutation of false bound 17) | A $\le 17$-ray KS set inside $B(4,1)$ or a valid KS colouring of `ksSet`. |
| **KS-03** | Exact pool minima: 31 in $B(3,3)$ and $B(3,4)$; 33 in $U(3,N)$ (entries 0 or $N$-th roots of unity) for $N = 6, 12, 18, 24$ only; 29 in $B(5,1)$. No Lean proof. | `certificate-checked` (SAT/DRUP proofs checked by the project's own checker `verify/drup_check.c`; among these seven pools, $B(3,3)$, $U(3,6)$ [minimum + uniqueness = 3], and $U(3,12)$ — alongside $B(3,2)$ and $B(4,1)$, 5 of 9 pools total — are also checked by third-party `drat-trim`/`lrat-check` and HOL4-verified `cake_lpr` in CI; also rests on the CNF encoder `src/ks_cnf.py` and the paper Lemmas 1, 3, 6, 7) | `verify/drup_check.c`, `scripts/verify_lrat.sh`, `results/RESULTS.md` | A smaller KS set inside any of those pools, or rejection of the CNF/DRUP/LRAT proof by `drat-trim`/`lrat-check`/`cake_lpr`. For $B(3,4)$, $U(3,18)$, $U(3,24)$ and $B(5,1)$ the proof files must first be regenerated (`docs/INDEX.md`). |
| **KS-04** | General minimal KS open problem ($24 \dots 31$ in $\mathbb{R}^3$) | `open` (NOT claimed) | `LIMITATIONS.md` | Explicitly out of scope; pool results say nothing about rays outside the stated pools. |

**Prior and parallel work.** The values 31 ($B(3,2)$, $B(3,3)$) and 33 ($U(3,6)$) were reported
earlier by Kernaghan (arXiv:2603.16988). Its version 10 of 23 November 2026, 13 days after this
repository's v1.0.0 (10 November 2026), certifies 31 for $B(3,2)$ and the 145-ray pool $B(3,3)$ and 33
(with exactly three minimum sets) for $U(3,6)$, and proves 31 for $B(3,2)$ and 33 for $U(3,6)$ in Lean.
The bound 18 holds for all KS sets in every dimension (Xu, Chen, Gühne, arXiv:2001.07656); KS-02 restricts
it to one finite pool. The counts of minimum sets (6, 3, 12, 16) are not Lean theorems.
