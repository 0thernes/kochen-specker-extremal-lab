/-
Kochen-Specker Extremal Lab — Sorry-Free Solution Module Matched Against `Challenge`.
-/
import KS.Box3H2
import KS.Box4H1

namespace KS.ComparatorTarget

theorem target_box3h2_minimum_31 :
    (∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 31 ∧ ¬ KS.VColorable (KS.boxRays 3 2) 3 T) ∧
    (∀ T, T < 2 ^ 49 → KS.card 49 T ≤ 30 → KS.VColorable (KS.boxRays 3 2) 3 T) :=
  KS.Box3H2.minimum_ks_size_vectors

theorem target_box4h1_minimum_18 :
    (∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 18 ∧ ¬ KS.VColorable (KS.boxRays 4 1) 4 T) ∧
    (∀ T, T < 2 ^ 40 → KS.card 40 T ≤ 17 → KS.VColorable (KS.boxRays 4 1) 4 T) :=
  KS.Box4H1.minimum_ks_size_vectors

theorem target_box3h2_nonvacuous_30 :
    ∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 30 ∧ KS.VColorable (KS.boxRays 3 2) 3 T := by
  refine ⟨2 ^ 30 - 1, by decide, by decide +kernel, ?_⟩
  exact KS.Box3H2.minimum_ks_size_vectors.2 (2 ^ 30 - 1) (by decide) (by decide +kernel)

theorem target_box4h1_nonvacuous_17 :
    ∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 17 ∧ KS.VColorable (KS.boxRays 4 1) 4 T := by
  refine ⟨2 ^ 17 - 1, by decide, by decide +kernel, ?_⟩
  exact KS.Box4H1.minimum_ks_size_vectors.2 (2 ^ 17 - 1) (by decide) (by decide +kernel)

end KS.ComparatorTarget
