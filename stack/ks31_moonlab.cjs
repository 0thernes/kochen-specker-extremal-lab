// ks31_moonlab.cjs -- stage 1 of the "stack" demonstration of the 31-ray
// Kochen-Specker (KS) set in results/ks31_box3_H2.json.
//
// HONEST LABELLING
//   * Moonlab (tsotchke/moonlab v1.2.1, vendored prebuilt WASM, MIT) is used here
//     as a CLASSICAL STATE-VECTOR SIMULATOR running on the CPU under Node.
//     Nothing in this file is an experiment on quantum hardware.
//   * The pseudo-random states come from a deterministic integer stream built on
//     the three integer mixers of tsotchke/quantum_rng ("quantum-inspired"
//     mixers; ordinary deterministic arithmetic, NOT quantum randomness).
//   * What is demonstrated is a numerical illustration (double precision,
//     tolerance 1e-12) of facts that are exact for integer vectors; the exact
//     statements are re-verified in integers by the other stages.
//
// Embedding.  A qutrit is embedded in two qubits: qutrit basis vector e_k
// (k = 0,1,2) is the 2-qubit basis state with amplitude index k, i.e.
// |00>, |01>, |10> in the "index written in binary" notation; the amplitude of
// index 3 (|11>) is 0.  A ray (x,y,z) is the state (x|00> + y|01> + z|10>)/norm.
//
// Run:  node stack/ks31_moonlab.cjs          (exit code 0 = all checks passed)
'use strict';
const path = require('node:path');
const fs = require('node:fs');

const ROOT = path.join(__dirname, '..');
const KS_JSON = path.join(ROOT, 'results', 'ks31_box3_H2.json');
const MOONLAB_JS = path.join(ROOT, 'third_party', 'moonlab', 'moonlab.js');
const TOL = 1e-12;
const N_STATES = 2000;

// ---------------------------------------------------------------------------
// Deterministic stream: JavaScript BigInt port of the integer mixers in
// tsotchke/quantum_rng src/quantum_rng/quantum_rng.c (commit 1a77e77, MIT,
// Copyright (c) 2024 Tsotchke): splitmix64 (upstream lines 61-70), hadamard_mix
// (lines 73-83), absorb_seed (lines 113-120), constants lines 12-24.
// The counter-mode stream on top of them is OUR construction (not an upstream
// generator):  S = absorb_seed(le64(seed));  out_i = hadamard_mix(S + (i+1)*GOLDEN_RATIO).
// The C twin of this code is stack/ks31_qrng.c.
// ---------------------------------------------------------------------------
const MASK = (1n << 64n) - 1n;
const QRNG_FINE_STRUCTURE = 0x7297352743776A1Bn;
const QRNG_PLANCK = 0x6955927086495225n;
const QRNG_GOLDEN_RATIO = 0x9E3779B97F4A7C15n;
const QRNG_SQRT2 = 0x6A09E667F3BCC908n;
const QRNG_HEISENBERG = 0xC13FA9A902A6328Fn;
const QRNG_SCHRODINGER = 0x91E10DA5C79E7B1Dn;
const QRNG_PAULI_X = 0x4C957F2D8A1E6B3Cn;
const QRNG_PAULI_Y = 0xD3E99E3B6C1A4F78n;
const QRNG_PAULI_Z = 0x8F142FC07892A5B6n;

