"""gen_lean.py - write a Lean 4 module that states and proves, by kernel
evaluation of two verified checkers, the exact minimum size of a
Kochen-Specker set inside a pool of integer rays.

usage: python scripts/gen_lean.py <Name> <kmin> boxfull <d> <H>
       python scripts/gen_lean.py --selftest
   Name   Lean namespace / file name (KS/<Name>.lean)
   kmin   the claimed minimum (the module proves: some set of kmin rays is KS,
          every set of at most kmin-1 rays is colorable)

The certificate trees are produced by src/gen_cert.py (search) and re-checked
in Python before the Lean file is written; Lean then checks them again with
its own checker (lean/KS/Basic.lean), whose soundness is a Lean theorem.

The module also proves (with lean/KS/Spec.lean) that its list of rays is the
pool `boxRays d H` and restates the result for the vectors themselves
(`minimum_ks_size_vectors`).  --selftest replays malformed refutations
through the Python pre-check `check_refutation_tokens`.
"""
from __future__ import annotations

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.setrecursionlimit(100000)

import pools
from gen_cert import CertDfs, check as check_tree
from ksdfs import KSDfs
from ksengine import bits, mask, popcount


def emit_cert(node):
    """Postfix tokens of a certificate node [I(list of rays), [[r, child], ...]]."""
    out = []

    def chain(children, idx):
        if idx == len(children):
            out.append(0)
            return
        r, sub = children[idx]
        emit(sub)
        chain(children, idx + 1)
        out.extend([1, r])

    def emit(nd):
        I, children = nd
        chain(children, 0)
        out.extend([2, mask(I)])

    emit(node)
    return out


def refutation(pool, T):
    """DPLL-style refutation tree for the KS set T, as postfix tokens.
    Node = ('split', b, [(v, sub), ...]) or ('conflict', b)."""
    Tm = mask(T)
    inside = [i for i, b in enumerate(pool.bases) if mask(b) & Tm == mask(b)]
    count = [0]

    bmask = [mask(b) for b in pool.bases]

    def rec(Z, ones):
        # Z = rays known to have value 0, ones = rays assumed to have value 1
        count[0] += 1
        best = None
        for i in inside:
            if bmask[i] & ones:
                continue                      # this basis already has its 1
            free = [v for v in pool.bases[i] if not (Z >> v) & 1]
            if not free:
                return ("conflict", i)
            if best is None or len(free) < len(best[1]):
                best = (i, free)
        if best is None:
            raise RuntimeError("the set is colorable: no refutation exists")
        i, free = best
        kids = []
        for v in free:
            kids.append((v, rec(Z | pool.adj[v], ones | (1 << v))))
        return ("split", i, kids)

    tree = rec(0, 0)
    out = []

    def chain(kids, idx):
        if idx == len(kids):
            out.append(0)
            return
        v, sub = kids[idx]
        emit(sub)
        chain(kids, idx + 1)
        out.extend([1, v])

    def emit(nd):
        if nd[0] == "conflict":
            out.extend([3, nd[1]])
        else:
            chain(nd[2], 0)
            out.extend([2, nd[1]])

    emit(tree)
    return out, count[0]


def decode_refutation(toks):
    """Mirror of `decodeRefu` (lean/KS/Basic.lean).  Returns (stack, consumed):
    the stack of decoded trees, last element = top, and the number of tokens
    read.  Exactly like the Lean decoder it STOPS at the first position where
    no rule applies (unknown tag, missing operand, too few trees on the stack);
    it never raises.  Trees: ("done",), ("child", v, sub, rest),
    ("split", b, kids), ("conflict", b)."""
    stack = []
    i = 0
    n = len(toks)
    while i < n:
        t = toks[i]
        if type(t) is not int or t < 0:
            break                              # not a natural number: no rule
        if t == 0:
            stack.append(("done",))
            i += 1
            continue
        if i + 1 >= n or type(toks[i + 1]) is not int or toks[i + 1] < 0:
            break                              # tags 1, 2, 3 need an operand
        x = toks[i + 1]
        if t == 1 and len(stack) >= 2:
            rest = stack.pop()
            sub = stack.pop()
            stack.append(("child", x, sub, rest))
        elif t == 2 and len(stack) >= 1:
            kids = stack.pop()
            stack.append(("split", x, kids))
        elif t == 3:
            stack.append(("conflict", x))
        else:
            break
        i += 2
    return stack, i


