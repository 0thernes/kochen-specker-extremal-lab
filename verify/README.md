# verify — independent checker for the colorability certificates

`verify_cert.mjs` is a small, dependency-free JavaScript program (Node 22 or
newer; developed on Node 25) that checks the certificate files in `../results`
and decides Kochen–Specker colorability of explicit ray sets by exhaustive
backtracking. It uses no SAT solver and no code from the search program: it was
written from the specification reproduced below, without reading the Python
sources in `../src` or `../scripts`. Its only inputs are the JSON files.

It is a second implementation in a different language, not a formal proof. For
the pools B(3, 2) and B(4, 1) the Lean 4 theorems are the authoritative
statements of the minimum; the status of every result is recorded in
`../results/RESULTS.md`. This checker exists so that the certificates can be
re-checked quickly by anyone with Node.

## Usage

```
node verify_cert.mjs <cert.json> [<cert2.json> ...] [--out summary.json]
node verify_cert.mjs --ks <rays.json> [--require-critical] [--out summary.json]
node test_verify.mjs            # about half a minute
node test_verify.mjs --full     # exhaustive version of the largest sweep, several minutes
```

Certificate mode prints one JSON summary per file (file name, SHA-256 of the
file bytes, `d`, `k`, number of rays, orthogonal pairs, bases, tree nodes,
verdict, and the first failed check if any) and exits 0 only if every file
passes.

`--ks` mode prints the number of orthogonal pairs and bases, whether the set is
colorable, and whether it is critical. It exits 0 only if the set is a KS set
(not colorable); with `--require-critical` it must also be critical.

## Definitions

A pool is a list of integer vectors (rays) in dimension `d`. Two rays are
orthogonal when their integer dot product is 0. A basis is a set of `d` mutually
orthogonal rays. A set `S` of rays is colorable when some `f : S -> {0,1}` has

1. no two orthogonal rays of `S` both with value 1, and
2. a ray with value 1 in every basis contained in `S`.

A set that is not colorable is a Kochen–Specker (KS) set. A KS set is critical
when removing any single ray leaves a colorable set.

## Certificate format and what a certificate claims

A certificate is a JSON object with keys `d`, `k`, `rays` (integer vectors),
`adj` (for each ray, the indices of the rays orthogonal to it), `bases` (the
`d`-tuples of ray indices that form bases) and `tree`. A tree node is
`[I, children]`, where `I` is a list of ray indices and `children` is a list of
`[r, childNode]` with `r` an index into `bases`. Other keys are ignored.

Claim: **every set of at most `k` rays of the pool is colorable.**

## Checking rule

A node is checked in a state `(S, F)`, where `S` is a set of rays and `F` a list
of basis indices. The root is checked in the state `S = {}`, `F = []`.

0. If some basis of `F` lies inside `S`, the node is accepted.
1. The rays of `I` are pairwise non-orthogonal.
2. Every basis `b` of the pool that contains no ray of `I` satisfies at least
   one of: (a) `|S ∪ b| > k`; (b) some basis of `F` lies inside `S ∪ b`;
   (c) `b` is the basis `r_j` of one of the children.
3. For each child `j`, in order, the child node is accepted in the state
   `(S ∪ r_j, F + [r_1, ..., r_{j-1}])`.

Why this proves the claim. By induction on the tree, an accepted node in state
`(S, F)` shows that every set `T` with `S ⊆ T`, `|T| ≤ k`, containing no basis of
`F`, is colorable. If a basis of `F` lies in `S` there is no such `T` (rule 0).
Otherwise, if `T` contains a child basis, take the first one, `r_j`: then `T`
contains `S ∪ r_j` and none of `r_1, ..., r_{j-1}`, so the child covers it
(rule 3). If `T` contains no child basis, give value 1 to the rays of `I` that
lie in `T` and 0 to the rest: no two of them are orthogonal (rule 1), and a
basis `b ⊆ T` with no ray of `I` is impossible, because (a) would give
`|T| ≥ |S ∪ b| > k`, (b) would put a basis of `F` inside `T`, and (c) would make
`b` a child basis inside `T` (rule 2). At the root this is the claim.

## What the verifier checks, in order

1. **Rays.** `d` is an integer ≥ 2; every ray is a vector of `d` integers that
   JSON parsed exactly (`Number.isSafeInteger`); no ray is zero; no two rays
   are proportional. Orthogonality is recomputed from the vectors in exact
   `BigInt` arithmetic and each `adj[i]` must equal, as a set, the computed
   neighbours of ray `i`.
2. **Bases.** All sets of `d` mutually orthogonal rays are enumerated by clique
   search on the recomputed orthogonality relation. The listed `bases` must be
   exactly this set: each entry a `d`-tuple of distinct, mutually orthogonal
   rays, no entry listed twice, none missing.
3. **Tree.** A structural pass checks every node and every index and counts the
   nodes. The tree is then replayed by the rule above, using only the recomputed
   orthogonality relation and the verified basis list.
4. **Summary.** The JSON summary is printed (and returned by the exported
   functions `verifyCertFile` / `verifyCertObject`); the exit status is non-zero
   unless every check passed.

The verifier stops at the first failed check and reports where it failed, for
example `rule 2 fails at node at path [0,0,0] (|S|=9, |F|=0): basis #5 {2,4,20} ...`.
The path is the list of child positions from the root.

## Colorability search (`--ks`)

`decideColorable` branches on a basis that has no ray of value 1 yet and the
fewest free rays: one of its free rays must take value 1, which forces its
orthogonal neighbours to 0; a ray whose value-1 branch has been exhausted is set
to 0 for the remaining branches. The search is exhaustive. A coloring that it
finds is re-checked directly against the two conditions. In `--ks` mode the
verdict is cross-checked by a second, differently organised search (rays
assigned one at a time in file order). Criticality is decided by repeating the
search on each of the sets obtained by deleting one ray.