function splitmix64(x) {
  x ^= x >> 30n;
  x = (x * 0xbf58476d1ce4e5b9n) & MASK;
  x ^= x >> 27n;
  x = (x * 0x94d049bb133111ebn) & MASK;
  x ^= x >> 31n;
  x = (x * QRNG_HEISENBERG) & MASK;
  x ^= x >> 29n;
  return x;
}
function hadamardMix(x) {
  x = splitmix64(x);
  x ^= (QRNG_PAULI_X * (x >> 12n)) & MASK;
  x = (x * QRNG_FINE_STRUCTURE) & MASK;
  x ^= (QRNG_PAULI_Y * (x >> 25n)) & MASK;
  x = (x * QRNG_PLANCK) & MASK;
  x ^= (QRNG_PAULI_Z * (x >> 27n)) & MASK;
  x = (x * QRNG_SCHRODINGER) & MASK;
  x ^= x >> 13n;
  return x;
}
function absorbSeed(bytes) {
  const len = BigInt(bytes.length);
  let h = QRNG_SQRT2 ^ splitmix64((len + QRNG_GOLDEN_RATIO) & MASK);
  for (const b of bytes) {
    h ^= (BigInt(b) + QRNG_GOLDEN_RATIO + ((h << 6n) & MASK) + (h >> 2n)) & MASK;
    h = hadamardMix(h);
  }
  return h ^ splitmix64(len);
}
function le64(seed) {
  const out = [];
  let s = BigInt(seed) & MASK;
  for (let i = 0; i < 8; i++) { out.push(Number(s & 0xFFn)); s >>= 8n; }
  return out;
}
class CounterStream {
  constructor(seed) { this.S = absorbSeed(le64(seed)); this.i = 0n; }
  next() {                                   // -> BigInt in [0, 2^64)
    this.i += 1n;
    return hadamardMix((this.S + this.i * QRNG_GOLDEN_RATIO) & MASK);
  }
  // Integer-to-double rule (documented, exact, platform independent):
  //   u = (x >> 11) / 2^53   in [0,1)   (top 53 bits; exactly representable)
  //   unit()   returns u
  //   signed() returns 2u - 1 in [-1,1) (exact in binary64)
  unit() { return Number(this.next() >> 11n) / 9007199254740992; }
  signed() { return 2 * this.unit() - 1; }
}
const hex16 = (x) => x.toString(16).padStart(16, '0');

