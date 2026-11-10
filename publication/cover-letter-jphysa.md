# Draft cover letter — Journal of Physics A: Mathematical and Theoretical

(Draft for the author to edit, sign and submit. Nothing has been sent.)

Dear Editors,

I submit the manuscript "Certified exact minima of Kochen-Specker sets inside coordinate pools: 31 and
33 rays in dimension three, 18 in dimension four, 29 in dimension five" for consideration as a Paper in
the section Quantum Mechanics and Quantum Information Theory.

**What the paper does.** The size of the smallest Kochen-Specker set is a long-standing open problem
(in dimension three: between 24 and 31 rays). The paper does not solve it and contains no set smaller
than a published one. It determines the exact minimum inside natural finite pools of rays, and
attaches to the answers certificates that can be checked without trusting the search: Lean 4 kernel
proofs for two pools, replayable search trees, and unsatisfiability proofs checked by a separate
checker. The paper states for each result what it rests on. The results are these. Among rays of
dimension three with integer coordinates of absolute value at most 2, 3 or 4 the minimum is 31, and
the minimum sets are exactly the six images of one Conway-Kochen-type set under the symmetries of the
cube. For coordinates that are 0 or N-th roots of unity, N = 6, 12, 18, 24, the minimum is 33. Among
the 40 rays of dimension four with coordinates 0, ±1 the minimum 18 is attained only by the 16 known
sets inside the 24 rays of Peres. Among the 121 rays of dimension five with coordinates 0, ±1 the
minimum is 29, the size of the set of Cabello, Estebaranz and García-Alcaine.

**Relation to earlier work.** Section 1.3 states what was reported before and what is new. Several of
the values had been reported without proof: 31 for integer coordinates up to 2, 3 and 4 and 33 for
sixth roots of unity (an arXiv preprint by M. Kernaghan and a forum note, both without certificates),
and 29 as the smallest critical set generated from the coordinates 0, ±1 in dimension five (Pavičić
and Megill, Phys. Rev. A 106, L060203, 2022, without a proof that nothing smaller exists). The 16 sets
of dimension four are the known sets counted by Waegell and Aravind (Found. Phys. 41 (2011) 1786), and
18 is known to be the minimum for all Kochen-Specker sets in dimension four (and a lower bound in
every dimension). New, to my knowledge, are the proofs with
their certificates, the exact minimum 33 for N = 12, 18 and 24, and the complete lists of minimum sets
for integer coordinates up to 3 and 4 and for sixth and twelfth roots of unity. The method combines a
known kind of cut with necessary conditions for critical sets and a symmetry normal form.

**How the work was produced.** As stated on the first page and in Section 9, and in the attached
statement, the research, programs, proofs and text were produced by an AI system (Claude, Anthropic)
at my request and under my direction. I take responsibility for the submission. Because of this, the
paper is built around independently checkable certificates, and the repository contains the programs,
the certificates, the Lean sources and the record of an internal review made before release
(`docs/REVIEW.md`; that review was made by the same AI system and is not peer review; it led to the
credits to Pavičić and Megill and to Waegell and Aravind named above):
https://github.com/0thernes/kochen-specker-extremal-lab

The manuscript has not been published and is not under consideration elsewhere. There was no external
funding and I have no competing interests.

Suggested referees and any exclusions: (to be completed by the author).

Yours sincerely,

Alexander S. Donahue
0thernes LLC, Washington, USA
0_0@0thernes.art
