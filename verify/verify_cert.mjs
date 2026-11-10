#!/usr/bin/env node
// verify_cert.mjs -- independent verifier for colorability certificates and KS sets.
//
// Plain JavaScript (Node >= 18), no dependencies, no SAT solver.
// Written from the written specification only (see README.md); it shares no
// code with the search program that produced the certificate files.
//
// Usage:
//   node verify_cert.mjs <cert.json> [<cert2.json> ...] [--out <summary.json>]
//   node verify_cert.mjs --ks <rays.json> [--require-critical] [--out <summary.json>]
//
// Exit status: 0 only if every requested check passes.

import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { basename } from 'node:path';

export const VERIFIER_VERSION = '1.0.0';

/** Error raised when the input fails a check (as opposed to a bug in the verifier). */
export class VerifyError extends Error {}

function fail(msg) {
  throw new VerifyError(msg);
}

function isIndex(x, n) {
  return Number.isInteger(x) && x >= 0 && x < n;
}

// ---------------------------------------------------------------------------
// Geometry: rays, orthogonality, bases
// ---------------------------------------------------------------------------

/**
 * Validate the rays and recompute orthogonality from the integer vectors.
 * All arithmetic is exact (BigInt).
 * Checks: d integer >= 2, every ray is a vector of d safe integers, no zero
 * ray, no two proportional rays (this includes equal and opposite rays).
 * Returns { n, orth, pairs } where orth[i][j] === 1 iff ray i . ray j = 0.
 */
export function analyseRays(d, rays) {
  if (!Number.isInteger(d) || d < 2) fail(`"d" must be an integer >= 2, got ${JSON.stringify(d)}`);
  if (!Array.isArray(rays) || rays.length === 0) fail('"rays" must be a non-empty list');
  const n = rays.length;
  const big = new Array(n);
  for (let i = 0; i < n; i++) {
    const v = rays[i];
    if (!Array.isArray(v) || v.length !== d) fail(`ray ${i} is not a vector of length ${d}`);
    let zero = true;
    for (let t = 0; t < d; t++) {
      // Number.isSafeInteger guarantees that JSON.parse did not lose precision.
      if (!Number.isSafeInteger(v[t])) fail(`ray ${i} coordinate ${t} is not a safe integer`);
      if (v[t] !== 0) zero = false;
    }
    if (zero) fail(`ray ${i} is the zero vector`);
    big[i] = v.map((x) => BigInt(x));
  }
  const orth = Array.from({ length: n }, () => new Uint8Array(n));
  let pairs = 0;
  for (let i = 0; i < n; i++) {
    const v = big[i];
    for (let j = i + 1; j < n; j++) {
      const w = big[j];
      // Proportional iff every 2x2 minor vanishes (both vectors are non-zero).
      let proportional = true;
      for (let a = 0; a < d && proportional; a++) {
        for (let b = a + 1; b < d; b++) {
          if (v[a] * w[b] !== v[b] * w[a]) {
            proportional = false;
            break;
          }
        }
      }
      if (proportional) fail(`rays ${i} and ${j} are proportional`);
      let dot = 0n;
      for (let t = 0; t < d; t++) dot += v[t] * w[t];
      if (dot === 0n) {
        orth[i][j] = 1;
        orth[j][i] = 1;
        pairs++;
      }
    }
  }
  return { n, orth, pairs };
}

/**
 * Enumerate ALL sets of d mutually orthogonal rays among the rays listed in
 * `subset` (default: all rays), as ascending index tuples, by plain clique
 * enumeration.
 */
export function enumerateBases(d, orth, subset) {
  const verts = subset ? subset.slice().sort((a, b) => a - b) : Array.from({ length: orth.length }, (_, i) => i);
  const out = [];
  const cur = [];
  const extend = (start) => {
    if (cur.length === d) {
      out.push(cur.slice());
      return;
    }
    for (let p = start; p < verts.length; p++) {
      const v = verts[p];
      let ok = true;
      for (let q = 0; q < cur.length; q++) {
        if (!orth[cur[q]][v]) {
          ok = false;
          break;
        }
      }
      if (ok) {
        cur.push(v);
        extend(p + 1);
        cur.pop();
      }
    }
  };
  extend(0);
  return out;
}

