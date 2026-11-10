# Lean 4 formalisation: exact minimum size of a Kochen-Specker set in two box pools

Lean 4.35.0, core library only (no Mathlib). No `sorry`, no `native_decide`, no
project axiom: every theorem below depends on at most the three standard axioms
`propext`, `Classical.choice`, `Quot.sound` (see "Axiom audit").

## What is proved

A Kochen-Specker (KS) set is a finite set S of rays in d-dimensional space with
no 0/1 assignment such that (i) no two orthogonal rays of S both get 1 and
(ii) every basis (d mutually orthogonal rays) inside S has a 1. The pool B(d,H)
is the set of rays of Z^d that have a representative with max-norm at most H.

| pool | rays | bases | minimum size of a KS set inside the pool | Lean theorem |
|---|---|---|---|---|
| B(3,2) | 49 | 26 | 31 | `KS.Box3H2.minimum_ks_size_vectors` |
| B(4,1) | 40 | 32 | 18 | `KS.Box4H1.minimum_ks_size_vectors` |

### The statement in plain words (B(3,2); B(4,1) is the same with 4, 1, 40, 18, 17)

Let `boxRays 3 2` be the list of the 49 primitive integer vectors of length 3
with entries between -2 and 2 whose first non-zero entry is positive, in
lexicographic order. A set of rays is given by the bit mask `T` of the positions
of its rays in that list (`T < 2 ^ 49`), and `card 49 T` is the number of its rays.

1. There is a set of exactly 31 rays that has no KS colouring.
2. Every set of at most 30 rays has a KS colouring.

"`T` has a KS colouring" (`VColorable`) means: there is a subset `c` of `T` (the
rays of value 1) such that no two different rays of `c` have dot product 0, and
every increasing list of 3 positions of pairwise orthogonal rays, all inside
`T`, contains a ray of `c`.

### The statement as Lean text

```lean
theorem KS.Box3H2.minimum_ks_size_vectors :
    (∃ T, T < 2 ^ 49 ∧ card 49 T = 31 ∧ ¬ VColorable (boxRays 3 2) 3 T) ∧
    (∀ T, T < 2 ^ 49 → card 49 T ≤ 30 → VColorable (boxRays 3 2) 3 T)

theorem KS.Box4H1.minimum_ks_size_vectors :
    (∃ T, T < 2 ^ 40 ∧ card 40 T = 18 ∧ ¬ VColorable (boxRays 4 1) 4 T) ∧
    (∀ T, T < 2 ^ 40 → card 40 T ≤ 17 → VColorable (boxRays 4 1) 4 T)
```

The definitions it uses, all of them (`KS/Spec.lean`, and `dot`, `card`, `Sub`
from `KS/Basic.lean`):

```lean
def intRange (H : Nat) : List Int :=
  (List.range (2 * H + 1)).map (fun (k : Nat) => (k : Int) - (H : Int))

def boxVectors : Nat → Nat → List (List Int)
  | 0, _ => [[]]
  | d + 1, H => (intRange H).flatMap (fun a => (boxVectors d H).map (fun v => a :: v))

def gcdList (v : List Int) : Nat := v.foldr (fun a g => Nat.gcd a.natAbs g) 0

def normalised : List Int → Bool
  | [] => false
  | a :: v => if a = 0 then normalised v else decide (0 < a)

def boxRays (d H : Nat) : List (List Int) :=
  (boxVectors d H).filter (fun v => normalised v && gcdList v == 1)

def dot (u v : List Int) : Int := (List.zipWith (· * ·) u v).foldl (· + ·) 0

def card (n m : Nat) : Nat := (List.range n).countP (fun i => m.testBit i)

def Sub (a b : Nat) : Prop := ∀ i, a.testBit i = true → b.testBit i = true

def VColorable (rays : List (List Int)) (d : Nat) (T : Nat) : Prop :=
  ∃ c : Nat, Sub c T ∧
    (∀ i j, c.testBit i = true → c.testBit j = true → i ≠ j →
        dot (rays.getD i []) (rays.getD j []) ≠ 0) ∧
    (∀ L : List Nat, L.length = d →
        L.Pairwise (fun i j => i < j ∧ dot (rays.getD i []) (rays.getD j []) = 0) →
        (∀ i, i ∈ L → T.testBit i = true) → ∃ i, i ∈ L ∧ c.testBit i = true)
```

