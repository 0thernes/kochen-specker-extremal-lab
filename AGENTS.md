# AGENTS.md

Canonical instructions for coding agents working in `kochen-specker-extremal-lab`.
`CLAUDE.md`, `GEMINI.md`, `.cursor/rules/build-standard.mdc`, and `llms.txt` only point here.
Full standard: `docs/build-standard.md` (Build Standard for LLMs v1.1.0, 90 items).

## Project

- **Name:** Kochen-Specker Extremal Lab (`kochen-specker-extremal-lab`)
- **Purpose:** Certified exact minimum sizes of Kochen-Specker sets inside nine finite coordinate ray pools (31 and 33 rays in 3D, 18 in 4D, 29 in 5D), featuring a **zero-Mathlib** Lean 4.35.0 formal core (`lean/KS/`) verified by six independent Lean kernels (`lake comparator --paranoid`) alongside independent SAT/DRUP certificates.
- **Author:** Alexander S. Donahue (independent researcher, ORCID `0009-0006-8168-9648`, `0_0@0thernes.art`)
- **Licenses:** `Apache-2.0` (`LICENSE`, all code) + `CC-BY-4.0` (`LICENSE-DOCS`, papers & docs)
- **Sibling Repository:** Multiqubit Pauli contextuality work lives separately in [`0thernes/pauli-contextuality-lab`](https://github.com/0thernes/pauli-contextuality-lab) so this repository keeps its minimal zero-Mathlib trust base.
- **Status:** Research preprint `v1.6.0`; NOT externally peer reviewed; AI-assisted under human direction; no general open-problem record is broken.

## Commands

- `just build`: Build zero-Mathlib Lean 4.35.0 core (`KS`, `Solution`) and compile C verifiers (`verify/`).
- `just test`: Run Python test suite (`tests/`).
- `just verify-lean`: Clean build + `KS/Audit.lean` + forbidden-token scan + 6-kernel `lake comparator --config comparator.json --paranoid`.
- `just reproduce`: Run tests, Lean verification, and certificate checks.
- `just audit`: Score repository against Build Standard v1.1.0 (`scripts/audit-repo.sh` / `scripts/Audit-Repo.ps1`).

## Hard Rules (Build Standard v1.1.0)

- **R1–R3:** Commit and push straight to `main`; zero branch protection, hooks, or merge gates; CI is informational.
- **R4:** No Dependabot/Renovate, PR templates, CodeRabbit, Copilot config, or `FUNDING.yml`.
- **R5–R8:** One-person lean; never fabricate; classify every finding as `bug | error | issue | problem | dilemma | conflict`.
- **Zero-Mathlib invariant:** Never add Mathlib to `lean/lakefile.toml` — keep the Lean trust base minimal.
- **`lean/Challenge.lean` intentional `sorry` stubs:** Only `Challenge.lean` contains `sorry` (comparator specification); zero `sorry`/`admit`/`native_decide`/custom `axiom` anywhere in `KS/` or `Solution.lean`.
