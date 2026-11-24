# Limitations & AI-Contribution Disclosure

- **Pool-restricted scope:** Every exact minimum applies **only** to subsets of the stated finite coordinate pool. Nothing here breaks a published record or settles the general minimal Kochen-Specker problem.
- **Kernel vs. certificate boundary:** `B(3,2) = 31` and `B(4,1) = 18` are proved inside Lean 4.35.0 (zero Mathlib, verified by 6 independent kernels via `lake comparator --paranoid`). The larger pools ($H=3,4$, roots of unity, dimension 5) rely on SAT/DRUP certificates checked by `verify/drup_check.c` outside Lean (re-checking via `drat-trim -> LRAT -> cake_lpr` is logged on the roadmap).
- **Not externally peer reviewed:** Research preprint (`v1.5.0`), no external refereeing or journal acceptance claimed.
- **Author & CRediT:** Alexander S. Donahue (independent researcher, ORCID `0009-0006-8168-9648`) — Conceptualization, Methodology, Project administration, Resources, Supervision, Validation direction. AI tools (Anthropic Claude, Google Gemini / Antigravity) drafted Lean code, solver tooling, and prose under human direction. No AI is listed as an author; the author takes full responsibility (`0_0@0thernes.art`).
- **Sibling Pauli repository:** Multiqubit Pauli contextuality studies live in [`0thernes/pauli-contextuality-lab`](https://github.com/0thernes/pauli-contextuality-lab) to preserve this repo's zero-Mathlib trust base.
