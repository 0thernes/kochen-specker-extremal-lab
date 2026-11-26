# Ready-to-Send Submission & Correspondence Dossier (`docs/submission-packet.md`)

> **Status:** Draft preparation packet awaiting human author review, line-by-line fidelity sign-off, and manual submission. Nothing in this file has been transmitted or submitted by any automated script.

## 1. Palomar Registry Draft Payload (`formalization.yaml`)

- **Repository:** `https://github.com/0thernes/kochen-specker-extremal-lab`
- **Lean toolchain:** `leanprover/lean4:v4.35.0` (**zero Mathlib**)
- **Challenge / Solution / Config:** `lean/Challenge.lean`, `lean/Solution.lean`, `lean/comparator.json`
- **6-kernel comparator command:** `cd lean && lake build --wfail KS Solution && lake env lean KS/Audit.lean && lake env leanchecker --fresh Solution && lake comparator --config comparator.json --paranoid`
- **4 targets verified across 6 independent kernels:**
  1. `KS.ComparatorTarget.target_box3h2_minimum_31`
  2. `KS.ComparatorTarget.target_box4h1_minimum_18`
  3. `KS.ComparatorTarget.target_box3h2_nonvacuous_30`
  4. `KS.ComparatorTarget.target_box4h1_nonvacuous_17`
- **Permanent Software Heritage snapshot:** `swh:1:snp:6df0f79e042201d9490512cc8dda65471db9fafb` (`v1.9.0`; updated snapshot recorded in `0thernes-research-archive` after `v2.0.0`)

## 2. Human Line-by-Line Statement Fidelity Sign-Off Checklist (Playbook v1.3)

Before flipping `human_line_by_line_review_recorded: false` → `true` in `formalization.yaml`, the author inspects and initials each item:

- [ ] Read `lean/KS/Basic.lean` (`Colorable`, `card`, `check`, `refute`) and confirm rules 1 & 2 match Kochen–Specker (1967) Definition in Section 2.
- [ ] Read `lean/KS/Spec.lean` (`boxRays`, `dot`, `VColorable`, `vcolorable_of_colorable`, `colorable_of_vcolorable`) — ~25 lines defining the integer-vector trust base.
- [ ] Read `lean/Challenge.lean` (all 4 targets including 30-ray and 17-ray non-vacuity targets) and verify zero vacuous hypotheses.
- [ ] Verify `results/RESULTS.md` register rows A1–A9 match `paper/ks-minimum.md` Table 2 and `publication/ks-minimum/ks-minimum.pdf`.
- [ ] Verify `publication/arxiv-metadata.txt` and `publication/zenodo-inquiry.md` before any external deposit.

## 3. Suggested Specialist Correspondence List (Draft Outreach Notes)

- **Adán Cabello / Stefan Trandafir** (University of Seville) — share certified exact pool minima for $B(3,2..4)=31$, $U(3,6..24)=33$ (matching Cabello 2025 14-basis complex set), and zero-Mathlib Lean 4 proofs for $B(3,2)$ and $B(4,1)$.
- **Mladen Pavičić / Mordecai Waegell** — share independent proof-checked confirmation of 29 in $B(5,1)$ (crediting Pavičić & Megill 2022) and exact uniqueness of the 16 Peres sets inside $B(4,1)$ (crediting Waegell & Aravind 2011).
- **Zhengyu Li / Curtis Bright / Vijay Ganesh / Stefan Szeider** — share independent `drat-trim` → LRAT → `lrat-check` + Lean 4 certificate pipeline for coordinate-pool KS minimality.
