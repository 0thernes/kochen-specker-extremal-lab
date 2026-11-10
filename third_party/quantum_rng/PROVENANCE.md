# quantum_rng provenance and scope

Upstream: [tsotchke/quantum_rng](https://github.com/tsotchke/quantum_rng).
Pinned commit: [`1a77e77f803c63883349b658361c06401cd8ceb7`](https://github.com/tsotchke/quantum_rng/tree/1a77e77f803c63883349b658361c06401cd8ceb7).

Verified against the upstream GitHub tree on 2026-11-09:

| Local/upstream path | Git blob SHA-1 |
|---|---|
| `src/quantum_rng/quantum_rng.c` | `6146323cc4a0c412a9c2936e38329d592d1fca59` |
| `src/quantum_rng/quantum_rng.h` | `62535c702eca5190026c8cd738ec886d6ecd69aa` |
| `src/common/secure_memory.h` | `ade22b336f45615d1b167d3f62b8617dabe58458` |
| `LICENSE` | `e42af9827970b426259e4e453b321b2ebcd6321c` |

These files match upstream after Git's CRLF-to-LF normalization. No local
changes were made to the vendored implementation, including the upstream
Windows-compatible secure-memory fallback. The MIT license is retained.

In this repository the vendored files are kept for reference and comparison:
`stack/ks31_qrng.c` contains a verbatim copy of three integer functions of
`quantum_rng.c` (`splitmix64`, `hadamard_mix`, `absorb_seed`) and the
constants they use, with the upstream MIT notice, and `scripts/run_stack.py`
compares that block line by line with the vendored source. The counter-mode
stream built on these functions is this project's own construction, not an
upstream generator; `stack/ks31_moonlab.cjs` re-implements it in JavaScript
and the two implementations are compared value by value. This is a
**classical, deterministic integer mixer**, not a physical quantum
random-number source. Quantum-themed identifiers and constants in the code do
not establish quantum behaviour. The functions used here are pure 64-bit
integer arithmetic, so the stream does not depend on floating-point or libm
behaviour (the upstream byte API, which is not used here, does). The Git blob
hashes in the table were recomputed from the files in this repository on
2026-11-10 (`git hash-object`, after CRLF-to-LF normalisation). No statistical
entropy, cryptographic unpredictability or hardware certification is claimed.