function basisKey(b) {
  return b.slice().sort((x, y) => x - y).join(',');
}

// ---------------------------------------------------------------------------
// Certificate verification
// ---------------------------------------------------------------------------

/**
 * Verify a certificate object.  Never throws on bad input: returns a summary
 * whose `verdict` is 'PASS' or 'FAIL' (with `error` describing the first
 * failed check).
 */
export function verifyCertObject(cert) {
  const summary = {
    d: null,
    k: null,
    rays: null,
    orthogonal_pairs: null,
    bases: null,
    nodes: null,
    nodes_visited: null,
    nodes_accepted_by_rule0: null,
    max_depth: null,
    checks: { rays: false, adj: false, bases: false, tree: false },
    claim: null,
    verdict: 'FAIL',
    error: null,
  };
  try {
    runCertChecks(cert, summary);
    summary.verdict = 'PASS';
    summary.claim = `every set of at most ${summary.k} rays of this ${summary.rays}-ray pool (d=${summary.d}) is colorable`;
  } catch (e) {
    if (e instanceof VerifyError) summary.error = e.message;
    else if (e instanceof RangeError) summary.error = `tree too deep for the verifier (${e.message})`;
    else throw e;
  }
  return summary;
}

function runCertChecks(cert, summary) {
  if (cert === null || typeof cert !== 'object' || Array.isArray(cert)) fail('certificate is not a JSON object');
  for (const key of ['d', 'k', 'rays', 'adj', 'bases', 'tree']) {
    if (!(key in cert)) fail(`missing key "${key}"`);
  }
  const { d, k, rays, adj, bases, tree } = cert;
  if (!Number.isInteger(k) || k < 0) fail(`"k" must be a non-negative integer, got ${JSON.stringify(k)}`);

  // (1) rays and orthogonality ------------------------------------------------
  const { n, orth, pairs } = analyseRays(d, rays);
  summary.d = d;
  summary.k = k;
  summary.rays = n;
  summary.orthogonal_pairs = pairs;
  summary.checks.rays = true;

  if (!Array.isArray(adj) || adj.length !== n) fail(`"adj" must be a list of ${n} neighbour lists`);
  for (let i = 0; i < n; i++) {
    const row = adj[i];
    if (!Array.isArray(row)) fail(`adj[${i}] is not a list`);
    const seen = new Uint8Array(n);
    for (const j of row) {
      if (!isIndex(j, n)) fail(`adj[${i}] contains an invalid ray index ${JSON.stringify(j)}`);
      if (seen[j]) fail(`adj[${i}] lists ray ${j} twice`);
      seen[j] = 1;
    }
    for (let j = 0; j < n; j++) {
      if (seen[j] !== orth[i][j]) {
        fail(
          seen[j]
            ? `adj[${i}] lists ray ${j}, but rays ${i} and ${j} are not orthogonal`
            : `adj[${i}] omits ray ${j}, but rays ${i} and ${j} are orthogonal`,
        );
      }
    }
  }
  summary.checks.adj = true;

  // (2) bases: listed set must equal the set of ALL d-cliques ---------------------
  if (!Array.isArray(bases)) fail('"bases" must be a list');
  const listedKeys = new Map();
  for (let bi = 0; bi < bases.length; bi++) {
    const b = bases[bi];
    if (!Array.isArray(b) || b.length !== d) fail(`bases[${bi}] is not a ${d}-tuple`);
    for (const x of b) if (!isIndex(x, n)) fail(`bases[${bi}] contains an invalid ray index ${JSON.stringify(x)}`);
    for (let a = 0; a < d; a++) {
      for (let c = a + 1; c < d; c++) {
        if (b[a] === b[c]) fail(`bases[${bi}] repeats ray ${b[a]}`);
        if (!orth[b[a]][b[c]]) fail(`bases[${bi}]: rays ${b[a]} and ${b[c]} are not orthogonal`);
      }
    }
    const key = basisKey(b);
    if (listedKeys.has(key)) fail(`bases[${bi}] duplicates bases[${listedKeys.get(key)}]`);
    listedKeys.set(key, bi);
  }
  const computed = enumerateBases(d, orth);
  for (const b of computed) {
    if (!listedKeys.has(b.join(','))) fail(`basis {${b.join(',')}} exists in the pool but is missing from "bases"`);
  }
  // Every listed basis is a d-clique (checked above), the keys are distinct, and
  // every computed clique is listed; equal counts therefore mean equal sets.
  if (computed.length !== bases.length) {
    fail(`"bases" has ${bases.length} entries but the pool has ${computed.length} bases`);
  }
  const nb = bases.length;
  summary.bases = nb;
  summary.checks.bases = true;

  // (3a) structural pass over the whole tree (iterative), counting nodes ----------
  let totalNodes = 0;
  {
    const stack = [tree];
    while (stack.length) {
      const node = stack.pop();
      totalNodes++;
      if (!Array.isArray(node) || node.length !== 2) fail(`tree node #${totalNodes} is not a pair [I, children]`);
      const [I, children] = node;
      if (!Array.isArray(I)) fail(`tree node #${totalNodes}: I is not a list`);
      for (const x of I) if (!isIndex(x, n)) fail(`tree node #${totalNodes}: I contains an invalid ray index ${JSON.stringify(x)}`);
      if (!Array.isArray(children)) fail(`tree node #${totalNodes}: children is not a list`);
      for (const c of children) {
        if (!Array.isArray(c) || c.length !== 2) fail(`tree node #${totalNodes}: a child is not a pair [r, node]`);
        if (!isIndex(c[0], nb)) fail(`tree node #${totalNodes}: child basis index ${JSON.stringify(c[0])} is invalid`);
        stack.push(c[1]);
      }
    }
  }
  summary.nodes = totalNodes;

  // (3b) replay by the checking rule ---------------------------------------------
  const inS = new Uint8Array(n); // membership of S
  let sizeS = 0;
  const F = []; // list of basis indices
  const inI = new Uint8Array(n); // scratch
  const inB = new Uint8Array(n); // scratch
  const path = []; // child positions from the root, for error messages
  let visited = 0;
  let rule0 = 0;
  let maxDepth = 0;
  const where = () => `node at path [${path.join(',')}] (|S|=${sizeS}, |F|=${F.length})`;

  const visit = (node) => {
    visited++;
    if (path.length > maxDepth) maxDepth = path.length;

    // Rule 0: some basis of F lies inside S -> accept.
    for (let t = 0; t < F.length; t++) {
      const fb = bases[F[t]];
      let inside = true;
      for (let a = 0; a < d; a++) {
        if (!inS[fb[a]]) {
          inside = false;
          break;
        }
      }
      if (inside) {
        rule0++;
        return;
      }
    }

    const I = node[0];
    const children = node[1];

    // Rule 1: the rays of I are pairwise non-orthogonal.
    for (let a = 0; a < I.length; a++) {
      for (let b = a + 1; b < I.length; b++) {
        if (orth[I[a]][I[b]]) fail(`rule 1 fails at ${where()}: rays ${I[a]} and ${I[b]} of I are orthogonal`);
      }
    }

    // Rule 2: every basis b with no ray of I satisfies (a), (b) or (c).
    for (const x of I) inI[x] = 1;
    const childBasis = new Set();
    for (const c of children) childBasis.add(c[0]); // bases are pairwise distinct, so index identity is set identity
    // For (b): basis f lies inside S u b  iff  (f minus S) is a subset of b.
    const missing = new Array(F.length);
    for (let t = 0; t < F.length; t++) {
      const fb = bases[F[t]];
      const m = [];
      for (let a = 0; a < d; a++) if (!inS[fb[a]]) m.push(fb[a]);
      missing[t] = m;
    }
    let failure = null;
    for (let bi = 0; bi < nb && failure === null; bi++) {
      const b = bases[bi];
      let hitsI = false;
      let extra = 0;
      for (let a = 0; a < d; a++) {
        if (inI[b[a]]) hitsI = true;
        if (!inS[b[a]]) extra++;
      }
      if (hitsI) continue;
      if (sizeS + extra > k) continue; // (a) |S u b| > k
      if (childBasis.has(bi)) continue; // (c) b is a child basis
      for (let a = 0; a < d; a++) inB[b[a]] = 1;
      let covered = false; // (b) some basis of F inside S u b
      for (let t = 0; t < missing.length && !covered; t++) {
        const m = missing[t];
        let sub = true;
        for (let a = 0; a < m.length; a++) {
          if (!inB[m[a]]) {
            sub = false;
            break;
          }
        }
        if (sub) covered = true;
      }
      for (let a = 0; a < d; a++) inB[b[a]] = 0;
      if (!covered) {
        failure = `rule 2 fails at ${where()}: basis #${bi} {${b.join(',')}} contains no ray of I, |S u b| = ${sizeS + extra} <= k = ${k}, no basis of F lies inside S u b, and it is not a child basis`;
      }
    }
    for (const x of I) inI[x] = 0;
    if (failure !== null) fail(failure);

    // Rule 3: child j is accepted in state (S u r_j, F + [r_1 .. r_{j-1}]).
    for (let j = 0; j < children.length; j++) {
      const r = children[j][0];
      const rb = bases[r];
      const added = [];
      for (let a = 0; a < d; a++) {
        if (!inS[rb[a]]) {
          inS[rb[a]] = 1;
          added.push(rb[a]);
        }
      }
      sizeS += added.length;
      path.push(j);
      visit(children[j][1]);
      path.pop();
      for (const x of added) inS[x] = 0;
      sizeS -= added.length;
      F.push(r);
    }
    F.length -= children.length;
  };

  visit(tree);
  if (sizeS !== 0 || F.length !== 0) throw new Error('internal error: state not restored after replay');
  summary.nodes_visited = visited;
  summary.nodes_accepted_by_rule0 = rule0;
  summary.max_depth = maxDepth;
  summary.checks.tree = true;
}

