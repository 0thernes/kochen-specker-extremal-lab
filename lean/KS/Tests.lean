/-
KS/Tests.lean

Regression tests for the checkers of KS/Basic.lean and the definitions of
KS/Spec.lean, on pools small enough to check by hand.  Every statement is
proved by `decide` (kernel evaluation), so `lake build` fails if a checker
starts to accept one of the malformed certificates below.

Three mutually orthogonal rays 0, 1, 2 (think of the coordinate axes):

* `one`  — the single basis {0,1,2} (dimension 3).  Every set of its rays is
           colourable, so NO refutation may be accepted.
* `tri`  — the three edges {0,1}, {0,2}, {1,2} listed as bases (dimension 2).
           The full set {0,1,2} is NOT colourable (a ray of value 1 in every
           edge needs two rays, and those are orthogonal), every set of at
           most two rays is.  So NO certificate for "all sets of at most 3
           rays are colourable" may be accepted.

The first malformed inputs are the historical ones: before the shape tests
`Refu.isNode` / `Cert.isNode` were added to the checkers, a `child` whose
subtree was a bare `done` (or a chain of children) was accepted and "proved"
the two false statements above.
-/
import KS.Spec

namespace KS.Tests

def one : Pool := ⟨3, [6, 5, 3], [7]⟩

def tri : Pool := ⟨3, [6, 5, 3], [3, 5, 6]⟩

/-- Two orthogonal rays; basis 1 has the mask 6, which is not below `2 ^ n`
(it mentions a ray 2 that the table does not have). -/
def wide : Pool := ⟨2, [2, 1], [1, 6]⟩

