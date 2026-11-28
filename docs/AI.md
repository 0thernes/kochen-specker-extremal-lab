<!-- SPDX-License-Identifier: CC-BY-4.0 -->
# AI-Contribution Statement and Venue Integrity Compliance (`docs/AI.md`)

Repository: **`kochen-specker-extremal-lab`** (`0TH-2026-004`, `v2.3.0`)  
Title: *Certified exact minima of Kochen-Specker sets inside coordinate pools: 31 and 33 rays in dimension three, 18 in dimension four, 29 in dimension five*

Following the Defensible Independent AI-Assisted Research Playbook (v1.3) and current COPE, ICMJE, arXiv, Nature Portfolio, Zenodo, JOSS, and Palomar Registry disclosure norms:

## Formal AI-Contribution Statement

```text
AI-CONTRIBUTION STATEMENT
Author: Alexander Stephen Donahue (ORCID 0009-0006-8168-9648), independent researcher.
Human contributions (CRediT): Conceptualization; Methodology; Formal analysis
  (problem selection, definition & statement-fidelity audit); Validation; Writing – review & editing.
AI tools used: Google Antigravity / Gemini (2026).
  - Assisted with algebraic exploration, Lean 4 tactic synthesis (leanprover/lean4:v4.35.0, 7 Palomar
    Comparator targets), polyglot verifier engineering, figure generation, and manuscript drafting.
  - Every formal Lean theorem was checked from scratch by the Lean kernel (leanprover/lean4:v4.35.0) and
    independent proof-checking infrastructure with axioms strictly within [propext, Quot.sound, Classical.choice]
    (zero sorryAx, zero Lean.ofReduceBool, zero custom axioms).
  - All bibliographic references, datasets, and computational artifacts were independently
    checked against primary sources and reproducible scripts in this repository.
Not done by AI: problem selection, epistemic boundary decisions, final statement sign-off,
  and release/publication decisions.
The author takes full responsibility for all content. No AI system is listed as an author.
```

## Venue-Specific Policy Alignment

| Venue | Applicable Requirement | Repository Compliance |
| :--- | :--- | :--- |
| **arXiv** | Human author assumes full responsibility; AI is not an author; endorsement required for first category submission | Single human author (`Alexander Stephen Donahue`), full disclosure in manuscript and `docs/AI.md`; no fabricated arXiv ID |
| **COPE / ICMJE** | Disclose exact tools used and scope; humans accountable for accuracy and citations | Disclosed in `formalization.yaml` and `docs/AI.md`; zero fabricated references |
| **Zenodo** | AI as tool only; grounded in human-conducted research; disclose; no AI creator metadata | Single human creator in `.zenodo.json` and `CITATION.cff`; full tool disclosure |
| **Palomar Registry** | `formalization.yaml` required; `module` header on `.lean` files; `Challenge.lean` compact; zero `sorry`/`native_decide`/custom axioms | `formalization.yaml` committed at repository root; `lean/comparator.json` (7 targets) audited strictly within `[propext, Quot.sound, Classical.choice]` |
| **ORCID** | Accurate attribution of verified research works and software releases | ORCID `0009-0006-8168-9648` linked across `CITATION.cff`, `.zenodo.json`, and `formalization.yaml` |

## Transcript & Redaction Notice

Session prompt and execution artifacts are archived locally by the author after redacting any local machine paths, credentials, tokens, or private identifiers; no unredacted personal data or secrets are committed to this repository.
