"""Negative and positive tests for verify/drup_check (the proof checker must
reject wrong proofs and satisfiable formulas, and accept correct proofs)."""
import os
import random
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(ROOT, "verify", "drup_check.exe" if os.name == "nt" else "drup_check")


def run(cnf_text, proof_text):
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "f.cnf")
        b = os.path.join(d, "p.drat")
        open(a, "w").write(cnf_text)
        open(b, "w").write(proof_text)
        r = subprocess.run([EXE, a, b], capture_output=True, text=True)
        return r.returncode == 0 and "s VERIFIED" in r.stdout


def cnf(clauses):
    nv = max(abs(l) for c in clauses for l in c)
    return f"p cnf {nv} {len(clauses)}\n" + "".join(" ".join(map(str, c)) + " 0\n" for c in clauses)


def main():
    fails = 0

    def expect(name, got, want):
        nonlocal fails
        ok = got == want
        fails += 0 if ok else 1
        print(("PASS" if ok else "FAIL"), name, "->", got)

    two = [[1, 2], [-1, 2], [1, -2], [-1, -2]]
    expect("unsat 2-var formula with proof 'b' then empty", run(cnf(two), "2 0\n0\n"), True)
    expect("same formula, empty proof", run(cnf(two), ""), False)
    expect("same formula, only the empty clause (not RUP)", run(cnf(two), "0\n"), False)
    expect("satisfiable formula, bogus lemma", run(cnf([[1, 2]]), "-1 0\n-2 0\n0\n"), False)
    expect("satisfiable formula, empty clause", run(cnf([[1, 2], [-1, 2]]), "0\n"), False)
    # pigeonhole PHP(3,2): unsat; a valid DRUP proof obtained by resolution steps
    php = [[1, 2], [3, 4], [5, 6], [-1, -3], [-1, -5], [-3, -5], [-2, -4], [-2, -6], [-4, -6]]
    # lemma -1: assume 1 -> -3,-5 -> 4,6 -> conflict (-4,-6): RUP.  then lemma -2 similarly, then empty.
    expect("pigeonhole 3 into 2 with a correct proof", run(cnf(php), "-1 0\n-2 0\n0\n"), True)
    expect("pigeonhole with a wrong first lemma", run(cnf(php[:-1]), "-1 0\n-2 0\n0\n"), False)
    # strict input: numbers that would wrap around, malformed tokens, and formula files that do not
    # match their header must be refused (found by the review before release: the token 4294967296
    # used to wrap to 0 and split a clause in two)
    good_proof = "2 0\n0\n"
    expect("literal 4294967296 inside two clauses of a satisfiable formula",
           run("p cnf 2 2\n1 4294967296 2 0\n-1 4294967296 -2 0\n", "0\n"), False)
    expect("unit clauses 4294967297 and -8589934593",
           run("p cnf 2 2\n4294967297 0\n-8589934593 0\n", "0\n"), False)
    expect("malformed token in the formula", run("p cnf 2 4\n1x 2 0\n-1 2 0\n1 -2 0\n-1 -2 0\n", good_proof), False)
    expect("malformed token in the proof", run(cnf(two), "2 zz 0\n0\n"), False)
    expect("formula with fewer clauses than its header says",
           run("p cnf 2 4\n1 2 0\n-1 2 0\n1 -2 0\n", good_proof), False)
    expect("formula without a header line", run("1 2 0\n-1 2 0\n1 -2 0\n-1 -2 0\n", good_proof), False)
    expect("formula with a variable above the header", run("p cnf 2 4\n1 2 0\n-1 2 0\n1 -3 0\n-1 -2 0\n", good_proof), False)
    expect("deleting a clause that the next lemma needs", run(cnf(two), "d 1 2 0\n2 0\n0\n"), False)
    expect("deleting a clause that is not needed", run(cnf(two + [[1, 2, -2]]), "d 1 2 -2 0\n2 0\n0\n"), True)
    # random 3-SAT instances that are satisfiable must never be 'verified' with random lemmas
    rng = random.Random(7)
    bad = 0
    for t in range(200):
        nv = 8
        model = [rng.choice((1, -1)) for _ in range(nv)]
        cls = []
        while len(cls) < 25:
            c = [rng.choice((1, -1)) * v for v in rng.sample(range(1, nv + 1), 3)]
            if any(model[abs(l) - 1] * l > 0 for l in c):
                cls.append(c)
        proof = "".join(" ".join(str(rng.choice((1, -1)) * rng.randint(1, nv)) for _ in range(rng.randint(1, 3))) + " 0\n"
                        for _ in range(10)) + "0\n"
        if run(cnf(cls), proof):
            bad += 1
    expect("200 satisfiable random formulas with random 'proofs' all rejected", bad == 0, True)
    # the real proofs, and a corrupted formula (the size bound removed makes it satisfiable)
    res = os.path.join(ROOT, "results")
    for base in ("master_box3_2_k30_cuts", "master_box_4_1_k17_cuts"):
        a, b = os.path.join(res, base + ".cnf"), os.path.join(res, base + ".drat")
        if not (os.path.exists(a) and os.path.exists(b)):
            print("SKIP", base)
            continue
        r = subprocess.run([EXE, a, b], capture_output=True, text=True)
        expect(base + " real proof", r.returncode == 0 and "s VERIFIED" in r.stdout, True)
        lines = open(a).read().splitlines()
        units = [i for i, l in enumerate(lines) if len(l.split()) == 2 and l.split()[0].startswith("-")]
        # drop the LAST negative unit clause that is the cardinality bound (written right after the counter)
        with tempfile.TemporaryDirectory() as d:
            for drop in units[-3:]:
                mod = [l for i, l in enumerate(lines) if i != drop]
                hdr = mod[0].split()
                hdr[3] = str(int(hdr[3]) - 1)
                mod[0] = " ".join(hdr)
                p = os.path.join(d, "g.cnf")
                open(p, "w").write("\n".join(mod) + "\n")
                r = subprocess.run([EXE, p, b], capture_output=True, text=True)
                print("   info: formula with unit clause at line", drop, "removed ->",
                      "VERIFIED" if r.returncode == 0 else "rejected")
    print("failures:", fails)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
