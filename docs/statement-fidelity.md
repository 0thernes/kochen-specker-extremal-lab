# Statement-Fidelity Audit (`docs/statement-fidelity.md`)

| Lean Declaration | Informal Claim | Literature Anchor | Fidelity Notes | Status |
|---|---|---|---|---|
| `KS.VColorable` (`Spec.lean`) | $T$ admits a KS 0/1 colouring | Kochen & Specker (1967) | Encodes at least one 1 per basis inside $T$ and no two orthogonal 1s via exact integer dot products over $\mathbb{R}^d$. | Mechanically verified; human sign-off open |
| `KS.boxRays d H` (`Spec.lean`) | Pool $B(d,H)$ of primitive integer rays with $\max$-norm $\le H$ | Kernaghan (`arXiv:2603.16988`) | `boxRays_exact` certifies each ray appears exactly once (`|B(3,2)|=49`, `|B(4,1)|=40`). | Mechanically verified |
| `KS.Box3H2.minimum_ks_size_vectors` | Minimum KS set in $B(3,2)$ has 31 rays | Kernaghan (`arXiv:2603.16988`) | Vector-only statement (`VColorable`, `boxRays 3 2`); non-vacuity witness `target_box3h2_nonvacuous_30`. | 6-kernel comparator verified |
| `KS.Box4H1.minimum_ks_size_vectors` | Minimum KS set in $B(4,1)$ has 18 rays | Waegell & Aravind, *Found. Phys.* 41 (2011) | Vector-only statement; non-vacuity witness `target_box4h1_nonvacuous_17`. Uniqueness (16 Peres sets) is certificate-checked outside Lean. | 6-kernel comparator verified |
| (DRUP certificates) | Minima 31/33 ($H=3,4$, roots of unity) and 29 (dim 5) | Pavičić & Megill, *PRA* 106 L060203 (2022) | Verified by `verify/drup_check.c` outside Lean; `drat-trim -> LRAT -> cake_lpr` planned in `ROADMAP.md`. | Certificate-only |
