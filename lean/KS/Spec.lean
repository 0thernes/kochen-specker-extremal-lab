/-
KS/Spec.lean

A specification of the results that mentions integer vectors only.

* `boxRays d H` — the pool B(d,H): one representative of every ray of Z^d that
  has a representative of max-norm at most `H` (the primitive vector whose
  first non-zero entry is positive), in lexicographic order.
* `VColorable rays d T` — the set `T` of rays (a bit mask of positions in the
  list `rays`) has a Kochen–Specker colouring, phrased with dot products of
  the listed vectors only: no adjacency table, no list of bases.
* `vcolorable_of_colorable`, `colorable_of_vcolorable` — for a pool table `P`
  that passes the three checks `adjMatches`, `basesAreCliques`,
  `basesComplete` of KS/Basic.lean, the table notion `Colorable P T` and the
  vector notion `VColorable rays d T` are equivalent.

No Mathlib.
-/
import KS.Basic

namespace KS

/-! ### The pool B(d,H) -/

/-- The integers `-H, -H+1, …, H` in increasing order. -/
def intRange (H : Nat) : List Int :=
  (List.range (2 * H + 1)).map (fun (k : Nat) => (k : Int) - (H : Int))

/-- All vectors of length `d` with entries in `-H..H`, in lexicographic order
(first entry most significant, entries compared as integers). -/
def boxVectors : Nat → Nat → List (List Int)
  | 0, _ => [[]]
  | d + 1, H => (intRange H).flatMap (fun a => (boxVectors d H).map (fun v => a :: v))

/-- The gcd of the absolute values of the entries (0 for the zero vector). -/
def gcdList (v : List Int) : Nat := v.foldr (fun a g => Nat.gcd a.natAbs g) 0

/-- The first non-zero entry is positive (false for the zero vector). -/
def normalised : List Int → Bool
  | [] => false
  | a :: v => if a = 0 then normalised v else decide (0 < a)

/-- The pool B(d,H): the primitive vectors of max-norm at most `H` whose first
non-zero entry is positive.  Every ray of Z^d with a representative of
max-norm at most `H` has exactly one representative in this list. -/
def boxRays (d H : Nat) : List (List Int) :=
  (boxVectors d H).filter (fun v => normalised v && gcdList v == 1)

theorem mem_intRange {H : Nat} {a : Int} :
    a ∈ intRange H ↔ -(H : Int) ≤ a ∧ a ≤ (H : Int) := by
  unfold intRange
  rw [List.mem_map]
  constructor
  · intro ⟨k, hk, hka⟩
    rw [List.mem_range] at hk
    omega
  · intro ⟨h1, h2⟩
    refine ⟨(a + (H : Int)).toNat, ?_, ?_⟩
    · rw [List.mem_range]; omega
    · omega

/-- `boxVectors d H` is exactly the set of integer vectors of length `d` with
all entries between `-H` and `H`. -/
theorem mem_boxVectors : ∀ (d H : Nat) (v : List Int),
    v ∈ boxVectors d H ↔ v.length = d ∧ ∀ a, a ∈ v → -(H : Int) ≤ a ∧ a ≤ (H : Int)
  | 0, H, v => by
    unfold boxVectors
    rw [List.mem_singleton]
    constructor
    · intro h
      subst h
      exact ⟨rfl, fun a ha => absurd ha List.not_mem_nil⟩
    · intro ⟨h, _⟩
      exact List.length_eq_zero_iff.mp h
  | d + 1, H, v => by
    unfold boxVectors
    rw [List.mem_flatMap]
    constructor
    · intro ⟨a, ha, hv⟩
      rw [List.mem_map] at hv
      obtain ⟨w, hw, hwv⟩ := hv
      subst hwv
      have ih := (mem_boxVectors d H w).mp hw
      refine ⟨by rw [List.length_cons, ih.1], ?_⟩
      intro b hb
      rcases List.mem_cons.mp hb with hba | hbw
      · rw [hba]; exact mem_intRange.mp ha
      · exact ih.2 b hbw
    · intro ⟨hlen, hall⟩
      cases v with
      | nil => exact absurd hlen (by simp)
      | cons a w =>
        refine ⟨a, mem_intRange.mpr (hall a List.mem_cons_self), ?_⟩
        rw [List.mem_map]
        refine ⟨w, (mem_boxVectors d H w).mpr ⟨?_, fun b hb => hall b (List.mem_cons_of_mem _ hb)⟩, rfl⟩
        rw [List.length_cons] at hlen
        omega

