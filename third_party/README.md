# Third-party files

This folder holds unmodified copies of files from three projects by Tsotchke. They are used only by the
demonstration of Section 6 of the paper (`stack/`, `scripts/run_stack.py`), which exercises the 31-ray
set on that software. **No theorem, certificate or count in this repository depends on them.**

| Folder | What is copied | Used by | Pinned upstream commit | Licence |
|---|---|---|---|---|
| `moonlab/` | `moonlab.wasm`, `moonlab.js` (prebuilt WebAssembly build of the Moonlab state-vector simulator, upstream version 1.2.1) | `stack/ks31_moonlab.cjs` | `cd3b2347e3739327548708073d7e4ac710cc6a6c` | MIT (`moonlab/LICENSE`) |
| `qgtl/` | `differential_geometry.c` and its header from quantum_geometric_tensor; `stub/cblas.h` is an empty stand-in written for this project | `stack/ks31_qgtl.c` | `770994aa8ddd858e6bb16eebb25250a7b9f67c96` | MIT (`qgtl/LICENSE`) |
| `quantum_rng/` | `quantum_rng.c`, `quantum_rng.h`, `secure_memory.h` | reference for the block copied into `stack/ks31_qrng.c` | `1a77e77f803c63883349b658361c06401cd8ceb7` | MIT (`quantum_rng/LICENSE`) |

Each folder has a `PROVENANCE.md` with the upstream path and the Git blob hash of every file, and a
statement of exactly which functions are exercised here and what is **not** claimed about the rest of
the upstream project.

## Checking the copies

The blob hashes can be recomputed without network access. For a text file (stored here with the line
endings of the working tree) normalise line endings first:

```
tr -d '\r' < third_party/qgtl/LICENSE | git hash-object --stdin --no-filters
git hash-object --no-filters third_party/moonlab/moonlab.wasm
```

and compare with the table in the folder's `PROVENANCE.md`. To compare with upstream, open the pinned
commit on GitHub; the same hash is shown by `git ls-tree` in a clone of the upstream repository.

## Honest labels

* Moonlab is a **classical** state-vector simulator. Nothing here runs on quantum hardware.
* The functions taken from quantum_rng are a deterministic integer mixer. They are **not** a source of
  quantum randomness, and no statistical or cryptographic quality is claimed.
* `moonlab.wasm` is a prebuilt binary. Its build from source was not reproduced here.
* The Eshkol compiler used by `stack/ks31.esk` is an installed tool and is not copied into this
  repository.

The names of these projects are used only to identify them. Their use here does not imply endorsement
by their authors.
