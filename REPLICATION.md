# Replication Protocol (`REPLICATION.md`)

```bash
git clone https://github.com/0thernes/kochen-specker-extremal-lab.git
cd kochen-specker-extremal-lab

# 1. Zero-Mathlib Lean 4.35.0 clean build, axiom audit & 6-kernel comparator (~30s)
cd lean
lake build KS Solution
lake env lean KS/Audit.lean
lake comparator --config comparator.json --paranoid
cd ..

# 2. Python unit & CNF tests
python -m unittest discover -s tests -v
```

## Replication Log

| Date | Replicator | Environment | Scope | Result |
|---|---|---|---|---|
| 2026-11-24 | Alexander S. Donahue (author / local & CI) | Windows 11 + Ubuntu 24.04, Lean 4.35.0 (zero Mathlib) | `lake build KS Solution`, `KS/Audit.lean`, 6-kernel `lake comparator --paranoid`, `tests/` | Pass (author-run; external human replication open) |
