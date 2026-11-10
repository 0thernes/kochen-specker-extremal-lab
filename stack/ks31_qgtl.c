/* ks31_qgtl.c -- stage 2 of the "stack" demonstration of the 31-ray KS set.
 *
 * Computes the Fubini-Study distance between all 465 pairs of the 31 rays with
 * the differential-geometry kernel of QGTL (tsotchke/quantum_geometric_tensor
 * v0.777, commit 770994a, MIT, Copyright (c) 2024 Tsotchke), linked against the
 * unmodified vendored file
 *   third_party/qgtl/src/quantum_geometric/distributed/differential_geometry.c
 * through diffgeo_engine_create / diffgeo_point_create / diffgeo_distance.
 *
 * HONEST LABELLING: this is ordinary double-precision classical arithmetic on
 * 3-component vectors (the kernel evaluates arccos|<a|b>| on normalised input).
 * It is a numerical cross-check of the exact integer orthogonality table, not a
 * proof and not an experiment on quantum hardware.  Only this one kernel of
 * QGTL is exercised; no claim is made about the rest of that library.
 *
 * The rays are read from the JSON file given as argv[1]
 * (default ../results/ks31_box3_H2.json); the kernel does not normalise its
 * input, so each integer ray is divided by its Euclidean norm here.
 *
 * Build (from the folder stack/):
 *   gcc -std=gnu11 -O1 -I ../third_party/qgtl/include -I ../third_party/qgtl/stub
 *       ../third_party/qgtl/src/quantum_geometric/distributed/differential_geometry.c
 *       ks31_qgtl.c -o ks31_qgtl.exe -lm
 */
#include "quantum_geometric/distributed/differential_geometry.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define NRAYS 31
#define TOL 1e-12

/* Minimal reader for the "rays":[[a,b,c],...] array of the KS JSON file. */
static int read_rays(const char* path, int rays[NRAYS][3]) {
    FILE* f = fopen(path, "rb");
    if (!f) return -1;
    static char buf[1 << 16];
    size_t len = fread(buf, 1, sizeof buf - 1, f);
    fclose(f);
    buf[len] = 0;
    const char* p = strstr(buf, "\"rays\"");
    if (!p) return -2;
    p = strchr(p, '[');
    if (!p) return -2;
    p++;                                   /* inside the outer array */
    int n = 0;
    while (*p && *p != ']') {
        if (*p == '[') {
            if (n >= NRAYS) return -3;
            char* end;
            p++;
            for (int k = 0; k < 3; k++) {
                rays[n][k] = (int)strtol(p, &end, 10);
                if (end == p) return -4;
                p = end;
                while (*p == ',' || *p == ' ') p++;
            }
            if (*p != ']') return -5;
            n++;
        }
        p++;
    }
    return n;
}

