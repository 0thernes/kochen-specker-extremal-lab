/-
Kochen-Specker Extremal Lab — Isolated Statement-Only Challenge File (`lake comparator`).

Imports ONLY `KS.Basic` and `KS.Spec` (definitions of `boxRays`, `card`, `VColorable`),
and NONE of the certificate proof modules (`KS.Box3H2`, `KS.Box4H1`).

Every `sorry` in this file is intentional — checked against sorry-free `Solution.lean` by:
    lake comparator --config comparator.json --paranoid
-/
import KS.Basic
import KS.Spec

namespace KS.ComparatorTarget

/-- Target 1: Minimum Kochen-Specker set size in B(3,2) (49 rays) is exactly 31. -/
theorem target_box3h2_minimum_31 :
    (∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 31 ∧ ¬ KS.VColorable (KS.boxRays 3 2) 3 T) ∧
    (∀ T, T < 2 ^ 49 → KS.card 49 T ≤ 30 → KS.VColorable (KS.boxRays 3 2) 3 T) := by
  sorry

/-- Target 2: Minimum Kochen-Specker set size in B(4,1) (40 rays) is exactly 18. -/
theorem target_box4h1_minimum_18 :
    (∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 18 ∧ ¬ KS.VColorable (KS.boxRays 4 1) 4 T) ∧
    (∀ T, T < 2 ^ 40 → KS.card 40 T ≤ 17 → KS.VColorable (KS.boxRays 4 1) 4 T) := by
  sorry

/-- Target 3 (Non-vacuity): B(3,2) contains a concrete 30-ray colourable subset. -/
theorem target_box3h2_nonvacuous_30 :
    ∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 30 ∧ KS.VColorable (KS.boxRays 3 2) 3 T := by
  sorry

/-- Target 4 (Non-vacuity): B(4,1) contains a concrete 17-ray colourable subset. -/
theorem target_box4h1_nonvacuous_17 :
    ∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 17 ∧ KS.VColorable (KS.boxRays 4 1) 4 T := by
  sorry

end KS.ComparatorTarget
