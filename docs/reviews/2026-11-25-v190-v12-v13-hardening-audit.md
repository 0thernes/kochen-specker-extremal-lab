# Hardening Audit (`v1.9.0` — Build Standard v1.2.0 & Playbook v1.3 Upgrade)

**Date:** 2026-11-25  
**Target:** `kochen-specker-extremal-lab` (`v1.8.0` → `v1.9.0`, zero-Mathlib Lean 4.35.0, registered as `0TH-2026-004` in `0thernes-research-archive`).  
**Standards:** Build Standard for LLMs `v1.2.0` (`90` items, `10` finding classes) & Defensible Independent AI Research Playbook `v1.3` (`43` checklist items, `H01`–`H48`).

> **Epistemic-honesty note (Playbook v1.3 H48):** This audit records strictly the literal cycles, automated checks, and defects found and resolved in this release — zero inflated pass multipliers. Historical `v1.8.0` review logs are retained verbatim for provenance, with this clarification noted in `ERRATA.md`.

## Cycle 1 — Build Standard v1.2.0 & Playbook v1.3 Structural Audit

| Finding Class | Location | Concrete Defect Found | Resolution & Verification |
|---|---|---|---|
| `error` | `repo.yaml` | Targeted obsolete `standard: "1.1.0"` and used invalid `stack: [lean, python, c-cpp]` (`"lean"` violates Draft 2020-12 enum). | Upgraded to `standard: "1.2.0"` and `stack: [python, c-cpp, node, other]`; validated against Draft 2020-12 `repo-standard.schema.json` in `tests/test_repo_integrity.py`. |
| `gap` | `docs/glossary.md` | 3-line self-referential stub pointing back to `glossary.md` without domain definitions or the 10 finding classes. | Replaced with complete domain glossary (ray, basis, KS colouring, $B(d,H)$, $U(d,N)$, core, colouring cut, DRUP, search tree) and all 10 Build Standard v1.2.0 finding classes. |
| `gap` | `ERRATA.md`, `docs/mega-atlas-cross-reference.md` | Missing Playbook v1.3 `ERRATA.md` (Checklist #39 / H28) and `0thernes/unsolved-problems-mega-atlas` (`1,900` problems) cross-reference. | Added `ERRATA.md` (DOI policy, corrections ledger, withdrawal plan) and `docs/mega-atlas-cross-reference.md` (honest `0 / 1,900` verdict; `QM-011` coordinate-pool boundary). |
| `hole` | `.github/workflows/{ci,pages,release}.yml` | Outdated Actions (`v4`/`v5`/`v2`), unverified `gitleaks-action@v2` (no `osv-scanner`), missing `continue-on-error: true` on `release.yml` attestation, missing `leanchecker --fresh`, missing adversarial false-variant Lean tests, and pre-H46 `axiom` regex. | Upgraded all workflows to `v7`/`v6`/`v5`/`v4`, SHA-256-verified `gitleaks v8.30.1` + `osv-scanner v2.7.1`, `leanchecker --fresh Solution`, 3 adversarial false-variant Lean tests, H46 lexer, and `git archive` source bundles. |
| `hole` | `scripts/run_all.py:392`, `scripts/check_docs.py:86`, `scripts/check_references.py:40` | `run_all.py` omitted `Solution.lean` from source scanning and used naive line regex; `check_docs.py` flagged a placeholder link example inside `docs/build-standard.md`; `check_references.py` lacked Crossref retraction checks. | Fixed all three scripts; `check_docs.py` now exits 0 with 0 problems. |

## Cycle 2 — Manuscript, `0.00 pt` LaTeX Typesetting & Reproducible Build Script Parity

| Finding Class | Location | Concrete Defect Found | Resolution & Verification |
|---|---|---|---|
| `conflict` | `scripts/build_latex.py` vs. `publication/ks-minimum/ks-minimum.tex` | `v1.3.0`/`v1.6.0` manually added `\hypersetup` and clickable ORCID/email to `ks-minimum.tex` without updating `scripts/build_latex.py`. | Updated `scripts/build_latex.py` to emit `\hypersetup{pdftitle=..., pdfauthor=...}`, clickable ORCID/email `\href`, and header-width-aware table columns. |
| `issue` | `publication/ks-minimum/ks-minimum.tex:367` | Residual `3.73 pt` overfull `\hbox` in Table 2. | Rebalanced Table 2 column widths (sum = `1.0000`) → **`0` overfull hboxes (`0.00 pt` max)**, 0 undefined refs, verified PDF `/Info` `/Title` & `/Author`. |
| `gap` | `paper/ks-minimum.md` & `ks-minimum.tex` Section 9 | Missing explicit CRediT author-contribution list and `ERRATA.md` reference (Playbook v1.3 Checklist #32/#39). | Added CRediT roles and `ERRATA.md` reference across Markdown, TeX, PDF, and HTML. |

## Cycle 3 — Verification Convergence & Honest `A24` Status

- **Lean 4.35.0 (zero Mathlib):** `lake build KS Solution`, `KS/Audit.lean` (`30` explicit + `149` exhaustive KS theorems strictly within `[propext, Classical.choice, Quot.sound]`), **`lake env leanchecker --fresh Solution` (exit 0)**, 3 adversarial false-variant Lean refutation tests, and 6-kernel `lake comparator --paranoid` in CI.
- **Build Standard v1.2.0 Audit (`A24` transparency):** `63/64` applicable items PASS (`98.4%`); `A24` remains honestly marked `partial` in `repo.yaml` because two historical cut-certificate JSON files (`results/master_roots_3_18_k32_cuts.json`, `8.64 MB`; `results/master_roots_3_24_k32_cuts.json`, `12.90 MB`, pinned in `results/proof_manifest.json`) are intentionally retained for offline proof replay.