export function sha256Hex(buf) {
  return createHash('sha256').update(buf).digest('hex');
}

/** Read, hash and verify one certificate file. */
export function verifyCertFile(path) {
  const buf = readFileSync(path);
  const head = { file: basename(path), sha256: sha256Hex(buf), bytes: buf.length };
  let cert;
  try {
    cert = JSON.parse(buf.toString('utf8'));
  } catch (e) {
    return { ...head, verdict: 'FAIL', error: `not valid JSON: ${e.message}` };
  }
  return { ...head, ...verifyCertObject(cert) };
}

// ---------------------------------------------------------------------------
// Colorability by exhaustive backtracking (no solver)
// ---------------------------------------------------------------------------

/**
 * Method A.  Decide whether the rays in `subset` admit f : subset -> {0,1}
 * with no two orthogonal rays both 1 and a 1 in every basis inside `subset`.
 * Branches on an uncovered basis with the fewest free rays: one of its rays
 * must take value 1.  Exhaustive.  Returns { colorable, ones, nodes, bases }.
 */
export function decideColorable(d, orth, subset) {
  const n = orth.length;
  const verts = subset ? subset.slice() : Array.from({ length: n }, (_, i) => i);
  const bases = enumerateBases(d, orth, verts);
  const val = new Int8Array(n).fill(-1); // -1 free, 0, 1 (only entries of `verts` are used)
  const trail = [];
  let nodes = 0;
  const assign = (x, v) => {
    val[x] = v;
    trail.push(x);
  };
  const undoTo = (mark) => {
    while (trail.length > mark) val[trail.pop()] = -1;
  };
  const rec = () => {
    nodes++;
    let best = null;
    let bestFree = Infinity;
    for (const b of bases) {
      let has1 = false;
      let free = 0;
      for (let a = 0; a < d; a++) {
        const v = val[b[a]];
        if (v === 1) {
          has1 = true;
          break;
        }
        if (v === -1) free++;
      }
      if (has1) continue;
      if (free === 0) return false; // basis entirely 0
      if (free < bestFree) {
        bestFree = free;
        best = b;
      }
    }
    if (best === null) return true; // every basis has a 1
    const entry = trail.length;
    for (let a = 0; a < d; a++) {
      const x = best[a];
      if (val[x] !== -1) continue;
      const mark = trail.length;
      assign(x, 1);
      for (const y of verts) {
        if (!orth[x][y]) continue;
        if (val[y] === 1) throw new Error('internal error: free ray with a neighbour of value 1');
        if (val[y] === -1) assign(y, 0);
      }
      if (rec()) return true; // keep the assignment as the witness
      undoTo(mark);
      assign(x, 0); // x = 1 is exhausted below this node
    }
    undoTo(entry);
    return false; // every ray of `best` is forced to 0
  };
  const colorable = rec();
  let ones = null;
  if (colorable) {
    ones = verts.filter((x) => val[x] === 1).sort((a, b) => a - b);
    checkColoring(d, orth, verts, bases, ones); // independent check of the witness
  }
  return { colorable, ones, nodes, bases: bases.length };
}

