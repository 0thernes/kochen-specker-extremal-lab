# Licence, authorship and publication notes

Kochen-Specker Extremal Lab, version 1.0.0, 10 November 2026.
Alexander S. Donahue, 0thernes LLC, Washington, USA. Contact: 0_0@0thernes.art.
ORCID: [0009-0006-8168-9648](https://orcid.org/0009-0006-8168-9648).

This page explains the repository's notices in plain language. **[LICENSE](LICENSE) governs the files
written for this project; [NOTICE](NOTICE) identifies the third-party components and their terms.**
This page does not change either and grants no additional rights.

## Copyright and licence

The copyright notice names **0thernes LLC (Alexander S. Donahue)**. The repository is released under a
custom **verification licence**. It permits anyone, free of charge, to download, build, run and study
the repository in order to check, reproduce or referee the results it reports, and to quote from it
with attribution. Redistribution of modified versions and commercial use require the written permission
of the copyright holder.

The repository is public under those terms. It is not offered under an unrestricted open-source
licence. If the paper is later deposited in an archive under a different licence, that licence applies
to the deposited copy only and has to be stated there; it does not silently change the terms of the
programs or of the third-party material. The work is provided as is, under the warranty and liability
provisions of [LICENSE](LICENSE).

## Third-party components

Files under `third_party/` are the work of their authors and keep their own licences.

| Component | Location | Terms |
|---|---|---|
| Moonlab, prebuilt WebAssembly engine and loader | `third_party/moonlab/` | [MIT licence](third_party/moonlab/LICENSE); [provenance](third_party/moonlab/PROVENANCE.md) |
| quantum_rng, legacy seeded generator sources | `third_party/quantum_rng/` | [MIT licence](third_party/quantum_rng/LICENSE); [provenance](third_party/quantum_rng/PROVENANCE.md) |
| quantum_geometric_tensor (QGTL), one source file and its header | `third_party/qgtl/` | [MIT licence](third_party/qgtl/LICENSE); [provenance](third_party/qgtl/PROVENANCE.md) |

These are unmodified copies of files by Tsotchke, pinned to the commits recorded in the provenance
files. The one file in `third_party/` written for this project is `third_party/qgtl/stub/cblas.h`, an
empty stand-in header. Keep the original copyright, licence and attribution notices when you copy
these files. Their use here does not imply endorsement by their authors.

Not vendored: the Lean development uses **no Mathlib** and no other Lean package. The Python programs
use python-sat (PySAT, MIT), OR-Tools (Apache 2.0), NumPy and NetworkX (BSD 3-Clause), which are
installed by pip and not copied into the repository. python-sat 1.9.dev21 bundles the two SAT solvers
used here, Glucose 4.1 and CaDiCaL 1.9.5 (both under the MIT licence); each keeps its own licence. The
Eshkol compiler is used through an installed copy for the demonstration of Section 6 of the paper; running it does not relicense Eshkol or make it part of this
project's copyright claim.

## Authorship, responsibility and AI disclosure

The research, the programs, the Lean proofs and the text of this repository were produced by an AI
system, **Claude (Anthropic)**, working as an agent at the request and under the direction of
**Alexander S. Donahue**, who is the author and is responsible for the release. An AI system is not an
author and is not listed as one.

A successful run of the programs, of the proof checker or of the Lean build shows what those tools
show and nothing more. It is not a statement that a human has refereed the manuscript. Where a venue
asks for a statement of contributions, approval or accountability, that statement has to describe what
the author actually did and cannot be inferred from this repository.

## Funding and interests

The work was funded by the author through 0thernes LLC. There was no external funding and there are
no competing interests. No university, laboratory, charitable or tax-exempt status is asserted.

## Prior work and priority

This summarises Section 1.3 of [the paper](paper/ks-minimum.md); the paper has the references.

Not claimed here:

* the values 31, 33, 18 and 29, which are the sizes of published sets (Conway and Kochen; Cabello and
  Pavičić; Cabello, Estebaranz and García-Alcaine);
* the minimum 31 for the 49 rays with integer coordinates up to 2 and the minimum 33 for sixth roots
  of unity, both reported as exact, without a certificate, by Kernaghan (arXiv:2603.16988), who also
  lists 31 for coordinates up to 3, finds six distinct 31-ray sets in the 49-ray pool by randomised
  minimisation, and proves that the pool of N-th roots of unity contains a Kochen-Specker set if and
  only if 6 divides N;
* the minimum 31 for integer coordinates up to 2, 3 and 4, reported in October 2026 in a note on the
  forum ProblemHive (post p/xfkay), obtained with CP-SAT and coloring cuts, which states itself that
  its solver logs are not a certificate;
* the bound 18 for all Kochen-Specker sets in dimension four (Pavičić, Merlet, McKay and Megill 2005)
  and in every dimension (Xu, Chen and Gühne 2020);
* the 16 Kochen-Specker sets of 18 rays in the 40-ray pool of dimension four: they are the 16 known
  sets inside the 24 rays of Peres (Waegell and Aravind, Found. Phys. 41 (2011) 1786);
* 29 rays as the smallest critical set generated from the coordinates 0, ±1 in dimension five:
  Pavičić and Megill (Phys. Rev. A 106, L060203, 2022) generate from these components a master set
  with 105 rays and 136 bases, which is the core of the pool B(5, 1), and report 29 rays and 16 bases
  as the smallest critical set of its class, with two non-isomorphic sets of that size (also Pavičić
  and Waegell 2024). No proof that nothing smaller exists is given there;
* the coloring-cut idea, which appears in the ProblemHive note and, as an unsatisfiable-subset loop,
  in Kernaghan's preprint.

So four of the values of dimension three (31 for integer bounds 2, 3 and 4; 33 for sixth roots of
unity) and the value 29 of dimension five had been reported before without proof, and the value 18
and the count 16 of dimension four were known.

Claimed as new, to our knowledge and within a literature search made on 9 and 10 November 2026 (arXiv,
Zenodo, GitHub and the open web, by topic and by the distinctive numbers):

1. proofs with certificates for the results: Lean 4 kernel proofs for the 49-ray pool and for the
   40-ray pool of dimension four, replayable search trees, and unsatisfiability proofs checked by a
   separate checker, at the level recorded for each result in [results/RESULTS.md](results/RESULTS.md);
2. complete lists of the minimum sets: exactly six for integer coordinates up to 3 and up to 4 (the
   same six as for 2), exactly 3 and 12 for sixth and twelfth roots of unity, each list a single
   orbit under the symmetries of the pool; and the fact that the 40-ray pool of dimension four
   contains no 18-ray Kochen-Specker set besides the 16 known ones;
3. the exact minimum 33 for twelfth, eighteenth and twenty-fourth roots of unity;
4. the proof that 29 is the minimum for coordinates 0, ±1 in dimension five, where 29 had been
   reported as the smallest set obtained, and the fact that every Kochen-Specker set in that pool
   contains at least three coordinate axes;
5. the method beyond the coloring cut: necessary conditions for critical sets as constraints, a
   symmetry normal form, an encoding whose unsatisfiability proofs are checked independently, and tree
   certificates with a checker proved sound in Lean.

The search was bounded. The ProblemHive post could be read but not independently dated beyond its own
status line. The first search missed two published facts: the report of 29 for the coordinates 0, ±1
in dimension five, and the 16 sets inside the 24 rays of Peres. Both were found in a review of the
manuscript before release, and the claims were narrowed accordingly ([docs/REVIEW.md](docs/REVIEW.md)).
A further overlap that was not found is possible; a pointer to one is welcome at the address above.
Nothing here is a claim of historical priority beyond what that search supports.

## Status of the work

This is a research preprint. It has not been peer reviewed. Before release it was examined in nine
reviewing passes made by instances of the AI system that produced it; that is an internal check and
does not replace peer review ([docs/REVIEW.md](docs/REVIEW.md)). A public repository, a release, a DOI
deposit, an arXiv announcement, a journal submission and an acceptance are different events; this
repository records none of the last four for version 1.0.0. Not every result is certified to the same
level: the register [results/RESULTS.md](results/RESULTS.md) records, for each result, what it rests
on and the outcome of each proof check. The Lean theorems cover two minimum values and not the counts
of minimum sets. No Kochen-Specker set smaller than a published one was found, and the general
minimal-set problem is not settled by pool results.

## Names

The names Tsotchke, Moonlab, quantum_rng, quantum_geometric_tensor, Eshkol, Lean, OR-Tools, PySAT,
Glucose, CaDiCaL, Node.js, GitHub, ProblemHive, Claude and Anthropic, and the names of the authors
cited, are used only to identify the tools, sources and prior work. They do not imply sponsorship,
endorsement or affiliation.
