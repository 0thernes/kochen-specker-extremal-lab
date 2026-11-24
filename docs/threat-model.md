# Threat Model

- **Statement weakening / vacuity:** Mitigated by isolated `lean/Challenge.lean` <-> `lean/Solution.lean` with non-vacuity targets (`30`-ray and `17`-ray colourable subsets) verified by 6-kernel `lake comparator --paranoid`.
- **Single-kernel bug:** Mitigated by multi-kernel replay (`leanchecker-paranoid`, `lean4lean`, `nanoda`, `con-leche`, `con-ron`).
- **Home-grown DRUP checker (`verify/drup_check.c`):** Compiled with `-Wall -Wextra -fsanitize=address,undefined` in CI and tracked for `drat-trim -> cake_lpr` upgrade in `ROADMAP.md`.
