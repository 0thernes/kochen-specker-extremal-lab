# Errata, Versioning Policy, and Withdrawal Plan (`ERRATA.md`)

This ledger records substantive mathematical, formalization, bibliographic, and metadata corrections across all releases of `kochen-specker-extremal-lab` (Defensible Independent AI Research Playbook v1.3, Checklist #39 & H28).

## 1. Versioning and DOI Policy

- **Single version source:** The canonical version lives in `VERSION` (SemVer `MAJOR.MINOR.PATCH`) and is synchronized across `CHANGELOG.md`, `CITATION.cff`, `formalization.yaml`, `lean/lakefile.toml`, `README.md`, `publication/zenodo-metadata.json`, `publication/orcid-work.bib`, and `paper/ks-minimum.md` / `publication/ks-minimum/ks-minimum.tex` via `tests/test_repo_integrity.py`.
- **Preprint revision convention:** Each tagged GitHub release (`vX.Y.Z`) freezes `ks-minimum.pdf`, `ks-minimum.md`, `PROOFS.md`, `RESULTS.md`, `ERRATA.md`, `SHA256SUMS`, and `git archive` source bundles. If deposited to Zenodo (pending eligibility confirmation via `publication/zenodo-inquiry.md`) or OSF Preprints (DOI fallback per Playbook v1.3 H13; HAL requires a formal affiliation), **cite the version-specific DOI** when referencing exact proof files, line numbers, or artifact hashes, and the **concept/all-versions DOI** only when citing the ongoing repository generically.
- **No fabricated identifiers:** No external DOI or arXiv identifier is asserted prior to an actual deposit.

## 2. Recorded Corrections Log

| Release | Date | Affected Artifact(s) | Class | Summary of Correction |
|---|---|---|---|---|
| **v2.1.0** | 2026-11-26 | `scripts/{verify_lrat.sh,gen_lean.py}`, `lean/**/*.lean`, `.github/workflows/ci.yml`, `paper/ks-minimum.md`, `publication/ks-minimum/*`, `src/{ksmin,exp_master,stats3d,ksmaster,ks_cnf}.py`, `tests/{test_properties_and_fuzz,test_repo_integrity}.py`, `results/RESULTS.md`, `LEGAL.md`, `lean/README.md`, `publication/zenodo-inquiry.md`, `docs/*`, `CITATION.cff`, `formalization.yaml`, `README.md`, `CLAIMS.md`, `LIMITATIONS.md`, `ROADMAP.md` | `gap` / `conflict` / `bug` / `error` | Reconciled and closed the 2026-11-26 independent statement-audit items P1–P6 (manuscript updated & recompiled to `0.00 pt` PDF), O1–O4, K2 (renamed CI checks to negative sanity checks), and K3 (`KS/Audit.lean` reports both total kernel constants `116` in `module` mode and `62` hand-written theorems; K1 remains documented transparently); added HOL4-formally-verified `cake_lpr` (`tanyongkiam/cake_lpr` `033aad5`, SHA-256 verified) to `scripts/verify_lrat.sh` for `B(3,2)`, `B(4,1)`, and `B(3,3)`; migrated all 9 zero-Mathlib `.lean` files + `scripts/gen_lean.py` to Lean 4.35 `module` headers (refreshed `data/MANIFEST.sha256` and re-sealed DigiCert RFC 3161 TSA + OpenTimestamps); aligned `publication/zenodo-inquiry.md` AI disclosure (`H48`) and adopted OSF Preprints DOI fallback (`H13`); fixed all 7 `mypy` errors (`0/47`); added Checklist #14 brute-force CNF equivalence test; fixed GFM table bare pipes in `docs/statement-fidelity.md` + regression guard; unified Software Heritage SWHID on `v2.0.0` `swh:1:snp:0f2c39bdae6bd37a98dc53f071bfa2208c1ef4e5`. |
| **v2.0.0** | 2026-11-26 | `scripts/{verify_lrat.sh,stamp_timestamps.py,dev.sh}`, `data/MANIFEST.sha256.{tsr,ots}`, `.github/workflows/ci.yml`, `docs/{TRIGGER-REGISTER,INDEX,threat-model,submission-packet}.md`, `publication/README.md`, `CITATION.cff`, `formalization.yaml` | `gap` / `hole` / `issue` | Fired Trigger T2 in CI via pinned, SHA-256-verified upstream `marijnheule/drat-trim` (`2e3b2dc`) emitting LRAT + `lrat-check` cross-verification of `B(3,2)`, `B(4,1)`, and `B(3,3)` UNSAT proofs (plus truncated-LRAT negative control); enforced zero-warning `lake build --wfail KS Solution`; sealed `data/MANIFEST.sha256` with DigiCert RFC 3161 TSA (`data/MANIFEST.sha256.tsr`, OpenSSL X.509 verified) + 3-calendar Bitcoin OpenTimestamps (`data/MANIFEST.sha256.ots`); embedded verified Software Heritage SWHID (`swh:1:snp:6df0f79e042201d9490512cc8dda65471db9fafb`); fixed stale `v1.0.0` version references in `docs/INDEX.md` and `publication/README.md`; recorded automated clean-clone replication in `REPLICATION.md`; added ready-to-review `docs/submission-packet.md`. |
| **v1.9.0** | 2026-11-25 | `repo.yaml`, `docs/glossary.md`, `.github/workflows/*`, `scripts/{build_latex,run_all,check_docs,check_references,dev.sh}`, `paper/ks-minimum.md`, `publication/ks-minimum/ks-minimum.tex`, `tests/test_repo_integrity.py` | `error` / `gap` / `hole` | Fixed JSON Schema violation in `repo.yaml` (`stack: [lean, python, c-cpp]` → `[python, c-cpp, node, other]`, `standard: "1.2.0"`); replaced self-referential 3-line `docs/glossary.md` stub with full domain + 10-finding-class glossary; upgraded to Build Standard v1.2.0 (10 finding classes synced live on GitHub, Actions v7/v6/v5/v4, SHA-256-verified `gitleaks v8.30.1` + `osv-scanner v2.7.1`, `continue-on-error: true` on release attestations) and Playbook v1.3 (`ERRATA.md`, `docs/mega-atlas-cross-reference.md`, `leanchecker --fresh Solution`, three negative Lean sanity checks [originally labelled adversarial tests; see K2/O4], H46 hardened `axiom` lexer, Crossref retraction checks, explicit CRediT & Errata text in manuscript Section 9); fixed `scripts/build_latex.py` so regenerating `ks-minimum.tex` preserves `\hypersetup`, clickable ORCID/email, and `0.00 pt` overfull hboxes (eliminating the `3.73 pt` Table 2 overfull); fixed `scripts/run_all.py` to scan `Solution.lean` with comment-aware H46 lexer; fixed `scripts/check_docs.py` false positive on `docs/build-standard.md`. Clarified historical `v1.8.0` review-log nomenclature under Playbook v1.3 H48 so current audits report strictly literal check cycles. |
| **v1.4.0** | 2026-11-24 | `verify/drup_check.c`, `publication/ks-minimum/ks-minimum.tex`, `docs/{INDEX,SUMMARY}.md` | `bug` / `issue` | Fixed 256-byte LeakSanitizer leak in `verify/drup_check.c`, aligned literature titles `[15]`, `[20]`, `[40]` against live arXiv/Crossref metadata, and fixed 6 case-sensitive `GLOSSARY.md` links. |
| **v1.2.0** | 2026-11-24 | `README.md`, `CONTRIBUTING.md`, `publication/ks-minimum/ks-minimum.tex`, `docs/glossary.md` | `error` / `concern` | Fixed Linux case-sensitivity on `docs/glossary.md` and scrubbed remaining legacy `0thernes LLC` and pre-Apache `verification licence` text after the `v1.1.0` Apache-2.0 / CC-BY-4.0 re-licensing. |
| **v1.0.0 (pre-release review)** | 2026-11-10 | `paper/ks-minimum.md`, `results/RESULTS.md`, `lean/KS/Basic.lean`, `docs/REVIEW.md` | `error` / `bug` | Withdrew an incorrect draft remark claiming five-axis critical KS sets in $B(5,1)$ might not exist (the initial sampler was biased; `results/d5_axes_sanity.json` exhibits 3,734 five-axis critical sets); credited two previously missed prior reports (Pavičić & Megill 2022 in 5D, Waegell & Aravind 2011 for the 16 Peres 4D sets) and narrowed novelty claims; corrected early Lean certificate checker bugs caught during soundness proofs and recorded counterexamples in `lean/KS/Tests.lean`. |

## 3. Correction & Withdrawal Plan

If a mathematical error, statement-fidelity mismatch between the paper and `lean/KS/Spec.lean`, soundness flaw in `verify/drup_check.c` or `verify/verify_cert.mjs`, or undisclosed prior art is discovered:

1. **Report intake:** Open a GitHub issue (tagged `error`, `bug`, or `hole`) or email `0_0@0thernes.art` with the exact commit/version, pool/theorem, and counterexample (a list of rays suffices).
2. **Triage & reproduction (target: within 72 hours):** Reproduce the discrepancy, classify it under the 10-class Build Standard v1.2.0 taxonomy, and record an explicit entry in this `ERRATA.md`, `CLAIMS.md`, and `results/RESULTS.md`.
3. **Correction release (non-fatal errors):** Publish a new SemVer release (`vX.Y.(Z+1)`) updating the register, proofs, code, and manuscript without force-pushing or rewriting tagged history.
4. **Formal withdrawal (fatal theorem failure):** If a headline pool minimum fails due to an unrepairable error:
   - Immediately add a prominent `[WITHDRAWN]` banner to `README.md`, `CLAIMS.md`, `results/RESULTS.md`, the manuscript PDF/HTML/TeX, and this `ERRATA.md` documenting the exact failure and crediting the discoverer.
   - Publish a superseding withdrawal version on GitHub Releases and any external preprint server where deposited, never silently deleting prior versions.

## 2026-11-26 statement audit

An independent statement audit of `v2.0.0` (commit `4c4dda9`) was made on 26 November 2026. Audit log:
https://github.com/0thernes/0thernes-research-archive/blob/main/docs/reviews/2026-11-26-statement-audit.md .
The audit confirmed that the two Lean theorems hold as stated (`KS.Box3H2.minimum_ks_size_vectors`,
31 in the 49-ray pool `B(3,2)`; `KS.Box4H1.minimum_ks_size_vectors`, 18 in the 40-ray pool `B(4,1)`;
axioms `propext`, `Classical.choice`, `Quot.sound` only). No theorem statement is affected by any item
below. The other seven pool values rest on SAT certificates outside Lean, and the unrestricted problems
stay open.

Corrected in this pass in `README.md`, `CLAIMS.md`, `LIMITATIONS.md`, `CITATION.cff` (abstract),
`formalization.yaml` (limitations text) and `docs/*.md`: the Lean credit is attached to 31 (`B(3,2)`)
and 18 (`B(4,1)`) only; the checker of the other seven values is named as the project's own, with the
third-party `drat-trim`/LRAT cross-check limited to `B(3,2)`, `B(4,1)` and `B(3,3)`; "6 independent
kernels" now reads as the official Lean kernel (default and paranoid mode) plus lean4lean, nanoda,
con-leche and con-ron; the axiom audit is described as 149 theorem constants, 62 of them written by
hand; the roots-of-unity value is restricted to `N = 6, 12, 18, 24`; and the parallel work of Kernaghan,
arXiv:2603.16988v10 (23 November 2026), is cited with dates.

### Errors in the `v2.0.0` paper (`paper/ks-minimum.md`, and the same text in `publication/ks-minimum/ks-minimum.tex`, `publication/ks-minimum/ks-minimum.pdf`, `docs/ks-minimum.pdf`, `docs/paper.html`) — **Resolved in `v2.1.0`**

| # | Where | What is wrong | Correction | Affects a theorem statement? |
|---|---|---|---|---|
| P1 | Section 1.3, Kernaghan item (`paper/ks-minimum.md` lines 104-111; `.tex` line 171) and reference [22] (`.md` line 543; `.tex` line 679), which cites v9 | Describes versions 1-9 only. Version 10 (23 November 2026) states that the procedure of versions 1-9 was unsound, certifies 31 for the 49-ray and the 145-ray pools and 33 (exactly three sets) for the 57-ray sixth-roots pool, and proves 31 (49-ray pool) and 33 (sixth roots) in Lean 4 with Mathlib. | Cite arXiv:2603.16988v10. Replace "by a SAT procedure for which no certificate is given" by: "Versions 1-9 reported 31 and 33 by a procedure the author later withdrew as unsound; version 10 (23 November 2026) certifies them again and proves the minima for the 49-ray and sixth-roots pools in Lean. For N = 12, 18, 24 it gives only the upper bound 33." | No |
| P2 | Section 1.3, last item (`.md` lines 125-126; `.tex` line 194) | "We found no formal proof of a minimality statement for KS sets" is printed in a release of 26 November 2026, three days after Kernaghan v10. | "Up to 10 November 2026 we found none. Since then Kernaghan (arXiv:2603.16988v10, 23 November 2026) has published independent Lean 4 proofs of the minima 31 (49-ray integer pool) and 33 (sixth roots of unity); our Lean proof for the 49-ray pool was released on 10 November 2026." | No |
| P3 | Section 4.3 (`.md` lines 333-335; `.tex` line 436) | "to our knowledge the first proof of a minimality statement for KS sets checked by a proof assistant" is a priority claim; concurrent independent work now exists. | "We know of no proof-assistant-checked minimality statement for a pool of KS rays released before our v1.0.0 (10 November 2026)." | No |
| P4 | Section 1.3, novelty item 2 (`.md` line 135; `.tex` line 210); Section 4.1 (`.md` lines 305-307) | Lists the count 3 for sixth roots of unity, and the proofs for H = 3, as new; Kernaghan v10 also gives the count 3 and certifies 31 for the 145-ray pool (after our v1.0.0). | Add "(the count 3 for sixth roots, and a certificate for H = 3, were given independently in arXiv:2603.16988v10, 23 November 2026)". | No |
| P5 | Section 1.2 (`.md` lines 82-83; `.tex` line 144) | The paraphrase of Pavičić and Waegell [32] drops the restriction of their sentence to sets with vector components {0, ±1}. | "write only that it seems likely that the smallest sets with vector components {0, ±1} have been found in dimensions four to eight". | No |
| P6 | Section 1.3 (`.md` lines 115-116; `.tex` line 183), Section 4.3 (`.md` lines 330-331) and the abstract (`.md` lines 35-36) | [39] (Waegell and Aravind 2011) counts 16 parity proofs of type 18-9 in Peres's 24 rays, not all 18-ray KS subsets. | "Peres's 24 rays contain 16 parity proofs with 18 rays and 9 bases [39]; our enumeration shows there is no other 18-ray KS set in the pool." | No |

### Other files outside the scope of the `9c8c016` pass — **Resolved in `v2.1.0`**

| # | Where | What is wrong | Correction |
|---|---|---|---|
| O1 | `lean/README.md` line 120; `results/RESULTS.md` line 62 | "prints the axioms of 26 theorems"; `lean/KS/Audit.lean` has 30 `#print axioms` lines. | Change 26 to 30. |
| O2 | `results/RESULTS.md` lines 236-241; `LEGAL.md` lines 65-69 | Kernaghan is described from v9 only ("no certificate"). | As P1. |
| O3 | `CITATION.cff` identifiers (lines 11-13), `formalization.yaml`, `docs/threat-model.md`, `docs/submission-packet.md` | The Software Heritage snapshot `swh:1:snp:6df0f79e042201d9490512cc8dda65471db9fafb` is labelled v1.9.0; the archive hub lists `swh:1:snp:0f2c39bdae6bd37a98dc53f071bfa2208c1ef4e5`. Which commit each snapshot holds was not verified. | Use one snapshot that contains the released commit, with a correct label. |
| O4 | Section 2 of this file, row v1.9.0; `docs/run-log.md` (v1.9.0 entry) | These historical entries call the three CI checks "adversarial false-variant Lean tests". | Read as "three negative sanity checks" (see K2). |

### Known issues in the formal code (`K2` and `K3` resolved in `v2.1.0`; `K1` documented transparently)

| # | Where | What is wrong | Correction | Affects a theorem statement? |
|---|---|---|---|---|
| K1 | `lean/Solution.lean` lines 19-27 (`target_box3h2_nonvacuous_30`, `target_box4h1_nonvacuous_17`) and the matching targets of `lean/Challenge.lean` | Both targets are one-line corollaries of the universal halves of the main theorems, not independent witnesses. The first 17 rays of `B(4,1)` contain no basis, so the 17-ray target never exercises the basis condition (the first 30 rays of `B(3,2)` contain 13 bases). | Use a 17-ray subset of an 18-ray KS set with an explicit colouring, or describe the targets as corollaries. | No: each main theorem carries both halves. |
| K2 | `.github/workflows/ci.yml` lines 192-229 ("Adversarial false-variant definition tests") | The three tests are `(KS.boxRays 3 2).length = 48`, `(KS.boxRays 4 1).length = 39` and `KS.card 49 (2 ^ 30 - 1) = 31`, each passing when `decide` fails. A failed `decide` is not a kernel-checked refutation, and none is a variant of a theorem. | Rename to "negative sanity checks", or add proved negations of real false variants (for example, that the bound 31 cannot be lowered to 30 in the existence half) to `lean/KS/Tests.lean`. | No |
| K3 | `lean/KS/Audit.lean` (sentinel `ALL_KS_THEOREMS_AXIOM_AUDIT_PASS`) | The count of 149 covers all theorem constants in `KS`, including automatically generated ones; 62 theorems are written by hand. | Print both numbers. | No |
