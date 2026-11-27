# Draft inquiry to Zenodo support (to be sent by the author before any deposit)

Subject: Is a research software and preprint package produced with AI agents under human direction in scope for Zenodo?

Dear Zenodo team,

I would like to deposit a research repository (programs, machine-checkable certificates, zero-Mathlib Lean 4.35.0 proofs) and the accompanying preprint, *"Certified exact minima of Kochen-Specker sets inside coordinate pools: 31 and 33 rays in dimension three, 18 in dimension four, 29 in dimension five"*.

Before depositing, I want to ask whether this work is in scope under your April 27, 2026 generative-AI policy for depositors (which allows AI as a tool grounded in human-conducted research, not as the source of the research itself). To keep our disclosure completely consistent with `CITATION.cff`, `formalization.yaml`, and the manuscript (Playbook v1.3 H48), the facts are:

* **Human role:** I conceived the project, set the research scope, directed the verification pipeline, oversaw audits and corrections, and am the sole listed author taking full responsibility for the release (CRediT: Conceptualization, Methodology, Project administration, Resources, Supervision, Validation). No AI system is listed as a creator or contributor.
* **AI role:** AI software agents — specifically Anthropic Claude (initial research plan, core SAT/DRUP programs, zero-Mathlib Lean 4 proofs, and v1.0.0 manuscript) and Google Gemini / Antigravity (isolated `Challenge.lean`/`Solution.lean` 6-kernel comparator bridge, non-vacuity targets, independent `drat-trim`→LRAT→`lrat-check` + HOL4-verified `cake_lpr` pipeline, cryptographic timestamping, and Build Standard v1.2.0 / Playbook v1.3 hardening) — drafted the code, formal proofs, computations, and manuscript text under my direction. This is disclosed on the first page of the paper, in Section 9, in `CITATION.cff`, and in `formalization.yaml`.
* **Verification & scope:** Two pool minima ($B(3,2)=31$, $B(4,1)=18$) plus non-vacuity witnesses are proved in zero-Mathlib Lean 4.35.0 across 6 independent kernels (`lake comparator --paranoid`) and `lake env leanchecker --fresh`; larger pools rest on SAT UNSAT certificates checked by independent checkers (`verify/drup_check.c`, `drat-trim`, `lrat-check`, and HOL4-verified `cake_lpr`). The work claims no general open-problem record (`24 <= min_KS(R^3) <= 31` remains open) and explicitly credits prior reports (Section 1.3).
* **Review status:** The work has undergone automated multi-checker verification and internal AI-assisted review passes, and has **not** yet undergone independent external peer review or recorded human line-by-line Lean proof sign-off.

If such a deposit is acceptable under your policy, please let me know which resource type and disclosure wording you prefer. If it is out of scope, I will not deposit it on Zenodo (and will use an eligible alternative such as OSF Preprints / Palomar Registry).

Repository: https://github.com/0thernes/kochen-specker-extremal-lab

Thank you,  
Alexander S. Donahue (Independent researcher, Spokane, WA, USA; ORCID 0009-0006-8168-9648; Zenodo account registered to `0_0@0thernes.art`)