`VColorable` mentions the list of vectors, `dot`, `Sub`, `testBit`, lists and
`d` only: no table of bit masks, no list of bases.

## Files

| file | content |
|---|---|
| `KS/Basic.lean` | The table form. `Pool` (number of rays, adjacency masks, list of basis masks), `Colorable`. Two certificate checkers with soundness proofs: `check` / `small_sets_colorable_root` (an accepted tree proves that every set of at most k rays is colourable) and `refute` / `not_colorable_of_refute_root` (an accepted tree proves that one given set is not colourable). The three Boolean table checks `adjMatches`, `basesAreCliques`, `basesComplete`. |
| `KS/Spec.lean` | The vector form. `boxRays` (the pool as a definition), `VColorable`. `mem_boxVectors`, `mem_boxRays`: membership in the pool spelled out (length d, entries between -H and H, first non-zero entry positive, gcd 1). `countP_parallel_of_boxExact`: meaning of the finite check `boxExact` (each non-zero vector of the box is parallel to exactly one listed ray). `cliquesListed_spec`: specification of the basis enumerator behind `basesComplete`. Bridge theorems `vcolorable_of_colorable` and `colorable_of_vcolorable`: for a table that passes the three checks, `Colorable P T` and `VColorable rays d T` are equivalent for every `T < 2 ^ P.n`. |
| `KS/Box3H2.lean`, `KS/Box4H1.lean` | Generated data modules, one per pool: the list `rays`, the table `pool`, the two certificates as token lists, and the theorems listed below. |
| `KS/Tests.lean` | Regression tests proved by `decide` on pools of three rays: correct certificates are accepted; the historical malformed certificates (a case whose subtree is a bare `done` or a chain of children), out-of-range basis indices, uncovered rays, wrong roots and the decoder edge cases (empty token list, unknown tag, missing operand) are rejected; the three table checks reject wrong tables; small values of the `Spec` definitions; the bridge used end to end on the coordinate axes. |
| `KS.lean` | Root module: imports the five modules above, so plain `lake build` checks everything. |
| `KS/Audit.lean` | Axiom audit script (`#print axioms`), not part of the library. |

Theorems of each data module (`n`, `d`, `H`, `kmin` are the concrete numbers):

| theorem | says |
|---|---|
| `adj_spec` | `adjMatches pool rays = true`: bit j of `adj[i]` is set exactly when i and j differ and the dot product of rays i and j is 0 |
| `bases_sound` | every listed basis is a set of exactly d mutually orthogonal rays |
| `bases_complete` | every set of d mutually orthogonal rays is listed |
| `cert_ok`, `small_sets_colorable` | every set of at most kmin-1 rays is colourable (table form) |
| `refu_ok`, `ksSet_lt`, `ksSet_card`, `ksSet_not_colorable` | the set `ksSet` has kmin rays and is not colourable (table form) |
| `minimum_ks_size` | the two halves together, table form |
| `rays_eq` | `rays = boxRays d H`: the literal list is the pool |
| `rays_length` | `(boxRays d H).length = n` |
| `boxRays_exact` | every non-zero integer vector of length d with entries between -H and H is parallel to exactly one vector of `boxRays d H` |
| `minimum_ks_size_vectors` | the result for the vectors themselves, from `minimum_ks_size`, the three table theorems, the bridge theorems and `rays_eq` |

The large facts (`adj_spec`, `bases_sound`, `bases_complete`, `cert_ok`,
`refu_ok`, `rays_eq`, `boxRays_exact`) are proved by `decide +kernel`: the Lean
kernel itself evaluates the Boolean check. The compiler is not trusted
(`native_decide` is not used).

## Build

```
cd lean
lake build                      # checks Basic, Spec, both data modules and Tests
lake env lean KS/Audit.lean     # prints the axioms of 26 theorems
```

Measured on the development machine (Windows 11, Lean 4.35.0, other heavy jobs
running at the same time): `lake build` from an empty build directory takes
53 seconds of wall-clock time (Box3H2 and Box4H1 dominate; Basic, Spec and
Tests take about 3 seconds each). The audit script takes 3 seconds.

## Axiom audit

Output of `lake env lean KS/Audit.lean`:

