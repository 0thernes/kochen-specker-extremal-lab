# Statement on the use of AI systems

Title: Certified exact minima of Kochen-Specker sets inside coordinate pools: 31 and 33 rays in
dimension three, 18 in dimension four, 29 in dimension five

Author: Alexander S. Donahue, 0thernes LLC, Washington, USA (ORCID 0009-0006-8168-9648)

1. The research plan, the programs, the computations, the Lean 4 proofs and the text of the manuscript
   were produced by an AI system, Claude (Anthropic), working as a software agent at the request and
   under the direction of the author, on 9 and 10 November 2026. Sub-tasks (literature reading,
   independent verifiers, reviews) were carried out by further instances of the same system.
2. An AI system is not an author. The author takes full responsibility for the content of the
   manuscript, for the correctness of the results as far as they have been verified, and for the
   decision to submit.
3. Safeguards used, because of point 1:
   * the mathematical results are accompanied by certificates that are checked by programs independent
     of the search that produced them (the Lean 4 kernel; a JavaScript verifier written from the
     specification only; a proof checker for unsatisfiability proofs), and the formulas of several
     results were also given to a second SAT solver. What each result rests on, and the outcome of
     each proof check, is recorded in `results/RESULTS.md` in the repository;
   * the literature was searched for prior art by topic and by the distinctive numbers, and the prior
     art found is described in Section 1.3;
   * the references were checked against Crossref or arXiv (the 38 references of the version that was
     reviewed; references added afterwards are to be checked again before submission, see
     `publication/README.md`);
   * before release the material was examined in nine reviewing passes without permission to change
     the repository, made by further instances of the same AI system. Their findings and what was
     changed are recorded in `docs/REVIEW.md`. This is an internal check, not peer review.
4. What the safeguards did not prevent, and what they do not cover. The first literature search
   missed two published facts: the report by Pavičić and Megill (Phys. Rev. A 106, L060203, 2022) of
   29 rays as the smallest critical set generated from the coordinates 0, ±1 in dimension five, and
   the 16 sets of 18 rays inside the 24 rays of Peres counted by Waegell and Aravind (Found. Phys. 41
   (2011) 1786). Both were found by the review before release, and the claims were narrowed; a further
   overlap that was not found is possible. A remark about dimension five that rested on a biased
   random sampler was wrong and was withdrawn. Not covered by any safeguard: the choice of definitions
   and the reading of the Lean statements, the completeness of the literature search, and the
   hand-written lemmas of `paper/PROOFS.md`, which have been checked by tests on small cases and by
   review but not formalised.
5. The author used no AI system to generate or alter data, images or references other than as stated
   above.
