# 3-Cycle Deep Hardening Audit — `v2.3.0` (2026-11-27)

- **Repository:** `0thernes/kochen-specker-extremal-lab` (`v2.2.0` `a433e72` → `v2.3.0`)
- **Frameworks Audited Against:** Build Standard for LLMs `v1.2.0` & Defensible Independent AI Research Playbook `v1.3`
- **Audit Scope:** All 9 Lean 4.35.0 modules, SAT/DRUP/LRAT/`cake_lpr` verification scripts, C11 checkers, Python/Node test suites, CI/Pages/Release workflows, cryptographic timestamps, Software Heritage provenance, and `ks-minimum.{md,tex,pdf,html}`.

## Cycle 1 — Forensic Inventory & Gap Identification
1. **`gap` (Lean checker completeness):** `KS/Basic.lean` proved soundness `isColoring_of_isColoringBool` but lacked the converse completeness theorem `isColoringBool_of_isColoring` and bidirectional `isColoringBool_iff`.
2. **`gap` (HOL4 `cake_lpr` dimension-5 & uniqueness coverage):** `scripts/verify_lrat.sh` covered 5 pools / 6 UNSAT proofs (`d=3,4` only), leaving `B(3,2)`/`B(4,1)`/`B(3,3)`/`U(3,12)` uniqueness and the 5D `B(5,1)` pool outside HOL4-verified `cake_lpr` CI.
3. **`gap` (Live tamper-injection negative gate):** `.github/workflows/ci.yml` tested 3 closed decidable facts via `decide`, without actively injecting a custom `axiom` into a temporary Lean file to test live end-to-end rejection by `#print axioms` and the H46 lexer.
4. **`gap` (Build Standard B13 isolated AST source-code mutation testing):** `tests/test_properties_and_fuzz.py` tested property invariants, fuzzing, and brute-force CNF equivalence, but lacked isolated AST source-code operator mutation tests against `src/pools.py` and `src/ks_cnf.py`.
5. **`issue` (Provenance & style hygiene):** `CITATION.cff`, `formalization.yaml`, `docs/threat-model.md`, `docs/submission-packet.md`, and `publication/README.md` still referenced the `v2.1.0` SWHID (`68ed4cd5...`) instead of the verified `v2.2.0` SWHID (`4c421f5d...`); `ks-minimum.tex` AI disclosure still read `v1.1.0--v2.1.0`; `src/{ks_cnf,ksmin}.py` and `tests/test_pools.py` had `ruff E731` lambda assignments.

## Cycle 2 — Hardening Execution
- Proved `KS.subMask_of_sub`, `KS.isColoringBool_of_isColoring`, and `KS.isColoringBool_iff` in `lean/KS/Basic.lean`; promoted `target_isColoringBool_iff` as Comparator Target 7 in `lean/{Challenge,Solution}.lean` and `lean/comparator.json`; updated `lean/KS/Audit.lean` (`38` explicit `#print axioms`, `126` kernel theorem constants / `71` hand-written).
- Expanded `scripts/verify_lrat.sh` to **11 UNSAT/uniqueness proofs across 6 pools spanning $d \in \{3,4,5\}$** under `verify/drup_check`, pinned `drat-trim` → LRAT → `lrat-check`, and HOL4-verified `cake_lpr` (plus truncated-LRAT negative control).
- Added the live tamper-injection negative gate to `.github/workflows/ci.yml` (`lean` job).
- Added 6/6 isolated AST source-code mutation tests (`test_ast_source_code_mutation_killing`) to `tests/test_properties_and_fuzz.py` and replaced `E731` lambdas with `def` functions.
- Synced verified `v2.2.0` SWHID `swh:1:snp:4c421f5d8b6cf9d06c224ed7bfafe88bc3392f4f`, bumped `2.2.0` → `2.3.0`, recompiled `ks-minimum.pdf` (`0.00 pt` overfull) + `arxiv-source.zip` + `docs/ks-minimum.pdf`, and re-sealed `data/MANIFEST.sha256` with fresh DigiCert RFC 3161 TSA + 3-calendar Bitcoin OpenTimestamps.

## Cycle 3 — Verification & Honest Residual Boundaries
- Verified zero-warning `lake build --wfail KS Solution`, `lake env lean KS/Audit.lean` (`126` kernel constants / `71` hand-written, 0 disallowed axioms), `lake env leanchecker --fresh Solution`, full Python unittest + AST mutation suite, Node verifier (`59/59`), `check_docs.py`, `stamp_timestamps.py --verify`, and Build Standard v1.2.0 `Audit-Repo.ps1`.
- **Honest residual boundaries preserved:** Pool-restricted exact minima only (`0 / 2,000` Mega-Atlas grand open problems settled); Lean proves `B(3,2) = 31` and `B(4,1) = 18` only; `B(3,4)`, `U(3,18)`, `U(3,24)`, and the remaining 82 branches of `B(5,1)` still rely on `verify/drup_check.c` (plus CaDiCaL second-solver where recorded); `human_line_by_line_review_recorded` remains `false`.
