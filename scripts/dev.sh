#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY="python"
cmd="${1:-help}"
case "$cmd" in
  build)
    (cd lean && lake build --wfail KS Solution)
    ;;
  test)
    "$PY" -m unittest discover -s tests -v
    "$PY" scripts/stamp_timestamps.py --verify
    if command -v node >/dev/null 2>&1; then
      node --test docs/assets/verify.test.mjs
    fi
    ;;
  verify-lean)
    (cd lean && lake build --wfail KS Solution)
    (cd lean && lake env lean KS/Audit.lean)
    (cd lean && lake env leanchecker --fresh Solution)
    (cd lean && lake comparator --config comparator.json --paranoid)
    ;;
  sanitizers)
    mkdir -p build/san
    gcc -O1 -g -std=c11 -Wall -Wextra -fsanitize=address,undefined -fno-omit-frame-pointer verify/drup_check.c -o build/san/drup_check_san
    printf "p cnf 2 4\n1 2 0\n1 -2 0\n-1 2 0\n-1 -2 0\n" > build/san/test.cnf
    printf "1 0\n0\n" > build/san/test.drup
    ./build/san/drup_check_san build/san/test.cnf build/san/test.drup | grep -q "s VERIFIED"
    gcc -O1 -g -std=gnu11 -Wall -Wextra -fsanitize=address,undefined -fno-omit-frame-pointer \
      -Ithird_party/qgtl/include -Ithird_party/qgtl/stub \
      third_party/qgtl/src/quantum_geometric/distributed/differential_geometry.c \
      stack/ks31_qgtl.c -lm -o build/san/ks31_qgtl_san
    ./build/san/ks31_qgtl_san results/ks31_box3_H2.json | grep -q "STAGE PASS"
    gcc -O1 -g -std=c11 -Wall -Wextra -fsanitize=address,undefined -fno-omit-frame-pointer \
      stack/ks31_qrng.c -o build/san/ks31_qrng_san
    ./build/san/ks31_qrng_san | grep -q "\[qrng\] PASS"
    echo "All 3 KS C11 ASan/UBSan checks passed."
    ;;
  reproduce)
    "$PY" -m unittest discover -s tests -v
    (cd lean && lake build KS Solution && lake env lean KS/Audit.lean)
    ;;
  *)
    echo "Usage: scripts/dev.sh {build|test|verify-lean|sanitizers|reproduce}"
    exit 2
    ;;
esac
