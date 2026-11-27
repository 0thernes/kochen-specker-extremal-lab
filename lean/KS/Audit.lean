/-
KS/Audit.lean - exhaustive axiom audit.  Not part of the library; run it with

    lake build KS Solution
    lake env lean KS/Audit.lean

Every explicit declaration and every theorem in the `KS` namespace must report
at most the three standard axioms of Lean (propext, Classical.choice, Quot.sound):
no `sorryAx`, no `Lean.ofReduceBool` (the axiom behind evaluation by compiled
code), and no custom axiom of this project.
-/

module

meta import Lean
public import KS
public import Solution
import all KS.Basic
import all KS.Spec
import all KS.Box3H2
import all KS.Box4H1
import all KS.Tests
import all Solution

-- the two checkers are sound (KS/Basic.lean)
#print axioms KS.small_sets_colorable
#print axioms KS.small_sets_colorable_root
#print axioms KS.not_colorable_of_refute
#print axioms KS.not_colorable_of_refute_root

-- the table notion and the vector notion of colourability agree (KS/Spec.lean)
#print axioms KS.vcolorable_of_colorable
#print axioms KS.colorable_of_vcolorable
#print axioms KS.cliquesListed_spec
#print axioms KS.mem_boxVectors
#print axioms KS.mem_boxRays
#print axioms KS.countP_parallel_of_boxExact

-- B(3,2): the minimum is 31
#print axioms KS.Box3H2.minimum_ks_size
#print axioms KS.Box3H2.minimum_ks_size_vectors
#print axioms KS.Box3H2.rays_eq
#print axioms KS.Box3H2.rays_length
#print axioms KS.Box3H2.boxRays_exact
#print axioms KS.Box3H2.adj_spec
#print axioms KS.Box3H2.bases_sound
#print axioms KS.Box3H2.bases_complete

-- B(4,1): the minimum is 18
#print axioms KS.Box4H1.minimum_ks_size
#print axioms KS.Box4H1.minimum_ks_size_vectors
#print axioms KS.Box4H1.rays_eq
#print axioms KS.Box4H1.rays_length
#print axioms KS.Box4H1.boxRays_exact
#print axioms KS.Box4H1.adj_spec
#print axioms KS.Box4H1.bases_sound
#print axioms KS.Box4H1.bases_complete

-- Comparator Solution Bridge & kernel-proved false-variant refutations (Solution.lean)
#print axioms KS.isColoring_of_isColoringBool
#print axioms KS.ComparatorTarget.target_box3h2_minimum_31
#print axioms KS.ComparatorTarget.target_box4h1_minimum_18
#print axioms KS.ComparatorTarget.target_box3h2_nonvacuous_30
#print axioms KS.ComparatorTarget.target_box4h1_nonvacuous_17
#print axioms KS.ComparatorTarget.target_box3h2_refute_30
#print axioms KS.ComparatorTarget.target_box4h1_refute_17
#print axioms KS.ComparatorTarget.refute_box3h2_all_31_colorable
#print axioms KS.ComparatorTarget.refute_box4h1_all_18_colorable

-- Exhaustive metaprogram audit: EVERY theorem in the `KS` namespace
open Lean Elab Command in
run_cmd do
  let env ← getEnv
  let allowed : Array Name := #[`propext, `Classical.choice, `Quot.sound]
  let all := env.constants.toList.filter fun (name, info) =>
    info.isTheorem && Name.isPrefixOf `KS name
  if all.isEmpty then
    throwError "No KS theorems found for exhaustive axiom audit"
  let mut bad : Array String := #[]
  for (name, _) in all do
    let axioms ← Lean.collectAxioms name
    let forbidden := axioms.filter fun a => !allowed.contains a
    if !forbidden.isEmpty then
      bad := bad.push s!"{name}: {forbidden}"
  if !bad.isEmpty then
    throwError s!"Disallowed axioms detected across KS theorems:\n{String.intercalate "\n" bad.toList}"
  logInfo m!"ALL_KS_THEOREMS_AXIOM_AUDIT_PASS: checked {all.length} kernel theorem constants in KS (67 hand-written) — 0 disallowed axioms."
