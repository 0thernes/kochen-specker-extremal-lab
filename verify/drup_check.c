/* drup_check.c - a small forward checker for DRUP proofs of unsatisfiability.

   usage: drup_check formula.cnf proof.drat

   Every proof line is a clause (a lemma) that must follow from the formula
   and the earlier lemmas by REVERSE UNIT PROPAGATION: assuming all its
   literals false and propagating units must give a conflict.  The proof is
   accepted when the empty clause has been derived.  Lemmas that are not RUP
   make the checker fail; it never accepts a RAT step.

   Deletion lines ("d ...") remove one stored copy of the named clause from
   the clause set used for later propagation.  This is sound: removing clauses
   can only make later lemmas harder to justify, and every literal already
   fixed at the top level was derived while its reasons were present, so it is
   a consequence of the original formula in any case.  A deletion that matches
   no stored clause (for example a unit clause, which is not stored) is
   ignored.

   Input is read strictly.  Every token must be a decimal integer of absolute
   value at most 10^8 (larger or malformed tokens stop the program, so that no
   number can wrap around), the formula file must have a "p cnf" line, and
   the number of clauses and the largest variable must agree with it, so that
   a truncated or altered formula file is refused.

   Exit status 0 and the line "s VERIFIED" only if the proof is accepted;
   1 if it is not; 2 if a file cannot be read or is malformed.

   Written for this project so that the proofs produced by the SAT solver do
   not have to be trusted; no code is shared with the solver.  Plain C99. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

/* allocation that stops with a message instead of continuing with a null pointer */
static void *xrealloc(void *p, size_t n) {
    void *q = realloc(p, n ? n : 1);
    if (!q) { printf("c out of memory\ns NOT VERIFIED\n"); exit(2); }
    return q;
}
static void *xmalloc(size_t n) { return xrealloc(NULL, n); }

typedef struct { int *lits; int size; int deleted; unsigned hash; long next; } Clause;

static Clause *clauses; static long nclauses, capclauses;
static long **watch; static int *wsize, *wcap;      /* indexed by literal code */
static signed char *val;                             /* by variable: 0 unassigned, 1 true, -1 false */
static unsigned char *mark;                          /* by literal code, scratch */
static int *trail; static long ntrail, qhead;
static int nvars;

#define HBITS 20
static long *bucket;                                 /* head clause index + 1, or 0 */

static int code(int lit) { return lit > 0 ? 2 * lit : 2 * (-lit) + 1; }
static int value(int lit) { int v = val[abs(lit)]; return lit > 0 ? v : -v; }

static unsigned lit_mix(int lit) {
    unsigned x = (unsigned)code(lit) * 2654435761u;
    x ^= x >> 15; x *= 2246822519u; x ^= x >> 13;
    return x;
}

/* order-independent hash of a set of distinct literals */
static unsigned set_hash(const int *lits, int n) {
    unsigned s = 0, x = 0;
    for (int i = 0; i < n; i++) { unsigned m = lit_mix(lits[i]); s += m; x ^= m * 31u + 7u; }
    return (s ^ (x << 1) ^ (unsigned)n * 40503u) & ((1u << HBITS) - 1u);
}

static void grow_vars(int v) {
    if (v <= nvars) return;
    int old = nvars; nvars = v;
    val = xrealloc(val, (size_t)(nvars + 1));
    mark = xrealloc(mark, (size_t)(2 * nvars + 2));
    watch = xrealloc(watch, sizeof(long *) * (size_t)(2 * nvars + 2));
    wsize = xrealloc(wsize, sizeof(int) * (size_t)(2 * nvars + 2));
    wcap = xrealloc(wcap, sizeof(int) * (size_t)(2 * nvars + 2));
    trail = xrealloc(trail, sizeof(int) * (size_t)(nvars + 1));
    for (int i = old + 1; i <= nvars; i++) {
        val[i] = 0;
        mark[2 * i] = mark[2 * i + 1] = 0;
        watch[2 * i] = watch[2 * i + 1] = NULL;
        wsize[2 * i] = wsize[2 * i + 1] = 0;
        wcap[2 * i] = wcap[2 * i + 1] = 0;
    }
}

static void add_watch(int lit, long c) {
    int k = code(lit);
    if (wsize[k] == wcap[k]) {
        wcap[k] = wcap[k] ? 2 * wcap[k] : 4;
        watch[k] = xrealloc(watch[k], sizeof(long) * (size_t)wcap[k]);
    }
    watch[k][wsize[k]++] = c;
}

static void assign(int lit) { val[abs(lit)] = lit > 0 ? 1 : -1; trail[ntrail++] = lit; }

