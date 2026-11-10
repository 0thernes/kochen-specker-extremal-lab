# Security

## What this repository is

Research programs, proof files and a static web page. It runs no service, stores no user data, and
contains no credentials, tokens or keys. The site under `docs/` is static: its scripts load only the
files in `docs/data/` from the same origin and send nothing anywhere.

## Reporting

Write to **0_0@0thernes.art** with the subject "security: kochen-specker-extremal-lab". Please do not
open a public issue for something that could harm a person who merely opens the site or runs the
documented commands. You will get an answer from the maintainer; there is no bounty programme.

In scope:

* a script or page in this repository that executes or loads something it should not (for example a
  data file that makes the site run injected code, or a script that writes outside the repository);
* a mismatch between a vendored file under `third_party/` and the upstream commit named in its
  `PROVENANCE.md`;
* a secret or personal datum that was committed by mistake.

Not a security matter, but very welcome as an ordinary issue (see `CONTRIBUTING.md`): any way to make a
verifier in this repository accept something false, for example a wrong certificate accepted by
`verify/verify_cert.mjs`, an invalid proof accepted by `verify/drup_check.c`, or a false statement
accepted by the Lean checkers. Those are correctness defects of the research and are handled in the
open.

## What a user should know before running things

* `third_party/moonlab/moonlab.wasm` is a prebuilt binary from the upstream project. It is used only by
  the optional demonstration `python scripts/run_all.py --stack`. Its hash is recorded in
  `third_party/moonlab/PROVENANCE.md`; its build from source was not reproduced here.
* `scripts/run_all.py` compiles `verify/drup_check.c` with the local C compiler and runs local Python
  and Node programs. It downloads nothing. The Lean toolchain named in `lean/lean-toolchain` is
  downloaded by elan on first use of `lake`.
* `pip install -r requirements.txt` installs pinned versions of third-party packages from PyPI.
* The continuous-integration workflow in `.github/workflows/ci.yml` pins the actions it uses by commit
  hash and has read-only permissions.

## Supported versions

Only the latest release on `main` is maintained.
