/* ks31_qrng.c -- stage 3 of the "stack" demonstration of the 31-ray KS set.
 *
 * Standalone, integer-only program.  It prints the seed-1 known-answer values
 * of three integer mixers and the first 8 outputs of the counter-mode stream
 * that stack/ks31_moonlab.cjs re-implements in JavaScript BigInt; the driver
 * scripts/run_stack.py compares the two implementations value by value.
 *
 * HONEST LABELLING: these mixers are a deterministic "quantum-inspired" integer
 * mixer.  They are ordinary 64-bit arithmetic; the physics-flavoured constant
 * names are upstream's and carry no physical meaning.  This is NOT quantum
 * randomness, not a hardware entropy source, and no statistical or
 * cryptographic quality is claimed.  Nothing here runs on quantum hardware.
 *
 * ---------------------------------------------------------------------------
 * The block between "BEGIN UPSTREAM" and "END UPSTREAM" is copied verbatim from
 *   tsotchke/quantum_rng, file src/quantum_rng/quantum_rng.c,
 *   commit 1a77e77f803c63883349b658361c06401cd8ceb7
 *   (vendored unchanged at third_party/quantum_rng/src/quantum_rng/quantum_rng.c):
 *     constants      upstream lines 12-24  (eleven #defines and upstream's one
 *                    comment line; QRNG_RYDBERG and QRNG_ELECTRON_G are unused here)
 *     splitmix64     upstream lines 61-70
 *     hadamard_mix   upstream lines 73-83
 *     absorb_seed    upstream lines 113-120
 *
 * MIT License
 * Copyright (c) 2024 Tsotchke
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * ---------------------------------------------------------------------------
 *
 * The counter-mode stream in main() is OUR construction on top of the upstream
 * mixers (it is not an upstream generator):
 *     S     = absorb_seed(le64(seed))           (seed as 8 little-endian bytes)
 *     out_i = hadamard_mix(S + (i+1) * QRNG_GOLDEN_RATIO),  i = 0, 1, 2, ...
 * No floating point, no libm, no clock: the output is identical on any platform
 * with a conforming C compiler.
 *
 * Build:  gcc -std=c11 -O2 -Wall -Wextra -o ks31_qrng.exe ks31_qrng.c
 */
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <inttypes.h>

/* ---- BEGIN UPSTREAM (verbatim) ------------------------------------------ */
#define QRNG_FINE_STRUCTURE 0x7297352743776A1BULL
#define QRNG_PLANCK 0x6955927086495225ULL
#define QRNG_RYDBERG 0x9E3779B97F4A7C15ULL
#define QRNG_ELECTRON_G 0x2B992DDFA232945ULL
#define QRNG_GOLDEN_RATIO 0x9E3779B97F4A7C15ULL
#define QRNG_SQRT2 0x6A09E667F3BCC908ULL

// New quantum mixing constants
#define QRNG_HEISENBERG 0xC13FA9A902A6328FULL
#define QRNG_SCHRODINGER 0x91E10DA5C79E7B1DULL
#define QRNG_PAULI_X 0x4C957F2D8A1E6B3CULL
#define QRNG_PAULI_Y 0xD3E99E3B6C1A4F78ULL
#define QRNG_PAULI_Z 0x8F142FC07892A5B6ULL

static inline uint64_t splitmix64(uint64_t x) {
    x ^= x >> 30;
    x *= 0xbf58476d1ce4e5b9ULL;
    x ^= x >> 27;
    x *= 0x94d049bb133111ebULL;
    x ^= x >> 31;
    x *= QRNG_HEISENBERG;
    x ^= x >> 29;
    return x;
}

static inline uint64_t hadamard_mix(uint64_t x) {
    x = splitmix64(x);
    x ^= QRNG_PAULI_X * (x >> 12);
    x *= QRNG_FINE_STRUCTURE;
    x ^= QRNG_PAULI_Y * (x >> 25);
    x *= QRNG_PLANCK;
    x ^= QRNG_PAULI_Z * (x >> 27);
    x *= QRNG_SCHRODINGER;
    x ^= x >> 13;
    return x;
}

static uint64_t absorb_seed(const uint8_t *seed, size_t seed_len) {
    uint64_t h = QRNG_SQRT2 ^ splitmix64((uint64_t)seed_len + QRNG_GOLDEN_RATIO);
    for (size_t i = 0; i < seed_len; i++) {
        h ^= (uint64_t)seed[i] + QRNG_GOLDEN_RATIO + (h << 6) + (h >> 2);
        h = hadamard_mix(h);
    }
    return h ^ splitmix64((uint64_t)seed_len);
}
/* ---- END UPSTREAM -------------------------------------------------------- */

int main(void) {
    const uint64_t seed = 1;
    uint8_t le64[8];
    uint64_t S, out[8];
    int i, ok;

    for (i = 0; i < 8; i++) le64[i] = (uint8_t)(seed >> (8 * i));
    S = absorb_seed(le64, 8);

    printf("[qrng] deterministic \"quantum-inspired\" integer mixers (NOT quantum randomness)\n");
    printf("splitmix64_1=%016" PRIx64 "\n", splitmix64(seed));
    printf("hadamard_mix_1=%016" PRIx64 "\n", hadamard_mix(seed));
    printf("absorb_seed_le64_1=%016" PRIx64 "\n", S);
    printf("stream_seed=%" PRIu64 "\n", seed);
    printf("stream_first8=");
    for (i = 0; i < 8; i++) {
        out[i] = hadamard_mix(S + (uint64_t)(i + 1) * QRNG_GOLDEN_RATIO);
        printf("%s%016" PRIx64, i ? " " : "", out[i]);
    }
    printf("\n");

    /* known answers recorded by the digest test (mixers_test.c) for seed 1 */
    ok = splitmix64(1) == 0x6b6a95bfe299a90eULL
      && hadamard_mix(1) == 0x7590e4342b418e25ULL
      && splitmix64(0) == 0 && hadamard_mix(0) == 0
      && splitmix64(0xdeadbeefcafebabeULL) == 0x8d1f67dbebc0a568ULL
      && hadamard_mix(0xdeadbeefcafebabeULL) == 0xd44c2a8f54e0d3f4ULL
      && out[0] == 0x5df9ef9ba7cdcca2ULL && out[1] == 0xddb5674ec90579d9ULL
      && out[2] == 0xe350bb351fce2bebULL && out[3] == 0x20275c35a4eaee84ULL
      && out[4] == 0x2f7cdc01c2c0ba7dULL;
    printf("[qrng] %s  known-answer self-check (mixers and first five stream outputs, seed 1)\n", ok ? "PASS" : "FAIL");
    return ok ? 0 : 1;
}
