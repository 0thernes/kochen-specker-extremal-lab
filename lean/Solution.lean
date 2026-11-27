/-
Kochen-Specker Extremal Lab — Sorry-Free Solution Module Matched Against `Challenge`.
-/

module

public import KS.Box3H2
public import KS.Box4H1

@[expose] public section

namespace KS.ComparatorTarget

theorem target_box3h2_minimum_31 :
    (∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 31 ∧ ¬ KS.VColorable (KS.boxRays 3 2) 3 T) ∧
    (∀ T, T < 2 ^ 49 → KS.card 49 T ≤ 30 → KS.VColorable (KS.boxRays 3 2) 3 T) :=
  KS.Box3H2.minimum_ks_size_vectors

theorem target_box4h1_minimum_18 :
    (∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 18 ∧ ¬ KS.VColorable (KS.boxRays 4 1) 4 T) ∧
    (∀ T, T < 2 ^ 40 → KS.card 40 T ≤ 17 → KS.VColorable (KS.boxRays 4 1) 4 T) :=
  KS.Box4H1.minimum_ks_size_vectors

/-- Target 3: Concrete 30-ray subset (`0x3b70c7ffc69e`, obtained by dropping ray 0 from the 31-ray
KS set `KS.Box3H2.ksSet`) containing 13 complete 3-bases (witnessed by `[1, 7, 20]`) together with
an independent explicit 0/1 colouring `0x183000e` verified directly via `KS.isColoringBool`. -/
theorem target_box3h2_nonvacuous_30 :
    ∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 30 ∧
      (∃ L : List Nat, L.length = 3 ∧
        L.Pairwise (fun i j => i < j ∧
          KS.dot ((KS.boxRays 3 2).getD i []) ((KS.boxRays 3 2).getD j []) = 0) ∧
        ∀ i, i ∈ L → T.testBit i = true) ∧
      KS.VColorable (KS.boxRays 3 2) 3 T := by
  refine ⟨0x3b70c7ffc69e, by decide, by decide +kernel, ?_, ?_⟩
  · refine ⟨[1, 7, 20], rfl, ?_, by decide⟩
    rw [← KS.Box3H2.rays_eq]
    decide +kernel
  · rw [← KS.Box3H2.rays_eq]
    exact KS.vcolorable_of_colorable KS.Box3H2.adj_spec KS.Box3H2.bases_sound
      KS.Box3H2.bases_complete 0x3b70c7ffc69e (by decide)
      ⟨0x183000e, KS.isColoring_of_isColoringBool KS.Box3H2.pool 0x3b70c7ffc69e 0x183000e
        (by decide) (by decide +kernel)⟩

/-- Target 4: Concrete 17-ray subset (`0x2aac0aaaac`, obtained by dropping ray 0 from the 18-ray
Peres KS set `KS.Box4H1.ksSet`) containing 7 complete 4-bases (witnessed by `[2, 7, 9, 26]`)
together with an independent explicit 0/1 colouring `0x8000200c` verified directly via `KS.isColoringBool`. -/
theorem target_box4h1_nonvacuous_17 :
    ∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 17 ∧
      (∃ L : List Nat, L.length = 4 ∧
        L.Pairwise (fun i j => i < j ∧
          KS.dot ((KS.boxRays 4 1).getD i []) ((KS.boxRays 4 1).getD j []) = 0) ∧
        ∀ i, i ∈ L → T.testBit i = true) ∧
      KS.VColorable (KS.boxRays 4 1) 4 T := by
  refine ⟨0x2aac0aaaac, by decide, by decide +kernel, ?_, ?_⟩
  · refine ⟨[2, 7, 9, 26], rfl, ?_, by decide⟩
    rw [← KS.Box4H1.rays_eq]
    decide +kernel
  · rw [← KS.Box4H1.rays_eq]
    exact KS.vcolorable_of_colorable KS.Box4H1.adj_spec KS.Box4H1.bases_sound
      KS.Box4H1.bases_complete 0x2aac0aaaac (by decide)
      ⟨0x8000200c, KS.isColoring_of_isColoringBool KS.Box4H1.pool 0x2aac0aaaac 0x8000200c
        (by decide) (by decide +kernel)⟩

theorem target_box3h2_refute_30 :
    ¬ (∃ T, T < 2 ^ 49 ∧ KS.card 49 T = 30 ∧ ¬ KS.VColorable (KS.boxRays 3 2) 3 T) := by
  rintro ⟨T, hT, hcard, hnot⟩
  exact hnot (KS.Box3H2.minimum_ks_size_vectors.2 T hT (by omega))

theorem target_box4h1_refute_17 :
    ¬ (∃ T, T < 2 ^ 40 ∧ KS.card 40 T = 17 ∧ ¬ KS.VColorable (KS.boxRays 4 1) 4 T) := by
  rintro ⟨T, hT, hcard, hnot⟩
  exact hnot (KS.Box4H1.minimum_ks_size_vectors.2 T hT (by omega))

/-- Additional kernel-proved false-variant refutations: raising the colourability bound to 31 (in B(3,2))
or 18 (in B(4,1)) is false, refuted directly by the explicit KS sets. -/
theorem refute_box3h2_all_31_colorable :
    ¬ (∀ T, T < 2 ^ 49 → KS.card 49 T ≤ 31 → KS.VColorable (KS.boxRays 3 2) 3 T) := by
  intro hall
  obtain ⟨T, hT, hcard, hnot⟩ := KS.Box3H2.minimum_ks_size_vectors.1
  exact hnot (hall T hT (by omega))

theorem refute_box4h1_all_18_colorable :
    ¬ (∀ T, T < 2 ^ 40 → KS.card 40 T ≤ 18 → KS.VColorable (KS.boxRays 4 1) 4 T) := by
  intro hall
  obtain ⟨T, hT, hcard, hnot⟩ := KS.Box4H1.minimum_ks_size_vectors.1
  exact hnot (hall T hT (by omega))

end KS.ComparatorTarget
