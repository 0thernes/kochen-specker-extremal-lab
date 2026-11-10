# Mathematical core (statements and proofs used by the programs)

This file is the reference for every argument the software relies on. The paper quotes it.

## 1. Setting

* A **pool** is a finite set `V` of rays (one-dimensional subspaces) of a `d`-dimensional real or
  complex inner-product space, `d ≥ 3`. Two rays are **orthogonal** when their inner product vanishes.
  A **basis** of the pool is a set of `d` mutually orthogonal rays of `V`.
* A subset `S ⊆ V` is **colorable** when there is `f : S → {0,1}` with
  (i) `f(u) + f(v) ≤ 1` for orthogonal `u, v ∈ S`, and
  (ii) every basis contained in `S` has a ray with `f = 1`.
  (By (i) a basis then has exactly one such ray.) A set that is not colorable is a
  **Kochen-Specker (KS) set**. This is the standard rank-one definition; only the rays of `S` are
  counted, and orthogonal pairs of `S` constrain `f` whether or not they lie in a basis inside `S`.
* Subsets of colorable sets are colorable. A KS set is **critical** when every proper subset is
  colorable. Every KS set contains a critical KS set, so the minimum size of a KS set in `V` is attained
  by a critical one.

## 2. Coloring cuts (duality)

Call `I ⊆ V` **independent** when no two rays of `I` are orthogonal, and let `Miss(I)` be the set of
bases of `V` that contain no ray of `I`.

**Lemma 1.** A subset `S ⊆ V` is a KS set if and only if for every independent `I ⊆ V` the set `S`
contains a basis of `Miss(I)`.

*Proof.* If `S` contains no basis of `Miss(I)`, put `f = 1` on `I ∩ S` and `0` elsewhere on `S`:
(i) holds because `I` is independent, (ii) because every basis inside `S` meets `I`, in a ray that lies
in `S`. Conversely, if `f` colors `S` then `I = f⁻¹(1)` is independent and `S` contains no basis of
`Miss(I)`. ∎

So each independent set `I` gives a **cut**: the clause "`S` contains at least one basis of `Miss(I)`"
holds for every KS set `S`. A cut is certified by `I` alone (check independence, recompute `Miss(I)`).
Symmetries of the pool (permutations of `V` preserving orthogonality) map cuts to cuts.

**Corollary 2 (correction sets).** If `C ⊆ V` is colorable then every KS set meets `V \ C`.

## 3. Necessary conditions for critical KS sets

**Lemma 3.** Let `T` be a critical KS set and `v ∈ T`. Then
(C1) `v` lies in a basis contained in `T`, and
(C2) `v` is orthogonal to at least `d` rays of `T`.

*Proof.* Let `c` color `T \ {v}`.
(C1) If no basis inside `T` contains `v`, extend `c` by `c(v) = 0`; (i) and (ii) still hold, so `T` is
colorable, a contradiction.
(C2) Suppose `v` has at most `d − 1` orthogonal partners in `T`. By (C1) it lies in a basis `b ⊆ T`,
which supplies `d − 1` partners, so the partners of `v` are exactly `b \ {v}` and `b` is the only basis
of `T` through `v`. If some ray of `b \ {v}` has `c = 1`, extend by `c(v) = 0`. Otherwise extend by
`c(v) = 1`: all partners of `v` have value 0, and `b` now has a 1. In both cases `T` is colorable. ∎

**Corollary 4 (core of a pool).** Deleting from `V`, repeatedly, every ray that lies in no basis or has
fewer than `d` orthogonal partners among the remaining rays does not delete any ray of a critical KS
set. The remaining set is the **core**; minimum KS sets of `V` and of its core coincide.

## 4. Search trees (third engine, and the Lean certificates)

A **state** is `(S, F)`: `S ⊆ V` and `F` a list of bases. A set `T` is *admissible* for `(S, F)` when
`S ⊆ T`, `|T| ≤ k`, and `T` contains no basis of `F`. A **node** carries an independent set `I` and
children `(r₁, N₁), …, (r_m, N_m)` with `r_j` bases and `N_j` nodes. The node is *accepted* in state
`(S, F)` when

0. some basis of `F` lies inside `S`; or
1. `I` is independent,
2. every basis `b ∈ Miss(I)` satisfies `|S ∪ b| > k`, or `S ∪ b` contains a basis of `F`, or
   `b ∈ {r₁,…,r_m}`, and
