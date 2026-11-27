# Ready-to-Send Submission & Correspondence Dossier (`docs/submission-packet.md`)

> **Status:** Draft preparation packet awaiting human author review, line-by-line fidelity sign-off, and manual submission. Nothing in this file has been transmitted or submitted by any automated script.

## 1. Palomar Registry Draft Payload (`formalization.yaml`)

- **Repository:** `https://github.com/0thernes/kochen-specker-extremal-lab`
- **Lean toolchain & Palomar compliance:** `leanprover/lean4:v4.35.0` (**zero Mathlib**; all 9 `.lean` files carry Lean 4.35 `module` headers, ≤ 10,000 lines, zero `.lean` symlinks; `Challenge.lean` ≤ 1,000 lines / 100 KiB)
- **Challenge / Solution / Config:** `lean/Challenge.lean`, `lean/Solution.lean`, `lean/comparator.json`
- **Comparator command (official Lean kernel default and paranoid, plus lean4lean, nanoda, con-leche, con-ron):** `cd lean && lake build --wfail KS Solution && lake env lean KS/Audit.lean && lake env leanchecker --fresh Solution && lake comparator --config comparator.json --paranoid`
- **7 targets accepted by these checkers (all 7 independent; closing `ERRATA.md` K1 & K2 in `v2.2.0` and adding full Boolean-checker completeness in `v2.3.0`):**
  1. `KS.ComparatorTarget.target_box3h2_minimum_31`
  2. `KS.ComparatorTarget.target_box4h1_minimum_18`
  3. `KS.ComparatorTarget.target_box3h2_nonvacuous_30` (explicit 30-ray subset with complete 3-basis + direct 0/1 colouring via `isColoring_of_isColoringBool`)
  4. `KS.ComparatorTarget.target_box4h1_nonvacuous_17` (explicit 17-ray subset with complete 4-basis + direct 0/1 colouring via `isColoring_of_isColoringBool`)
  5. `KS.ComparatorTarget.target_box3h2_refute_30` (kernel-proved refutation of false bound 30)
  6. `KS.ComparatorTarget.target_box4h1_refute_17` (kernel-proved refutation of false bound 17)
  7. `KS.ComparatorTarget.target_isColoringBool_iff` (soundness AND completeness `isColoringBool P T c = true ↔ IsColoring P T c` for `T < 2 ^ P.n`)
- **Permanent Software Heritage snapshot:** `swh:1:snp:4c421f5d8b6cf9d06c224ed7bfafe88bc3392f4f` (`v2.2.0`; refreshed via Save Code Now on each release)
- **DOI fallback note (Playbook v1.3 H13):** Wait for Zenodo's reply to `publication/zenodo-inquiry.md`; if Zenodo declines, deposit via **OSF Preprints** (moderated, DOI on acceptance). Do not deposit to HAL until a formal affiliation exists.
- **Export-control self-screen (Playbook v1.3 #37):** Pure mathematical foundations / combinatorics (`15 CFR 734.8` published fundamental research); no controlled cryptographic, defense, or dual-use implementation. Consult counsel if any doubt arises prior to commercial use.

## 2. Human Line-by-Line Statement Fidelity Sign-Off Checklist (Playbook v1.3)

Before flipping `human_line_by_line_review_recorded: false` → `true` in `formalization.yaml`, the author inspects and initials each item:

- [ ] Read `lean/KS/Basic.lean` (`Colorable`, `card`, `check`, `refute`) and confirm rules 1 & 2 match Kochen–Specker (1967) Definition in Section 2.
- [ ] Read `lean/KS/Spec.lean` (`boxRays`, `dot`, `VColorable`, `vcolorable_of_colorable`, `colorable_of_vcolorable`) — ~25 lines defining the integer-vector trust base.
- [ ] Read `lean/Challenge.lean` (all 7 targets including independent basis-bearing non-vacuity witnesses, kernel-proved false-variant refutations, and `target_isColoringBool_iff`) and verify zero vacuous hypotheses.
- [ ] Verify `results/RESULTS.md` register rows A1–A9 match `paper/ks-minimum.md` Table 2 and `publication/ks-minimum/ks-minimum.pdf`.
- [ ] Verify `publication/arxiv-metadata.txt` and `publication/zenodo-inquiry.md` before any external deposit.

## 3. Suggested Specialist Correspondence List (Draft Outreach Notes)

- **Adán Cabello / Stefan Trandafir** (University of Seville) — share certified exact pool minima for $B(3,2..4)=31$, $U(3,N)=33$ for $N = 6, 12, 18, 24$ (matching Cabello 2025 14-basis complex set), and zero-Mathlib Lean 4 proofs for $B(3,2)$ and $B(4,1)$.
- **Mladen Pavičić / Mordecai Waegell** — share independent proof-checked confirmation of 29 in $B(5,1)$ (crediting Pavičić & Megill 2022) and exact uniqueness of the 16 Peres sets inside $B(4,1)$ (crediting Waegell & Aravind 2011).
- **Zhengyu Li / Curtis Bright / Vijay Ganesh / Stefan Szeider** — share the `drat-trim` → LRAT → `lrat-check` + HOL4-formally-verified `cake_lpr` cross-check (11 UNSAT/uniqueness proofs across 6 pools spanning $d \in \{3,4,5\}$) + zero-Mathlib Lean 4 certificate pipeline for coordinate-pool KS minimality.