def check_refutation_tokens(pool, T, toks, strict=True):
    """Independent replay of the postfix refutation.  Mirrors, clause by
    clause, `refuteRoot pool T (refuOfList toks)` of lean/KS/Basic.lean:

      refuOfList  the top of the decoder stack, `done` if the stack is empty;
      refuteRoot  the root must be a `split`;
      refute      conflict b : b < #bases, basis b inside T, basis b inside Z;
                  done       : accepted;
                  child v    : the subtree is a `split` or a `conflict`
                               (Refu.isNode), the subtree is checked with
                               Z | adj[v], the rest of the chain with Z;
                  split b    : b < #bases, basis b inside T, coversAll,
                               the chain of cases is checked with Z;
      coversAll   the basis mask is below 2^n and each of its rays is in Z or
                  is one of the case rays of the chain;
      adjOf, baseOf  0 when the index is out of range (List.getD).

    With strict=True (the default, used as the pre-check of the generator) a
    malformed token stream is REJECTED: the decoder must read every token and
    leave exactly one tree.  With strict=False the function follows the Lean
    decoder literally (it checks whatever tree is on top of the stack when
    decoding stops), so it returns exactly the Boolean that Lean computes.
    The function returns False on any malformed input; it does not raise."""
    try:
        toks = list(toks)
    except TypeError:
        return False
    stack, consumed = decode_refutation(toks)
    if strict and (consumed != len(toks) or len(stack) != 1):
        return False
    root = stack[-1] if stack else ("done",)
    n = pool.n
    Tm = mask(T)
    bm = [mask(b) for b in pool.bases]
    adj = list(pool.adj)

    def base_of(b):
        return bm[b] if b < len(bm) else 0

    def adj_of(v):
        return adj[v] if v < len(adj) else 0

    def sub_mask(a, b):
        return a & b == a

    def is_node(nd):
        return nd[0] in ("split", "conflict")

    def kid_rays(nd):
        out = []
        while nd[0] == "child":
            out.append(nd[1])
            nd = nd[3]
        return out

    def covers_all(bmask, Z, rays):
        if not bmask < (1 << n):
            return False
        return all((not (bmask >> i) & 1) or (Z >> i) & 1 or i in rays for i in range(n))

    def ref(nd, Z):
        while True:                            # iterate along a chain of children
            if nd[0] == "conflict":
                b = nd[1]
                return b < len(bm) and sub_mask(base_of(b), Tm) and sub_mask(base_of(b), Z)
            if nd[0] == "done":
                return True
            if nd[0] == "child":
                v, sub, rest = nd[1], nd[2], nd[3]
                if not (is_node(sub) and ref(sub, Z | adj_of(v))):
                    return False
                nd = rest
                continue
            b, kids = nd[1], nd[2]             # split
            if not (b < len(bm) and sub_mask(base_of(b), Tm)
                    and covers_all(base_of(b), Z, kid_rays(kids))):
                return False
            nd = kids

    return root[0] == "split" and ref(root, 0)


def encode_refutation(tree):
    """Postfix tokens of a refutation tree in the tuple form used by
    decode_refutation (the inverse of the decoder on well-formed trees)."""
    out = []

    def emit(nd):
        if nd[0] == "done":
            out.append(0)
        elif nd[0] == "child":
            emit(nd[2])
            emit(nd[3])
            out.extend([1, nd[1]])
        elif nd[0] == "split":
            emit(nd[2])
            out.extend([2, nd[1]])
        else:
            out.extend([3, nd[1]])

    emit(tree)
    return out