/-- The coordinate axes of Z^3. -/
def e3 : List (List Int) := [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

/-! ### Refutations (`refute`): positive examples -/

/-- A correct refutation of the full set of `tri`: split on edge {0,1};
if ray 0 has value 1 then edge {1,2} is all 0; if ray 1 has value 1 then edge
{0,2} is all 0. -/
def triRefu : Refu := .split 0 (.child 0 (.conflict 2) (.child 1 (.conflict 1) .done))

/-- The same tree in postfix form. -/
def triRefuToks : List Nat := [3, 2, 3, 1, 0, 1, 1, 1, 0, 2, 0]

example : refuOfList triRefuToks = triRefu := rfl

example : refuteRoot tri 7 triRefu = true := by decide

example : refuteRoot tri 7 (refuOfList triRefuToks) = true := by decide

/-- The checker result turned into the mathematical statement. -/
example : ¬ Colorable tri 7 := not_colorable_of_refute_root tri 7 triRefu (by decide)

/-! ### Refutations: malformed inputs are rejected -/

/-- (i) The historical malformed refutation of a single basis: the three cases
are bare `done`s. -/
example : refuteRoot one 7
    (.split 0 (.child 0 .done (.child 1 .done (.child 2 .done .done)))) = false := by decide

/-- The same in postfix form, through the decoder. -/
example : refuteRoot one 7 (refuOfList [0, 0, 1, 2, 0, 1, 1, 0, 1, 0, 2, 0]) = false := by decide

/-- Bare `done` cases on the triangle. -/
example : refuteRoot tri 7 (.split 0 (.child 0 .done (.child 1 .done .done))) = false := by decide

/-- The subtree of a case is a chain of children instead of a split or conflict. -/
example : refuteRoot tri 7
    (.split 0 (.child 0 (.child 2 (.conflict 2) .done) (.child 1 (.conflict 1) .done))) = false := by
  decide

/-- Basis index out of range in a split (basis 3 does not exist; `baseOf`
would return the empty mask, which lies inside every set). -/
example : refuteRoot tri 7 (.split 3 .done) = false := by decide

/-- Basis index out of range in a conflict. -/
example : refuteRoot tri 7
    (.split 0 (.child 0 (.conflict 7) (.child 1 (.conflict 7) .done))) = false := by decide

/-- A ray of the split basis is not covered by a case. -/
example : refuteRoot tri 7 (.split 0 (.child 0 (.conflict 2) .done)) = false := by decide

/-- A conflict on a basis whose rays are not all known to be 0. -/
example : refuteRoot tri 7
    (.split 0 (.child 0 (.conflict 0) (.child 1 (.conflict 1) .done))) = false := by decide

/-- The root is not a split. -/
example : refuteRoot tri 7 (.conflict 0) = false := by decide

example : refuteRoot tri 7 .done = false := by decide

example : refuteRoot tri 7 (.child 0 (.conflict 2) .done) = false := by decide

/-- The correct refutation of {0,1,2} does not refute a smaller set: the split
basis, or a conflict basis, is not inside it. -/
example : refuteRoot tri 5 triRefu = false := by decide

example : refuteRoot tri 3 triRefu = false := by decide

/-- The bound in `coversAll`: a basis mask that is not below `2 ^ n` cannot be
split on (its ray 2 would never be examined). -/
example : refuteRoot wide 7 (.split 0 (.child 0 (.split 1 .done) .done)) = false := by decide

/-! ### Refutations: decoder edge cases -/

/-- (iii) The empty token list decodes to `done`, which is rejected. -/
example : refuOfList [] = .done := rfl

example : refuteRoot tri 7 (refuOfList []) = false := by decide

example : refuteRoot one 7 (refuOfList []) = false := by decide

/-- Unknown tag; `child` with an empty stack; missing operand. -/
example : refuteRoot tri 7 (refuOfList [7]) = false := by decide

example : refuteRoot tri 7 (refuOfList [1, 0]) = false := by decide

example : refuteRoot tri 7 (refuOfList [0, 2]) = false := by decide

/-- Documented behaviour, not a defect: the decoder stops at the first token
it cannot read and the checker then examines the tree on top of the stack.
Here that tree is the correct refutation, so the (true) statement is accepted.
Soundness does not depend on the decoder: whatever tree is checked, it is
checked by the verified checker.  The Python pre-check of the generator
refuses such streams. -/
example : refuteRoot tri 7 (refuOfList (triRefuToks ++ [9])) = true := by decide

example : refuteRoot tri 7 (refuOfList (0 :: triRefuToks)) = true := by decide

/-! ### Certificates (`check`): positive examples -/

/-- Every set of rays of `one` is colourable: give ray 0 the value 1. -/
example : checkRoot one 3 (.node 1 .done) = true := by decide

/-- A correct certificate that every set of at most 2 rays of `tri` is
colourable: ray 0 hits the edges {0,1} and {0,2}; if the set contains the edge
{1,2} (basis 2) use ray 1, and the edge {0,2} no longer fits in the budget. -/
def triCert : Cert := .node 1 (.child 2 (.node 2 .done) .done)

def triCertToks : List Nat := [0, 2, 2, 0, 1, 2, 2, 1]

example : certOfList triCertToks = triCert := rfl

example : checkRoot tri 2 triCert = true := by decide

example : checkRoot tri 2 (certOfList triCertToks) = true := by decide

example : ∀ T, T < 2 ^ 3 → card 3 T ≤ 2 → Colorable tri T :=
  small_sets_colorable_root tri 2 triCert (by decide)

/-! ### Certificates: malformed inputs are rejected -/

/-- (ii) The historical malformed certificates for the false statement "every
set of at most 3 rays of `tri` is colourable": the subtree of a child is a
bare `done`, or a chain of children. -/
example : checkRoot tri 3 (.node 1 (.child 1 .done (.child 2 .done .done))) = false := by decide

example : checkRoot tri 3 (.node 1 (.child 1 (.child 2 .done .done) .done)) = false := by decide

/-- The correct certificate for budget 2 does not pass with budget 3. -/
example : checkRoot tri 3 triCert = false := by decide

/-- Children for all three edges with empty colourings below. -/
example : checkRoot tri 3 (.node 0 (.child 0 (.node 0 .done)
    (.child 1 (.node 0 .done) (.child 2 (.node 0 .done) .done)))) = false := by decide

/-- The root is not a node. -/
example : checkRoot tri 2 .done = false := by decide

example : checkRoot tri 2 (.child 2 (.node 2 .done) .done) = false := by decide

/-- The set `I` contains two orthogonal rays. -/
example : checkRoot tri 2 (.node 3 .done) = false := by decide

/-- A basis that `I` misses is not handled. -/
example : checkRoot tri 2 (.node 1 .done) = false := by decide

/-! ### Certificates: decoder edge cases -/

/-- (iii) The empty token list decodes to `done`, which is rejected, even for a
true statement. -/
example : certOfList [] = .done := rfl

example : checkRoot tri 3 (certOfList []) = false := by decide

example : checkRoot one 3 (certOfList []) = false := by decide

/-- Unknown tag; `child` with an empty stack; missing operand. -/
example : checkRoot tri 2 (certOfList [5]) = false := by decide

example : checkRoot tri 2 (certOfList [1, 0]) = false := by decide

example : checkRoot tri 2 (certOfList [2]) = false := by decide

/-! ### The three table checks -/

example : adjMatches one e3 = true := by decide

example : adjMatches tri e3 = true := by decide

/-- A wrong adjacency entry is detected. -/
example : adjMatches ⟨3, [6, 5, 2], [7]⟩ e3 = false := by decide

/-- A table that claims an orthogonality the vectors do not have. -/
example : adjMatches one [[1, 0, 0], [0, 1, 0], [0, 1, 1]] = false := by decide

example : basesAreCliques one 3 = true := by decide

example : basesAreCliques tri 2 = true := by decide

/-- Wrong size; a listed "basis" that mentions a ray outside the table. -/
example : basesAreCliques one 2 = false := by decide

example : basesAreCliques ⟨3, [6, 5, 3], [3, 5, 6, 9]⟩ 2 = false := by decide

/-- A listed "basis" of two rays that are not orthogonal. -/
example : basesAreCliques ⟨3, [6, 1, 1], [3, 5, 6]⟩ 2 = false := by decide

example : basesComplete one 3 = true := by decide

example : basesComplete tri 2 = true := by decide

/-- A missing basis is detected. -/
example : basesComplete ⟨3, [6, 5, 3], [3, 5]⟩ 2 = false := by decide

example : basesComplete ⟨3, [6, 5, 3], []⟩ 3 = false := by decide

/-! ### The definitions of KS/Spec.lean -/

example : boxVectors 1 1 = [[-1], [0], [1]] := by decide

example : (boxVectors 3 2).length = 125 := by decide +kernel

/-- B(2,1): the four rays of Z^2 with entries in -1..1. -/
example : boxRays 2 1 = [[0, 1], [1, -1], [1, 0], [1, 1]] := by decide

/-- B(3,1) has (27 - 1) / 2 = 13 rays. -/
example : (boxRays 3 1).length = 13 := by decide +kernel

example : gcdList [4, -6] = 2 := by decide

example : gcdList [0, 0] = 0 := by decide

example : normalised [0, 2, -1] = true := by decide

example : normalised [0, -1, 2] = false := by decide

example : normalised [0, 0, 0] = false := by decide

example : parallel [1, -2, 0] [-2, 4, 0] = true := by decide

example : parallel [1, 2, 0] [2, 4, 1] = false := by decide

example : parallel [1, 0] [0, 1] = false := by decide

/-- Every non-zero vector of the box is parallel to exactly one listed ray. -/
example : boxExact 2 1 = true := by decide +kernel

example : boxExact 3 1 = true := by decide +kernel

/-- The count detects a missing and a doubled ray: the vector [1, 1] is
parallel to no ray of the list without it, and to two rays of a list that
contains both [1, 1] and [2, 2]. -/
example : [[0, 1], [1, -1], [1, 0]].countP (fun u => parallel u [1, 1]) = 0 := by decide

example : [[0, 1], [1, 1], [2, 2]].countP (fun u => parallel u [1, 1]) = 2 := by decide

example : dot [1, 2, 3] [3, 0, -1] = 0 := by decide

example : dot [1, 1] [1, 1] = 2 := by decide

/-! ### The bridge, end to end, on the coordinate axes

With `d = 3` the only basis among the axes is the triple itself, and the full
set is colourable; with `d = 2` the bases are the three pairs, and the full
set is not colourable.  Both statements are about the vectors `e3` only. -/

example : VColorable e3 3 7 :=
  vcolorable_of_colorable (P := one) (by decide) (by decide) (by decide) 7 (by decide)
    (small_sets_colorable_root one 3 (.node 1 .done) (by decide) 7 (by decide) (by decide))

example : ¬ VColorable e3 2 7 := fun h =>
  not_colorable_of_refute_root tri 7 triRefu (by decide)
    (colorable_of_vcolorable (P := tri) (by decide) (by decide) (by decide) 7 (by decide) h)

end KS.Tests
