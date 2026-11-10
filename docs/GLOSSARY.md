# Glossary

Kochen-Specker Extremal Lab, version 1.0.0. Plain definitions of the terms used in the
[README](../README.md), the [paper](../paper/ks-minimum.md), the register
[results/RESULTS.md](../results/RESULTS.md) and the programs. The exact statements and proofs are in
[paper/PROOFS.md](../paper/PROOFS.md).

## Geometry

| Term | Meaning in this project |
|---|---|
| Ray | A one-dimensional subspace: a line through the origin, a direction without a sense. It is written as a non-zero vector; vectors that are multiples of each other are the same ray. |
| Dimension d | The dimension of the space the rays live in. Here d is 3, 4 or 5 for the exact results and up to 8 for the randomised searches. |
| Orthogonal | Two rays are orthogonal when their inner product is zero (they are at right angles). In the integer pools this is an integer dot product; in the root-of-unity pools it is decided exactly, by reducing the inner product modulo a cyclotomic polynomial. No floating-point arithmetic is involved. |
| Orthogonal pair | Two orthogonal rays of a set. The 31-ray set has 71 of them. |
| Basis | A set of d mutually orthogonal rays of the pool. In dimension three a basis is three rays at right angles to each other. Other papers say "context". |
| Pool | A finite set of rays fixed in advance. All questions in this project are about subsets of a pool. A pool result says nothing about rays outside the pool. |
| B(d, H) | The pool of all rays of Zᵈ that have a representative whose coordinates are integers of absolute value at most H. B(3, 2) has 49 rays, B(4, 1) has 40, B(5, 1) has 121. Called `box` in the programs. |
| U(d, N) | The pool of all rays of Cᵈ whose entries are 0 or N-th roots of unity. U(3, 6) has 57 rays. Called `roots` in the programs. |
| Coordinate axis | A ray with exactly one non-zero coordinate, written e0, e1, and so on. |
| E8 root rays | The 120 rays spanned by the 240 roots of the E8 lattice, in dimension 8. Used only in the randomised searches. |
| Symmetry of a pool | A permutation of the rays of the pool that preserves orthogonality. For B(d, H): permutations of the coordinates combined with sign changes ("signed coordinate permutations"). For U(3, N): coordinate permutations, multiplication of single coordinates by N-th roots of unity, and complex conjugation. |
| Orbit | The set of all images of one set of rays under the symmetries of the pool. "Exactly 6, one orbit" means there are six sets and each is an image of any other. |

## Colorings and Kochen-Specker sets

| Term | Meaning in this project |
|---|---|
| Coloring | A labelling f of the rays of a set S with 0 or 1 such that (i) no two orthogonal rays of S both get 1 and (ii) every basis contained in S has a ray with 1. By (i), such a basis then has exactly one ray with 1. |
| Colorable | A set S is colorable when it has a coloring. Subsets of colorable sets are colorable. |
| Kochen-Specker set (KS set) | A set of rays that is not colorable. Only the rays of the set are counted. Orthogonal pairs constrain the labelling whether or not they lie in a basis inside the set. |
| Critical KS set | A KS set all of whose proper subsets are colorable: removing any ray destroys the property. Every KS set contains a critical one, so the minimum size is attained by a critical set. |
| Minimum (in a pool) | The smallest number of rays of a KS set contained in the pool. "Minimum 31" means: some 31-ray subset of the pool is a KS set and every subset with at most 30 rays is colorable. |
| Record | The smallest KS set known in a given dimension without restriction to a pool (31 in dimension three, 18 in dimension four, 29 in dimension five). No result of this project is below a record. |
| Smallest published set of that kind | The comparison used for each pool: the smallest KS set in the literature made of rays of the same kind as the pool. For the root-of-unity pools of dimension three this is the 33-ray complex set of Cabello and of Pavičić; 33 is not the record of dimension three (that is 31), and what the cited papers single out about that set is its number of bases (14). |
| Lower bound (general) | A proved statement "every KS set in dimension d has at least n rays", for all rays, not a pool. In dimension three it is 24; this project does not change it. |

