# `v2.2.0` Formal Closure & Verification Audit (`2026-11-26`)

- **Repository:** `0thernes/kochen-specker-extremal-lab`
- **Target Release:** `v2.2.0` (following `v2.1.0` `888ee43`, CI `45939136064`, Release `45940283452`, SWH `swh:1:snp:68ed4cd5af45b8fa4ed21a82f8f3dfd69ac901ae`)
- **Standards Audited Against:** Build Standard for LLMs `v1.2.0` (`repo-standard.schema.json`, 10 finding classes, Rules R1–R8) and Defensible Independent AI Research Playbook `v1.3` (H01–H48, Part D Palomar Registry).

## 1. Formal-Code Errata Closed Inside Lean 4.35.0

All three formal-code items (`K1`–`K3`) logged in the 2026-11-26 independent statement audit (`ERRATA.md`) are now closed directly in Lean 4.35.0 (zero Mathlib, 9/9 `module` headers, `--wfail`):

1. **`K1` Closed — Independent Basis-Bearing Non-Vacuity Witnesses (`lean/KS/Basic.lean`, `lean/Challenge.lean`, `lean/Solution.lean`):**
   - Added pure zero-Mathlib `KS.isColoringBool (P : Pool) (T c : Nat) : Bool` and kernel-proved soundness theorem `KS.isColoring_of_isColoringBool`.
   - Strengthened `target_box3h2_nonvacuous_30` to exhibit `T = 0x3b70c7ffc69e` (30-ray subset of the 31-ray Conway–Kochen `ksSet`, containing 13 complete 3-bases witnessed by `[1, 7, 20]`) and prove `VColorable (boxRays 3 2) 3 T` directly from the explicit 0/1 colouring `c = 0x183000e` via `isColoring_of_isColoringBool` (zero appeal to `minimum_ks_size_vectors`).
   - Strengthened `target_box4h1_nonvacuous_17` to exhibit `T = 0x2aac0aaaac` (17-ray subset of the 18-ray Peres `ksSet`, containing 7 complete 4-bases witnessed by `[2, 7, 9, 26]`) and prove `VColorable (boxRays 4 1) 4 T` directly from the explicit 0/1 colouring `c = 0x8000200c` via `isColoring_of_isColoringBool`.
2. **`K2` Formal Half Closed — Kernel-Proved Refutations of Perturbed Headline Bounds (`lean/Challenge.lean`, `lean/Solution.lean`, `lean/comparator.json`):**
   - Added Comparator Targets 5 & 6 (`target_box3h2_refute_30`, `target_box4h1_refute_17`) refuting existence of any $\le 30$-ray KS set in $B(3,2)$ or $\le 17$-ray KS set in $B(4,1)$, plus `refute_box3h2_all_31_colorable` and `refute_box4h1_all_18_colorable` refuting colourability of all 31-ray / 18-ray subsets.
   - `lean/comparator.json` now exports **6** isolated comparator targets checked by the official Lean kernel (default and paranoid) plus `lean4lean`, `nanoda`, `con-leche`, and `con-ron`.
3. **`K3` Updated (`lean/KS/Audit.lean`):**
   - Prints **35** explicit `#print axioms` lines and exhaustively audits **122** kernel theorem constants in `KS` (**67** hand-written: 59 in `KS/*.lean` + 8 in `Solution.lean`), strictly within `[propext, Classical.choice, Quot.sound]`.

## 2. Independent SAT/LRAT + HOL4 `cake_lpr` Expansion (`scripts/verify_lrat.sh`)

Expanded Linux CI `scripts/verify_lrat.sh` from 3 pools to **5 pools / 6 UNSAT proofs**, adding:
- `U(3,6)` lower bound (`k = 32`, 2,305 vars / 8,885 clauses, Glucose4 UNSAT in 0.0 s),
- `U(3,6)` exact uniqueness (`k = 33`, 3 sets excluded via `KS_BLOCKED`, 2,329 vars / 8,983 clauses, Glucose4 UNSAT in 0.0 s),
- `U(3,12)` lower bound (`k = 32`, 9,010 vars / 38,504 clauses, Glucose4 UNSAT in 1.3 s),

alongside `B(3,2)` (`k = 30`), `B(4,1)` (`k = 17`), `B(3,3)` (`k = 30`), and the truncated-LRAT negative control rejected by both `lrat-check` and HOL4-formally-verified `cake_lpr`.

## 3. Metadata, Timestamps & Manuscript Checks

- Fixed lingering `arXiv:2603.16988v9` citation in `publication/zenodo-metadata.json` (`v10`, 23 November 2026) and aligned AI disclosures across `README.md`, `paper/ks-minimum.md`, `publication/zenodo-metadata.json`, and `publication/orcid-work.bib`.
- Rebuilt `publication/ks-minimum/ks-minimum.{tex,pdf}`, `docs/ks-minimum.pdf`, `docs/paper.html`, and `publication/ks-minimum/arxiv-source.zip` (`0.00 pt` max overfull hbox).
- Refreshed `data/MANIFEST.sha256` after the Lean edits and re-sealed both `data/MANIFEST.sha256.tsr` (DigiCert RFC 3161 TSA) and `data/MANIFEST.sha256.ots` (3-calendar Bitcoin OpenTimestamps).
- Verified `lake build --wfail KS Solution`, `lake build Challenge`, `lake env lean KS/Audit.lean`, `lake env leanexport Solution`, `python -m unittest discover -s tests -v`, `python scripts/check_docs.py`, `python scripts/stamp_timestamps.py --verify`, and `node verify/test_verify.mjs`.
