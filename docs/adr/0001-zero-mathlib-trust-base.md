# ADR 0001: Preserve Zero-Mathlib Lean 4 Trust Base Separate from Pauli Monorepo

- **Status:** Accepted (2026-11-24)
- **Context:** Multiqubit Pauli contextuality repositories (`hoggar-bound`, `hoggar-bound-lab`, `contextuality-tensor-lab`, `contextuality-evidence-lab`) all depend on Mathlib v4.35.0 and were consolidated into `0thernes/pauli-contextuality-lab`. By contrast, `kochen-specker-extremal-lab` uses pure Lean 4.35.0 with zero external dependencies and rebuilds from clean in under 30 seconds.
- **Decision:** Keep `kochen-specker-extremal-lab` as an independent zero-Mathlib repository while re-licensing to `Apache-2.0` + `CC-BY-4.0`, correcting author attribution to `Alexander S. Donahue (independent researcher)`, and adding 6-kernel `Challenge.lean` / `Solution.lean` comparator verification.
- **Consequences:** Minimal formal trust base preserved; full Mathlib-free reproducibility.