/** Check directly that the rays `ones` (value 1) form a valid coloring of `verts`. */
export function checkColoring(d, orth, verts, bases, ones) {
  const is1 = new Uint8Array(orth.length);
  const inV = new Uint8Array(orth.length);
  for (const x of verts) inV[x] = 1;
  for (const x of ones) {
    if (!inV[x]) throw new Error('internal error: coloring uses a ray outside the set');
    is1[x] = 1;
  }
  for (let a = 0; a < ones.length; a++) {
    for (let b = a + 1; b < ones.length; b++) {
      if (orth[ones[a]][ones[b]]) throw new Error('internal error: witness coloring has two orthogonal rays of value 1');
    }
  }
  for (const b of bases) {
    if (!b.some((x) => is1[x])) throw new Error('internal error: witness coloring leaves a basis without value 1');
  }
  return true;
}

/**
 * Method B (cross-check, deliberately different): assign the rays one at a
 * time in the given order, value 1 then 0, rejecting as soon as two
 * orthogonal rays are both 1 or a fully assigned basis has no 1.
 * Returns { colorable, nodes } or { colorable: null } if `nodeLimit` is hit.
 */
export function decideColorableByRayOrder(d, orth, subset, nodeLimit = 2e8) {
  const n = orth.length;
  const verts = subset ? subset.slice() : Array.from({ length: n }, (_, i) => i);
  const m = verts.length;
  const pos = new Int32Array(n).fill(-1);
  verts.forEach((x, p) => (pos[x] = p));
  const bases = enumerateBases(d, orth, verts);
  // closing[p] = bases whose last ray (in assignment order) is at position p
  const closing = Array.from({ length: m }, () => []);
  for (const b of bases) {
    let last = -1;
    for (const x of b) if (pos[x] > last) last = pos[x];
    closing[last].push(b);
  }
  const earlier = verts.map((x, p) => verts.filter((y, q) => q < p && orth[x][y]));
  const val = new Int8Array(n);
  let nodes = 0;
  let aborted = false;
  const rec = (p) => {
    if (p === m) return true;
    if (++nodes > nodeLimit) {
      aborted = true;
      return false;
    }
    const x = verts[p];
    for (let v = 1; v >= 0; v--) {
      if (v === 1 && earlier[p].some((y) => val[y] === 1)) continue;
      val[x] = v;
      let ok = true;
      for (const b of closing[p]) {
        if (!b.some((y) => val[y] === 1)) {
          ok = false;
          break;
        }
      }
      if (ok && rec(p + 1)) return true;
      if (aborted) return false;
    }
    val[x] = 0;
    return false;
  };
  const colorable = rec(0);
  return aborted ? { colorable: null, nodes } : { colorable, nodes };
}