/-- Membership in the pool: a vector of length `d`, entries between `-H` and
`H`, first non-zero entry positive, gcd of the entries equal to 1. -/
theorem mem_boxRays (d H : Nat) (v : List Int) :
    v ∈ boxRays d H ↔
      (v.length = d ∧ ∀ a, a ∈ v → -(H : Int) ≤ a ∧ a ≤ (H : Int)) ∧
        normalised v = true ∧ gcdList v = 1 := by
  unfold boxRays
  rw [List.mem_filter, mem_boxVectors, Bool.and_eq_true, beq_iff_eq]

/-! ### Each ray of the box is listed exactly once -/

/-- Two integer vectors of the same length are linearly dependent: all 2×2
minors `u_i v_j - u_j v_i` vanish.  For non-zero vectors this says that they
span the same ray. -/
def parallel (u v : List Int) : Bool :=
  (List.zip u v).all (fun p => (List.zip u v).all (fun q => p.1 * q.2 == q.1 * p.2))

/-- A finite check: every non-zero vector of the box is parallel to exactly
one vector of `boxRays d H`. -/
def boxExact (d H : Nat) : Bool :=
  (boxVectors d H).all (fun v =>
    v.all (fun a => a == 0) || (boxRays d H).countP (fun u => parallel u v) == 1)

/-- What the check `boxExact` says: every non-zero integer vector of length
`d` with entries between `-H` and `H` is parallel to exactly one listed ray.
In other words, every ray of Z^d that has a representative of max-norm at
most `H` occurs exactly once in `boxRays d H`. -/
theorem countP_parallel_of_boxExact {d H : Nat} (h : boxExact d H = true) (v : List Int)
    (hlen : v.length = d) (hbox : ∀ a, a ∈ v → -(H : Int) ≤ a ∧ a ≤ (H : Int))
    (hne : ∃ a, a ∈ v ∧ a ≠ 0) :
    (boxRays d H).countP (fun u => parallel u v) = 1 := by
  unfold boxExact at h
  rw [List.all_eq_true] at h
  have h1 := h v ((mem_boxVectors d H v).mpr ⟨hlen, hbox⟩)
  rw [Bool.or_eq_true, List.all_eq_true, beq_iff_eq] at h1
  rcases h1 with h1 | h1
  · obtain ⟨a, ha, hane⟩ := hne
    exact absurd (beq_iff_eq.mp (h1 a ha)) hane
  · exact h1

/-! ### Colourability in terms of the vectors -/

/-- The set `T` of rays (bit mask of positions in the list `rays`) has a
Kochen–Specker colouring: there is a set `c ⊆ T` (the rays of value 1) such
that no two distinct rays of `c` are orthogonal, and every basis inside `T`
(an increasing list of `d` positions of pairwise orthogonal rays, all in `T`)
contains a ray of `c`. -/
def VColorable (rays : List (List Int)) (d : Nat) (T : Nat) : Prop :=
  ∃ c : Nat, Sub c T ∧
    (∀ i j, c.testBit i = true → c.testBit j = true → i ≠ j →
        dot (rays.getD i []) (rays.getD j []) ≠ 0) ∧
    (∀ L : List Nat, L.length = d →
        L.Pairwise (fun i j => i < j ∧ dot (rays.getD i []) (rays.getD j []) = 0) →
        (∀ i, i ∈ L → T.testBit i = true) → ∃ i, i ∈ L ∧ c.testBit i = true)