/* returns 1 on conflict */
static int propagate(void) {
    while (qhead < ntrail) {
        int lit = trail[qhead++];          /* lit became true; visit clauses watching -lit */
        int k = code(-lit);
        int i = 0, j = 0, n = wsize[k];
        long *ws = watch[k];
        while (i < n) {
            long ci = ws[i++];
            Clause *c = &clauses[ci];
            if (c->deleted) continue;      /* drop the watch of a deleted clause */
            int *l = c->lits;
            if (l[0] == -lit) { l[0] = l[1]; l[1] = -lit; }
            if (value(l[0]) == 1) { ws[j++] = ci; continue; }
            int found = 0;
            for (int t = 2; t < c->size; t++) {
                if (value(l[t]) != -1) {
                    int tmp = l[1]; l[1] = l[t]; l[t] = tmp;
                    add_watch(l[1], ci);   /* l[1] != -lit, so another list */
                    found = 1; break;
                }
            }
            if (found) continue;
            ws[j++] = ci;
            if (value(l[0]) == -1) {       /* conflict */
                while (i < n) ws[j++] = ws[i++];
                wsize[k] = j;
                return 1;
            }
            assign(l[0]);
        }
        wsize[k] = j;
    }
    return 0;
}

static void backtrack(long pos) {
    while (ntrail > pos) val[abs(trail[--ntrail])] = 0;
    qhead = pos;
}

static int top_conflict = 0;

/* removes duplicate literals in place; returns the new size */
static int dedupe(int *lits, int size) {
    int n = 0;
    for (int i = 0; i < size; i++) {
        int k = code(lits[i]);
        if (!mark[k]) { mark[k] = 1; lits[n++] = lits[i]; }
    }
    for (int i = 0; i < n; i++) mark[code(lits[i])] = 0;
    return n;
}

/* add a clause at top level (literals false at top level are kept; watches chosen
   among non-false literals when possible) */
static void add_clause(int *lits, int size) {
    if (top_conflict) return;
    int n = dedupe(lits, size);
    int satisfied = 0, nf = 0;
    int *copy = xmalloc(sizeof(int) * (size_t)(n > 0 ? n : 1));
    memcpy(copy, lits, sizeof(int) * (size_t)n);
    for (int i = 0; i < n; i++) {
        if (value(copy[i]) == 1) satisfied = 1;
        if (value(copy[i]) != -1) { int t = copy[nf]; copy[nf] = copy[i]; copy[i] = t; nf++; }
    }
    if (satisfied) { free(copy); return; }            /* true at top level: redundant */
    if (nf == 0) { top_conflict = 1; free(copy); return; }
    if (nf == 1) {
        assign(copy[0]);
        if (propagate()) top_conflict = 1;
        free(copy);
        return;
    }
    if (nclauses == capclauses) {
        capclauses = capclauses ? 2 * capclauses : 1024;
        clauses = xrealloc(clauses, sizeof(Clause) * (size_t)capclauses);
    }
    Clause *c = &clauses[nclauses];
    c->lits = copy; c->size = n; c->deleted = 0;
    c->hash = set_hash(copy, n);
    c->next = bucket[c->hash];
    bucket[c->hash] = nclauses + 1;
    add_watch(copy[0], nclauses); add_watch(copy[1], nclauses);
    nclauses++;
}

/* delete one stored clause with exactly this literal set, if there is one */
static int delete_clause(int *lits, int size) {
    int n = dedupe(lits, size);
    if (n < 2) return 0;
    unsigned h = set_hash(lits, n);
    for (int i = 0; i < n; i++) mark[code(lits[i])] = 1;
    int done = 0;
    for (long p = bucket[h]; p && !done; p = clauses[p - 1].next) {
        Clause *c = &clauses[p - 1];
        if (c->deleted || c->size != n) continue;
        int same = 1;
        for (int i = 0; i < n && same; i++) if (!mark[code(c->lits[i])]) same = 0;
        if (same) { c->deleted = 1; done = 1; }      /* literals are distinct, so equal sets */
    }
    for (int i = 0; i < n; i++) mark[code(lits[i])] = 0;
    return done;
}

#define MAXVAR 100000000            /* variables above this are refused, so nothing can overflow */

static const char *cur_file = "";   /* for error messages */
static long header_vars = -1, header_clauses = -1;   /* from the "p cnf" line, -1 if absent */
static int max_var_seen = 0;       /* largest variable read so far */

static void bad_input(const char *what) {
    printf("c %s: %s\ns NOT VERIFIED\n", cur_file, what);
    exit(2);
}

