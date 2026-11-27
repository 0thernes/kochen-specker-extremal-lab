/-
Kochen-Specker Extremal Lab — Isolated Statement-Only Challenge File (`lake comparator`).

Imports ONLY `KS.Basic` and `KS.Spec` (definitions of `boxRays`, `card`, `VColorable`),
and NONE of the certificate proof modules (`KS.Box3H2`, `KS.Box4H1`).

Every `sorry` in this file is intentional — checked against sorry-free `Solution.lean` by:
    lake comparator --config comparator.json --paranoid
-/

module

public import KS.Basic
public import KS.Spec

@[expose] public section

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

/-- Target 3 (Basis-bearing non-vacuity): B(3,2) contains a concrete 30-ray colourable subset
that contains a complete 3-ray orthogonal basis (exercising the basis condition directly). -/
theorem target_box3h2_nonvacuous_30 :
    ∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 30 ∧
      (∃ L : List Nat, L.length = 3 ∧
        L.Pairwise (fun i j => i < j ∧
          KS.dot ((KS.boxRays 3 2).getD i []) ((KS.boxRays 3 2).getD j []) = 0) ∧
        ∀ i, i ∈ L → T.testBit i = true) ∧
      KS.VColorable (KS.boxRays 3 2) 3 T := by
  sorry

/-- Target 4 (Basis-bearing non-vacuity): B(4,1) contains a concrete 17-ray colourable subset
that contains a complete 4-ray orthogonal basis (exercising the basis condition directly). -/
theorem target_box4h1_nonvacuous_17 :
    ∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 17 ∧
      (∃ L : List Nat, L.length = 4 ∧
        L.Pairwise (fun i j => i < j ∧
          KS.dot ((KS.boxRays 4 1).getD i []) ((KS.boxRays 4 1).getD j []) = 0) ∧
        ∀ i, i ∈ L → T.testBit i = true) ∧
      KS.VColorable (KS.boxRays 4 1) 4 T := by
  sorry

/-- Target 5 (Kernel-proved false-variant refutation): the bound 31 in B(3,2) cannot be lowered to 30. -/
theorem target_box3h2_refute_30 :
    ¬ (∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 30 ∧ ¬ KS.VColorable (KS.boxRays 3 2) 3 T) := by
  sorry

/-- Target 6 (Kernel-proved false-variant refutation): the bound 18 in B(4,1) cannot be lowered to 17. -/
theorem target_box4h1_refute_17 :
    ¬ (∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 17 ∧ ¬ KS.VColorable (KS.boxRays 4 1) 4 T) := by
  sorry

end KS.ComparatorTarget
