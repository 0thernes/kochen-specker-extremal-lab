# Changelog

## [Unreleased]

- Extend `drat-trim` -> LRAT -> formally verified `cake_lpr` replay to `B(3,4)`, `U(3,18)`, `U(3,24)`, and the remaining 82 dimension-5 branches/cubes.

## [2.3.0] — 2026-11-27

### 3-Cycle Deep Hardening: Boolean-Checker Completeness (`isColoringBool_iff`, 7-Target Comparator), 11-Proof / 6-Pool / 3-Dimension HOL4 `cake_lpr` CI Coverage, Live Tamper-Injection Gate & Isolated AST Source-Code Mutation Suite

- **Lean 4.35.0 Soundness AND Completeness (`lean/KS/Basic.lean`, `Challenge.lean`, `Solution.lean`, `comparator.json`, `KS/Audit.lean`):** Proved `KS.subMask_of_sub`, `KS.isColoringBool_of_isColoring`, and full bidirectional equivalence **`KS.isColoringBool_iff`** (`isColoringBool P T c = true ↔ IsColoring P T c` for `T < 2 ^ P.n`), promoted as Comparator Target 7 (`target_isColoringBool_iff`). Updated `KS/Audit.lean` (`38` explicit `#print axioms` declarations + exhaustive audit of all `126` kernel theorem constants in `KS`, `71` hand-written; zero warnings `--wfail`; `lake env leanchecker --fresh Solution`; 6-kernel `lake comparator --paranoid`).
- **Expanded HOL4-Verified `cake_lpr` CI Coverage to 11 UNSAT/Uniqueness Proofs Across 6 Pools Spanning ALL THREE Dimensions $d \in \{3,4,5\}$ (`scripts/verify_lrat.sh`):** Added exact uniqueness UNSAT proofs for `B(3,2)` (`k=31`), `B(4,1)` (`k=18`), `B(3,3)` (`k=31`), and `U(3,12)` (`k=33`) PLUS the **5-dimensional** `B(5,1)` three-axis branch `in:0,1,2;out:3,4` (`k=28`) — all 11 proofs independently cross-verified live in CI by `verify/drup_check`, pinned `drat-trim` → LRAT → `lrat-check`, and HOL4-formally-verified `cake_lpr` (`s VERIFIED UNSAT`), plus truncated-LRAT negative control.
- **Live Tamper-Injection Negative Gate (`.github/workflows/ci.yml`) & Isolated AST Source-Code Mutation Suite (`tests/test_properties_and_fuzz.py`):** Added a live CI gate planting a temporary custom `axiom evil_tamper_axiom : False` and verifying active rejection by BOTH Lean `#print axioms` allowlist AND the H46 forbidden-token lexer; added 6/6 isolated AST source-code operator-mutation tests against in-memory AST copies of `src/pools.py` and `src/ks_cnf.py` (100% mutant kill rate); replaced `ruff E731` lambda assignments in `src/ks_cnf.py`, `src/ksmin.py`, and `tests/test_pools.py` with proper `def` functions.
- **Fresh Provenance, Timestamp Re-Seal & `0.00 pt` PDF:** Synced verified `v2.2.0` Software Heritage snapshot `swh:1:snp:4c421f5d8b6cf9d06c224ed7bfafe88bc3392f4f` and CI/SLSA receipts across `CITATION.cff`, `formalization.yaml`, `docs/{threat-model,submission-packet,run-log}.md`, and `publication/README.md`; updated AI disclosure range `v1.1.0--v2.3.0` in `publication/ks-minimum/ks-minimum.tex`; recompiled `ks-minimum.pdf` (`0.00 pt` overfull hbox) + `arxiv-source.zip` + `docs/ks-minimum.pdf`; re-sealed `data/MANIFEST.sha256` with fresh DigiCert RFC 3161 TSA + 3-calendar Bitcoin OpenTimestamps; logged the 3-cycle audit in `docs/reviews/2026-11-27-v230-3cycle-completeness-cake-lpr-audit.md`.

## [2.2.0] — 2026-11-26

