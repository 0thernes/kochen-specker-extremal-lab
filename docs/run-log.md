# Run Log

| Date | Command | Outcome |
|---|---|---|
| 2026-11-24 | `v1.1.0` Gold Standard upgrade (`Apache-2.0` + `CC-BY-4.0`, `Challenge.lean` / `Solution.lean` 6-kernel comparator, Build Standard v1.1.0) | Verified locally & pushed to `main` |
| 2026-11-24 | `v1.4.0` Pass 4 hardening (`drup_check_san` 256B LeakSanitizer fix, split-job Pages, Release PDF asset + SLSA, live `lean-audit-ci.log` verification, 26/26 semantic citation checks) | Verified locally & 100% green CI |
| 2026-11-24 | `v1.5.0` Pass 5 hardening (exhaustive `Lean.collectAxioms` metaprogram in `KS/Audit.lean`, `ks31_qgtl`/`ks31_qrng` ASan/UBSan CI, `data/MANIFEST.sha256` & `docs/data/manifest.json` tests, `zenodo-metadata.json` scrub) | Local & CI verification |
| 2026-11-24 | `v1.6.0` Pass 6 hardening (zero Python `B023`/`B007` bugbears, clickable ORCID/email in `ks-minimum.pdf`, CI `concurrency:` guard, web-file CRLF guard) | Local & CI verification |
