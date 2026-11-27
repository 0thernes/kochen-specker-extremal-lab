#!/usr/bin/env bash
# Trigger T2 & Playbook v1.3 Checklist #13: Independent multi-checker DRAT -> LRAT verification
# using pinned, SHA-256-verified upstream marijnheule/drat-trim (drat-trim.c + lrat-check.c)
# AND HOL4-formally-verified tanyongkiam/cake_lpr (basis_ffi.c + cake_lpr.S / cake_lpr_arm8.S).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${PYTHON:-python3}"
command -v "$PY" >/dev/null 2>&1 || PY="python"

DRAT_COMMIT="2e3b2dc0ecf938addbd779d42877b6ed69d9a985"
DRAT_TRIM_SHA="d834b649f437e091597f5347f259b9f681087f89ca0844d0cee250a1a1a0c2ee"
LRAT_CHECK_SHA="bf07c2ac96b9035da1ebcc578cb95e956a2b795629d613154cdb307f8a8f4a95"

CAKE_COMMIT="033aad53d1733bd4b8ca41cf6f1b5fb5d84f8de2"
CAKE_FFI_SHA="bd498883fdc0577d734a771fe8197c5ff571f2abdd769b8dc95d46818db5cbbc"
ARCH="$(uname -m)"
if [ "$ARCH" = "x86_64" ]; then
  CAKE_ASM="cake_lpr.S"
  CAKE_ASM_SHA="d20ceae0d8fe973a03a1ba8db623b2594161721ab9091305ae60cd581dcc78f7"
elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
  CAKE_ASM="cake_lpr_arm8.S"
  CAKE_ASM_SHA="50b63e18facbf1e6a814ab4bd5c9c9175d59ba3eb271286ffaabff5499c4852b"
else
  echo "ERROR: Unsupported architecture for cake_lpr: $ARCH" >&2
  exit 1
fi

WORK="$(mktemp -d "${TMPDIR:-/tmp}/ks_lrat_XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

echo "=== Downloading pinned marijnheule/drat-trim ($DRAT_COMMIT) & tanyongkiam/cake_lpr ($CAKE_COMMIT) ==="
curl -sSfL "https://raw.githubusercontent.com/marijnheule/drat-trim/${DRAT_COMMIT}/drat-trim.c" -o "$WORK/drat-trim.c"
curl -sSfL "https://raw.githubusercontent.com/marijnheule/drat-trim/${DRAT_COMMIT}/lrat-check.c" -o "$WORK/lrat-check.c"
curl -sSfL "https://raw.githubusercontent.com/tanyongkiam/cake_lpr/${CAKE_COMMIT}/basis_ffi.c" -o "$WORK/basis_ffi.c"
curl -sSfL "https://raw.githubusercontent.com/tanyongkiam/cake_lpr/${CAKE_COMMIT}/${CAKE_ASM}" -o "$WORK/${CAKE_ASM}"

echo "${DRAT_TRIM_SHA}  $WORK/drat-trim.c" | sha256sum -c -
echo "${LRAT_CHECK_SHA}  $WORK/lrat-check.c" | sha256sum -c -
echo "${CAKE_FFI_SHA}  $WORK/basis_ffi.c" | sha256sum -c -
echo "${CAKE_ASM_SHA}  $WORK/${CAKE_ASM}" | sha256sum -c -

gcc -O2 -o "$WORK/drat-trim" "$WORK/drat-trim.c"
gcc -O2 -o "$WORK/lrat-check" "$WORK/lrat-check.c"
gcc -O2 -o "$WORK/cake_lpr" "$WORK/basis_ffi.c" "$WORK/${CAKE_ASM}"
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
  echo "=== Verifying ${label} (k=${k}) with drup_check + drat-trim -> LRAT -> lrat-check + HOL4 cake_lpr ==="
  (cd "$ROOT" && "$PY" src/ks_cnf.py "${base}.json" "$k" - g4 "$kind" "$@") | grep -E "cuts re-verified|excluded|CNF:|g4: UNSAT"
  "$WORK/drup_check" "${base}.cnf" "${base}.drat" | grep -q "s VERIFIED"
  "$WORK/drat-trim" "${base}.cnf" "${base}.drat" -L "${base}.lrat" | grep -q "s VERIFIED"
  "$WORK/lrat-check" "${base}.cnf" "${base}.lrat" | grep -q "c VERIFIED"
  "$WORK/cake_lpr" "${base}.cnf" "${base}.lrat" | grep -q "s VERIFIED UNSAT"
  echo "PASS [${label}]: drup_check + drat-trim + lrat-check + HOL4-verified cake_lpr (s VERIFIED UNSAT)"
}

check_pool "B3_2_k30" "results/master_box3_2_k30_cuts.json" 30 box3 2
check_pool "B4_1_k17" "results/master_box_4_1_k17_cuts.json" 17 box 4 1
check_pool "B3_3_k30" "results/master_box3_3_k30_cuts.json" 30 box3 3
check_pool "U3_6_k32" "results/enumerate_roots_3_6_k33_cuts.json" 32 roots 3 6
KS_BLOCKED="results/enumerate_roots_3_6_k33.json" check_pool "U3_6_k33_unique" "results/enumerate_roots_3_6_k33_cuts.json" 33 roots 3 6
check_pool "U3_12_k32" "results/master_roots_3_12_k32_cuts.json" 32 roots 3 12

# Negative control: truncated LRAT proof must be rejected by BOTH lrat-check AND cake_lpr
head -n 2 "$WORK/results/B3_2_k30.lrat" > "$WORK/results/corrupted.lrat"
if "$WORK/lrat-check" "$WORK/results/B3_2_k30.cnf" "$WORK/results/corrupted.lrat" 2>&1 | grep -q "c VERIFIED"; then
  echo "ERROR: lrat-check accepted a corrupted/truncated LRAT proof!" >&2
  exit 1
fi
if "$WORK/cake_lpr" "$WORK/results/B3_2_k30.cnf" "$WORK/results/corrupted.lrat" 2>&1 | grep -q "s VERIFIED UNSAT"; then
  echo "ERROR: cake_lpr accepted a corrupted/truncated LRAT proof!" >&2
  exit 1
fi
echo "PASS [negative control]: both lrat-check and HOL4-verified cake_lpr rejected truncated LRAT proof."
echo "ALL_DRAT_TRIM_LRAT_CAKE_LPR_CHECKS_PASS"
