/-
KS/Basic.lean

Kochen–Specker colourings of a finite pool of rays, and two certificate
checkers whose soundness is proved here once and for all:

* `check`   — a tree certificate that EVERY set of at most `k` rays of the
              pool is colourable (so the pool contains no KS set of size ≤ k);
* `refute`  — a tree certificate that ONE given set of rays is not colourable
              (so it is a KS set).

No Mathlib.  Sets of rays are bit masks: ray `i` belongs to the set `m`
exactly when `m.testBit i = true`.
-/

namespace KS

/-- The orthogonality structure of a finite pool of rays.
`adj[i]` is the mask of the rays orthogonal to ray `i`; `bases` lists the
masks of the bases (maximal sets of mutually orthogonal rays, `d` rays each). -/
structure Pool where
  n : Nat
  adj : List Nat
  bases : List Nat

def Pool.adjOf (P : Pool) (i : Nat) : Nat := P.adj.getD i 0

def Pool.baseOf (P : Pool) (b : Nat) : Nat := P.bases.getD b 0

/-- Number of rays (among rays `0 .. n-1`) in the set `m`. -/
def card (n m : Nat) : Nat := (List.range n).countP (fun i => m.testBit i)

/-- `a ⊆ b` for masks, as a computation. -/
def subMask (a b : Nat) : Bool := a &&& b == a

/-- `a ⊆ b` for masks, as a proposition. -/
def Sub (a b : Nat) : Prop := ∀ i, a.testBit i = true → b.testBit i = true

/-- `c` is a valid Kochen–Specker colouring of the ray set `T`:
the rays of value 1 form the set `c`, a subset of `T`;
no two orthogonal rays both have value 1;
every basis contained in `T` has a ray of value 1. -/
def IsColoring (P : Pool) (T c : Nat) : Prop :=
  Sub c T ∧
  (∀ i j, c.testBit i = true → c.testBit j = true → (P.adjOf i).testBit j = false) ∧
  (∀ b, b ∈ P.bases → Sub b T → ∃ i, b.testBit i = true ∧ c.testBit i = true)

def Colorable (P : Pool) (T : Nat) : Prop := ∃ c, IsColoring P T c

/-! ### Certificates that all small sets are colourable -/

/-- A search-tree certificate.  `node I kids`: at this node the set `I` of
pairwise non-orthogonal rays is used; `kids` is the chain of children,
`child r sub rest` meaning "the final set contains basis number `r`"
(subtree `sub`), followed by the remaining children `rest`. -/
inductive Cert where
  | done : Cert
  | child (r : Nat) (sub : Cert) (rest : Cert) : Cert
  | node (I : Nat) (kids : Cert) : Cert

def Cert.kidBases : Cert → List Nat
  | .child r _ rest => r :: rest.kidBases
  | _ => []

/-- `I` is a set of pairwise non-orthogonal rays. -/
def indep (P : Pool) (I : Nat) : Bool :=
  (List.range P.n).all (fun i => !I.testBit i || (P.adjOf i &&& I == 0))

/-- Some basis of the list `F` (given by indices) lies inside `S`. -/
def forbiddenInside (P : Pool) (S : Nat) (F : List Nat) : Bool :=
  F.any (fun f => subMask (P.baseOf f) S)

/-- Every basis that `I` misses is a child, or completes a forbidden basis,
or does not fit in the budget of `k` rays. -/
def missedOK (P : Pool) (k S : Nat) (F kids : List Nat) (I : Nat) : Bool :=
  (List.range P.bases.length).all (fun b =>
    (P.baseOf b &&& I != 0) || kids.contains b ||
      forbiddenInside P (S ||| P.baseOf b) F || decide (k < card P.n (S ||| P.baseOf b)))