## Results (2026-11-09 and 2026-11-10, Node v25.8.2)

| file | d | k | rays | orthogonal pairs | bases | tree nodes | verdict |
|---|---|---|---|---|---|---|---|
| `cert_box3_H2_k30.json` | 3 | 30 | 49 | 138 | 26 | 255 | PASS |
| `cert_box4_H1_k17.json` | 4 | 17 | 40 | 220 | 32 | 509 | PASS |
| `cert_box3_H3_k30.json` (the 97-ray core of the 145-ray pool) | 3 | 30 | 97 | 282 | 50 | 11247 | PASS |
| `cert_box3_H3full_k30.json` (the whole 145-ray pool) | 3 | 30 | 145 | 546 | 50 | 11330 | PASS |

| file | d | rays | orthogonal pairs | bases | verdict |
|---|---|---|---|---|---|
| `ks31_box3_H2.json` | 3 | 31 | 71 | 17 | KS set (not colorable), critical: all 31 one-ray deletions are colorable |

SHA-256 of the files as checked:

```
40737e825fcfd72d2d94547c8c4a543d4b51631a4197dedb42e35e208160d29f  cert_box3_H2_k30.json
6b955e6cbefaf4cea9878d942cb3629c2f80f7a1504860ad6cd147f1ebe3e0a4  cert_box4_H1_k17.json
97a56e1a5c34676fa1d480352dd629f1bbce8614de71aa123263bb479189b048  cert_box3_H3_k30.json
2bb824dab2d8045fdd02c949ce6088944d505f4e59c256fbdca8e686e8d2a88a  cert_box3_H3full_k30.json
10031b3bdc4b2db3778ef3b0028d89f04f9b5d87edb582d09c5c0590ca6a7736  ks31_box3_H2.json
```

The machine-readable record of the last test run is
`../results/verify_summary.json` (`verify_summary_full.json` for `--full`).

## Tests (`test_verify.mjs`)

(a) The four certificates pass and the KS file is a critical KS set. A second,
deliberately literal implementation of the rule inside the test file (the
"reference replay": plain `Set`s, fresh copies of `S` and `F` at every node,
`Number` dot products) accepts the same four certificates.

(b) Negative tests. Corrupted in-memory copies must be rejected:

- the four required corruptions of the 49-ray certificate: one child deleted
  (two positions), one ray index changed inside an `I` (once so that rule 1
  breaks, once so that `I` stays pairwise non-orthogonal and rule 2 breaks),
  `k` raised by one, one basis dropped from the list (two positions);
- `k` raised by one in the other two certificates;
- wrong `adj` entries, a changed ray coordinate, proportional rays, a zero ray,
  a non-integer coordinate, a bogus or duplicated basis, an empty tree, an empty
  root `I`, out-of-range indices, a wrong `d`, a missing key, a malformed node;
- sweeps over every position: every single child deleted (254 mutants of the
  49-ray certificate and 508 of the 40-ray one, all rejected), all children of
  one internal node removed (176, all rejected), every single basis dropped
  (26 and 32, all rejected), every single `adj` entry flipped (2352, all
  rejected);
- the command line returns exit status 1 for a corrupted file, truncated JSON
  and a missing file, and for `--ks` on a colorable set.

Two sweeps contain mutants that the verifier accepts, and should accept:

- changing one ray index of an `I` to another ray. In the exhaustive run
  (`--full`) 586 of the 121224 single-index changes of the 49-ray certificate
  are accepted and 120638 rejected. An accepted mutant is still a valid
  certificate: the replacement ray is non-orthogonal to the rest of `I` and hits
  every basis that the replaced ray was needed for, so by the argument above it
  still proves the claim;
- swapping two adjacent children (36 of 78 accepted): the order of children only
  matters when a later child relies on an earlier sibling's basis through `F`.

For these sweeps the test compares the verifier with the reference replay:
every accepted mutant must be accepted by the reference and a fixed sample of
the rejected ones must be rejected by it. There were no disagreements.

(c) Cross-checks of the colorability search:

- the 18-ray set of Cabello, Estebaranz and García-Alcaine in dimension 4 is
  found non-colorable and critical, and brute force over all 2^18 assignments
  agrees;
- the two backtracking searches and brute force agree on 140 subsets of the
  pools (12 to 21 rays, 20 of them non-colorable);
- the 31-ray set of `ks31_box3_H2.json` is, up to proportionality, a subset of
  the 49-ray, the 97-ray and the 145-ray pool, and the 18-ray set is a subset of
  the 40-ray pool. The certified values of `k` (30, 30, 30, 17) are therefore the
  largest possible for these pools, which is also why raising `k` by one must
  be, and is, rejected;
- 300 random subsets of exactly `k` rays of each pool are colorable.

## Limits

- The verifier checks a certificate against the rays listed in the same file.
  It does not check that those rays are the pool a paper describes (for example
  "all integer vectors with entries of absolute value at most 2, up to sign and
  scale"). That identification has to be made separately; the ray count and the
  SHA-256 pin down which file was checked.
- A PASS depends on the correctness of this program and of the Node runtime.
  The checks are simple and the tree replay is duplicated by the reference
  replay in the tests, but neither is machine-verified.
- Ray coordinates must be safe integers (absolute value below 2^53) so that
  `JSON.parse` is exact; arithmetic on them is exact (`BigInt`).
- Recursion depth of the replay equals the depth of the tree (at most 16 in the
  files above). A tree too deep for the JavaScript stack is reported as a
  failure, never as a pass.
