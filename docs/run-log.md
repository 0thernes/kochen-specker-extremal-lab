# Run Log

| Date | Command | Outcome |
|---|---|---|
| 2026-11-24 | `v1.1.0` Gold Standard upgrade (`Apache-2.0` + `CC-BY-4.0`, `Challenge.lean` / `Solution.lean` 6-kernel comparator, Build Standard v1.1.0) | Verified locally & pushed to `main` |
| 2026-11-24 | `v1.4.0` Pass 4 hardening (`drup_check_san` 256B LeakSanitizer fix, split-job Pages, Release PDF asset + SLSA, live `lean-audit-ci.log` verification, 26/26 semantic citation checks) | Verified locally & 100% green CI |
| 2026-11-24 | `v1.5.0` Pass 5 hardening (exhaustive `Lean.collectAxioms` metaprogram in `KS/Audit.lean`, `ks31_qgtl`/`ks31_qrng` ASan/UBSan CI, `data/MANIFEST.sha256` & `docs/data/manifest.json` tests, `zenodo-metadata.json` scrub) | Local & CI verification |
| 2026-11-24 | `v1.6.0` Pass 6 hardening (zero Python `B023`/`B007` bugbears, clickable ORCID/email in `ks-minimum.pdf`, CI `concurrency:` guard, web-file CRLF guard) | Local & CI verification |
| 2026-11-24 | `v1.7.0` Pass 7 hardening (zero `ruff E9,F,B,S`, `S310` scheme check, `ALL_KS_THEOREMS_AXIOM_AUDIT_PASS` in `run_all.py`, 3-engine `dev.sh sanitizers`, clickable `paper.html` ORCID/email, live Pages browser QA) | Local & CI verification |
| 2026-11-24 | `v1.8.0` 200-pass elite TOC hardening (`SIM115` context-manager fixes in `scripts/{build_latex,build_paper,ablate_c1c2}.py`, `RUF005`, `59/59` Node verifier, 3-engine C11 ASan/UBSan, 6-kernel Lean, 200-pass audit record, live Pages QA) | Local & CI verification |
| 2026-11-25 | `v1.9.0` Build Standard v1.2.0 & Playbook v1.3 upgrade (`repo.yaml` schema fix, 10 finding classes, full `docs/glossary.md`, `ERRATA.md`, `docs/mega-atlas-cross-reference.md`, `leanchecker --fresh Solution`, 3 adversarial Lean rejection tests, H46 lexer, SHA-256-verified `gitleaks`+`osv-scanner`, `0.00 pt` `ks-minimum.pdf`, `scripts/build_latex.py` parity) | Local & CI verification |
| 2026-11-26 | `v2.0.0` Trigger T2 (`drat-trim` → LRAT → `lrat-check` CI verification for `B(3,2)`, `B(4,1)`, `B(3,3)`), DigiCert RFC 3161 TSA + 3-calendar OpenTimestamps (`data/MANIFEST.sha256.{tsr,ots}`), `lake build --wfail KS Solution`, permanent SWHID embedding, automated clean-clone replication, and `docs/submission-packet.md` | Local & CI verification |