## The method

| Term | Meaning in this project |
|---|---|
| Independent set | A set of rays of the pool no two of which are orthogonal. Giving 1 to its rays and 0 to all others never violates rule (i). |
| Miss(I) | For an independent set I: the bases of the pool that contain no ray of I. |
| Cut (coloring cut) | The condition "S contains at least one basis of Miss(I)". By Lemma 1 every KS set satisfies the cut of every independent set I. A cut is verified from I alone: check that I is independent and recompute Miss(I). |
| Witness (of a cut) | The independent set I from which a cut is recomputed. The cut files in `results/` store each cut with its witness. |
| Correction set | A set of rays whose removal makes a set colorable. Corollary 2: if C is a colorable subset of the pool, every KS set contains a ray outside C. Used for Lemma 7. |
| Conditions (C1), (C2) | Two properties of every ray v of a critical KS set T (Lemma 3): (C1) v lies in a basis contained in T; (C2) v is orthogonal to at least d rays of T. |
| Core | What is left of a pool after repeatedly deleting every ray that lies in no basis or has fewer than d orthogonal partners among the remaining rays. Smallest KS sets of a pool lie in its core (Corollary 4). B(3, 3) has 145 rays and a core of 97. |
| Candidate problem | For a bound k: find a set of at most k rays that satisfies (C1), (C2), all cuts collected so far and, where used, the symmetry and case constraints. Variables: one per ray ("chosen") and one per basis ("all its rays chosen"). |
| Counterexample-guided search | Solve the candidate problem; if the solution is colorable, turn a coloring into a new cut that the solution violates, add it (with its images under the symmetries), and repeat. If the candidate problem becomes infeasible, the pool has no KS set with at most k rays. |
| Bound k | The size limit of a run. To prove "minimum 31" the run uses k = 30 and must end with "infeasible". |
| Normal form | A standard position that every set can be moved to by a symmetry (Lemma 6): coordinates sorted by how many chosen rays use them, and e0 − ej chosen only if e0 + ej is. It lets the search look at one representative per symmetry class. Also called symmetry breaking. |
| Case | A restriction of the search to sets containing some named rays and avoiding others. For B(5, 1) the three cases are: exactly the axes e0, e1, e2; exactly e0, e1, e2, e3; all five axes. Written `in:0,1,2;out:3,4` in the commands. |
| Cube | One of the 81 sub-cases into which the five-axis case of B(5, 1) is split, by the state of each of the four pairs (e0 + ej, e0 − ej): neither ray chosen, only the first, or both. 3⁴ = 81. |
| Search tree (engine C) | An exhaustive search: each node holds an independent set and has one child for each basis that set misses and that can still be added within the bound. A node without children is closed because its independent set colors every remaining admissible set. |
| Tree certificate | The trace of such a search, stored as a JSON file (`results/cert_*.json`). It claims "every set of at most k rays of the pool is colorable" and is replayed by a checker using the rule of Lemma 5. |
| Refutation tree | The certificate for the opposite kind of statement, "this one set is not colorable": a case tree on which ray of a basis has value 1. Used in the Lean modules for the 31-ray and the 18-ray set. |
| Exhaustive tree search | A complete run of the tree search without a stored certificate (row A4 of the register). |
| Enumeration | Listing all KS sets of minimum size in a pool with engine A: the candidate problem is solved again and again, each found set being excluded together with its whole orbit, until it is infeasible (`scripts/enumerate_min.py`). |
| Uniqueness run | The proof-checked confirmation of an enumeration (`scripts/certify_unique.sh`; register, section C.1): engine B solves the candidate problem for k = minimum with one extra clause per listed KS set that excludes it. "Unsatisfiable", with a checked proof, means that every KS set with at most k rays is one of the listed sets (for B(d, H), where the formula contains symmetry breaking: an image of a listed set). The run also re-proves the minimum. |
| Closure check | Part of a uniqueness run for B(d, H): the encoder verifies that the list of excluded sets is closed under the signed coordinate permutations, and stops otherwise. Without it, "every minimum set is an image of a listed one" would not give the count. |
| Positive control | A run that must find something, made to show that a search which found nothing was able to find. Here: with the bound raised to 29 the three-axis and the four-axis case of B(5, 1) each find a 29-ray KS set, and with bound 31 one cube of the five-axis case finds a 31-ray KS set with all five axes; a unit test (`tests/test_cnf.py`, class `FiveAxisControl`) plants that set in the formula of its cube. |
| Randomised search | A walk on critical KS sets that removes a few rays and repairs the set (`src/kslocal.py`, `src/hunt.py`). It can find small sets; it proves nothing about the minimum. Status word: "search only". |
| Master hypergraph | In the papers of Pavičić and Megill: the hypergraph of all bases formed by the vectors with components from a small set. Where one exists for the same vectors, the core of our pool has the same numbers of rays and bases. |

