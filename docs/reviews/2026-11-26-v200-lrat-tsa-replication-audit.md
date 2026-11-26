# Audit Record: `v2.0.0` Independent LRAT Checker, `--wfail`, RFC 3161 TSA/OTS, SWHID, and Clean-Clone Replication (`2026-11-26`)

- **Repository:** `0thernes/kochen-specker-extremal-lab`
- **Target release:** `v2.0.0`
- **Date:** 2026-11-26
- **Auditor:** Automated verification pass under human direction (`Alexander S. Donahue`, ORCID `0009-0006-8168-9648`)
- **Human line-by-line Lean review status:** `false` (unchanged — see `formalization.yaml` and `docs/submission-packet.md`)

## Scope Verified

1. **Zero-Warning Lean 4.35.0 Build (`--wfail`):**
   - `lake build --wfail KS Solution` enforced in `.github/workflows/ci.yml` and `scripts/dev.sh` and confirmed passing cleanly on a zero-cache clean clone (10 jobs, 0 warnings, `76.8s` including `KS/Audit.lean` checking 149/149 theorems).
2. **Trigger T2 — Independent Second UNSAT Proof Checker (`drat-trim` → LRAT → `lrat-check`):**
   - Added `scripts/verify_lrat.sh`, which fetches pinned commit `2e3b2dc0ecf938addbd779d42877b6ed69d9a985` of `marijnheule/drat-trim`, verifies SHA-256 digests of `drat-trim.c` (`d834b649f437...`) and `lrat-check.c` (`bf07c2ac96b9...`), compiles both with GCC, regenerates UNSAT proofs for `B(3,2)` (`k=30`), `B(4,1)` (`k=17`), and `B(3,3)` (`k=30`), cross-checks them through `verify/drup_check`, `drat-trim`, and `lrat-check`, and runs a truncated-LRAT negative control. Wired directly into `.github/workflows/ci.yml`.
3. **Cryptographic Timestamps (Playbook v1.3 #26):**
   - Sealed `data/MANIFEST.sha256` (`45ad1f8fa20dc3cd866ec548889116ee8ffa93710a960624175b61e066a88e3e`) with DigiCert RFC 3161 TSA (`data/MANIFEST.sha256.tsr`, 5,995 bytes) and 3-calendar Bitcoin OpenTimestamps (`data/MANIFEST.sha256.ots`, 931 bytes).
   - Verified cross-platform + full OpenSSL X.509 DigiCert CA chain (`Verification: OK`) via `scripts/stamp_timestamps.py --verify` in CI, `scripts/dev.sh`, and `tests/test_repo_integrity.py`.
4. **Permanent Software Heritage SWHID & Submission Packet:**
   - Recorded `swh:1:snp:6df0f79e042201d9490512cc8dda65471db9fafb` (`visit_status: full`) across `CITATION.cff`, `formalization.yaml`, `README.md`, `docs/threat-model.md`, and manuscripts.
   - Added draft-labeled `docs/submission-packet.md` (Palomar payload, human fidelity review checklist, specialist correspondence notes).
5. **Manuscript Compilation (`0.00 pt` Overfull):**
   - Recompiled `publication/ks-minimum/ks-minimum.pdf` (121,064 bytes) with Tectonic: exit 0, `0` overfull hboxes (`0.00 pt`), synced to `docs/ks-minimum.pdf`, refreshed `arxiv-source.zip`, `build-record.json`, and `llms-full.txt`.
6. **Automated Clean-Clone Replication (`B44`):**
   - Executed fresh `git clone --depth 1` into an isolated temporary workspace on `Z:\` (`_tmp_clean_rep_ks`, deleted after completion), passing zero-cache `lake build --wfail KS Solution`, `KS/Audit.lean` (`149/149`), `verify/test_verify.mjs` (`59/59`), and `docs/assets/verify.test.mjs`; recorded honestly in `REPLICATION.md` as author-automated (external human replication remains open).

## Remaining Honest Open Items

- External independent human replication and human line-by-line review sign-off (`human_line_by_line_review_recorded: false`).
- External scholarly submissions (Palomar Registry, Zenodo/arXiv, specialist correspondence) remain drafts awaiting author action.
- `A24` (`98.4%`, `63/64`): intentionally kept honest due to the committed `>5 MB` SAT cut-archive artifact `results/master_roots_3_18_k32_cuts.json` (required for offline reproducibility of the `B(3,3)` $k=32$ audit).
