# Moonlab provenance

Upstream: [tsotchke/moonlab](https://github.com/tsotchke/moonlab).
Pinned commit: [`cd3b2347e3739327548708073d7e4ac710cc6a6c`](https://github.com/tsotchke/moonlab/tree/cd3b2347e3739327548708073d7e4ac710cc6a6c).
Upstream `VERSION.txt` at that commit is `1.2.1`.

Verified against the upstream GitHub tree on 2026-11-09:

| Local file | Upstream path | Git blob SHA-1 |
|---|---|---|
| `moonlab.js` | `docs/moonlab.js` | `0881441708dd08062bd2addace26b14f224274ec` |
| `moonlab.wasm` | `docs/moonlab.wasm` | `3c356543328855a45ee954a8fc930d3108cee160` |
| `LICENSE` | `LICENSE` | `60548d1cce27eee2c91f88e03ac5ec51cad9f661` |

The JS and license match upstream after Git's CRLF-to-LF normalization; the
WASM is byte-identical. No source modifications were made to these vendored
files. The upstream MIT license is retained. This is a pinned prebuilt binary;
the lab has not reproduced its compiler/toolchain build from source.

The lab uses Moonlab as a **classical state-vector simulator**, running its
WASM CPU functions under Node. No hardware quantum device, hardware entropy,
or quantum computational advantage is involved. The wrapper's WASM32 state
layout (`num_qubits`, `state_dim`, then `amplitudes` pointer at byte offset 8)
matches [`src/quantum/state.h`](https://github.com/tsotchke/moonlab/blob/cd3b2347e3739327548708073d7e4ac710cc6a6c/src/quantum/state.h).
This private-layout access is tied to the pinned artifact and must be
rechecked when upgrading.

In this repository the files are used by `stack/ks31_moonlab.cjs` only
(state initialisation, normalisation and the amplitude buffers of two-qubit
states). `scripts/run_stack.py` records SHA-256 fingerprints of the vendored
files and runs that program. The Git blob hashes in the table were recomputed
from the files in this repository on 2026-11-10 (`git hash-object`, after
CRLF-to-LF normalisation for the two text files). No claim is made about
unused Moonlab algorithms or backends.
