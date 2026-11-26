# Changelog

## [Unreleased]

- Re-verify non-Lean SAT/DRUP proofs via `drat-trim` -> LRAT -> formally verified `cake_lpr`.

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