/* reads one integer token; returns 1 and sets *out, or 0 at end of file.  Anything that is not a
   decimal integer of absolute value at most MAXVAR, followed by white space or the end of the
   file, stops the program: a token is never truncated, wrapped or silently skipped. */
static int read_int(FILE *f, int *out) {
    int c, neg = 0, digits = 0;
    long v = 0;
    do { c = fgetc(f); } while (c != EOF && isspace(c));
    if (c == EOF) return 0;
    if (c == '-') { neg = 1; c = fgetc(f); }
    while (c != EOF && isdigit(c)) {
        v = v * 10 + (c - '0');
        if (v > MAXVAR) bad_input("integer out of range");
        digits++;
        c = fgetc(f);
    }
    if (!digits || (c != EOF && !isspace(c))) bad_input("malformed token (not an integer)");
    *out = neg ? -(int)v : (int)v;
    return 1;
}

/* reads the next clause from f into buf; returns its size, or -1 at end of file (a clause cut
   off by the end of the file is dropped); *is_del is set when the line started with 'd' */
static int read_clause(FILE *f, int **buf, int *cap, int allow_d, int *is_del) {
    int c, n = 0;
    *is_del = 0;
    for (;;) {
        c = fgetc(f);
        if (c == EOF) return -1;
        if (isspace(c)) continue;
        if (c == 'c') { while (c != '\n' && c != EOF) c = fgetc(f); continue; }
        if (c == 'p') {
            char line[256];
            if (!fgets(line, sizeof line, f)) return -1;
            if (!allow_d && sscanf(line, " cnf %ld %ld", &header_vars, &header_clauses) != 2)
                bad_input("malformed \"p cnf\" line");
            continue;
        }
        if (c == 'd' && allow_d) { *is_del = 1; continue; }
        ungetc(c, f);
        break;
    }
    for (;;) {
        int lit;
        if (!read_int(f, &lit)) return -1;
        if (lit == 0) return n;
        if (n == *cap) { *cap = *cap ? 2 * *cap : 64; *buf = xrealloc(*buf, sizeof(int) * (size_t)*cap); }
        (*buf)[n++] = lit;
        if (abs(lit) > max_var_seen) max_var_seen = abs(lit);
        grow_vars(abs(lit));
    }
}

int main(int argc, char **argv) {
    if (argc != 3) { fprintf(stderr, "usage: drup_check formula.cnf proof.drat\n"); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror(argv[1]); return 2; }
    int *buf = NULL, cap = 0, n, is_del;
    long norig = 0, nlemma = 0, ndel = 0, ndel_found = 0;
    bucket = xmalloc(sizeof(long) << HBITS);
    memset(bucket, 0, sizeof(long) << HBITS);
    grow_vars(1);
    cur_file = argv[1];
    while ((n = read_clause(f, &buf, &cap, 0, &is_del)) >= 0) { add_clause(buf, n); norig++; }
    fclose(f);
    /* the formula must be the file its header describes: a truncated or altered file is refused */
    if (header_clauses < 0) bad_input("no \"p cnf\" line");
    if (norig != header_clauses || max_var_seen > header_vars)
        bad_input("the clauses do not match the \"p cnf\" line (truncated or altered file)");
    if (!top_conflict && propagate()) top_conflict = 1;
    f = fopen(argv[2], "r");
    if (!f) { perror(argv[2]); return 2; }
    cur_file = argv[2];
    int derived_empty = top_conflict;
    while (!derived_empty && (n = read_clause(f, &buf, &cap, 1, &is_del)) != -1) {
        if (is_del) { ndel++; ndel_found += delete_clause(buf, n); continue; }
        nlemma++;
        long pos = ntrail;
        int sat = 0;
        for (int i = 0; i < n && !sat; i++) {
            int v = value(buf[i]);
            if (v == 1) sat = 1;
            else if (v == 0) assign(-buf[i]);
        }
        int ok = sat || propagate();
        backtrack(pos);
        if (!ok) {
            printf("c lemma %ld is not implied by unit propagation\ns NOT VERIFIED\n", nlemma);
            return 1;
        }
        add_clause(buf, n);
        if (top_conflict) derived_empty = 1;
    }
    fclose(f);
    printf("c %ld original clauses, %ld lemmas checked, %ld deletion lines (%ld applied)\n",
           norig, nlemma, ndel, ndel_found);
    if (derived_empty) { printf("s VERIFIED\n"); return 0; }
    printf("c the empty clause was not derived\ns NOT VERIFIED\n");
    return 1;
}