/-- Shape test: the certificate is a `node`.  The subtree of a `child` must be
a `node` (a `done` or `child` there would prove nothing about the sets that
contain the child's basis). -/
def Cert.isNode : Cert → Bool
  | .node _ _ => true
  | _ => false

/-- The checker.  State: `S` = rays already known to be in the set, `F` =
bases (indices) known not to be contained in the set. -/
def check (P : Pool) (k : Nat) : Cert → Nat → List Nat → Bool
  | .done, _, _ => true
  | .child r sub rest, S, F =>
      sub.isNode && check P k sub (S ||| P.baseOf r) F && check P k rest S (r :: F)
  | .node I kids, S, F =>
      forbiddenInside P S F ||
        (indep P I && missedOK P k S F kids.kidBases I && check P k kids S F)

/-! #### Helper lemmas on masks -/

theorem sub_of_subMask {a b : Nat} (h : subMask a b = true) : Sub a b := by
  intro i hi
  have h' : a &&& b = a := by simpa [subMask] using h
  have h2 : (a &&& b).testBit i = true := by rw [h']; exact hi
  rw [Nat.testBit_and, Bool.and_eq_true] at h2
  exact h2.2

theorem sub_trans {a b c : Nat} (h1 : Sub a b) (h2 : Sub b c) : Sub a c :=
  fun i hi => h2 i (h1 i hi)

theorem sub_or {a b c : Nat} (h1 : Sub a c) (h2 : Sub b c) : Sub (a ||| b) c := by
  intro i hi
  rw [Nat.testBit_or, Bool.or_eq_true] at hi
  cases hi with
  | inl ha => exact h1 i ha
  | inr hb => exact h2 i hb

theorem lt_of_testBit {T n i : Nat} (hT : T < 2 ^ n) (hi : T.testBit i = true) : i < n := by
  apply Nat.lt_of_not_le
  intro hle
  have h2 : T < 2 ^ i :=
    Nat.lt_of_lt_of_le hT (Nat.pow_le_pow_right (by decide) hle)
  rw [Nat.testBit_lt_two_pow h2] at hi
  exact Bool.noConfusion hi

theorem card_mono {n a b : Nat} (h : Sub a b) : card n a ≤ card n b := by
  unfold card
  exact List.countP_mono_left (fun i _ hi => h i hi)

theorem exists_testBit_of_ne_zero {x : Nat} (h : x ≠ 0) : ∃ i, x.testBit i = true := by
  apply Classical.byContradiction
  intro hne
  apply h
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.zero_testBit]
  cases hx : x.testBit i with
  | false => rfl
  | true => exact absurd ⟨i, hx⟩ hne

theorem baseOf_eq_getElem {P : Pool} {b : Nat} (h : b < P.bases.length) :
    P.baseOf b = P.bases[b] := by
  unfold Pool.baseOf
  rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem h]
  rfl

theorem baseOf_mem {P : Pool} {b : Nat} (h : b < P.bases.length) :
    P.baseOf b ∈ P.bases := by
  rw [baseOf_eq_getElem h]
  exact List.getElem_mem h

theorem exists_baseOf_of_mem {P : Pool} {b : Nat} (h : b ∈ P.bases) :
    ∃ idx, idx < P.bases.length ∧ P.baseOf idx = b := by
  obtain ⟨i, hi, hb⟩ := List.getElem_of_mem h
  exact ⟨i, hi, by rw [baseOf_eq_getElem hi]; exact hb⟩

theorem forbidden_spec {P : Pool} {S : Nat} {F : List Nat}
    (h : forbiddenInside P S F = true) : ∃ f, f ∈ F ∧ Sub (P.baseOf f) S := by
  unfold forbiddenInside at h
  rw [List.any_eq_true] at h
  obtain ⟨f, hf, hs⟩ := h
  exact ⟨f, hf, sub_of_subMask hs⟩

/-- `T` is a set of at most `k` rays of the pool that is compatible with the
checker state: it contains `S` and contains none of the bases listed in `F`. -/
def Adm (P : Pool) (k S : Nat) (F : List Nat) (T : Nat) : Prop :=
  T < 2 ^ P.n ∧ Sub S T ∧ card P.n T ≤ k ∧ ∀ f, f ∈ F → ¬ Sub (P.baseOf f) T

