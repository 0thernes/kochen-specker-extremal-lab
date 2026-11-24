# Gold Standard & Playbook v1.1 Audit (`v1.0.0` → `v1.1.0`, 2026-11-24)

Addresses the findings from `DEFENSIBLE_INDEPENDENT_AI_RESEARCH_PLAYBOOK.md` v1.1 and Build Standard for LLMs v1.1.0:

1. **`[problem]` Fixed:** Removed premature `0thernes LLC` assertions from `LICENSE`, `CITATION.cff`, `LEGAL.md`, and `README.md`; standardized attribution to `Alexander S. Donahue (independent researcher, ORCID 0009-0006-8168-9648)`.
2. **`[issue]` Fixed:** Re-licensed code to `Apache-2.0` (`LICENSE`) and manuscripts/docs to `CC-BY-4.0` (`LICENSE-DOCS`).
3. **`[issue]` Fixed:** Added isolated `lean/Challenge.lean`, sorry-free `lean/Solution.lean`, `lean/comparator.json`, and explicit non-vacuity targets (`30`-ray subset of `B(3,2)`, `17`-ray subset of `B(4,1)`), checked by 6-kernel `lake comparator --paranoid`.
4. **`[issue]` Fixed:** Added full Build Standard v1.1.0 files (`AGENTS.md`, `repo.yaml`, `formalization.yaml`, `CLAIMS.md`, `LIMITATIONS.md`, `REPLICATION.md`, `ROADMAP.md`, `justfile`, `Audit-Repo.ps1`, cross-platform CI + ASan/UBSan + SLSA release workflow).
5. **`[issue]` Open (tracked in `ROADMAP.md`):** Re-verify non-Lean DRUP proofs via `drat-trim -> LRAT -> cake_lpr`.