## Engines and certificates

| Term | Meaning in this project |
|---|---|
| Engine A | The counterexample-guided search with the CP-SAT solver of Google OR-Tools solving the candidate problem (`src/ksmaster.py`). Its answer "infeasible" is a solver answer without a proof. |
| Engine B | The final candidate problem encoded from scratch as a CNF formula, with every cut re-verified from its witness, and solved by the SAT solver Glucose 4.1 through PySAT (`src/ks_cnf.py`; incremental variant `src/ks_satcegar.py`). An "unsatisfiable" answer comes with a DRUP proof. Where the register names CaDiCaL, the formula of engine B was solved by that solver. |
| Glucose | The SAT solver of engine B (version 4.1, bundled with PySAT). It writes DRUP proofs. On the formula of U(3, 24) it ran out of its 32-bit clause memory. |
| CaDiCaL | A second SAT solver (version 1.9.5, bundled with PySAT; solver name `cadical195`; MIT licence), used where Glucose ran out of memory (row A7) and as a check of Glucose's answers (row A9); its proofs for row A7 and for the four-axis case of row A9 were checked by `drup_check`. It writes its proof in the binary DRAT format, which `scripts/prove_cnf.py` converts to text for `drup_check`. |
| Second solver | Status word of the register: the formula file of engine B was also solved by CaDiCaL 1.9.5 (`scripts/second_solver.py` for the answer only, `scripts/prove_cnf.py` with a proof). Both solvers read the same file, so their agreement checks the solvers against each other, not the encoding. |
| Engine C | The exhaustive tree search (`src/ksdfs.py`) and its certificates (`src/gen_cert.py`). |
| CP-SAT | A constraint solver from OR-Tools. Trusted only for results marked "A". |
| SAT solver, CDCL | A program that decides whether a Boolean formula can be satisfied. CDCL (conflict-driven clause learning) is the standard algorithm; Glucose and CaDiCaL are CDCL solvers. |
| CNF | Conjunctive normal form: a Boolean formula written as a list of clauses, each clause an "or" of variables or negated variables. The input format of SAT solvers. |
| Two-sided sequential counter | The way counting constraints ("at most k rays", "at least d partners") are written in CNF here. Two-sided means each auxiliary variable is equivalent to "at least j of the first i inputs are true", so the constraint is encoded exactly. |
| Unsatisfiable | No assignment satisfies the formula. For the formula of a candidate problem this means: no critical KS set with at most k rays (in normal form, in the given case). |
| DRUP proof | A list of clauses ("lemmas") produced by the solver, each of which follows from the earlier ones by unit propagation, ending with the empty clause. Checking it confirms unsatisfiability without trusting the solver. DRUP stands for "delete reverse unit propagation"; the files have the extension `.drat` because DRAT is the more general format that contains DRUP. |
| Lemma (in a proof file) | One learned clause of a DRUP proof. "2 447 lemmas checked" is the number of such clauses the checker verified. |
| `drup_check` | The proof checker of this project, `verify/drup_check.c`: a forward reverse-unit-propagation checker of about 310 lines of C. It reads its input strictly (every token a decimal integer of absolute value at most 10^8; the formula must have a "p cnf" line that matches its clauses) and prints `s VERIFIED` when it accepts a proof. Exit status 0 accepted, 1 rejected, 2 unreadable input or out of memory. It is tested, not formally verified. |
| Proof-checked | Status word: the DRUP proof of the run was accepted by `drup_check`. |
| VERIFIED | Verdict in sections C and D of the register: the proof was accepted by `drup_check` (the checker printed `s VERIFIED` and ended with exit status 0). |
| `verify_cert.mjs` | The independent JavaScript verifier for tree certificates, written from the specification without reading the Python sources. It recomputes orthogonality and all bases from the integer vectors before replaying the tree. |
| Tree (status word) | The tree certificate was replayed by `verify_cert.mjs`. |
| Lean 4 | A proof assistant. Statements and proofs are written in its language and checked by a small trusted program, the kernel. |
| Kernel-checked | Accepted by the Lean kernel. In this project the certificate checks are evaluated by the kernel itself (`decide +kernel`), not by compiled code (`native_decide` is not used). |
| Lean (status word) | The statement is a Lean theorem checked by the kernel. |
| Axioms | Assumptions a Lean proof depends on. The theorems here depend on at most `propext`, `Classical.choice` and `Quot.sound`, the three standard axioms of Lean; `lake env lean KS/Audit.lean` prints them for 26 theorems. |
| `sorry` | The Lean keyword for a missing proof. The Lean sources contain none. |
| Mathlib | The large community library of mathematics for Lean. This project does not use it. |
| Data module | A generated Lean file (`lean/KS/Box3H2.lean`, `lean/KS/Box4H1.lean`) that lists the vectors, the orthogonality table, the bases and the certificates of one pool. It proves that the table and the list of bases are right for the vectors (`adj_spec`, `bases_sound`, `bases_complete`), that the list of vectors is the pool (`rays_eq`, `boxRays_exact`), and the minimum for that pool (`minimum_ks_size_vectors`). Written by `scripts/gen_lean.py`. |
| `boxRays d H` | The pool B(d, H) as a Lean definition (`lean/KS/Spec.lean`): the list of integer vectors of length d with entries between −H and H whose first non-zero entry is positive and whose entries have greatest common divisor 1. It contains one representative of every ray of the pool; `boxRays_exact` proves that every non-zero integer vector of the box is parallel to exactly one of them. |
| `VColorable` | Colorability stated in Lean for vectors (`lean/KS/Spec.lean`): a set T of positions in a list of vectors has a coloring, where orthogonal means "dot product zero" and a basis is an increasing list of d positions of pairwise orthogonal vectors. It mentions no table and no list of bases. The main Lean theorems are stated with it. |
| Table form, vector form | The two ways the Lean development states colorability: for a table of bit masks (`Colorable`, used by the certificate checkers) and for the integer vectors (`VColorable`). Two theorems prove that they agree for every table that passes the three checks of its data module. |
| Mask | A set of rays stored as a natural number: ray i is in the set when bit i is 1. The Lean statements speak of masks T below 2⁴⁹ (or 2⁴⁰), read as sets of positions in the list `boxRays d H`. |
| Trust base | What one has to believe for a result to hold: for "Lean", the kernel and the reading of the statement and of the definitions it uses (`boxRays`, `dot`, `card`, `Sub`, `VColorable`, about 25 lines), and no table, certificate or checker; for "proof-checked", the pool construction, the encoder, the cut verification, the proof checker and Lemmas 1, 3, 6, 7. |

## Other

| Term | Meaning in this project |
|---|---|
| Register | The file `results/RESULTS.md`, the single source of truth for every number and status. |
| Stack demonstration | A run of the 31-ray set on four pieces of the Tsotchke software (Moonlab, QGTL, quantum_rng, Eshkol), described in Section 6 of the paper. All of it is classical computation; it is not an experiment and not part of any proof. |
| State-independent gap | For the 31-ray set: every quantum state gives total probability 1 in each of the 17 bases (17 in all), while a labelling obeying rule (i) gives a 1 to at most 16 of the 17 bases. |
| Preprint | A paper made public before peer review. |
