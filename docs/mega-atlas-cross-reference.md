# Cross-Reference Against `0thernes/unsolved-problems-mega-atlas` (`1,900` Open Problems)

**Audit Date:** 2026-11-25  
**Target Catalog:** [`0thernes/unsolved-problems-mega-atlas`](https://github.com/0thernes/unsolved-problems-mega-atlas) (`1,900` open problems, verified at commit `f838db1d7`)  
**Repository:** `kochen-specker-extremal-lab` (`v1.9.0`, registered as `0TH-2026-004` in `0thernes-research-archive`)

## Honest Headline Verdict

- **Mega-Atlas grand problems completely solved:** **`0 / 1,900`**
- **Nearest Mega-Atlas entry:** **`QM-011`** (*Kochen–Specker minimal ray sets and quantum contextuality*) — **UNSOLVED in general** (`24 <= min_KS(R^3) <= 31`; `18 <= min_KS(R^d)` for `d >= 5`).

## Exact Scope Boundary (Pool-Restricted Subcases vs. Grand Open Problem)

| Problem | Status | Verification Level | Exact Statement |
|---|---|---|---|
| **General minimal KS set in $\mathbb{R}^3$ (`QM-011`)** | **OPEN (NOT solved)** | — | Known bounds remain $24 \le m_3 \le 31$. Pool results say nothing about rays outside the tested finite pools. |
| **$B(3,2)$ (49 rays) & $B(4,1)$ (40 rays) exact pool minima** | **Settled (restricted)** | **Zero-Mathlib Lean 4.35.0 (6 kernels + `leanchecker --fresh`)** | `KS.Box3H2.minimum_ks_size_vectors` (`31`) and `KS.Box4H1.minimum_ks_size_vectors` (`18`); 30 explicit + 149 exhaustive KS theorems strictly within `[propext, Classical.choice, Quot.sound]`. |
| **$B(3,3)$, $B(3,4)$, $U(3,6..24)$, $B(5,1)$ exact pool minima & orbit enumerations** | **Settled (restricted)** | **SAT/DRUP + JS search-tree certificates (outside Lean)** | Exact minima `31`, `33`, `29` and orbit counts (`6`, `3`, `12`, `16`) verified by `verify/drup_check.c` and `verify/verify_cert.mjs`; `drat-trim -> LRAT -> cake_lpr` upgrade logged on `ROADMAP.md`. |
| **Multiqubit Pauli contextuality sibling work (`QM-011`)** | **Settled (subcases)** | **Lean 4.35.0 + Mathlib (6 kernels)** | Maintained separately in [`0thernes/pauli-contextuality-lab`](https://github.com/0thernes/pauli-contextuality-lab) (`0TH-2026-009`), keeping this repository's zero-Mathlib trust base minimal. |

No grand problem in `unsolved-problems-mega-atlas` is claimed as solved.
