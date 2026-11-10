/-
KS/Audit.lean - axiom audit.  Not part of the library; run it with

    lake build
    lake env lean KS/Audit.lean

Every line must report at most the three standard axioms of Lean
(propext, Classical.choice, Quot.sound): no `sorryAx`, no `Lean.ofReduceBool`
(the axiom behind evaluation by compiled code), no axiom of this project.
-/
import KS

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
