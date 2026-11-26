# Replication Protocol (`REPLICATION.md`)

```bash
git clone https://github.com/0thernes/kochen-specker-extremal-lab.git
cd kochen-specker-extremal-lab

# 1. Zero-Mathlib Lean 4.35.0 clean build (--wfail), axiom audit & 6-kernel comparator (~77s cold)
cd lean
lake build --wfail KS Solution
lake env lean KS/Audit.lean
lake comparator --config comparator.json --paranoid
cd ..

# 2. Cryptographic timestamps (RFC 3161 TSA + OpenTimestamps) & independent LRAT proof audit
python scripts/stamp_timestamps.py --verify
bash scripts/verify_lrat.sh

# 3. Node.js & Python verification suites
node verify/test_verify.mjs
node --test docs/assets/verify.test.mjs
python -m unittest discover -s tests -v
```

## Replication Log

| Date | Replicator | Environment | Scope | Result |
|---|---|---|---|---|
| 2026-11-24 | Alexander S. Donahue (author / local & CI) | Windows 11 + Ubuntu 24.04, Lean 4.35.0 (zero Mathlib) | `lake build KS Solution`, `KS/Audit.lean`, 6-kernel `lake comparator --paranoid`, `tests/` | Pass (author-run; external human replication open) |
| 2026-11-26 | Alexander S. Donahue (automated clean-clone check, zero `.lake` cache) | Windows 11 + WSL2, fresh `git clone --depth 1`, Lean 4.35.0, Node 22 | `lake build --wfail KS Solution` (10 jobs, 0 warnings) + `KS/Audit.lean` (`149/149` theorems, 0 disallowed axioms, `76.8s`) + `verify/test_verify.mjs` (`59/59`) + `docs/assets/verify.test.mjs` | Pass (author-automated clean-clone; independent external human replication still open) |