/-- Soundness of `check` at every position of the tree.  A `node` accepted in
state `(S, F)` shows that every admissible set is colourable; a chain of
children accepted in state `(S, F)` shows this for every admissible set that
contains the basis of one of the children. -/
theorem check_sound (P : Pool) (k : Nat) : ∀ (C : Cert) (S : Nat) (F : List Nat),
    check P k C S F = true →
    (C.isNode = true → ∀ T, Adm P k S F T → Colorable P T) ∧
    (∀ T, Adm P k S F T →
      (∃ r, r ∈ C.kidBases ∧ Sub (P.baseOf r) T) → Colorable P T) := by
  intro C
  induction C with
  | done =>
    intro S F _
    refine ⟨fun h => by simp [Cert.isNode] at h, ?_⟩
    intro T _ ⟨r, hr, _⟩
    simp [Cert.kidBases] at hr
  | child r sub rest ihs ihr =>
    intro S F h
    simp only [check, Bool.and_eq_true] at h
    obtain ⟨⟨hnode, hsub⟩, hrest⟩ := h
    refine ⟨fun h => by simp [Cert.isNode] at h, ?_⟩
    intro T hT ⟨r', hr', hsubr'⟩
    obtain ⟨hlt, hST, hcard, hF⟩ := hT
    by_cases hrT : Sub (P.baseOf r) T
    · exact (ihs _ _ hsub).1 hnode T ⟨hlt, sub_or hST hrT, hcard, hF⟩
    · have hadm : Adm P k S (r :: F) T := by
        refine ⟨hlt, hST, hcard, ?_⟩
        intro f hf
        rcases List.mem_cons.mp hf with hfr | hfF
        · rw [hfr]; exact hrT
        · exact hF f hfF
      simp only [Cert.kidBases, List.mem_cons] at hr'
      rcases hr' with hrr | hr'
      · rw [hrr] at hsubr'; exact absurd hsubr' hrT
      · exact (ihr _ _ hrest).2 T hadm ⟨r', hr', hsubr'⟩
  | node I kids ih =>
    intro S F h
    refine ⟨fun _ => ?_, ?_⟩
    · intro T hT
      obtain ⟨hlt, hST, hcard, hF⟩ := hT
      simp only [check, Bool.or_eq_true, Bool.and_eq_true] at h
      rcases h with hforb | ⟨⟨hind, hmiss⟩, hkids⟩
      · obtain ⟨f, hf, hfs⟩ := forbidden_spec hforb
        exact absurd (sub_trans hfs hST) (hF f hf)
      · by_cases hk : ∃ r, r ∈ kids.kidBases ∧ Sub (P.baseOf r) T
        · exact (ih _ _ hkids).2 T ⟨hlt, hST, hcard, hF⟩ hk
        · refine ⟨I &&& T, ?_, ?_, ?_⟩
          · intro i hi
            rw [Nat.testBit_and, Bool.and_eq_true] at hi
            exact hi.2
          · intro i j hi hj
            rw [Nat.testBit_and, Bool.and_eq_true] at hi hj
            have hin : i < P.n := lt_of_testBit hlt hi.2
            unfold indep at hind
            rw [List.all_eq_true] at hind
            have h1 := hind i (List.mem_range.mpr hin)
            rw [hi.1] at h1
            have h0 : P.adjOf i &&& I = 0 := by simpa using h1
            have h2 : (P.adjOf i &&& I).testBit j = false := by
              rw [h0]; exact Nat.zero_testBit j
            rw [Nat.testBit_and, hj.1, Bool.and_true] at h2
            exact h2
          · intro b hb hbT
            obtain ⟨idx, hidx, hbe⟩ := exists_baseOf_of_mem hb
            subst hbe
            unfold missedOK at hmiss
            rw [List.all_eq_true] at hmiss
            have h1 := hmiss idx (List.mem_range.mpr hidx)
            simp only [Bool.or_eq_true, bne_iff_ne, ne_eq, decide_eq_true_eq] at h1
            rcases h1 with ((hne | hc) | hfb) | hbig
            · obtain ⟨i, hi⟩ := exists_testBit_of_ne_zero hne
              rw [Nat.testBit_and, Bool.and_eq_true] at hi
              refine ⟨i, hi.1, ?_⟩
              rw [Nat.testBit_and, hi.2, hbT i hi.1]
              rfl
            · exact absurd ⟨idx, List.contains_iff_mem.mp hc, hbT⟩ hk
            · obtain ⟨f, hf, hfs⟩ := forbidden_spec hfb
              exact absurd (sub_trans hfs (sub_or hST hbT)) (hF f hf)
            · have h3 : card P.n (S ||| P.baseOf idx) ≤ card P.n T :=
                card_mono (sub_or hST hbT)
              omega
    · intro T _ ⟨r, hr, _⟩
      simp [Cert.kidBases] at hr