3. each `N_j` is accepted in state `(S ∪ r_j, F + [r₁,…,r_{j−1}])`.

**Lemma 5.** If a node is accepted in state `(S, F)`, every set admissible for `(S, F)` is colorable.
In particular an accepted root in state `(∅, [])` proves that every subset of `V` with at most `k` rays
is colorable.

*Proof.* Induction on the tree. Let `T` be admissible. In case 0 no admissible set exists. Otherwise,
if `T` contains some `r_j`, take the least such `j`; then `T` is admissible for
`(S ∪ r_j, F + [r₁..r_{j−1}])` and the claim follows from `N_j`. If `T` contains no `r_j`, then `T`
contains no basis of `Miss(I)`: such a basis `b ⊆ T` would have `|S ∪ b| ≤ |T| ≤ k`, would not complete a
basis of `F` inside `T`, and is not a child. By Lemma 1 (its easy direction) `I ∩ T` colors `T`. ∎

This is `KS.check` and theorem `KS.small_sets_colorable` in `lean/KS/Basic.lean`. The dual statement,
that one given set is not colorable, is certified by a case tree over "which ray of this basis has
value 1" (`KS.refute`, theorem `KS.not_colorable_of_refute`).

## 5. Counterexample-guided search (first and second engines)

Variables `x_v` (ray chosen) and `y_b` (basis chosen), with `y_b ⇔ ⋀_{v∈b} x_v`. The **candidate
problem** for a bound `k` asks for an assignment satisfying

* (C1) `x_v ⇒ ⋁_{b∋v} y_b`, (C2) `x_v ⇒ Σ_{w ⟂ v} x_w ≥ d`, (K) `Σ_v x_v ≤ k`,
* all cuts collected so far, `⋁_{b∈Miss(I)} y_b`,
* optional case constraints and symmetry-breaking constraints (Section 6).

By Lemmas 1 and 3 every critical KS set with at most `k` rays (in the normal form of Section 6)
satisfies the candidate problem. A solution `S` is tested: if it is not colorable it is a KS set with
at most `k` rays; otherwise a coloring of `S` is extended to an independent set `I` of `V` that misses
few bases, and the cut of `I`, which `S` violates, is added together with its images under the pool's
symmetries. When the candidate problem becomes infeasible there is **no KS set with at most `k` rays
in `V`**.

Engine A solves the candidate problem with CP-SAT. Engine B re-encodes the final candidate problem
(with every collected cut re-verified from its witness `I`) as plain CNF, with two-sided sequential
counters for (C2), (K) and the counting constraints of Section 6, solves it with a CDCL solver that
writes a DRUP proof, and the proof is checked by `verify/drup_check.c`.

## 6. Symmetry and cases for integer boxes

Let `V` be the rays of `Zᵈ` with a representative of max-norm at most `H` (or its core). Signed
coordinate permutations act on `V`.

**Lemma 6 (normal form).** Let coordinates be partitioned into groups. Every `S ⊆ V` is mapped, by a
permutation preserving each group followed by sign changes of coordinates `1, …, d−1`, to a set with
(a) `n_a ≥ n_b` for consecutive coordinates `a, b` of a group, where `n_j` is the number of chosen rays
with non-zero `j`-th entry, and (b) `x[e₀+e_j] ≥ x[e₀−e_j]` for `j = 1..d−1`.

*Proof.* Sort each group by `n_j`. Changing the sign of coordinate `j ≥ 1` swaps `e₀+e_j` and `e₀−e_j`,
fixes `e₀ ± e_i` for `i ≠ j`, and changes no `n_i`; apply it for those `j` that violate (b). ∎

**Lemma 7 (axes in dimension 5, entries 0, ±1).** In the pool `{0,±1}⁵` (121 rays, core 105 rays, 136
bases) every basis contains a coordinate axis `e_m`, and every KS set contains at least three axes.

*Proof.* The first statement is a finite check (the bases are a 4-dimensional basis of a coordinate
hyperplane together with the axis orthogonal to it). For the second, the pool with any three axes
removed is colorable (an explicit coloring for `{e₀,e₁,e₂}` is in `results/`, and coordinate
permutations give the other triples); apply Corollary 2 to the ten triples. ∎

Hence a critical KS set in this pool can be moved by a coordinate permutation to one whose axes are
exactly `{e₀,e₁,e₂}`, exactly `{e₀,e₁,e₂,e₃}`, or all five: three cases, each treated with the groups
"axes inside" and "axes outside" in Lemma 6.
