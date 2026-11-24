#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY="python"
cmd="${1:-help}"
case "$cmd" in
  build)
    (cd lean && lake build KS Solution)
    ;;
  test)
    "$PY" -m unittest discover -s tests -v
    ;;
  verify-lean)
    (cd lean && lake build KS Solution)
    (cd lean && lake env lean KS/Audit.lean)
    (cd lean && lake comparator --config comparator.json --paranoid)
    ;;
  sanitizers)
    mkdir -p build/san
    gcc -O1 -g -std=c11 -Wall -Wextra -fsanitize=address,undefined verify/drup_check.c -o build/san/drup_check_san
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