/-! ### From the table to the vectors -/

/-- The bit mask of a list of positions. -/
def maskOf (L : List Nat) : Nat := L.foldr (fun i m => 2 ^ i ||| m) 0

theorem maskOf_cons (i : Nat) (L : List Nat) : maskOf (i :: L) = 2 ^ i ||| maskOf L := rfl

theorem testBit_maskOf (L : List Nat) (j : Nat) : (maskOf L).testBit j = true ↔ j ∈ L := by
  induction L with
  | nil =>
    have h0 : maskOf [] = 0 := rfl
    rw [h0, Nat.zero_testBit]
    exact ⟨fun h => Bool.noConfusion h, fun h => absurd h List.not_mem_nil⟩
  | cons i L ih =>
    rw [maskOf_cons, Nat.testBit_or, Bool.or_eq_true, ih, Nat.testBit_two_pow,
      decide_eq_true_eq, List.mem_cons]
    exact ⟨fun h => h.elim (fun h => Or.inl h.symm) Or.inr,
      fun h => h.elim (fun h => Or.inl h.symm) Or.inr⟩

/-- What `adjMatches` says, entry by entry. -/
theorem adj_of_adjMatches {P : Pool} {rays : List (List Int)}
    (h : adjMatches P rays = true) {i j : Nat} (hi : i < P.n) (hj : j < P.n) :
    (P.adjOf i).testBit j = (i != j && dot (rays.getD i []) (rays.getD j []) == 0) := by
  unfold adjMatches at h
  rw [Bool.and_eq_true, List.all_eq_true] at h
  have h1 := h.2 i (List.mem_range.mpr hi)
  rw [List.all_eq_true] at h1
  exact beq_iff_eq.mp (h1 j (List.mem_range.mpr hj))

theorem adj_true_iff {P : Pool} {rays : List (List Int)}
    (h : adjMatches P rays = true) {i j : Nat} (hi : i < P.n) (hj : j < P.n) :
    (P.adjOf i).testBit j = true ↔ i ≠ j ∧ dot (rays.getD i []) (rays.getD j []) = 0 := by
  rw [adj_of_adjMatches h hi hj, Bool.and_eq_true, bne_iff_ne, beq_iff_eq]

