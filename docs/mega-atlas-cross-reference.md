# Cross-Reference Against `0thernes/unsolved-problems-mega-atlas` (`1,900` Open Problems)

**Audit Date:** 2026-11-26  
**Target Catalog:** [`0thernes/unsolved-problems-mega-atlas`](https://github.com/0thernes/unsolved-problems-mega-atlas) (`1,900` open problems, verified at commit `f838db1d7`)  
**Repository:** `kochen-specker-extremal-lab` (`v2.1.0`, registered as `0TH-2026-004` in `0thernes-research-archive`)

## Honest Headline Verdict

- **Mega-Atlas grand problems completely solved:** **`0 / 1,900`**
- **Nearest Mega-Atlas entry:** **`QM-011`** (*Kochen–Specker minimal ray sets and quantum contextuality*) — **UNSOLVED in general** (`24 <= min_KS(R^3) <= 31`; `18 <= min_KS(R^d)` for `d >= 5`).

## Exact Scope Boundary (Pool-Restricted Subcases vs. Grand Open Problem)

| Problem | Status | Verification Level | Exact Statement |
|---|---|---|---|
| **General minimal KS set in $\mathbb{R}^3$ (`QM-011`)** | **OPEN (NOT solved)** | — | Known bounds remain $24 \le m_3 \le 31$. Pool results say nothing about rays outside the tested finite pools. |
| **$B(3,2)$ (49 rays) & $B(4,1)$ (40 rays) exact pool minima** | **Settled (restricted)** | **Zero-Mathlib Lean 4.35.0 (9/9 `module` headers; official kernel default and paranoid, lean4lean, nanoda, con-leche, con-ron, `leanchecker --fresh`)** | `KS.Box3H2.minimum_ks_size_vectors` (`31`) and `KS.Box4H1.minimum_ks_size_vectors` (`18`); 30 explicit declarations and all 116 theorem constants in `KS` under Lean 4.35 `module` mode (62 hand-written) within `[propext, Classical.choice, Quot.sound]`. Kernaghan `arXiv:2603.16988v10` (23 Nov 2026) independently proves `31` for `B(3,2)` in Lean, after this repository's `v1.0.0` (10 Nov 2026). |
| **$B(3,3)$, $B(3,4)$, $U(3,6..24)$, $B(5,1)$ exact pool minima & orbit enumerations** | **Supported by certificates (restricted)** | **SAT/DRUP certificates outside Lean; JS tree certificate for `B(3,3)` only** | Exact minima `31` (`B(3,3)`, `B(3,4)`), `33` (`U(3,N)`, `N = 6, 12, 18, 24` only), `29` (`B(5,1)`) and orbit counts (`6`, `3`, `12`, `16`) checked by the project's own `verify/drup_check.c`; third-party `drat-trim -> LRAT -> lrat-check` and HOL4-formally-verified `cake_lpr` in CI for `B(3,3)` only among these pools (plus `B(3,2)` and `B(4,1)`); `cake_lpr` replay of the 83 dim-5 cubes logged on `ROADMAP.md`. Kernaghan `arXiv:2603.16988v10` also certifies `31` for `B(3,3)` and `33` (3 sets) for `U(3,6)`, and proves the latter in Lean. |
| **Multiqubit Pauli contextuality sibling work (`QM-011`)** | **Related / bounded results** | **Lean 4.35.0 + Mathlib (12 comparator targets on 6 kernels)** | Maintained separately in [`0thernes/pauli-contextuality-lab`](https://github.com/0thernes/pauli-contextuality-lab) (`0TH-2026-009`), keeping this repository's zero-Mathlib trust base minimal. |

No grand problem in `unsolved-problems-mega-atlas` is claimed as solved.
