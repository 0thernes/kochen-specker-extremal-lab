#!/usr/bin/env bash
# certify.sh - re-prove a result of engine A with a plain SAT solver (DRUP proof) and check the
# proof with verify/drup_check.
# usage: scripts/certify.sh <cuts-basename> <k> <case|-> <kind> [args...]
# Exit status 0 only if the proof of THIS run was written and VERIFIED.  A proof file left by an
# earlier run is deleted first, so it can never be checked against a new formula.  Variables that
# would restrict the run to one cube are cleared: this script certifies whole cases only.
set -u
unset KS_FIX_IN KS_FIX_OUT KS_CUBE_TAG KS_BLOCKED
cd "$(dirname "$0")/.."
base="$1"; k="$2"; case_="$3"; shift 3
log="logs/certify_${base}.log"
exe="verify/drup_check"; [ -x "verify/drup_check.exe" ] && exe="verify/drup_check.exe"
status=1
run() {
  echo "=== $(date +%H:%M:%S) certify $base k=$k case=$case_ pool=$*"
  rm -f "results/${base}.drat"
  if python -u src/ks_cnf.py "results/${base}.json" "$k" "$case_" g4 "$@"; then
    if [ -f "results/${base}.drat" ]; then
      "./$exe" "results/${base}.cnf" "results/${base}.drat"
      rc=$?
      echo "drup_check exit=$rc"
      [ "$rc" -eq 0 ] && status=0
    else
      echo "NO PROOF FILE WAS WRITTEN"
    fi
  else
    echo "ENCODE/SOLVE FAILED (the formula is satisfiable, or an error occurred): nothing was proved"
  fi
  echo "=== $(date +%H:%M:%S) done, status=$status"
}
tmp="$(mktemp)"
run "$@" > "$tmp" 2>&1
cat "$tmp" >> "$log"
grep -h -E "case |cuts re-verified|CNF:|UNSAT|SAT in|lemmas checked|VERIFIED|FAILED|NO PROOF|status=" "$tmp" | tail -8
rm -f "$tmp"
exit $status