/**
 * Analyse a ray set {"d":..,"rays":[..]}: orthogonal pairs, bases, colorability
 * (KS or not), and criticality (is every one-ray-deleted subset colorable?).
 */
export function analyseKSObject(obj) {
  const summary = {
    d: null,
    rays: null,
    orthogonal_pairs: null,
    bases: null,
    colorable: null,
    search_nodes: null,
    cross_check: null,
    critical: null,
    removals_colorable: null,
    removals_not_colorable: null,
    verdict: 'FAIL',
    error: null,
  };
  try {
    if (obj === null || typeof obj !== 'object' || Array.isArray(obj)) fail('input is not a JSON object');
    for (const key of ['d', 'rays']) if (!(key in obj)) fail(`missing key "${key}"`);
    const { d, rays } = obj;
    const { n, orth, pairs } = analyseRays(d, rays);
    summary.d = d;
    summary.rays = n;
    summary.orthogonal_pairs = pairs;
    const all = Array.from({ length: n }, (_, i) => i);
    const res = decideColorable(d, orth, all);
    summary.bases = res.bases;
    summary.colorable = res.colorable;
    summary.search_nodes = res.nodes;
    const other = decideColorableByRayOrder(d, orth, all);
    if (other.colorable === null) summary.cross_check = 'skipped (node limit)';
    else if (other.colorable !== res.colorable) throw new Error('internal error: the two backtracking methods disagree');
    else summary.cross_check = `agrees (ray-order search, ${other.nodes} nodes)`;
    // Criticality: remove each ray in turn.
    const stillKS = [];
    let col = 0;
    for (let i = 0; i < n; i++) {
      const rest = all.filter((x) => x !== i);
      const r = decideColorable(d, orth, rest);
      if (r.colorable) col++;
      else stillKS.push(i);
    }
    summary.removals_colorable = col;
    summary.removals_not_colorable = stillKS;
    summary.critical = !res.colorable && stillKS.length === 0;
    summary.verdict = res.colorable
      ? 'COLORABLE (not a KS set)'
      : summary.critical
        ? 'KS set (not colorable), critical'
        : 'KS set (not colorable), not critical';
  } catch (e) {
    if (e instanceof VerifyError) summary.error = e.message;
    else throw e;
  }
  return summary;
}