```
'KS.small_sets_colorable' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.small_sets_colorable_root' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.not_colorable_of_refute' depends on axioms: [propext, Quot.sound]
'KS.not_colorable_of_refute_root' depends on axioms: [propext, Quot.sound]
'KS.vcolorable_of_colorable' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.colorable_of_vcolorable' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.cliquesListed_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.mem_boxVectors' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.mem_boxRays' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.countP_parallel_of_boxExact' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box3H2.minimum_ks_size' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box3H2.minimum_ks_size_vectors' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box3H2.rays_eq' does not depend on any axioms
'KS.Box3H2.rays_length' does not depend on any axioms
'KS.Box3H2.boxRays_exact' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box3H2.adj_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box3H2.bases_sound' depends on axioms: [propext]
'KS.Box3H2.bases_complete' depends on axioms: [propext]
'KS.Box4H1.minimum_ks_size' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box4H1.minimum_ks_size_vectors' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box4H1.rays_eq' does not depend on any axioms
'KS.Box4H1.rays_length' does not depend on any axioms
'KS.Box4H1.boxRays_exact' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box4H1.adj_spec' depends on axioms: [propext, Classical.choice, Quot.sound]
'KS.Box4H1.bases_sound' depends on axioms: [propext]
'KS.Box4H1.bases_complete' depends on axioms: [propext]
```

## How the data modules are generated

The two data modules are written by `scripts/gen_lean.py`, run from the project
root; do not edit them by hand.

```
python scripts/gen_lean.py Box3H2 31 boxfull 3 2
python scripts/gen_lean.py Box4H1 18 boxfull 4 1
python scripts/gen_lean.py --selftest
```

The generator builds the pool with `src/pools.py` (`box_pool`), finds a KS set
of the claimed size and a refutation tree for it, builds the search-tree
certificate for "every smaller set is colourable" with `src/gen_cert.py`,
replays both in Python, and writes the Lean module. The search is
deterministic: running the generator again reproduces the same file.

Nothing in the Python code is trusted by the Lean result. The token lists are
plain data; Lean decodes them and runs its own checkers, whose soundness is
proved in `KS/Basic.lean`. A wrong certificate makes `lake build` fail.

The Python pre-check `check_refutation_tokens` mirrors the Lean checker
`refuteRoot` clause by clause (the subtree of a case must be a split or a
conflict; basis indices must be in range; the bound in `coversAll`; `adjOf` and
`baseOf` return 0 out of range). It never raises on malformed input. By default
it is stricter than Lean in one respect: it refuses a token stream that the
decoder does not read completely or that leaves more than one tree, where the
Lean decoder stops at the first unreadable token and checks the tree on top of
its stack. With `strict=False` it returns exactly the Boolean that Lean
computes. `--selftest` replays the malformed refutations of `KS/Tests.lean`
through it.

## What remains to be trusted

1. The Lean kernel (version 4.35.0), including its built-in arithmetic on
   natural numbers and bit operations, which `decide +kernel` relies on.
2. The definitions that the final statement is made of, printed in full above:
   `boxRays` (with `intRange`, `boxVectors`, `gcdList`, `normalised`), `dot`,
   `card`, `Sub`, `VColorable`. A reader has to agree that they say what the
   plain-words statement says. Three proved facts help with `boxRays`:
   `mem_boxVectors` and `mem_boxRays` characterise its elements, and
   `boxRays_exact` shows that every ray of the box is listed exactly once (this
   one uses the extra definition `parallel`: all 2-by-2 minors of the two
   vectors vanish).
3. The reading of a set of rays as the bit mask of positions in `boxRays d H`:
   position i is in the set `T` exactly when `T.testBit i = true`, positions
   run from 0 to n-1 (`rays_length`), `T < 2 ^ n` says that `T` has no other
   bits, and `card n T` counts the positions.
4. The reading of "basis inside T" as an increasing list of d positions of
   pairwise orthogonal vectors. For d pairwise orthogonal non-zero vectors of
   Z^d this is the usual notion of an orthogonal basis.

Not trusted: the table `pool` (tied to the vectors by `adj_spec`,
`bases_sound`, `bases_complete` and the bridge theorems), the certificates, the
Python generator, the Lean compiler.

Outside the scope of this development: only the two pools above are formalised
in Lean. The other pools of the paper rely on other kinds of certificates
(`verify/drup_check.c`, `verify/verify_cert.mjs`); their status is recorded in
`results/RESULTS.md`.