def selftest():
    """The malformed refutations of lean/KS/Tests.lean, replayed in Python:
    the pre-check must reject what the Lean checker rejects and accept what it
    accepts.  usage: python scripts/gen_lean.py --selftest"""
    from types import SimpleNamespace
    # the pools of lean/KS/Tests.lean, three mutually orthogonal rays each:
    # `one` has the single basis {0,1,2} (every set of its rays is colourable);
    # `tri` lists the three edges as bases (its full set {0,1,2} is NOT
    # colourable: one ray of each edge needs two rays, and those are orthogonal)
    one = SimpleNamespace(n=3, adj=[6, 5, 3], bases=[(0, 1, 2)])
    tri = SimpleNamespace(n=3, adj=[6, 5, 3], bases=[(0, 1), (0, 2), (1, 2)])
    # two rays 0 and 1, orthogonal; bases {0} and {1, 2}: basis 1 has the mask 6,
    # which is not below 2^n = 4 (ray 2 is outside the table)
    wide = SimpleNamespace(n=2, adj=[2, 1], bases=[(0,), (1, 2)])
    done = ("done",)
    full = [0, 1, 2]

    def chain(*kids):
        nd = done
        for v, sub in reversed(kids):
            nd = ("child", v, sub, nd)
        return nd

    enc = encode_refutation
    good = ("split", 0, chain((0, ("conflict", 2)), (1, ("conflict", 1))))
    cases = [
        # (name, pool, T, tokens, value of the Lean checker, value in strict mode)
        ("correct refutation of the triangle", tri, full, enc(good), True, True),
        ("children are bare `done` (the historical malformed refutation)", one, full,
         enc(("split", 0, chain((0, done), (1, done), (2, done)))), False, False),
        ("the same on the triangle", tri, full,
         enc(("split", 0, chain((0, done), (1, done)))), False, False),
        ("child subtree is a chain, not a split or conflict", tri, full,
         enc(("split", 0, chain((0, chain((2, ("conflict", 2)))), (1, ("conflict", 1))))), False, False),
        ("basis index out of range in a split", tri, full, enc(("split", 3, done)), False, False),
        ("basis index out of range in a conflict", tri, full,
         enc(("split", 0, chain((0, ("conflict", 7)), (1, ("conflict", 7))))), False, False),
        ("a ray of the split basis is not covered", tri, full,
         enc(("split", 0, chain((0, ("conflict", 2))))), False, False),
        ("conflict on a basis whose rays are not all 0", tri, full,
         enc(("split", 0, chain((0, ("conflict", 0)), (1, ("conflict", 1))))), False, False),
        ("root is a conflict", tri, full, [3, 0], False, False),
        ("split basis not inside T", tri, [0, 2], enc(good), False, False),
        ("conflict basis not inside T", tri, [0, 1], enc(good), False, False),
        ("basis mask not below 2^n (the bound in coversAll)", wide, full,
         enc(("split", 0, chain((0, ("split", 1, done))))), False, False),
        ("empty token list", tri, full, [], False, False),
        ("unknown tag", tri, full, [7], False, False),
        ("child with an empty stack", tri, full, [1, 0], False, False),
        ("operand missing", tri, full, [0, 2], False, False),
        ("negative token", tri, full, [-1], False, False),
        ("token that is not an integer", tri, full, ["2", 0], False, False),
        # decoding stops with a correct refutation on top of the stack: Lean
        # checks that tree and accepts; the strict pre-check refuses the stream
        ("correct tree followed by an unknown tag", tri, full, enc(good) + [9], True, False),
        ("correct tree above a leftover tree", tri, full, [0] + enc(good), True, False),
    ]
    bad = 0
    for name, pool, T, toks, want_lean, want_strict in cases:
        got_lean = check_refutation_tokens(pool, T, toks, strict=False)
        got_strict = check_refutation_tokens(pool, T, toks)
        ok = (got_lean, got_strict) == (want_lean, want_strict)
        bad += not ok
        print(f"  {'ok  ' if ok else 'FAIL'} lean={got_lean!s:5} strict={got_strict!s:5} {name}")
    ok = check_refutation_tokens(tri, full, None) is False
    bad += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} tokens that are not a list are refused")
    print("selftest:", "all ok" if not bad else f"{bad} FAILED")
    return bad == 0