/-- Specification of the enumerator `cliquesListed`: if it accepts, then every
increasing list of `fuel` pairwise adjacent rays taken from the candidates at
positions `≥ lo` completes `cur` to a listed basis. -/
theorem cliquesListed_spec (P : Pool) : ∀ (fuel lo cand cur : Nat),
    cliquesListed P fuel lo cand cur = true →
    ∀ L : List Nat, L.length = fuel → L.Pairwise (fun a b => a < b) →
      (∀ i, i ∈ L → lo ≤ i ∧ i < P.n ∧ cand.testBit i = true) →
      L.Pairwise (fun a b => (P.adjOf a).testBit b = true) →
      (cur ||| maskOf L) ∈ P.bases := by
  intro fuel
  induction fuel with
  | zero =>
    intro lo cand cur h L hlen _ _ _
    have hL : L = [] := List.length_eq_zero_iff.mp hlen
    subst hL
    have h0 : cur ||| maskOf [] = cur := Nat.or_zero cur
    rw [h0]
    unfold cliquesListed at h
    exact List.contains_iff_mem.mp h
  | succ fuel ih =>
    intro lo cand cur h L hlen hlt hmem hadj
    cases L with
    | nil => exact absurd hlen (by simp)
    | cons i L' =>
      rw [List.pairwise_cons] at hlt hadj
      have hi := hmem i List.mem_cons_self
      unfold cliquesListed at h
      rw [List.all_eq_true] at h
      have h1 := h i (List.mem_range.mpr hi.2.1)
      rw [hi.2.2, decide_eq_true hi.1] at h1
      have h2 : cliquesListed P fuel (i + 1) (cand &&& P.adjOf i) (cur ||| 2 ^ i) = true := by
        simpa using h1
      have hmem' : ∀ j, j ∈ L' →
          i + 1 ≤ j ∧ j < P.n ∧ (cand &&& P.adjOf i).testBit j = true := by
        intro j hj
        have hj' := hmem j (List.mem_cons_of_mem _ hj)
        refine ⟨Nat.succ_le_of_lt (hlt.1 j hj), hj'.2.1, ?_⟩
        rw [Nat.testBit_and, hj'.2.2, hadj.1 j hj]
        rfl
      have hlen' : L'.length = fuel := by
        rw [List.length_cons] at hlen
        omega
      have h3 := ih (i + 1) _ _ h2 L' hlen' hlt.2 hmem' hadj.2
      rw [maskOf_cons, ← Nat.or_assoc]
      exact h3

/-- Every increasing list of `d` pairwise adjacent rays of the pool is a
listed basis. -/
theorem maskOf_mem_bases {P : Pool} {d : Nat} (h : basesComplete P d = true)
    (L : List Nat) (hlen : L.length = d) (hlt : L.Pairwise (fun a b => a < b))
    (hn : ∀ i, i ∈ L → i < P.n)
    (hadj : L.Pairwise (fun a b => (P.adjOf a).testBit b = true)) :
    maskOf L ∈ P.bases := by
  unfold basesComplete at h
  have h1 := cliquesListed_spec P d 0 (2 ^ P.n - 1) 0 h L hlen hlt ?_ hadj
  · rw [Nat.zero_or] at h1
    exact h1
  · intro i hi
    refine ⟨Nat.zero_le i, hn i hi, ?_⟩
    rw [Nat.testBit_two_pow_sub_one, decide_eq_true (hn i hi)]

/-- A colouring of the table is a colouring in the sense of the vectors. -/
theorem vcolorable_of_colorable {P : Pool} {rays : List (List Int)} {d : Nat}
    (hadj : adjMatches P rays = true) (_hsound : basesAreCliques P d = true)
    (hcomplete : basesComplete P d = true) :
    ∀ T, T < 2 ^ P.n → Colorable P T → VColorable rays d T := by
  intro T hT ⟨c, hcT, hc1, hc2⟩
  refine ⟨c, hcT, ?_, ?_⟩
  · intro i j hi hj hij hdot
    have hin : i < P.n := lt_of_testBit hT (hcT i hi)
    have hjn : j < P.n := lt_of_testBit hT (hcT j hj)
    have h1 := hc1 i j hi hj
    rw [(adj_true_iff hadj hin hjn).mpr ⟨hij, hdot⟩] at h1
    exact Bool.noConfusion h1
  · intro L hlen hpair hLT
    have hn : ∀ i, i ∈ L → i < P.n := fun i hi => lt_of_testBit hT (hLT i hi)
    have hlt : L.Pairwise (fun a b => a < b) := hpair.imp (fun h => h.1)
    have hadjL : L.Pairwise (fun a b => (P.adjOf a).testBit b = true) :=
      hpair.imp_of_mem (fun ha hb h =>
        (adj_true_iff hadj (hn _ ha) (hn _ hb)).mpr ⟨Nat.ne_of_lt h.1, h.2⟩)
    have hbase := maskOf_mem_bases hcomplete L hlen hlt hn hadjL
    have hsub : Sub (maskOf L) T := fun i hi => hLT i ((testBit_maskOf L i).mp hi)
    obtain ⟨i, hi, hci⟩ := hc2 (maskOf L) hbase hsub
    exact ⟨i, (testBit_maskOf L i).mp hi, hci⟩

/-! ### From the vectors to the table -/

/-- What `basesAreCliques` says about one listed basis. -/
theorem basis_of_basesAreCliques {P : Pool} {d : Nat} (h : basesAreCliques P d = true)
    {b : Nat} (hb : b ∈ P.bases) :
    b < 2 ^ P.n ∧ card P.n b = d ∧
      ∀ i j, i < P.n → j < P.n → b.testBit i = true → b.testBit j = true → i ≠ j →
        (P.adjOf i).testBit j = true := by
  unfold basesAreCliques at h
  rw [List.all_eq_true] at h
  have h1 := h b hb
  rw [Bool.and_eq_true, Bool.and_eq_true, decide_eq_true_eq, beq_iff_eq, List.all_eq_true] at h1
  obtain ⟨⟨hlt, hcard⟩, hall⟩ := h1
  refine ⟨hlt, hcard, ?_⟩
  intro i j hi hj hbi hbj hij
  have h2 := hall i (List.mem_range.mpr hi)
  rw [hbi, Bool.not_true, Bool.false_or, List.all_eq_true] at h2
  have h3 := h2 j (List.mem_range.mpr hj)
  rw [hbj, Bool.not_true, Bool.false_or, Bool.or_eq_true, beq_iff_eq] at h3
  rcases h3 with h3 | h3
  · exact absurd h3 hij
  · exact h3

/-- A colouring in the sense of the vectors is a colouring of the table. -/
theorem colorable_of_vcolorable {P : Pool} {rays : List (List Int)} {d : Nat}
    (hadj : adjMatches P rays = true) (hsound : basesAreCliques P d = true)
    (_hcomplete : basesComplete P d = true) :
    ∀ T, T < 2 ^ P.n → VColorable rays d T → Colorable P T := by
  intro T hT ⟨c, hcT, hc1, hc2⟩
  refine ⟨c, hcT, ?_, ?_⟩
  · intro i j hi hj
    have hin : i < P.n := lt_of_testBit hT (hcT i hi)
    have hjn : j < P.n := lt_of_testBit hT (hcT j hj)
    cases hadjij : (P.adjOf i).testBit j with
    | false => rfl
    | true =>
      have h1 := (adj_true_iff hadj hin hjn).mp hadjij
      exact absurd h1.2 (hc1 i j hi hj h1.1)
  · intro b hb hbT
    obtain ⟨_, hcard, hclique⟩ := basis_of_basesAreCliques hsound hb
    have hmemL : ∀ i, i ∈ (List.range P.n).filter (fun i => b.testBit i) →
        i < P.n ∧ b.testBit i = true := by
      intro i hi
      rw [List.mem_filter, List.mem_range] at hi
      exact hi
    have hlen : ((List.range P.n).filter (fun i => b.testBit i)).length = d := by
      rw [← List.countP_eq_length_filter]
      exact hcard
    have hlt : ((List.range P.n).filter (fun i => b.testBit i)).Pairwise (fun a b => a < b) :=
      List.Pairwise.filter _ List.pairwise_lt_range
    have hpair : ((List.range P.n).filter (fun i => b.testBit i)).Pairwise
        (fun i j => i < j ∧ dot (rays.getD i []) (rays.getD j []) = 0) :=
      hlt.imp_of_mem (fun {x y} hx hy hxy =>
        ⟨hxy, ((adj_true_iff hadj (hmemL x hx).1 (hmemL y hy).1).mp
          (hclique x y (hmemL x hx).1 (hmemL y hy).1 (hmemL x hx).2 (hmemL y hy).2
            (Nat.ne_of_lt hxy))).2⟩)
    obtain ⟨i, hi, hci⟩ := hc2 _ hlen hpair (fun i hi => hbT i (hmemL i hi).2)
    exact ⟨i, (hmemL i hi).2, hci⟩

/-- For a pool table that passes the three checks, the two notions agree. -/
theorem colorable_iff_vcolorable {P : Pool} {rays : List (List Int)} {d : Nat}
    (hadj : adjMatches P rays = true) (hsound : basesAreCliques P d = true)
    (hcomplete : basesComplete P d = true) (T : Nat) (hT : T < 2 ^ P.n) :
    Colorable P T ↔ VColorable rays d T :=
  ⟨vcolorable_of_colorable hadj hsound hcomplete T hT,
   colorable_of_vcolorable hadj hsound hcomplete T hT⟩

end KS
