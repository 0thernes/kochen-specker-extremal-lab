# QGTL provenance and scope

Upstream: [tsotchke/quantum_geometric_tensor](https://github.com/tsotchke/quantum_geometric_tensor).
Pinned commit: [`770994aa8ddd858e6bb16eebb25250a7b9f67c96`](https://github.com/tsotchke/quantum_geometric_tensor/tree/770994aa8ddd858e6bb16eebb25250a7b9f67c96)
(upstream commit description: v0.777 beta release).

Verified against the upstream GitHub tree on 2026-11-09:

| Local/upstream path | Git blob SHA-1 |
|---|---|
| `src/quantum_geometric/distributed/differential_geometry.c` | `f2f92a68a92f7d4866eea24e6e9a810c21b94e6a` |
| `include/quantum_geometric/distributed/differential_geometry.h` | `0222e4dbeb60fd2e003f025466d7ffa1ec424c60` |
| `LICENSE` | `e42af9827970b426259e4e453b321b2ebcd6321c` |

These files match upstream after Git's CRLF-to-LF normalization. The MIT
license is retained. The one local compatibility file is `stub/cblas.h`, an
empty header explicitly labeled as local. The compiled translation unit has
no calls to BLAS, so no BLAS implementation is replaced or emulated.

In this repository one program uses this source: `stack/ks31_qgtl.c` calls
`diffgeo_engine_create`, `diffgeo_point_create` and `diffgeo_distance` (the
Fubini-Study distance, arccos of the absolute overlap) on the 31 rays of the
Conway-Kochen-type set, **normalised by the caller**: the kernel does not
normalise its input. `scripts/run_stack.py` builds and runs that program and
compares the result (71 pairs at distance pi/2) with the exact integer
orthogonality table. The Git blob hashes in the table were recomputed from
the files in this repository on 2026-11-10 (`git hash-object`, after
CRLF-to-LF normalisation). Only this kernel is exercised. The broader QGTL
library, the generic-coordinate QGT entry point, distributed algorithms, GPU
paths and other geometry routines are not validated here.
