# Contributing

This is a research repository maintained by one person. The most useful contribution is a report that
something stated here is wrong, unsupported, or already known.

## Reporting an error or prior work

Open an issue at https://github.com/0thernes/kochen-specker-extremal-lab/issues or write to
0_0@0thernes.art. A good report contains:

1. **The claim**, quoted, with the file and line (paper, `results/RESULTS.md`, README, a Lean statement).
2. **The evidence**: a command and its output, a counterexample (a list of rays is enough), two lines
   that contradict each other, or a reference with page or section.
3. **What you ran it on** (operating system, Python, Node and Lean versions), if it is a failed check.

Reports of earlier work that already contains one of the results are especially welcome. If the report
is right, the register, the paper and the changelog are corrected and the reporter is credited unless
they ask not to be.

## How changes are made

* Fixes are applied by the maintainer directly on `main`. Please send an issue with a patch or a clear
  description rather than a pull request; pull requests may be closed after their content has been
  applied by hand.
* `results/RESULTS.md` is the single source of truth. A number may appear in the paper, the README or
  the site only if the register has it, with an evidence file and a status word. A new result needs a
  register row, its evidence in `results/` or `logs/`, and a line in `docs/INDEX.md`, in that order.
* Status words are not upgraded by argument. "Lean" needs a kernel-checked theorem, "proof-checked" a
  line `s VERIFIED` in a log, "tree" a certificate replayed by `verify/verify_cert.mjs`.
* Before anything is committed: `python scripts/run_all.py` must end with exit code 0, and after a
  change under `lean/` so must `lake build` and the audit `lake env lean KS/Audit.lean`.
* Generated files are regenerated, not edited: `lean/KS/Box3H2.lean` and `lean/KS/Box4H1.lean`
  (`scripts/gen_lean.py`), `docs/data/` (`scripts/build_site_data.py`), `docs/paper.html` and the PDF
  (`scripts/build_paper.py`, `scripts/build_latex.py`).

## Reports produced with AI systems

They are welcome under the same rule as any other report: the claim must be reproducible from what the
report contains. Say which system produced it. This repository was itself produced by an AI system
under human direction (see `LEGAL.md`).

## Licence

The repository is released under the verification licence in `LICENSE`. It allows downloading,
building, running and studying the material in order to check it. It does not allow redistribution of
modified versions without written permission, so please do not publish forks that present changed
results under this project's name. By sending a patch you agree that it may be included under the same
licence.
