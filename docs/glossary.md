# Glossary (`docs/glossary.md`)

## Domain Terms (Kochen–Specker Contextuality)

- **Ray:** A one-dimensional subspace (direction through the origin) of $\mathbb{R}^d$ or $\mathbb{C}^d$, represented canonically by a primitive vector (entries with $\gcd = 1$ and positive first nonzero entry in $B(d, H)$).
- **Orthogonality:** Two rays are orthogonal if the inner product of their representative vectors vanishes ($\langle u, v \rangle = 0$).
- **Basis:** A set of $d$ pairwise orthogonal rays in dimension $d$ (an orthogonal $d$-tuple).
- **KS colouring (0/1 colouring):** A map $f : S \to \{0, 1\}$ assigning $f(u) + f(v) \le 1$ to every orthogonal pair $u, v \in S$ and at least one $1$ (hence exactly one $1$) to every basis contained in $S$.
- **Kochen–Specker (KS) set:** A finite set of rays $S$ admitting no KS colouring.
- **Critical KS set:** A KS set all of whose proper subsets are colourable.
- **Coordinate pool $B(d, H)$:** All rays of $\mathbb{Z}^d$ spanned by nonzero integer vectors with $\max_i |v_i| \le H$.
- **Cyclotomic pool $U(d, N)$:** All rays of $\mathbb{C}^d$ spanned by nonzero vectors with entries in $\{0\} \cup \mu_N$ ($N$-th roots of unity).
- **Core of a pool:** The subset obtained by repeatedly deleting rays that lie in no basis or have fewer than $d$ orthogonal neighbours; every critical KS set lies inside the core (Lemma 3).
- **Colouring cut:** For an independent set $I \subseteq V$, the necessary constraint that any KS set must contain at least one basis of $\mathrm{Miss}(I)$ (Lemma 1).
- **DRUP certificate:** Deletion Reverse Unit Propagation proof of CNF unsatisfiability checked by `verify/drup_check.c` without trusting the SAT solver.
- **Search-tree certificate:** An exhaustive branching tree of independent sets and excluded bases verified independently by `verify/verify_cert.mjs` and (for $B(3,2)$ and $B(4,1)$) by a soundness-proved Lean 4 checker.

## Finding Classes (Build Standard v1.2.0)

Every issue, review finding, and audit item is classified using the 10-class Build Standard v1.2.0 taxonomy (`.github/labels.tsv`):

- **bug** — code does not behave as intended.
- **error** — a mistake in facts, logic, math, data, or configuration.
- **issue** — a general defect, snag, or maintenance task.
- **problem** — a larger root cause or systemic failure.
- **concern** — a risk, smell, or fragile area that has not broken yet.
- **dilemma** — a trade-off between two competing valid choices.
- **conflict** — two rules, specs, docs, or behaviors contradict each other.
- **gap** — something expected or promised is missing.
- **hole** — an edge case, bypass, or security/validation/proof loophole.
- **blindspot** — an unexamined assumption, untested path, or missing perspective.