int main(int argc, char** argv) {
    const char* path = argc > 1 ? argv[1] : "../results/ks31_box3_H2.json";
    int rays[NRAYS][3];
    int n = read_rays(path, rays);
    int fails = 0;

    printf("[qgtl] QGTL diffgeo kernel: classical double-precision arithmetic, no quantum hardware\n");
    printf("[qgtl] %s  read 31 integer rays from %s  (n=%d)\n", n == NRAYS ? "PASS" : "FAIL", path, n);
    if (n != NRAYS) return 1;

    diffgeo_engine_t* e = diffgeo_engine_create();   /* default: projective Hilbert space, Fubini-Study */
    if (!e) { printf("[qgtl] FAIL  diffgeo_engine_create\n"); return 1; }

    diffgeo_point_t* pt[NRAYS];
    for (int i = 0; i < NRAYS; i++) {
        double nrm = sqrt((double)(rays[i][0] * rays[i][0] + rays[i][1] * rays[i][1] + rays[i][2] * rays[i][2]));
        ComplexDouble v[3];
        for (int k = 0; k < 3; k++) { v[k].real = rays[i][k] / nrm; v[k].imag = 0.0; }
        pt[i] = diffgeo_point_create(e, v, 3);
        if (!pt[i]) { printf("[qgtl] FAIL  diffgeo_point_create(%d)\n", i); return 1; }
    }

    int pairs = 0, orth_int = 0, orth_fs = 0, mismatch = 0, not_smaller = 0, self_bad = 0;
    double min_non = 1e300, max_non = -1e300, max_orth_dev = 0.0;
    int amin = -1, bmin = -1, amax = -1, bmax = -1;
    static unsigned char orth[NRAYS][NRAYS];
    for (int i = 0; i < NRAYS; i++) {
        double dself = diffgeo_distance(e, pt[i], pt[i]);
        if (!(fabs(dself) <= 1e-7)) self_bad++;      /* acos near 1 is ill-conditioned: loose bound */
        for (int j = i + 1; j < NRAYS; j++) {
            int dot = rays[i][0] * rays[j][0] + rays[i][1] * rays[j][1] + rays[i][2] * rays[j][2];
            double d = diffgeo_distance(e, pt[i], pt[j]);
            int is_orth_fs = fabs(d - M_PI / 2) <= TOL;
            pairs++;
            if (dot == 0) orth_int++;
            if (is_orth_fs) {
                orth_fs++;
                orth[i][j] = orth[j][i] = 1;
                if (fabs(d - M_PI / 2) > max_orth_dev) max_orth_dev = fabs(d - M_PI / 2);
            } else {
                if (!(d < M_PI / 2 - TOL)) not_smaller++;
                if (d < min_non) { min_non = d; amin = i; bmin = j; }
                if (d > max_non) { max_non = d; amax = i; bmax = j; }
            }
            if (is_orth_fs != (dot == 0)) mismatch++;
        }
    }
    int triples = 0;
    for (int i = 0; i < NRAYS; i++)
        for (int j = i + 1; j < NRAYS; j++)
            if (orth[i][j])
                for (int k = j + 1; k < NRAYS; k++)
                    if (orth[i][k] && orth[j][k]) triples++;

#define CHECK(cond, ...) do { int ok_ = (cond); if (!ok_) fails++; \
        printf("[qgtl] %s  ", ok_ ? "PASS" : "FAIL"); printf(__VA_ARGS__); printf("\n"); } while (0)

    CHECK(pairs == 465, "all %d pairs of the 31 rays evaluated with diffgeo_distance", pairs);
    CHECK(mismatch == 0, "distance equals pi/2 within 1e-12 exactly for the integer-orthogonal pairs  (mismatches=%d, max |d - pi/2| = %.3g)",
          mismatch, max_orth_dev);
    CHECK(orth_fs == 71 && orth_int == 71, "number of orthogonal pairs is 71  (Fubini-Study=%d, integer=%d)", orth_fs, orth_int);
    CHECK(not_smaller == 0, "distance is smaller than pi/2 for all %d non-orthogonal pairs", pairs - orth_fs);
    CHECK(triples == 17, "mutually orthogonal triples from the Fubini-Study table: %d (expected 17)", triples);
    CHECK(self_bad == 0, "distance of each ray to itself is 0 within 1e-7");
    printf("[qgtl] minimum non-orthogonal distance = %.15f  (rays %d,%d)\n", min_non, amin, bmin);
    printf("[qgtl] maximum non-orthogonal distance = %.15f  (rays %d,%d);  pi/2 = %.15f\n", max_non, amax, bmax, M_PI / 2);

    /* machine-readable lines for run_stack.py */
    printf("pairs_total=%d\n", pairs);
    printf("orthogonal_pairs=%d\n", orth_fs);
    printf("bases=%d\n", triples);
    printf("min_nonorthogonal_distance=%.17g\n", min_non);
    printf("max_nonorthogonal_distance=%.17g\n", max_non);
    printf("max_orthogonal_deviation=%.17g\n", max_orth_dev);

    for (int i = 0; i < NRAYS; i++) diffgeo_point_destroy(pt[i]);
    diffgeo_engine_destroy(e);
    printf("[qgtl] %s (%d failed checks)\n", fails ? "STAGE FAIL" : "STAGE PASS", fails);
    return fails ? 1 : 0;
}