def lean_list(items, per_line=8, indent="  "):
    lines = []
    for s in range(0, len(items), per_line):
        lines.append(indent + ", ".join(items[s:s + per_line]))
    return "[\n" + ",\n".join(lines) + "]"


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--selftest":
        raise SystemExit(0 if selftest() else 1)
    name = sys.argv[1]
    kmin = int(sys.argv[2])
    kind = sys.argv[3]
    args = sys.argv[4:]
    if kind != "boxfull":
        raise SystemExit("only boxfull is supported")
    d, H = int(args[0]), int(args[1])
    quiet = lambda *a: None
    pool = pools.box_pool(d, H, log=quiet)
    n = pool.n
    t0 = time.time()
    # 1. a KS set with kmin rays (exhaustive search finds one)
    dfs = KSDfs(pool, kmin, sym=None, log=quiet)
    res = dfs.run()
    if res["status"] != "found" or len(res["ks"]) != kmin:
        raise SystemExit(f"no KS set with exactly {kmin} rays found: {res['status']}")
    ks = sorted(res["ks"])
    assert pool.is_ks(ks)
    refu, refu_nodes = refutation(pool, ks)
    assert check_refutation_tokens(pool, ks, refu)
    # 2. certificate that every set of at most kmin-1 rays is colorable
    cd = CertDfs(pool, kmin - 1, sym=None, log=quiet)
    tree = cd.tree(0, [])
    cert = {"k": kmin - 1, "rays": [list(r) for r in pool.rays], "d": d,
            "adj": [sorted(bits(a)) for a in pool.adj], "bases": [list(b) for b in pool.bases], "tree": tree}
    ok, nodes = check_tree(cert)
    assert ok
    toks = emit_cert(tree)
    print(f"{name}: pool {n} rays, {len(pool.bases)} bases; KS set {kmin} rays (refutation {refu_nodes} nodes, "
          f"{len(refu)} tokens); certificate {nodes} nodes, {len(toks)} tokens; {time.time()-t0:.1f}s")

    hexs = lambda m: hex(m)
    L = []
    L.append("/-")
    L.append(f"KS/{name}.lean - generated by scripts/gen_lean.py {' '.join(sys.argv[1:])}")
    L.append("")
    L.append(f"Pool: all rays of Z^{d} with a representative of max-norm at most {H} ({n} rays,")
    L.append(f"{len(pool.bases)} bases).  Proved here by kernel evaluation of the checkers of KS/Basic.lean:")
    L.append(f"  * a set of {kmin} rays that is not colourable (a Kochen-Specker set);")
    L.append(f"  * every set of at most {kmin-1} rays is colourable.")
    L.append(f"The last four theorems restate this for the vectors themselves: `rays` is the pool")
    L.append(f"`boxRays {d} {H}` of KS/Spec.lean, which lists every ray of the box exactly once, and")
    L.append(f"colourability is `VColorable` (dot products only).")
    L.append("Do not edit by hand.")
    L.append("-/")
    L.append("import KS.Spec")
    L.append("")
    L.append("set_option maxRecDepth 1000000")
    L.append("set_option maxHeartbeats 0")
    L.append("")
    L.append(f"namespace KS.{name}")
    L.append("")
    L.append("/-- The rays, as primitive integer vectors (first non-zero entry positive). -/")
    L.append("def rays : List (List Int) := " + lean_list(["[" + ", ".join(str(c) for c in r) + "]" for r in pool.rays], 6))
    L.append("")
    L.append("/-- Orthogonality table and list of bases of the pool, as bit masks. -/")
    L.append("def pool : Pool where")
    L.append(f"  n := {n}")
    L.append("  adj := " + lean_list([hexs(a) for a in pool.adj], 6, "    "))
    L.append("  bases := " + lean_list([hexs(mask(b)) for b in pool.bases], 6, "    "))
    L.append("")
    L.append("/-- The table agrees with the vectors: bit `j` of `adj[i]` is set iff `i ≠ j` and the")
    L.append("dot product of rays `i` and `j` vanishes. -/")
    L.append("theorem adj_spec : adjMatches pool rays = true := by decide +kernel")
    L.append("")
    L.append(f"/-- Every listed basis consists of {d} mutually orthogonal rays. -/")
    L.append(f"theorem bases_sound : basesAreCliques pool {d} = true := by decide +kernel")
    L.append("")
    L.append(f"/-- Every set of {d} mutually orthogonal rays of the pool is listed. -/")
    L.append(f"theorem bases_complete : basesComplete pool {d} = true := by decide +kernel")
    L.append("")
    L.append(f"/-- Search-tree certificate ({nodes} nodes) in postfix form. -/")
    L.append("def certToks : List Nat := " + lean_list([hexs(t) for t in toks], 12))
    L.append("")
    L.append(f"theorem cert_ok : checkRoot pool {kmin-1} (certOfList certToks) = true := by decide +kernel")
    L.append("")
    L.append(f"/-- Every set of at most {kmin-1} rays of the pool has a Kochen-Specker colouring. -/")
    L.append(f"theorem small_sets_colorable : ∀ T, T < 2 ^ {n} → card {n} T ≤ {kmin-1} → Colorable pool T :=")
    L.append(f"  small_sets_colorable_root pool {kmin-1} _ cert_ok")
    L.append("")
    L.append(f"/-- A set of {kmin} rays of the pool (as a mask). -/")
    L.append(f"def ksSet : Nat := {hexs(mask(ks))}")
    L.append("")
    L.append(f"/-- Refutation tree ({refu_nodes} nodes) in postfix form. -/")
    L.append("def refuToks : List Nat := " + lean_list([str(t) for t in refu], 16))
    L.append("")
    L.append("theorem refu_ok : refuteRoot pool ksSet (refuOfList refuToks) = true := by decide +kernel")
    L.append("")
    L.append(f"theorem ksSet_lt : ksSet < 2 ^ {n} := by decide +kernel")
    L.append("")
    L.append(f"theorem ksSet_card : card {n} ksSet = {kmin} := by decide +kernel")
    L.append("")
    L.append(f"/-- The {kmin}-ray set has no Kochen-Specker colouring: it is a Kochen-Specker set. -/")
    L.append("theorem ksSet_not_colorable : ¬ Colorable pool ksSet :=")
    L.append("  not_colorable_of_refute_root pool ksSet _ refu_ok")
    L.append("")
    L.append(f"/-- The minimum size of a Kochen-Specker set inside the pool is exactly {kmin}. -/")
    L.append(f"theorem minimum_ks_size :")
    L.append(f"    (∃ T, T < 2 ^ {n} ∧ card {n} T = {kmin} ∧ ¬ Colorable pool T) ∧")
    L.append(f"    (∀ T, T < 2 ^ {n} → card {n} T ≤ {kmin-1} → Colorable pool T) :=")
    L.append("  ⟨⟨ksSet, ksSet_lt, ksSet_card, ksSet_not_colorable⟩, small_sets_colorable⟩")
    L.append("")
    L.append("/-! ### The same result for the vectors themselves (KS/Spec.lean) -/")
    L.append("")
    L.append(f"/-- The list `rays` is the pool B({d},{H}): the primitive integer vectors of length {d} with")
    L.append(f"entries in -{H}..{H} whose first non-zero entry is positive, in lexicographic order. -/")
    L.append(f"theorem rays_eq : rays = boxRays {d} {H} := by decide +kernel")
    L.append("")
    L.append(f"/-- The pool B({d},{H}) has {n} rays. -/")
    L.append(f"theorem rays_length : (boxRays {d} {H}).length = {n} := by decide +kernel")
    L.append("")
    L.append(f"/-- Every ray of Z^{d} with a representative of max-norm at most {H} is listed exactly once:")
    L.append(f"each non-zero integer vector of length {d} with entries in -{H}..{H} is parallel to exactly one")
    L.append(f"vector of `boxRays {d} {H}`. -/")
    L.append(f"theorem boxRays_exact :")
    L.append(f"    ∀ v : List Int, v.length = {d} → (∀ a, a ∈ v → -{H} ≤ a ∧ a ≤ {H}) → (∃ a, a ∈ v ∧ a ≠ 0) →")
    L.append(f"      (boxRays {d} {H}).countP (fun u => parallel u v) = 1 :=")
    L.append(f"  countP_parallel_of_boxExact (d := {d}) (H := {H}) (by decide +kernel)")
    L.append("")
    L.append(f"/-- The minimum size of a Kochen-Specker set inside B({d},{H}) is exactly {kmin}, stated with the")
    L.append(f"vectors only.  A set of rays is the bit mask `T` of their positions in `boxRays {d} {H}`;")
    L.append(f"`VColorable` speaks about dot products of the listed vectors and nothing else. -/")
    L.append(f"theorem minimum_ks_size_vectors :")
    L.append(f"    (∃ T, T < 2 ^ {n} ∧ card {n} T = {kmin} ∧ ¬ VColorable (boxRays {d} {H}) {d} T) ∧")
    L.append(f"    (∀ T, T < 2 ^ {n} → card {n} T ≤ {kmin-1} → VColorable (boxRays {d} {H}) {d} T) := by")
    L.append("  rw [← rays_eq]")
    L.append("  obtain ⟨⟨T, hT, hcard, hnot⟩, hall⟩ := minimum_ks_size")
    L.append("  exact ⟨⟨T, hT, hcard, fun h => hnot")
    L.append("      (colorable_of_vcolorable adj_spec bases_sound bases_complete T hT h)⟩,")
    L.append("    fun T hT hcard =>")
    L.append("      vcolorable_of_colorable adj_spec bases_sound bases_complete T hT (hall T hT hcard)⟩")
    L.append("")
    L.append(f"end KS.{name}")
    L.append("")
    path = os.path.join(ROOT, "lean", "KS", f"{name}.lean")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print("wrote", path, os.path.getsize(path), "bytes")
    print("KS set rays:", [pool.rays[v] for v in ks])


if __name__ == "__main__":
    main()