/-- Soundness of `check`: an accepted certificate proves that every set of at
most `k` rays of the pool is colourable. -/
theorem small_sets_colorable (P : Pool) (k : Nat) (I : Nat) (kids : Cert)
    (h : check P k (.node I kids) 0 [] = true) :
    ∀ T, T < 2 ^ P.n → card P.n T ≤ k → Colorable P T := by
  intro T hT hcard
  refine (check_sound P k (.node I kids) 0 [] h).1 rfl T ⟨hT, ?_, hcard, ?_⟩
  · intro i hi
    rw [Nat.zero_testBit] at hi
    exact Bool.noConfusion hi
  · intro f hf
    exact absurd hf List.not_mem_nil

/-- Flat (postfix) encoding of a certificate, so that large trees can be
written as a list of numbers: `0` = `done`; `1, r` = `child r` (pops the
rest-chain, then the subtree); `2, I` = `node I` (pops the children chain). -/
def decodeCert : List Nat → List Cert → List Cert
  | 0 :: rest, st => decodeCert rest (.done :: st)
  | 1 :: r :: rest, rst :: sub :: st => decodeCert rest (.child r sub rst :: st)
  | 2 :: I :: rest, kids :: st => decodeCert rest (.node I kids :: st)
  | _, st => st

def certOfList (toks : List Nat) : Cert := (decodeCert toks []).headD .done

/-- Root check: the certificate must be a `node` and is checked from the
empty state. -/
def checkRoot (P : Pool) (k : Nat) : Cert → Bool
  | .node I kids => check P k (.node I kids) 0 []
  | _ => false

theorem small_sets_colorable_root (P : Pool) (k : Nat) (C : Cert)
    (h : checkRoot P k C = true) :
    ∀ T, T < 2 ^ P.n → card P.n T ≤ k → Colorable P T := by
  cases C with
  | done => simp [checkRoot] at h
  | child r sub rest => simp [checkRoot] at h
  | node I kids => exact small_sets_colorable P k I kids h

/-! ### Certificates that a given set is not colourable -/

/-- A refutation tree.  `split b kids`: basis number `b` lies inside the set,
so one of its rays has value 1; `kids` is the chain of cases
`child v sub rest` ("ray `v` has value 1").  `conflict b`: basis `b` lies
inside the set and all its rays are already known to have value 0. -/
inductive Refu where
  | conflict (b : Nat) : Refu
  | done : Refu
  | child (v : Nat) (sub : Refu) (rest : Refu) : Refu
  | split (b : Nat) (kids : Refu) : Refu

def Refu.kidRays : Refu → List Nat
  | .child v _ rest => v :: rest.kidRays
  | _ => []

/-- Every ray of the basis mask `bm` is known to have value 0 (lies in `Z`)
or is one of the listed cases. -/
def coversAll (n bm Z : Nat) (rays : List Nat) : Bool :=
  decide (bm < 2 ^ n) &&
    (List.range n).all (fun i => !bm.testBit i || Z.testBit i || rays.contains i)

/-- Shape test: the refutation is a `split` or a `conflict`.  The subtree of
a `child` must be one of these (a `done` or `child` there would refute
nothing in the case "ray `v` has value 1"). -/
def Refu.isNode : Refu → Bool
  | .conflict _ => true
  | .split _ _ => true
  | _ => false

