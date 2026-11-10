# Publication package

Everything here is prepared for the author to submit. Nothing in this folder has been submitted by the
build process: each venue below requires the author's own login and personal statements, and those
steps are left to the author on purpose.

| Venue | What is ready | What only the author can do |
|---|---|---|
| GitHub release and Pages | the tag v1.0.0, the release and the site under `docs/` are requested by the release process; see `docs/REPORT.md` for what was done | — |
| Software Heritage | an archive request for the repository URL is requested by the release process; see `docs/REPORT.md` for what was done | — |
| Internet Archive | snapshots of the site, the paper and the repository page are requested by the release process; see `docs/REPORT.md` for what was done | — |
| Google Scholar | `docs/paper.html` carries the `citation_*` meta tags and links the PDF | nothing to submit; indexing is automatic and can take weeks |
| arXiv | `ks-minimum/arxiv-source.zip` (TeX source and `00README.json`), `ks-minimum/ks-minimum.pdf`, abstract in `arxiv-metadata.txt` | log in, obtain endorsement for the category if asked, upload, confirm the authorship and licence statements, press Submit |
| Journal of Physics A | `cover-letter-jphysa.md`, `ai-use-statement.md`, the same TeX source | create the submission in the journal's system, confirm authorship criteria, sign the publishing agreement |
| Zenodo | `zenodo-metadata.json`, `zenodo-inquiry.md` | read the note below first; deposit only if Zenodo confirms the work is in scope |
| ORCID | `orcid-work.bib` | log in to ORCID and add the work (import BibTeX) once a public identifier exists |
| OpenAIRE | nothing to upload | OpenAIRE harvests arXiv and Zenodo records; claim the record in the OpenAIRE portal with your ORCID after it appears |

## Notes on each venue (checked 9 November 2026; re-check before acting)

* **arXiv.** Significant use of generative AI must be reported in the paper (it is: first page and
  Section 9). An AI system cannot be an author; the author takes full responsibility for the content.
  A first submission to a category needs an endorsement unless the account has an institutional
  e-mail. Suggested primary category `quant-ph`, cross-list `math.CO`. The abstract in
  `arxiv-metadata.txt` is the paper's abstract shortened; it has 1857 characters, under the
  1920-character limit. The page count in the "Comments" line has to be compared with the final PDF
  before uploading. arXiv moderators may decline AI-produced work; that decision is theirs.
* **Journal of Physics A.** Disclosed AI assistance is allowed, but the listed author must meet the
  authorship criteria: contribution, critical revision, final approval, accountability. The author
  should be able to answer referees' technical questions; `docs/SUMMARY.md` and `paper/PROOFS.md` are
  written to help with that. Submit to one journal at a time.
* **Zenodo.** Zenodo's policy of 27 April 2026 requires content to be grounded in research conducted
  by its human authors, with AI as a tool and not as the source. This work was produced by an AI
  system under the author's direction, so it may be out of scope. `zenodo-inquiry.md` is a draft
  message to Zenodo support asking for a ruling before any deposit. A Zenodo record and its DOI are
  permanent; do not deposit first and ask later.
* **ORCID / OpenAIRE.** These are registries, not repositories: they list works that exist elsewhere.
  Add the arXiv record (or the journal article) to ORCID when it exists; OpenAIRE picks it up from
  there and from arXiv.

## Before submitting anywhere

1. Read the paper once through, with `docs/SUMMARY.md` beside it. You are the responsible author.
2. Read `docs/REVIEW.md`. It records what an internal review before release found and what was
   changed, among other things two earlier reports that the first literature search had missed
   (Pavičić and Megill 2022 for dimension five; Waegell and Aravind 2011 for the 16 sets of dimension
   four). Section 1.3 of the paper, the cover letter and the metadata in this folder credit them; keep
   those credits in anything you rewrite. That review was made by the AI system that produced the
   work and is not peer review.
3. Open `results/RESULTS.md` and check that every proof check needed for a statement in the abstract
   is recorded there as VERIFIED. If one is not, wait for it or weaken the sentence.
4. Run `python scripts/run_all.py --lean` and `python scripts/check_docs.py` on your machine and keep
   the output with your records.
5. Check the reference list once more against Crossref (`scripts/check_references.py` prints each
   entry with the best Crossref match), in particular the references added after the review.