### Complete Closure of All 2026-11-26 Formal-Code Audit Errata (`K1` & `K2`), 6-Target Comparator Bridge & 5-Pool HOL4 `cake_lpr` CI Coverage

- **Formal Closure of `ERRATA.md` `K1` (Independent Basis-Bearing Non-Vacuity Witnesses in Lean 4.35.0):** Added pure zero-Mathlib `KS.isColoringBool` and soundness theorem `KS.isColoring_of_isColoringBool` to `lean/KS/Basic.lean`, and strengthened Comparator Targets 3 and 4 (`target_box3h2_nonvacuous_30`, `target_box4h1_nonvacuous_17`) in `lean/Challenge.lean` and `lean/Solution.lean` so each explicitly requires a complete $d$-ray orthogonal basis inside `T` and proves `VColorable` directly from an explicit 0/1 colouring (`0x3b70c7ffc69e` / `0x183000e` with 13 complete 3-bases; `0x2aac0aaaac` / `0x8000200c` with 7 complete 4-bases) without appealing to the main universal theorems.
- **Formal Closure of `ERRATA.md` `K2` (Kernel-Proved Refutations of Perturbed Headline Bounds):** Added Comparator Targets 5 and 6 (`target_box3h2_refute_30`, `target_box4h1_refute_17`) to `lean/Challenge.lean`, `lean/Solution.lean`, and `lean/comparator.json` (6 comparator targets total) alongside `refute_box3h2_all_31_colorable` and `refute_box4h1_all_18_colorable`, proving in the Lean kernel that neither headline bound can be lowered or negated. Updated `lean/KS/Audit.lean` (`35` explicit `#print axioms` declarations + exhaustive audit of all `122` kernel theorem constants in `KS`, `67` hand-written; zero warnings `--wfail`; `lake env leanchecker --fresh Solution`; 6-kernel `lake comparator --paranoid`).
- **Expanded HOL4-Verified `cake_lpr` CI Coverage to 5 of 9 Pools / 6 UNSAT Proofs (`scripts/verify_lrat.sh`):** Added `U(3,6)` (`k=32`), `U(3,6)` exact uniqueness (`k=33`, 3 sets excluded via `KS_BLOCKED`), and `U(3,12)` (`k=32`) alongside `B(3,2)`, `B(4,1)`, and `B(3,3)` — all cross-verified in Linux CI via `verify/drup_check`, pinned `drat-trim` → LRAT → `lrat-check`, and HOL4-formally-verified `cake_lpr` (`s VERIFIED UNSAT`), plus truncated-LRAT negative control.
- **Metadata & Provenance Hygiene:** Fixed lingering `arXiv:2603.16988v9` citation in `publication/zenodo-metadata.json` (`v10`, 23 November 2026); aligned AI disclosures across `README.md`, `publication/zenodo-metadata.json`, `publication/orcid-work.bib`, and `paper/ks-minimum.md`; refreshed `data/MANIFEST.sha256` and re-sealed DigiCert RFC 3161 TSA + Bitcoin OpenTimestamps; updated Software Heritage SWHID to verified `v2.1.0` snapshot `swh:1:snp:68ed4cd5af45b8fa4ed21a82f8f3dfd69ac901ae`; recompiled `ks-minimum.pdf` (`0.00 pt` overfull hbox) and recorded audit log in `docs/reviews/2026-11-26-v220-k1-k2-formal-closure-audit.md`.

## [2.1.0] — 2026-11-26

### Playbook v1.3 Closure: HOL4-Verified `cake_lpr` (Checklist #13), Palomar Lean 4.35 `module` Headers (Part D #3), Aligned AI Disclosure (`H48`), OSF Fallback (`H13`) & Zero `mypy` Errors