/-- The refutation checker.  `Z` = rays known to have value 0. -/
def refute (P : Pool) (T : Nat) : Refu → Nat → Bool
  | .conflict b, Z =>
      decide (b < P.bases.length) && subMask (P.baseOf b) T && subMask (P.baseOf b) Z
  | .done, _ => true
  | .child v sub rest, Z =>
      sub.isNode && refute P T sub (Z ||| P.adjOf v) && refute P T rest Z
  | .split b kids, Z =>
      decide (b < P.bases.length) && subMask (P.baseOf b) T &&
        coversAll P.n (P.baseOf b) Z kids.kidRays && refute P T kids Z

/-- Soundness of `refute` at every position of the tree.  For a colouring `c`
of `T` whose value is 0 on all rays of `Z`: an accepted `split`/`conflict`
is contradictory outright; an accepted chain of cases is contradictory as
soon as one of its case rays has value 1. -/
theorem refute_sound (P : Pool) (T : Nat) : ∀ (R : Refu) (Z : Nat),
    refute P T R Z = true →
    ∀ c, IsColoring P T c → (∀ i, Z.testBit i = true → c.testBit i = false) →
      (R.isNode = true → False) ∧
      ((∃ v, v ∈ R.kidRays ∧ c.testBit v = true) → False) := by
  intro R
  induction R with
  | conflict b =>
    intro Z h c hc hZ
    simp only [refute, Bool.and_eq_true, decide_eq_true_eq] at h
    obtain ⟨⟨hb, hbT⟩, hbZ⟩ := h
    refine ⟨fun _ => ?_, ?_⟩
    · obtain ⟨i, hi, hci⟩ := hc.2.2 (P.baseOf b) (baseOf_mem hb) (sub_of_subMask hbT)
      rw [hZ i (sub_of_subMask hbZ i hi)] at hci
      exact Bool.noConfusion hci
    · intro ⟨v, hv, _⟩
      simp [Refu.kidRays] at hv
  | done =>
    intro Z _ c _ _
    refine ⟨fun h => by simp [Refu.isNode] at h, ?_⟩
    intro ⟨v, hv, _⟩
    simp [Refu.kidRays] at hv
  | child v sub rest ihs ihr =>
    intro Z h c hc hZ
    simp only [refute, Bool.and_eq_true] at h
    obtain ⟨⟨hnode, hsub⟩, hrest⟩ := h
    refine ⟨fun h => by simp [Refu.isNode] at h, ?_⟩
    intro ⟨v', hv', hcv'⟩
    cases hcv : c.testBit v with
    | true =>
      have hZ' : ∀ j, (Z ||| P.adjOf v).testBit j = true → c.testBit j = false := by
        intro j hj
        rw [Nat.testBit_or, Bool.or_eq_true] at hj
        cases hj with
        | inl hz => exact hZ j hz
        | inr ha =>
          cases hcj : c.testBit j with
          | false => rfl
          | true =>
            have h2 := hc.2.1 v j hcv hcj
            rw [ha] at h2
            exact Bool.noConfusion h2
      exact (ihs _ hsub c hc hZ').1 hnode
    | false =>
      simp only [Refu.kidRays, List.mem_cons] at hv'
      rcases hv' with hvv | hv'
      · rw [hvv, hcv] at hcv'
        exact Bool.noConfusion hcv'
      · exact (ihr _ hrest c hc hZ).2 ⟨v', hv', hcv'⟩
  | split b kids ih =>
    intro Z h c hc hZ
    simp only [refute, Bool.and_eq_true, decide_eq_true_eq] at h
    obtain ⟨⟨⟨hb, hbT⟩, hcov⟩, hkids⟩ := h
    refine ⟨fun _ => ?_, ?_⟩
    · obtain ⟨i, hi, hci⟩ := hc.2.2 (P.baseOf b) (baseOf_mem hb) (sub_of_subMask hbT)
      unfold coversAll at hcov
      rw [Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true] at hcov
      obtain ⟨hlt, hall⟩ := hcov
      have hin : i < P.n := lt_of_testBit hlt hi
      have h1 := hall i (List.mem_range.mpr hin)
      rw [hi] at h1
      simp only [Bool.not_true, Bool.false_or, Bool.or_eq_true] at h1
      rcases h1 with hz | hk
      · rw [hZ i hz] at hci
        exact Bool.noConfusion hci
      · exact (ih _ hkids c hc hZ).2 ⟨i, List.contains_iff_mem.mp hk, hci⟩
    · intro ⟨v, hv, _⟩
      simp [Refu.kidRays] at hv

/-- Soundness of `refute`: an accepted refutation proves that `T` has no
valid colouring, i.e. `T` is a Kochen–Specker set. -/
theorem not_colorable_of_refute (P : Pool) (T : Nat) (b : Nat) (kids : Refu)
    (h : refute P T (.split b kids) 0 = true) : ¬ Colorable P T := by
  intro ⟨c, hc⟩
  refine (refute_sound P T (.split b kids) 0 h c hc ?_).1 rfl
  intro i hi
  rw [Nat.zero_testBit] at hi
  exact Bool.noConfusion hi

/-- Flat (postfix) encoding of a refutation: `0` = `done`; `1, v` = `child v`
(pops the rest-chain, then the subtree); `2, b` = `split b` (pops the
children chain); `3, b` = `conflict b`. -/
def decodeRefu : List Nat → List Refu → List Refu
  | 0 :: rest, st => decodeRefu rest (.done :: st)
  | 1 :: v :: rest, rst :: sub :: st => decodeRefu rest (.child v sub rst :: st)
  | 2 :: b :: rest, kids :: st => decodeRefu rest (.split b kids :: st)
  | 3 :: b :: rest, st => decodeRefu rest (.conflict b :: st)
  | _, st => st

def refuOfList (toks : List Nat) : Refu := (decodeRefu toks []).headD .done

def refuteRoot (P : Pool) (T : Nat) : Refu → Bool
  | .split b kids => refute P T (.split b kids) 0
  | _ => false

theorem not_colorable_of_refute_root (P : Pool) (T : Nat) (R : Refu)
    (h : refuteRoot P T R = true) : ¬ Colorable P T := by
  cases R with
  | conflict b => simp [refuteRoot] at h
  | done => simp [refuteRoot] at h
  | child v sub rest => simp [refuteRoot] at h
  | split b kids => exact not_colorable_of_refute P T b kids h

/-! ### Tying a pool table to explicit integer vectors -/

/-- Dot product of two integer vectors. -/
def dot (u v : List Int) : Int := (List.zipWith (· * ·) u v).foldl (· + ·) 0

/-- The adjacency masks of `P` agree with orthogonality of the listed
vectors: bit `j` of `adj[i]` is set exactly when `i ≠ j` and the dot product
of ray `i` and ray `j` is zero. -/
def adjMatches (P : Pool) (rays : List (List Int)) : Bool :=
  rays.length == P.n && P.adj.length == P.n &&
  (List.range P.n).all (fun i => (List.range P.n).all (fun j =>
    (P.adjOf i).testBit j == (i != j && dot (rays.getD i []) (rays.getD j []) == 0)))

/-- Every listed basis is a set of exactly `d` mutually orthogonal rays of
the pool. -/
def basesAreCliques (P : Pool) (d : Nat) : Bool :=
  P.bases.all (fun bm => decide (bm < 2 ^ P.n) && card P.n bm == d &&
    (List.range P.n).all (fun i => !bm.testBit i ||
      (List.range P.n).all (fun j => !bm.testBit j || i == j || (P.adjOf i).testBit j)))

/-- Every set of `d` mutually orthogonal rays is listed as a basis
(`fuel` = number of rays still to choose, `lo` = smallest index allowed,
`cand` = rays orthogonal to all chosen ones, `cur` = chosen rays). -/
def cliquesListed (P : Pool) : Nat → Nat → Nat → Nat → Bool
  | 0, _, _, cur => P.bases.contains cur
  | fuel + 1, lo, cand, cur =>
      (List.range P.n).all (fun i => !(decide (lo ≤ i) && cand.testBit i) ||
        cliquesListed P fuel (i + 1) (cand &&& P.adjOf i) (cur ||| 2 ^ i))

def basesComplete (P : Pool) (d : Nat) : Bool := cliquesListed P d 0 (2 ^ P.n - 1) 0

end KS
