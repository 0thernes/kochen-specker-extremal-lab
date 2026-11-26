# Threat Model

- **Statement weakening / vacuity:** Mitigated by isolated `lean/Challenge.lean` <-> `lean/Solution.lean` with non-vacuity targets (`30`-ray and `17`-ray colourable subsets) verified by 6-kernel `lake comparator --paranoid`.
- **Single-kernel bug:** Mitigated by multi-kernel replay (`leanchecker-paranoid`, `lean4lean`, `nanoda`, `con-leche`, `con-ron`).
- **Home-grown DRUP checker (`verify/drup_check.c`):** Compiled with `-Wall -Wextra -fsanitize=address,undefined` in CI, cross-checked against pinned, SHA-256-verified upstream `drat-trim` → LRAT → `lrat-check` (`scripts/verify_lrat.sh`) for `B(3,2)`, `B(4,1)`, and `B(3,3)` in CI, and tracked for full `cake_lpr` replay of all 83 dim-5 cubes in `ROADMAP.md`.
- **Tampering / retroactive dating:** Mitigated by `data/MANIFEST.sha256` sealed with both DigiCert RFC 3161 TSA (`data/MANIFEST.sha256.tsr`, OpenSSL X.509 verified in Linux CI) and 3-calendar Bitcoin OpenTimestamps (`data/MANIFEST.sha256.ots`), Sigstore/Rekor SLSA release attestations, and Software Heritage snapshots (`swh:1:snp:6df0f79e042201d9490512cc8dda65471db9fafb`).
