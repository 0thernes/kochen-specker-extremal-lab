#!/usr/bin/env bash
# certify_unique.sh - proof-checked confirmation of "exactly these KS sets of minimum size":
# re-run the enumeration (engine A), then let engine B prove that no further KS set with at most
# k rays exists once the listed ones are excluded, and check the proof.  For pools with symmetry
# breaking, src/ks_cnf.py also checks that the list is closed under the symmetry group.
# usage: scripts/certify_unique.sh <k> <kind> [args...]
# Exit status 0 only if the proof of THIS run was written and VERIFIED.  The summary printed at the
# end shows lines of this run only.  Variables that would restrict the run to one cube are cleared.
set -u
unset KS_FIX_IN KS_FIX_OUT KS_CUBE_TAG KS_BLOCKED
cd "$(dirname "$0")/.."
k="$1"; shift
tag="enumerate_$(echo "$*" | tr ' ' '_')_k${k}"
log="logs/unique_${tag}.log"
exe="verify/drup_check"; [ -x "verify/drup_check.exe" ] && exe="verify/drup_check.exe"
status=1
run() {
  echo "=== $(date +%H:%M:%S) uniqueness $tag"
  rm -f "results/${tag}_cuts.drat"
  if python -u scripts/enumerate_min.py "$k" "$@"; then
    if KS_BLOCKED="results/${tag}.json" python -u src/ks_cnf.py "results/${tag}_cuts.json" "$k" - g4 "$@"; then
      if [ -f "results/${tag}_cuts.drat" ]; then
        "./$exe" "results/${tag}_cuts.cnf" "results/${tag}_cuts.drat"
        rc=$?
        echo "drup_check exit=$rc"
        [ "$rc" -eq 0 ] && status=0
      else
        echo "NO PROOF FILE WAS WRITTEN"
      fi
    else
      echo "ENCODE/SOLVE FAILED (a further KS set exists, the list is not closed, or an error occurred)"
    fi
  else
    echo "ENUMERATION FAILED"
  fi
  echo "=== $(date +%H:%M:%S) done, status=$status"
}
tmp="$(mktemp)"
run "$@" > "$tmp" 2>&1
cat "$tmp" >> "$log"
grep -h -E "ENUMERATION|case |excluded|closed|CNF:|UNSAT|SAT in|lemmas checked|VERIFIED|FAILED|NO PROOF|status=" "$tmp" | tail -10
rm -f "$tmp"
exit $status