export function analyseKSFile(path) {
  const buf = readFileSync(path);
  const head = { file: basename(path), sha256: sha256Hex(buf), bytes: buf.length };
  let obj;
  try {
    obj = JSON.parse(buf.toString('utf8'));
  } catch (e) {
    return { ...head, verdict: 'FAIL', error: `not valid JSON: ${e.message}` };
  }
  return { ...head, ...analyseKSObject(obj) };
}

// ---------------------------------------------------------------------------
// Command line
// ---------------------------------------------------------------------------

function main(argv) {
  const files = [];
  let ks = false;
  let requireCritical = false;
  let out = null;
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--ks') ks = true;
    else if (a === '--require-critical') requireCritical = true;
    else if (a === '--out') out = argv[++i];
    else if (a === '-h' || a === '--help') {
      console.log(
        'usage:\n  node verify_cert.mjs <cert.json> [...] [--out file]\n  node verify_cert.mjs --ks <rays.json> [...] [--require-critical] [--out file]',
      );
      return 0;
    } else if (a.startsWith('--')) {
      console.error(`unknown option ${a}`);
      return 2;
    } else files.push(a);
  }
  if (files.length === 0) {
    console.error('no input file given (try --help)');
    return 2;
  }
  const results = [];
  let ok = true;
  for (const f of files) {
    let res;
    try {
      res = ks ? analyseKSFile(f) : verifyCertFile(f);
    } catch (e) {
      if (e && e.code) res = { file: basename(f), verdict: 'FAIL', error: `cannot read file: ${e.code}` };
      else throw e;
    }
    res = { mode: ks ? 'ks' : 'certificate', verifier: `verify_cert.mjs ${VERIFIER_VERSION}`, ...res };
    results.push(res);
    console.log(JSON.stringify(res, null, 2));
    if (ks) {
      if (res.error || res.colorable !== false) ok = false;
      if (requireCritical && res.critical !== true) ok = false;
    } else if (res.verdict !== 'PASS') ok = false;
  }
  if (out) writeFileSync(out, JSON.stringify(results.length === 1 ? results[0] : results, null, 2) + '\n');
  return ok ? 0 : 1;
}

const invoked = process.argv[1] ? basename(process.argv[1]).toLowerCase() : '';
if (invoked === 'verify_cert.mjs' || invoked === 'verify_cert') {
  process.exitCode = main(process.argv.slice(2));
}