- **HOL4-Formally-Verified `cake_lpr` in CI (Playbook v1.3 Checklist #13 / Trigger T2):** Upgraded `scripts/verify_lrat.sh` to download pinned, SHA-256-verified `tanyongkiam/cake_lpr` (`033aad53d173`, `basis_ffi.c` + `cake_lpr.S`/`cake_lpr_arm8.S`), compile `cake_lpr` with GCC, and verify `s VERIFIED UNSAT` on `B(3,2)` (`k=30`), `B(4,1)` (`k=17`), and `B(3,3)` (`k=30`) alongside `verify/drup_check`, `drat-trim`, and `lrat-check`, plus verifying that BOTH `lrat-check` and `cake_lpr` reject a truncated LRAT negative control.
- **Palomar Registry `module` Headers Across 100% of Lean Files (Playbook v1.3 Part D #3 & Checklist #9):** Migrated all 9 zero-Mathlib `.lean` files (`KS/Basic.lean`, `KS/Spec.lean`, `KS/Box3H2.lean`, `KS/Box4H1.lean`, `KS/Tests.lean`, `KS.lean`, `KS/Audit.lean`, `Challenge.lean`, `Solution.lean`) and `scripts/gen_lean.py` to Lean 4.35 `module` + `public import` + `@[expose] public section`, passing zero-warning `lake build --wfail KS Solution`, `lake env leanexport Solution`, `lake env leanchecker --fresh Solution`, and `lake comparator --paranoid` (official Lean kernel default/paranoid plus `lean4lean`, `nanoda`, `con-leche`, `con-ron`), with a permanent regression check in `tests/test_repo_integrity.py`.
- **2026-11-26 Statement-Audit Reconciliation & Errata Closure (`P1`–`P6`, `O1`–`O4`, `K2`, `K3`):** Preserved all claim narrowings from `9c8c016` and resolved the remaining audit items in place — updated `paper/ks-minimum.md`, `publication/ks-minimum/ks-minimum.{tex,pdf}`, `docs/{ks-minimum.pdf,paper.html}`, `results/RESULTS.md`, `LEGAL.md`, and `lean/README.md` with dated citations to Kernaghan `arXiv:2603.16988v10` (23 Nov 2026), exact Waegell–Aravind (2011) parity-proof wording, Pavičić–Waegell `{0, ±1}` qualifier, and `30` explicit audit declarations; renamed `.github/workflows/ci.yml` closed-fact checks honestly to `Negative Lean sanity checks`; updated `KS/Audit.lean` to report both total kernel theorem constants (`116` under Lean 4.35 `module` mode) and hand-written count (`62`); kept `K1` documented transparently in `ERRATA.md` and `docs/statement-fidelity.md`.
- **Epistemic Alignment (`H48` & `H13`), Brute-Force CNF Test (`#14`), Zero `mypy` Errors & Broken GFM Table Fix:** Aligned `publication/zenodo-inquiry.md` AI disclosure with `CITATION.cff` and `formalization.yaml` (`H48`); switched DOI fallback from HAL to OSF Preprints (`H13`); fixed all 7 `mypy` errors across `src/{ksmin,exp_master,stats3d,ksmaster}.py` (`0` errors across all 47 Python files); added cross-platform small-pool brute-force + independent naive CNF encoder equivalence test in `tests/test_properties_and_fuzz.py` (`#14`); fixed unescaped vertical bars breaking GFM tables in `docs/statement-fidelity.md` (with permanent regression guard); unified Software Heritage SWHID on `v2.0.0` (`swh:1:snp:0f2c39bdae6bd37a98dc53f071bfa2208c1ef4e5`); recorded literal 3-cycle + 10-pass Playbook audit in `docs/reviews/2026-11-26-v210-3cycle-cake-lpr-module-audit.md`.

## [2.0.0] — 2026-11-26

### Trigger T2 (`drat-trim` → LRAT → `lrat-check`), DigiCert RFC 3161 + Bitcoin OTS Timestamps, Zero-Warning `--wfail` Lean & Submission Dossier

- **Independent Second Proof Checker — Trigger T2 (`scripts/verify_lrat.sh`, `.github/workflows/ci.yml`):** Added automated Linux CI verification downloading pinned, SHA-256-verified upstream `marijnheule/drat-trim` (`2e3b2dc`), cross-checking regenerated UNSAT proofs for `B(3,2)` (`k=30`), `B(4,1)` (`k=17`), and `B(3,3)` (`k=30`) through THREE independent checkers (`verify/drup_check`, `drat-trim`, and `lrat-check` on emitted LRAT proofs) plus a truncated-LRAT negative control.
- **Cryptographic Timestamping & Permanent Archival Identifiers (Playbook v1.3 #26 / Trigger T8):** Sealed `data/MANIFEST.sha256` with both a live **DigiCert RFC 3161 TSA** token (`data/MANIFEST.sha256.tsr`, OpenSSL X.509 verified in Linux CI) and a **3-calendar Bitcoin OpenTimestamps** proof (`data/MANIFEST.sha256.ots`) via `scripts/stamp_timestamps.py` (enforced across 3 OSes in CI and `tests/test_repo_integrity.py`); embedded permanent Software Heritage snapshot `swh:1:snp:6df0f79e042201d9490512cc8dda65471db9fafb` in `CITATION.cff`, `formalization.yaml`, `publication/README.md`, and `docs/threat-model.md`.
- **Zero-Warning Lean Enforcement, Clean-Clone Replication & Ready-to-Review Submission Packet:** Upgraded Lean builds to `lake build --wfail KS Solution` (`0` warnings) in `ci.yml` and `scripts/dev.sh`; fixed stale `v1.0.0` headers in `docs/INDEX.md` and `publication/README.md`; recorded automated clean-clone replication in `REPLICATION.md`; added `docs/submission-packet.md` (draft Palomar payload, specialist correspondence notes, and human line-by-line fidelity checklist); recompiled `ks-minimum.pdf` (`0.00 pt` overfull hbox) and updated `docs/ks-minimum.pdf`, `docs/paper.html`, and `arxiv-source.zip`.

## [1.9.0] — 2026-11-25

### Build Standard v1.2.0, Playbook v1.3, Zero-Overflow PDF (`0.00 pt`), `leanchecker --fresh` & Mega-Atlas Cross-Reference

- **Build Standard v1.2.0 Upgrade (`10` Finding Classes & Schema Validity):**
  - Fixed JSON Schema violation in `repo.yaml` (`stack: [lean, python, c-cpp]` → `[python, c-cpp, node, other]`, `standard: "1.2.0"`) and added permanent Draft 2020-12 schema + 10-class regression checks in `tests/test_repo_integrity.py`.
  - Upgraded verbatim Build Standard v1.2.0 scaffolding (`scripts/Audit-Repo.ps1`, `scripts/audit-repo.sh`, `scripts/audit-checks.tsv`, `repo-standard.schema.json`, `docs/build-standard.md`, `.github/labels.tsv` synced live on GitHub, `.github/ISSUE_TEMPLATE/bug.yml`), replaced the 3-line self-referential `docs/glossary.md` stub with a complete domain + 10-finding-class glossary, and updated `AGENTS.md`, `CONTRIBUTING.md`, and `justfile`.
  - Upgraded all 3 GitHub Actions workflows (`ci.yml`, `pages.yml`, `release.yml`) to `actions/checkout@v7`, `setup-python@v7`, `setup-node@v7`, `upload-artifact@v7`, `configure-pages@v6`, `upload-pages-artifact@v5`, `deploy-pages@v5`, `attest-build-provenance@v4` (with `continue-on-error: true`), weekly schedule, Build Standard audit artifact upload, **SHA-256-verified** `gitleaks v8.30.1` + `osv-scanner v2.7.1`, and `git archive` release bundles + automated CHANGELOG release notes.
- **Defensible Independent AI Research Playbook v1.3 Upgrade:**
  - Added [`ERRATA.md`](ERRATA.md) (version-vs-concept DOI policy, honest corrections ledger, formal withdrawal plan) and [`docs/mega-atlas-cross-reference.md`](docs/mega-atlas-cross-reference.md) (`0 / 1,900` Mega-Atlas grand problems completely solved; bounded `QM-011` coordinate-pool subcases certified).
  - Added independent **`lake env leanchecker --fresh Solution`** replay (Playbook v1.3 H04), **3 adversarial false-variant Lean rejection tests** (Checklist #12), and the hardened H46 `(private|protected|noncomputable|scoped|local)* axiom` lexer across `.github/workflows/ci.yml`, `scripts/dev.sh`, `scripts/run_all.py` (which now also scans `Solution.lean`), and `tests/test_repo_integrity.py`.
  - Added Crossref retraction-status checking (`retracted` flag via `update-to` / `is-retracted`) in `scripts/check_references.py` and fixed `scripts/check_docs.py` false positive on `docs/build-standard.md`.
- **Manuscript & `0.00 pt` Overfull Hbox Polish (`paper/ks-minimum.md`, `scripts/build_latex.py`, `publication/ks-minimum/ks-minimum.{tex,pdf}`):**
  - Added explicit **CRediT author contributions** and **Errata & versioning** (`ERRATA.md`) to Section 9; fixed `scripts/build_latex.py` so regenerating `ks-minimum.tex` preserves `\hypersetup`, clickable ORCID/email `\href` links, and Table 2 column widths; recompiled `ks-minimum.pdf` via Tectonic with **literal `0` overfull hboxes (`0.00 pt` max)** (eliminating the `3.73 pt` Table 2 overflow) and synced `docs/ks-minimum.pdf` & `docs/paper.html`; logged the literal 3-cycle audit in `docs/reviews/2026-11-25-v190-v12-v13-hardening-audit.md`.

## [1.8.0] — 2026-11-24

### 200-Pass Elite TOC Hardening (Resource-Hygiene `SIM115` Fixes, `RUF005`, Full 200-Pass Audit Record)

- **Context-Manager File-Handle Safety (`SIM115`) & `RUF005` Hygiene:** Replaced all unclosed raw `open(...)` file handles with explicit `with open(...)` context managers across `scripts/build_latex.py`, `scripts/build_paper.py`, and `scripts/ablate_c1c2.py`, and simplified list concatenation (`[kind, *args]`) in `scripts/ablate_c1c2.py`.
- **200-Pass Forensic Audit & Verification (`docs/reviews/2026-11-24-200-pass-elite-hardening-audit.md`):** Verified all 14 zero-Mathlib `.lean` modules (30 explicit + 149 exhaustive KS theorems, 4/4 6-kernel comparator parity), `node verify/test_verify.mjs` (`59/59`), all 3 C11 ASan/UBSan engines (`0` warnings), 40/40 citation bijection in `ks-minimum.tex`, MathJax CDN SRI in `docs/paper.html`, and recompiled `ks-minimum.pdf` cleanly with Tectonic (`0` overfull hboxes ≥ 5 pt).

## [1.7.0] — 2026-11-24

### Pass 7 TOC Deep-Dive Hardening (Zero `ruff E9,F,B,S`, Exhaustive `run_all` Lean Sentinel, Dev Sanitizers & Live Pages QA)

- **Zero `ruff E9,F,B,S` Security/Quality Findings:** Added explicit `https://`/`http://` URL scheme validation (`S310`) in `scripts/check_references.py` and removed all 33 unused imports/variables and extraneous f-strings (`F401`/`F541`/`F841`) across `src/`, `scripts/`, and `tests/`.
- **Exhaustive Lean Sentinel in `run_all.py` & Fresh `README.md` Counts:** Updated `scripts/run_all.py` `stage_lean` to require the `ALL_KS_THEOREMS_AXIOM_AUDIT_PASS:` exhaustive 149-theorem KS namespace sentinel alongside all 30 explicit `#print axioms` checks, and synced `README.md` (`26` → `30 explicit + exhaustive 149-theorem KS audit`).
- **Local Dev Parity & Interactive Paper Polish:** Upgraded `scripts/dev.sh` and `justfile` so `test` runs Node certificate verifier tests and `sanitizers` compiles & executes all 3 C11 ASan/UBSan engines (`drup_check_san`, `ks31_qgtl_san`, `ks31_qrng_san`); made ORCID and email clickable links in `docs/paper.html`; verified live GitHub Pages (`docs/index.html` & `docs/paper.html`) in browser QA.

## [1.6.0] — 2026-11-24

### Pass 6 TOC Deep-Dive Hardening (Zero Python Bugbear Findings, Clickable PDF ORCID/Email & CI Concurrency)

- **Zero Python Bugbear (`E9,F821,F822,F823,B`) Findings:** Fixed late-binding loop-variable closures (`B023`) in `scripts/build_paper.py` (`cell(tag, k, c, aligns=aligns)`) and `tests/test_verify_tools.py` (`move(r, perm=perm)`), plus all `B007` unused loop variables in `tests/{test_cnf,test_drup,test_run_all}.py`.
- **Clickable ORCID & Correspondence Hyperlinks in `ks-minimum.pdf`:** Added clickable `\href` links to ORCID (`0009-0006-8168-9648`) and email (`0_0@0thernes.art`) on page 1 of `publication/ks-minimum/ks-minimum.tex` and recompiled `ks-minimum.pdf` cleanly with Tectonic (synced to `docs/ks-minimum.pdf`, 0 overfull hboxes ≥ 5 pt).
- **CI Concurrency & Web CRLF Regression Guard:** Added `concurrency:` cancellation group to `.github/workflows/ci.yml` and expanded `tests/test_repo_integrity.py` CRLF guard to cover `.js`, `.mjs`, `.css`, and `.html` files alongside `.lean`/`.py`/`.c`/`.h`.

## [1.5.0] — 2026-11-24

### Pass 5 TOC Deep-Dive Hardening (Exhaustive Lean Axiom Metaprogram, C11 Stack Sanitizers & Metadata Sync)

- **Exhaustive `Lean.collectAxioms` Namespace Audit (`lean/KS/Audit.lean`):** Expanded `KS/Audit.lean` from 26 manual `#print axioms` lines to **30 explicit `#print axioms`** (adding all 4 `KS.ComparatorTarget.*` targets) PLUS an exhaustive `Lean.collectAxioms` metaprogram auditing **every single theorem in the `KS` namespace**, enforced in `.github/workflows/ci.yml` via the `ALL_KS_THEOREMS_AXIOM_AUDIT_PASS:` sentinel.
- **Expanded C11 ASan/UBSan Coverage:** Fixed error-path cleanup in `stack/ks31_qgtl.c` and expanded `.github/workflows/ci.yml` to compile and run both `stack/ks31_qgtl.c` and `stack/ks31_qrng.c` under `-Wall -Wextra -fsanitize=address,undefined` alongside `verify/drup_check.c`.
- **Bracket-Path Safety (`glob.escape`):** Fixed unescaped `glob.glob(os.path.join(ROOT, ...))` calls in `tests/_common.py` and `scripts/run_all.py` so checkouts inside directories containing literal brackets (`[...]`) run all 123 unit tests cleanly.
- **SHA-256 Manifests & Version Metadata Sync:** Added `data/MANIFEST.sha256` and `docs/data/manifest.json` SHA-256 verification plus `README.md`/`zenodo-metadata.json` version checks to `tests/test_repo_integrity.py`; scrubbed residual `0thernes LLC`/`other-closed`/`verification licence` fields from `publication/zenodo-metadata.json`; updated `README.md`, `AGENTS.md`, `llms-full.txt`, `LEGAL.md`, `LIMITATIONS.md`, `docs/paper.html`, `paper/ks-minimum.md`, `publication/orcid-work.bib`, and `publication/ks-minimum/ks-minimum.tex/.pdf` to `v1.5.0`.

## [1.4.0] — 2026-11-24

### Pass 4 TOC Deep-Dive Hardening (CI, Release PDF, Citations, Links, & Security)

- **GitHub Release PDF Asset & Workflow Hardening:** Added `publication/ks-minimum/ks-minimum.pdf` directly to `.github/workflows/release.yml` release assets + SHA256SUMS + SLSA provenance; added explicit `timeout-minutes:` to `pages.yml` and `release.yml`; added runtime execution of ASan/UBSan-instrumented `verify/drup_check_san`, `set -o pipefail`, live Lean axiom-allowlist parsing of `results/lean-audit-ci.log`, comment-aware nested Lean forbidden-token scanning, and cross-platform `node --test docs/assets/verify.test.mjs` to `ci.yml`.
- **Manuscript, BibTeX & Link Polish:** Fixed remaining `3.73 pt` table-header overfull hbox (`0` overfull hboxes ≥ 1 pt) and aligned exact literature titles `[15]`, `[20]`, `[40]` against live arXiv/Crossref metadata (`26/26` citations semantically verified); synced `publication/orcid-work.bib`, `lean/lakefile.toml`, `VERSION`, `CITATION.cff`, and `formalization.yaml` to `1.4.0`; fixed all 6 uppercase `GLOSSARY.md` references in `docs/INDEX.md` and `docs/SUMMARY.md`.
- **Tooling & Security Hygiene:** Fixed `.NET CurrentDirectory` bug in `scripts/Audit-Repo.ps1`, replaced deprecated `datetime.datetime.utcnow()` in `scripts/run_stack.py`, fixed `.gitleaks.toml` with `regexTarget = "line"`, and expanded `tests/test_repo_integrity.py` with case-exact Markdown link, `lakefile.toml` version, CRLF, and nested-comment Lean hygiene gates.

## [1.3.0] - 2026-11-24

### Fixed & Added
- Replaced residual pre-Apache `verification licence` sentence inside `publication/ks-minimum/ks-minimum.tex`, `paper/ks-minimum.md`, and `docs/paper.html`, added `\hypersetup` PDF Author/Title metadata, updated the manuscript version banner to `v1.3.0` (`CC-BY-4.0`), and recompiled `ks-minimum.pdf` cleanly via Tectonic (synced to `docs/ks-minimum.pdf`).
- Added automated `tests/test_repo_integrity.py` enforcing version consistency, Apache-2.0/CC-BY-4.0 hygiene, zero broken `docs/` HTML links, and zero forbidden Lean tokens across all proof modules.
- Verified all 24 arXiv IDs and 2 DOIs in `ks-minimum.tex` live online (0 failures).

## [1.2.0] - 2026-11-24

### Fixed
- Fixed Linux case-sensitivity failure on `A44` (`docs/GLOSSARY.md` -> `docs/glossary.md`).
- Removed remaining legacy `0thernes LLC` and pre-Apache `verification licence` prose across `README.md`, `CONTRIBUTING.md`, `docs/`, `paper/`, and `publication/`, and recompiled `ks-minimum.pdf` via Tectonic.
- Added surgical `.gitleaks.toml` allowlist for the SHA-256 hex digest of `scripts/scan_large_tokens.py` inside `results/run_all.json` (0 false-positive secret warnings).
- Honestly documented `A24` in `repo.yaml` as `partial` due to the two intentionally preserved historical 8-12 MB JSON cut certificates in `results/`.

## [1.1.0] - 2026-11-24

### Added
- Isolated `lean/Challenge.lean`, sorry-free `lean/Solution.lean`, `lean/comparator.json`, and explicit non-vacuity targets (`30`-ray subset of `B(3,2)`, `17`-ray subset of `B(4,1)`), verified across six Lean 4.35.0 kernels via `lake comparator --paranoid`.
- Build Standard for LLMs v1.1.0 & Defensible Playbook v1.1 infrastructure (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/build-standard.mdc`, `llms.txt`, `CLAIMS.md`, `LIMITATIONS.md`, `REPLICATION.md`, `ROADMAP.md`, `SUPPORT.md`, `repo.yaml`, `formalization.yaml`, `justfile`, `scripts/Audit-Repo.ps1`, `docs/statement-fidelity.md`, `docs/adr/0001-zero-mathlib-trust-base.md`, `.github/workflows/release.yml` with `SHA256SUMS` + SLSA attestations, C11 ASan/UBSan & cross-platform CI).

### Changed
- Re-licensed code under **Apache-2.0** (`LICENSE`) and manuscripts/docs under **CC-BY-4.0** (`LICENSE-DOCS`).
- Standardized author attribution to `Alexander S. Donahue (independent researcher, ORCID 0009-0006-8168-9648)` with CRediT disclosure, removing unformed LLC references.
- Cross-linked sibling consolidated multiqubit Pauli repository `0thernes/pauli-contextuality-lab` while preserving this repository's minimal zero-Mathlib trust base.

## After 1.0.0 (not released)

* The release and its archiving are recorded: `docs/REPORT.md`, section 8, and
  `results/release_archiving.json` (CI run, release assets, GitHub Pages, Software Heritage snapshot,
  Internet Archive captures, each compared byte for byte with the files at the tag v1.0.0);
  `publication/README.md` says which venues are done. No result, proof or paper text changed.

## 1.0.0 (10 November 2026)

First public release.

### Results (see `results/RESULTS.md`, the register, for the status of each)

* Exact minimum size of a Kochen-Specker set inside nine pools of rays: 31 for integer coordinates up
  to 2, 3 and 4 in dimension three; 33 for coordinates 0 or N-th roots of unity, N = 6, 12, 18, 24, in
  dimension three; 18 for coordinates 0, +1, -1 in dimension four; 29 for coordinates 0, +1, -1 in
  dimension five.
* All Kochen-Specker sets of minimum size in six of these pools: 6, 6, 6, 3, 12 and 16 sets, one orbit
  under the symmetries of the pool in each case.
* Several of these values had been reported before without proof (31 for integer bounds 2, 3 and 4;
  33 for sixth roots of unity; 29 as the smallest set generated from 0, +1, -1 in dimension five), and
  the 16 minimum sets of dimension four are the known sets inside the 24 rays of Peres (Waegell and
  Aravind 2011). What is new is mainly the proofs; see the paper, Section 1.3.
* No Kochen-Specker set smaller than a published one was found. The general minimal-set problem is
  not settled by pool results.

### Evidence

* Lean 4 (no Mathlib): soundness of two certificate checkers, and kernel-checked theorems for the
  49-ray pool of dimension three and the 40-ray pool of dimension four, stated both for the tables of
  bit masks and for the integer vectors themselves (`boxRays d H`, `VColorable`).
* Search-tree certificates replayed by an independent JavaScript verifier, three of them covering
  whole pools.
* Unsatisfiability proofs (DRUP) of the candidate problems, checked by `verify/drup_check.c`, for the
  minimum values and for the counts of minimum sets. The formulas of the 24th-root pool and of
  dimension five were also solved by a second SAT solver (CaDiCaL); for the 24th-root pool, where
  Glucose ran out of memory, and for the four-axis case of dimension five the CaDiCaL proofs were
  checked as well.
* The lemmas the programs rely on, with proofs: `paper/PROOFS.md`.

### Contents

* `paper/` the paper and the proofs of the lemmas; `publication/` the files prepared for the author's
  submissions (nothing has been submitted by the build process).
* `src/`, `scripts/`, `verify/`, `tests/` the programs, the checkers and their tests; one command,
  `python scripts/run_all.py`, repeats the small checks.
* `lean/` the Lean development; `results/`, `logs/` certificates, cut files with their witnesses,
  explicit sets, enumerations and the logs of the runs.
* `docs/` the site with an in-browser verifier, the built paper, and the documents: summary, index of
  claims and evidence, glossary, verification report, review before release, trigger register.
* `stack/`, `third_party/` a demonstration of the 31-ray set on Moonlab, QGTL, quantum_rng and Eshkol
  (classical computation; not part of any proof).

### Review before release

* Nine reviewing passes (the Lean development, the lemmas, symmetry breaking and uniqueness, the
  encoder, the proof pipeline, the numbers, prior work and references, independent reconstructions of
  the pools, independent re-runs). No theorem and no headline number changed. What changed: two
  missed prior reports are now credited and the novelty claims were narrowed; the Lean theorems are
  stated for integer vectors; a wrong remark about dimension five (five-axis sets "may not exist")
  was withdrawn; the proof checker reads its input strictly; the certification scripts report failure
  correctly; several durations and counts were corrected. Details: `docs/REVIEW.md`.

### Known limits

* Not peer reviewed. Produced by an AI system under human direction (see `LEGAL.md`).
* The proof checker and the JavaScript verifier are tested, not formally verified.
* Runs that did not finish, and work that is deliberately deferred, are listed in section G of the
  register and in `docs/TRIGGER-REGISTER.md`.