// ---------------------------------------------------------------------------
(async () => {
  const lines = [];
  const say = (s) => { console.log(s); lines.push(s); };
  let failures = 0;
  const check = (name, ok, detail) => {
    if (!ok) failures++;
    say(`[moonlab] ${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  (' + detail + ')' : ''}`);
    return ok;
  };

  say('[moonlab] Moonlab is a CLASSICAL state-vector simulator (WASM on CPU); no quantum hardware is involved.');
  const ks = JSON.parse(fs.readFileSync(KS_JSON, 'utf8'));
  const rays = ks.rays;
  const n = rays.length;
  check('31 integer rays in R^3 loaded', n === 31 && rays.every((r) => r.length === 3 && r.every(Number.isInteger)), `n=${n}`);

  // exact integer facts (reference for the floating-point simulator checks)
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const orthInt = [];
  for (let i = 0; i < n; i++) { orthInt.push([]); for (let j = 0; j < n; j++) orthInt[i].push(i !== j && dot(rays[i], rays[j]) === 0); }
  const pairsInt = [];
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) if (orthInt[i][j]) pairsInt.push([i, j]);

  // ---- simulator plumbing (layout as in the vendored PROVENANCE note) --------
  const factory = require(MOONLAB_JS);
  const M = await factory({});
  const STATE_BYTES = 256;
  function newState(nq) {
    const p = M._malloc(STATE_BYTES);
    M.HEAPU8.fill(0, p, p + STATE_BYTES);
    const rc = M._quantum_state_init(p, nq);
    if (rc !== 0) throw new Error('quantum_state_init rc=' + rc);
    return p;
  }
  const dimOf = (p) => M.HEAPU32[(p + 4) >> 2];
  const ampPtr = (p) => M.HEAPU32[(p + 8) >> 2];
  function writeAmps(p, amps) {              // amps: 4 x [re, im], written into the simulator's own buffer
    const a = ampPtr(p) >> 3;
    for (let i = 0; i < 4; i++) { M.HEAPF64[a + 2 * i] = amps[i][0]; M.HEAPF64[a + 2 * i + 1] = amps[i][1]; }
  }
  function normalise(p) {
    const rc = M._quantum_state_normalize(p);
    if (rc !== 0) throw new Error('quantum_state_normalize rc=' + rc);
  }
  // |<a|b>|^2 computed from the two simulator amplitude buffers (all 4 amplitudes)
  function overlap2(pa, pb) {
    const a = ampPtr(pa) >> 3, b = ampPtr(pb) >> 3;
    let re = 0, im = 0;
    for (let i = 0; i < 4; i++) {
      const ar = M.HEAPF64[a + 2 * i], ai = M.HEAPF64[a + 2 * i + 1];
      const br = M.HEAPF64[b + 2 * i], bi = M.HEAPF64[b + 2 * i + 1];
      re += ar * br + ai * bi;               // conj(a) * b
      im += ar * bi - ai * br;
    }
    return re * re + im * im;
  }
  const norm2 = (p) => overlap2(p, p);       // = (sum |amp|^2)^2, equals 1 for a unit vector
  const amp3 = (p) => { const a = ampPtr(p) >> 3; return Math.hypot(M.HEAPF64[a + 6], M.HEAPF64[a + 7]); };
  const rayAmps = (r) => [[r[0], 0], [r[1], 0], [r[2], 0], [0, 0]];

  // ---- (a) orthogonality structure from simulator amplitudes ----------------
  const rayState = rays.map(() => newState(2));
  check('simulator state dimension is 4 (two qubits)', rayState.every((p) => dimOf(p) === 4));
  rays.forEach((r, i) => { writeAmps(rayState[i], rayAmps(r)); normalise(rayState[i]); });
  check('all 31 prepared ray states are unit vectors with zero |11> amplitude',
    rayState.every((p) => Math.abs(norm2(p) - 1) < TOL && amp3(p) === 0));

  let simPairs = 0, mismatch = 0, maxOrthOverlap = 0, minNonOrthOverlap = Infinity;
  const orthSim = rays.map(() => new Array(n).fill(false));
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    const o = overlap2(rayState[i], rayState[j]);
    const isOrth = o < TOL;
    if (isOrth) { simPairs++; maxOrthOverlap = Math.max(maxOrthOverlap, o); } else minNonOrthOverlap = Math.min(minNonOrthOverlap, o);
    if (isOrth !== orthInt[i][j]) mismatch++;
    orthSim[i][j] = orthSim[j][i] = isOrth;
  }
  check('pairs with |<u|v>|^2 < 1e-12 are exactly the integer-orthogonal pairs', mismatch === 0,
    `465 pairs, mismatches=${mismatch}, max orthogonal overlap=${maxOrthOverlap.toExponential(2)}, min non-orthogonal overlap=${minNonOrthOverlap.toFixed(6)}`);
  check('number of orthogonal pairs is 71', simPairs === 71 && pairsInt.length === 71, `simulator=${simPairs}, integer=${pairsInt.length}`);
  const bases = [];
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) if (orthSim[i][j])
    for (let k = j + 1; k < n; k++) if (orthSim[i][k] && orthSim[j][k]) bases.push([i, j, k]);
  check('number of mutually orthogonal triples (bases) is 17', bases.length === 17, `found ${bases.length}`);
  const pairs = pairsInt;

  // ---- stream known-answer test ---------------------------------------------
  const KAT = ['5df9ef9ba7cdcca2', 'ddb5674ec90579d9', 'e350bb351fce2beb', '20275c35a4eaee84', '2f7cdc01c2c0ba7d'];
  const kat = new CounterStream(1);
  const first8 = [];
  for (let i = 0; i < 8; i++) first8.push(hex16(kat.next()));
  check('JS BigInt counter-mode stream reproduces the 5 seed-1 outputs of the C test',
    KAT.every((v, i) => v === first8[i]), first8.slice(0, 5).join(' '));
  say('[moonlab] stream first 8 outputs (seed 1): ' + first8.join(' '));
  const mixKat = { splitmix64_1: hex16(splitmix64(1n)), hadamard_mix_1: hex16(hadamardMix(1n)), absorb_seed_le64_1: hex16(absorbSeed(le64(1))) };
  check('mixer known answers splitmix64(1), hadamard_mix(1)',
    mixKat.splitmix64_1 === '6b6a95bfe299a90e' && mixKat.hadamard_mix_1 === '7590e4342b418e25',
    `${mixKat.splitmix64_1} ${mixKat.hadamard_mix_1}`);

  // ---- (b) state independence on N pseudo-random qutrit states ---------------
  // Per state: 6 stream outputs -> (re,im) of the three qutrit amplitudes via
  // signed(); then 5 outputs -> gate angles 2*pi*unit().  A draw with squared
  // norm below 1e-6 would be rejected and redrawn (counted; expected 0).
  // The same gate sequence G is applied in the simulator to psi AND to each of
  // the 31 ray states, and p_v = |<G v|G psi>|^2 is computed from the simulator
  // buffers (all four amplitudes).  The un-gated value |<v|psi>|^2 is computed
  // too; unitarity of the simulated gates makes the two agree.
  function applyGates(p, g) {
    let rc = 0;
    rc |= M._gate_hadamard(p, 0);
    rc |= M._gate_cnot(p, 0, 1);
    rc |= M._gate_u3(p, 1, g[0], g[1], g[2]);
    rc |= M._gate_ry(p, 0, g[3]);
    rc |= M._gate_cnot(p, 1, 0);
    rc |= M._gate_rz(p, 1, g[4]);
    if (rc !== 0) throw new Error('gate rc=' + rc);
  }
  const stream = new CounterStream(1);
  const psiRaw = newState(2), psiGate = newState(2), rayGate = newState(2);
  let rejected = 0, maxPairSum = 0, maxBasisDev = 0, maxTotalDev = 0, maxGateDev = 0, maxLeak = 0;
  let pairViol = 0, basisViol = 0, totalViol = 0, gateViol = 0;
  const p = new Float64Array(n), p0 = new Float64Array(n);
  for (let s = 0; s < N_STATES; s++) {
    let c;
    for (;;) {
      c = []; for (let k = 0; k < 6; k++) c.push(stream.signed());
      if (c.reduce((a, x) => a + x * x, 0) >= 1e-6) break;
      rejected++;
    }
    const g = []; for (let k = 0; k < 5; k++) g.push(2 * Math.PI * stream.unit());
    const amps = [[c[0], c[1]], [c[2], c[3]], [c[4], c[5]], [0, 0]];
    writeAmps(psiRaw, amps); normalise(psiRaw);
    writeAmps(psiGate, amps); normalise(psiGate); applyGates(psiGate, g);
    for (let v = 0; v < n; v++) {
      p0[v] = overlap2(rayState[v], psiRaw);
      writeAmps(rayGate, rayAmps(rays[v])); normalise(rayGate); applyGates(rayGate, g);
      p[v] = overlap2(rayGate, psiGate);
      const d = Math.abs(p[v] - p0[v]);
      if (d > maxGateDev) maxGateDev = d;
      if (d > TOL) gateViol++;
    }
    maxLeak = Math.max(maxLeak, Math.abs(norm2(psiGate) - 1));
    for (const [i, j] of pairs) {
      const t = p[i] + p[j];
      if (t > maxPairSum) maxPairSum = t;
      if (t > 1 + TOL) pairViol++;
    }
    let total = 0;
    for (const [i, j, k] of bases) {
      const t = p[i] + p[j] + p[k];
      const d = Math.abs(t - 1);
      if (d > maxBasisDev) maxBasisDev = d;
      if (d > TOL) basisViol++;
      total += t;
    }
    const dt = Math.abs(total - bases.length);
    if (dt > maxTotalDev) maxTotalDev = dt;
    if (dt > 17 * TOL) totalViol++;
  }
  say(`[moonlab] ${N_STATES} pseudo-random qutrit states (seed 1, ${stream.i} stream outputs used, ${rejected} draws rejected)`);
  check('gated and un-gated probabilities agree within 1e-12 (simulated gates are unitary)', gateViol === 0,
    `max |p_gated - p_plain| = ${maxGateDev.toExponential(2)}, max |norm^2 - 1| after gates = ${maxLeak.toExponential(2)}`);
  check('p_u + p_v <= 1 + 1e-12 for every orthogonal pair and every state', pairViol === 0,
    `${N_STATES} x ${pairs.length} sums, max = ${maxPairSum.toFixed(15)}`);
  check('sum of p over each of the 17 bases equals 1 within 1e-12 for every state', basisViol === 0,
    `${N_STATES} x ${bases.length} sums, max deviation = ${maxBasisDev.toExponential(2)}`);
  check('sum over all 17 bases equals 17 for every state', totalViol === 0, `max deviation = ${maxTotalDev.toExponential(2)}`);

  // ---- (c) exact classical maximum by exhaustive backtracking ----------------
  // 0/1 assignments to the 31 rays such that two orthogonal rays never both get
  // 1.  Under that rule a basis holds at most one 1, so "exactly one 1" means
  // "hit".  Rays are decided in index order; a ray may get 1 only if no earlier
  // orthogonal ray has 1.  The only pruning is the obvious bound "bases already
  // hit + bases that can still be hit"; otherwise the search is exhaustive.
  const basesOf = rays.map(() => []);
  bases.forEach((b, bi) => b.forEach((v) => basesOf[v].push(bi)));
  const value = new Int8Array(n);            // 1 = assigned 1
  const hit = new Int32Array(bases.length);
  const lastRay = bases.map((b) => Math.max(...b));
  let best = -1, bestAssign = null, nodes = 0;
  function search(v, nHit) {
    nodes++;
    let possible = nHit;                      // bases not hit that still have an undecided, unblocked ray
    for (let b = 0; b < bases.length; b++) if (hit[b] === 0 && lastRay[b] >= v) {
      let can = false;
      for (const w of bases[b]) if (w >= v) { let blocked = false; for (let u = 0; u < v; u++) if (value[u] && orthInt[u][w]) { blocked = true; break; } if (!blocked) { can = true; break; } }
      if (can) possible++;
    }
    if (possible <= best) return;
    if (v === n) { best = nHit; bestAssign = Array.from(value); return; }
    let free = true;
    for (let u = 0; u < v; u++) if (value[u] && orthInt[u][v]) { free = false; break; }
    if (free) {
      value[v] = 1; let add = 0;
      for (const b of basesOf[v]) { if (hit[b] === 0) add++; hit[b]++; }
      search(v + 1, nHit + add);
      for (const b of basesOf[v]) hit[b]--;
      value[v] = 0;
    }
    search(v + 1, nHit);
  }
  search(0, 0);
  // independent re-check of the witness
  let witnessOk = bestAssign !== null;
  if (witnessOk) {
    for (const [i, j] of pairs) if (bestAssign[i] && bestAssign[j]) witnessOk = false;
    const cnt = bases.filter((b) => b.reduce((a, v) => a + bestAssign[v], 0) === 1).length;
    if (cnt !== best) witnessOk = false;
  }
  // Second pass with NO pruning at all: visit every admissible 0/1 assignment
  // (every set of pairwise non-orthogonal rays), count them, and record the
  // maximum and how many assignments attain it.
  let admissible = 0, plainBest = -1, plainBestCount = 0;
  (function plain(v, nHit) {
    if (v === n) {
      admissible++;
      if (nHit > plainBest) { plainBest = nHit; plainBestCount = 1; } else if (nHit === plainBest) plainBestCount++;
      return;
    }
    let free = true;
    for (let u = 0; u < v; u++) if (value[u] && orthInt[u][v]) { free = false; break; }
    if (free) {
      value[v] = 1; let add = 0;
      for (const b of basesOf[v]) { if (hit[b] === 0) add++; hit[b]++; }
      plain(v + 1, nHit + add);
      for (const b of basesOf[v]) hit[b]--;
      value[v] = 0;
    }
    plain(v + 1, nHit);
  })(0, 0);
  const Mcl = best;
  check('classical maximum M (bases with exactly one 1, orthogonal rays never both 1) is below 17', Mcl < 17 && witnessOk,
    `M = ${Mcl}, search nodes = ${nodes}, witness re-checked`);
  check('unpruned enumeration of all admissible assignments gives the same maximum', plainBest === Mcl,
    `${admissible} admissible assignments, maximum ${plainBest} attained by ${plainBestCount} of them`);
  say(`[moonlab] classical optimum witness (rays assigned 1): ${bestAssign.map((x, i) => (x ? i : -1)).filter((i) => i >= 0).join(' ')}`);
  say(`[moonlab] STATE-INDEPENDENT GAP: quantum 17 for every state versus classical at most ${Mcl}`);
  say('[moonlab] ("quantum 17" = sum over the 17 bases of Born probabilities, evaluated numerically on a classical simulator)');

  const result = {
    stage: 'moonlab', ok: failures === 0, failures,
    simulator: 'Moonlab WASM (classical state-vector simulator)', glue_version: M.version || null,
    rays: n, orthogonal_pairs: simPairs, bases: bases.length, bases_list: bases,
    max_orthogonal_overlap: maxOrthOverlap, min_nonorthogonal_overlap: minNonOrthOverlap,
    n_states: N_STATES, stream_seed: 1, stream_outputs_used: Number(stream.i), rejected_draws: rejected,
    stream_first8: first8, mixer_kat: mixKat,
    max_pair_sum: maxPairSum, max_basis_sum_deviation: maxBasisDev, max_total_deviation: maxTotalDev,
    max_gate_invariance_deviation: maxGateDev,
    quantum_value: bases.length, classical_max: Mcl, classical_witness: bestAssign, search_nodes: nodes,
    admissible_assignments: admissible, assignments_attaining_max: plainBestCount,
    tolerance: TOL,
  };
  console.log('RESULT_JSON ' + JSON.stringify(result));
  say(`[moonlab] ${failures === 0 ? 'STAGE PASS' : 'STAGE FAIL'} (${failures} failed checks)`);
  process.exit(failures === 0 ? 0 : 1);
})().catch((e) => { console.error('[moonlab] FAIL  exception: ' + (e && e.stack || e)); process.exit(2); });
