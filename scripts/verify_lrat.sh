#!/usr/bin/env bash
# Trigger T2: Independent second-checker DRAT -> LRAT verification using pinned,
# SHA-256-verified upstream marijnheule/drat-trim (drat-trim.c + lrat-check.c).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY="python"

DRAT_COMMIT="2e3b2dc0ecf938addbd779d42877b6ed69d9a985"
DRAT_TRIM_SHA="d834b649f437e091597f5347f259b9f681087f89ca0844d0cee250a1a1a0c2ee"
LRAT_CHECK_SHA="bf07c2ac96b9035da1ebcc578cb95e956a2b795629d613154cdb307f8a8f4a95"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/ks_lrat_XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

echo "=== Downloading pinned marijnheule/drat-trim ($DRAT_COMMIT) ==="
curl -sSfL "https://raw.githubusercontent.com/marijnheule/drat-trim/${DRAT_COMMIT}/drat-trim.c" -o "$WORK/drat-trim.c"
curl -sSfL "https://raw.githubusercontent.com/marijnheule/drat-trim/${DRAT_COMMIT}/lrat-check.c" -o "$WORK/lrat-check.c"
echo "${DRAT_TRIM_SHA}  $WORK/drat-trim.c" | sha256sum -c -
echo "${LRAT_CHECK_SHA}  $WORK/lrat-check.c" | sha256sum -c -

gcc -O2 -o "$WORK/drat-trim" "$WORK/drat-trim.c"
gcc -O2 -o "$WORK/lrat-check" "$WORK/lrat-check.c"
gcc -O2 -std=c11 -Wall -Wextra -o "$WORK/drup_check" "$ROOT/verify/drup_check.c"

mkdir -p "$WORK/results"

check_pool() {
  local label="$1"
  local cuts_src="$2"
  local k="$3"
  local kind="$4"
  shift 4
  local base="$WORK/results/${label}"
  cp "$ROOT/$cuts_src" "${base}.json"
  echo "=== Verifying ${label} (k=${k}) with drup_check + drat-trim -> LRAT -> lrat-check ==="
  (cd "$ROOT" && "$PY" src/ks_cnf.py "${base}.json" "$k" - g4 "$kind" "$@") | grep -E "cuts re-verified|CNF:|g4: UNSAT"
  "$WORK/drup_check" "${base}.cnf" "${base}.drat" | grep -q "s VERIFIED"
  "$WORK/drat-trim" "${base}.cnf" "${base}.drat" -L "${base}.lrat" | grep -q "s VERIFIED"
  "$WORK/lrat-check" "${base}.cnf" "${base}.lrat" | grep -q "c VERIFIED"
  echo "PASS [${label}]: drup_check (VERIFIED) + drat-trim (VERIFIED) + lrat-check (LRAT VERIFIED)"
}

check_pool "B3_2_k30" "results/master_box3_2_k30_cuts.json" 30 box3 2
check_pool "B4_1_k17" "results/master_box_4_1_k17_cuts.json" 17 box 4 1
check_pool "B3_3_k30" "results/master_box3_3_k30_cuts.json" 30 box3 3

# Negative control: truncated LRAT proof must be rejected by lrat-check
head -n 2 "$WORK/results/B3_2_k30.lrat" > "$WORK/results/corrupted.lrat"
if "$WORK/lrat-check" "$WORK/results/B3_2_k30.cnf" "$WORK/results/corrupted.lrat" 2>&1 | grep -q "c VERIFIED"; then
  echo "ERROR: lrat-check accepted a corrupted/truncated LRAT proof!" >&2
  exit 1
fi
echo "PASS [negative control]: lrat-check rejected truncated LRAT proof."
echo "ALL_DRAT_TRIM_LRAT_CHECKS_PASS"
