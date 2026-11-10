#!/usr/bin/env node
// test_verify.mjs -- tests for verify_cert.mjs
//
//   node test_verify.mjs
//
// (a) runs the verifier on the three certificate files and the KS file;
// (b) negative tests: corrupted in-memory copies of the certificates must be rejected;
// (c) cross-checks of the colorability search against brute force and against
//     known Kochen-Specker sets.
// Writes ../results/verify_summary.json and exits non-zero on any failure.

import { readFileSync, writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import {
  VERIFIER_VERSION,
  verifyCertFile,
  verifyCertObject,
  analyseKSFile,
  analyseKSObject,
  analyseRays,
  enumerateBases,
  decideColorable,
  decideColorableByRayOrder,
} from './verify_cert.mjs';

const RESULTS = new URL('../results/', import.meta.url);
const resultPath = (name) => fileURLToPath(new URL(name, RESULTS));
const VERIFIER = fileURLToPath(new URL('./verify_cert.mjs', import.meta.url));
const FULL = process.argv.includes('--full'); // exhaustive version of the largest sweep (several minutes)

/**
 * Reference replay: a second, deliberately literal implementation of the
 * checking rule (plain Sets, fresh copies of S and F at every node, Number
 * dot products).  Slow; used only to cross-check the verifier's tree replay.
 * Assumes the geometry part of the certificate (rays, bases) is intact.
 */
function referenceAccepts(cert) {
  const { k, rays, bases, tree } = cert;
  const orthogonal = (i, j) => rays[i].reduce((s, x, t) => s + x * rays[j][t], 0) === 0;
  const sameSet = (a, b) => a.length === b.length && a.every((x) => b.includes(x));
  const accept = (node, S, F) => {
    if (F.some((f) => bases[f].every((x) => S.has(x)))) return true; // rule 0
    const [I, children] = node;
    for (let a = 0; a < I.length; a++) for (let b = a + 1; b < I.length; b++) if (orthogonal(I[a], I[b])) return false; // rule 1
    for (const b of bases) {
      // rule 2
      if (b.some((x) => I.includes(x))) continue;
      const U = new Set([...S, ...b]);
      if (U.size > k) continue;
      if (F.some((f) => bases[f].every((x) => U.has(x)))) continue;
      if (children.some((c) => sameSet(bases[c[0]], b))) continue;
      return false;
    }
    for (let j = 0; j < children.length; j++) {
      // rule 3
      const earlier = children.slice(0, j).map((c) => c[0]);
      if (!accept(children[j][1], new Set([...S, ...bases[children[j][0]]]), [...F, ...earlier])) return false;
    }
    return true;
  };
  return accept(tree, new Set(), []);
}

const CERTS = [
  { file: 'cert_box3_H2_k30.json', d: 3, k: 30, rays: 49 },
  { file: 'cert_box4_H1_k17.json', d: 4, k: 17, rays: 40 },
  { file: 'cert_box3_H3_k30.json', d: 3, k: 30, rays: 97 },
  // the same bound for the whole 145-ray pool, without the reduction to the core
  { file: 'cert_box3_H3full_k30.json', d: 3, k: 30, rays: 145 },
];
const KS_FILE = 'ks31_box3_H2.json';

const report = {
  verifier: `verify_cert.mjs ${VERIFIER_VERSION}`,
  node: process.version,
  certificates: [],
  ks: null,
  negative_tests: [],
  sweeps: [],
  cross_checks: [],
  failures: [],
  verdict: 'FAIL',
};
let checks = 0;

function record(ok, label, detail) {
  checks++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${label}${detail ? ' -- ' + detail : ''}`);
  if (!ok) report.failures.push(label);
  return ok;
}
const short = (s, m = 150) => (s && s.length > m ? s.slice(0, m - 3) + '...' : s);

// ---------------------------------------------------------------------------
// (a) positive runs
// ---------------------------------------------------------------------------
console.log('== (a) certificate files ==');
const loaded = {};
for (const c of CERTS) {
  const res = verifyCertFile(resultPath(c.file));
  report.certificates.push(res);
  loaded[c.file] = JSON.parse(readFileSync(resultPath(c.file), 'utf8'));
  const shapeOk = res.d === c.d && res.k === c.k && res.rays === c.rays;
  record(
    res.verdict === 'PASS' && shapeOk,
    `verify ${c.file}`,
    `verdict=${res.verdict} d=${res.d} k=${res.k} rays=${res.rays} pairs=${res.orthogonal_pairs} bases=${res.bases} nodes=${res.nodes} sha256=${res.sha256}` +
      (res.error ? ` error=${res.error}` : ''),
  );
  record(referenceAccepts(loaded[c.file]) === true, `reference replay also accepts ${c.file}`);
}

console.log('== (a) KS file ==');
const ksRes = analyseKSFile(resultPath(KS_FILE));
report.ks = ksRes;
record(
  ksRes.colorable === false && ksRes.critical === true && !ksRes.error,
  `ks ${KS_FILE}`,
  `rays=${ksRes.rays} pairs=${ksRes.orthogonal_pairs} bases=${ksRes.bases} colorable=${ksRes.colorable} critical=${ksRes.critical} (${ksRes.removals_colorable}/${ksRes.rays} one-ray deletions colorable) verdict="${ksRes.verdict}" sha256=${ksRes.sha256}`,
);

// ---------------------------------------------------------------------------
// (b) negative tests on corrupted in-memory copies
// ---------------------------------------------------------------------------
const base49 = loaded['cert_box3_H2_k30.json'];
const clone = (o) => structuredClone(o);

/** All tree nodes of a certificate object, in preorder. */
function nodesOf(cert) {
  const out = [];
  const walk = (node) => {
    out.push(node);
    for (const c of node[1]) walk(c[1]);
  };
  walk(cert.tree);
  return out;
}

/**
 * Corrupt a copy and require rejection.  With ref=true (corruptions of the
 * tree or of k that leave the certificate well formed) the reference replay
 * must reject it as well.
 */
function expectReject(label, mutate, source = base49, ref = false) {
  const c = clone(source);
  mutate(c);
  const res = verifyCertObject(c);
  let rejected = res.verdict !== 'PASS';
  let note = rejected ? short(res.error) : 'ACCEPTED A CORRUPTED CERTIFICATE';
  if (ref && referenceAccepts(c)) {
    rejected = false;
    note = 'REFERENCE REPLAY DISAGREES (accepts) -- ' + note;
  }
  report.negative_tests.push({ test: label, rejected, reference_checked: ref, reason: res.error });
  record(rejected, `reject: ${label}`, note);
}
const REF = true;

console.log('== (b) negative tests (49-ray certificate unless stated) ==');
{
  const sanity = verifyCertObject(clone(base49));
  record(sanity.verdict === 'PASS', 'control: unmodified in-memory copy passes');
  const lower = clone(base49);
  lower.k -= 1;
  record(verifyCertObject(lower).verdict === 'PASS', 'control: lowering k by one (a weaker claim) still passes');
}

// the four required corruptions
expectReject('delete one child (first child of the root)', (c) => {
  c.tree[1].splice(0, 1);
}, base49, REF);
expectReject('delete one child (last child of the deepest internal node)', (c) => {
  let best = null;
  let bestDepth = -1;
  const walk = (node, depth) => {
    if (node[1].length > 0 && depth > bestDepth) {
      best = node;
      bestDepth = depth;
    }
    for (const ch of node[1]) walk(ch[1], depth + 1);
  };
  walk(c.tree, 0);
  best[1].pop();
}, base49, REF);
expectReject('change one ray index inside the root I (to a ray orthogonal to another ray of I)', (c) => {
  const { orth } = analyseRays(c.d, c.rays);
  const I = c.tree[0];
  for (let p = 0; p < I.length; p++) {
    for (let y = 0; y < c.rays.length; y++) {
      if (I.includes(y)) continue;
      if (I.some((x, q) => q !== p && orth[x][y])) {
        I[p] = y;
        return;
      }
    }
  }
  throw new Error('test setup: no such replacement found');
}, base49, REF);
expectReject('change one ray index inside some I so that I stays pairwise non-orthogonal (first such node in preorder)', (c) => {
  const { orth } = analyseRays(c.d, c.rays);
  for (const node of nodesOf(c)) {
    const I = node[0];
    for (let p = 0; p < I.length; p++) {
      for (let y = 0; y < c.rays.length; y++) {
        if (I.includes(y)) continue;
        if (I.every((x, q) => q === p || !orth[x][y])) {
          I[p] = y;
          return;
        }
      }
    }
  }
  throw new Error('test setup: no such replacement found');
}, base49, REF);
expectReject('raise k by one (30 -> 31)', (c) => {
  c.k += 1;
}, base49, REF);
expectReject('drop one basis from the list (the last one)', (c) => {
  c.bases.pop();
});
expectReject('drop one basis from the list (the first one)', (c) => {
  c.bases.shift();
});

// further corruptions
expectReject('raise k by one in the 40-ray d=4 certificate (17 -> 18)', (c) => void (c.k += 1), loaded['cert_box4_H1_k17.json'], REF);
expectReject('raise k by one in the 97-ray certificate (30 -> 31)', (c) => void (c.k += 1), loaded['cert_box3_H3_k30.json'], REF);
expectReject('remove one neighbour from adj', (c) => {
  const i = c.adj.findIndex((r) => r.length > 0);
  c.adj[i].pop();
});
expectReject('add a false neighbour to adj', (c) => {
  const { orth } = analyseRays(c.d, c.rays);
  const j = orth[0].findIndex((v, idx) => idx !== 0 && !v);
  c.adj[0].push(j);
});
expectReject('change one ray coordinate (ray 0 -> [3,0,1])', (c) => {
  c.rays[0] = [3, 0, 1];
});
expectReject('make two rays proportional (ray 1 = -2 * ray 0)', (c) => {
  c.rays[1] = c.rays[0].map((x) => -2 * x);
});
expectReject('zero ray', (c) => {
  c.rays[5] = [0, 0, 0];
});
expectReject('non-integer ray coordinate', (c) => {
  c.rays[5][0] = 0.5;
});
expectReject('append a bogus basis (three non-orthogonal rays)', (c) => {
  const { orth } = analyseRays(c.d, c.rays);
  for (let a = 0; a < c.rays.length; a++)
    for (let b = a + 1; b < c.rays.length; b++)
      if (!orth[a][b]) {
        c.bases.push([a, b, (b + 1) % c.rays.length]);
        return;
      }
});
expectReject('duplicate a basis in the list', (c) => {
  c.bases.push(c.bases[0].slice().reverse());
});
expectReject('replace the whole tree by an empty leaf', (c) => {
  c.tree = [[], []];
}, base49, REF);
expectReject('empty the root I', (c) => {
  c.tree[0] = [];
}, base49, REF);
expectReject('child basis index out of range', (c) => {
  c.tree[1][0][0] = c.bases.length;
});
expectReject('ray index out of range inside an I', (c) => {
  c.tree[0][0] = c.rays.length;
});
expectReject('k given as a string', (c) => {
  c.k = '30';
});
expectReject('wrong dimension d', (c) => {
  c.d = 4;
});
expectReject('missing "tree" key', (c) => {
  delete c.tree;
});
expectReject('malformed node (children not a list)', (c) => {
  c.tree[1][0][1] = [[], 0];
});

// Single-mutation sweeps.  Each generator mutates one working copy in place,
// emits it, and undoes the mutation.
//
// mode 'all'  : every mutant must be rejected (geometry corruptions).
// mode 'tree' : mutations of the tree.  A mutant may legitimately remain a
//   valid certificate (e.g. a ray of I replaced by another ray that hits the
//   same bases); by the soundness argument of the rule it then still proves
//   the claim.  Here the verifier is compared with the reference replay: every
//   accepted mutant must be accepted by the reference, and every `refEvery`-th
//   rejected mutant must be rejected by it.  Counts are reported.
console.log('== (b) single-mutation sweeps ==');
function sweep(label, source, generate, mode, refEvery = 1) {
  let total = 0;
  let rejected = 0;
  let refChecked = 0;
  let refDisagree = 0;
  const acceptedExamples = [];
  const t0 = Date.now();
  const work = clone(source);
  generate(work, (what) => {
    total++;
    const pass = verifyCertObject(work).verdict === 'PASS';
    if (pass) {
      if (acceptedExamples.length < 5) acceptedExamples.push(what);
    } else rejected++;
    if (mode === 'tree' && (pass || rejected % refEvery === 0)) {
      refChecked++;
      if (referenceAccepts(work) !== pass) refDisagree++;
    }
  });
  const intact = JSON.stringify(work) === JSON.stringify(source);
  const accepted = total - rejected;
  const entry = {
    sweep: label,
    mode,
    mutants: total,
    rejected,
    accepted,
    accepted_examples: acceptedExamples,
    reference_checked: refChecked,
    reference_disagreements: refDisagree,
    ms: Date.now() - t0,
  };
  report.sweeps.push(entry);
  const ok = intact && total > 0 && refDisagree === 0 && (mode === 'tree' || accepted === 0);
  record(
    ok,
    `sweep: ${label}`,
    `${total} mutants, ${rejected} rejected, ${accepted} accepted` +
      (mode === 'tree' ? `; reference replay agrees on ${refChecked - refDisagree}/${refChecked} checked` : '') +
      (accepted ? ` (accepted e.g. ${acceptedExamples.slice(0, 2).join('; ')})` : '') +
      (intact ? '' : ' TEST BUG: working copy not restored'),
  );
  return entry;
}

const genDeleteChild = (w, emit) => {
  nodesOf(w).forEach((node, ni) => {
    for (let j = 0; j < node[1].length; j++) {
      const [removed] = node[1].splice(j, 1);
      emit(`node ${ni} child ${j}`);
      node[1].splice(j, 0, removed);
    }
  });
};
// perPosition = Infinity: every ray outside I; otherwise a fixed spread of that many replacements.
const genChangeI = (perPosition) => (w, emit) => {
  nodesOf(w).forEach((node, ni) => {
    const I = node[0];
    for (let p = 0; p < I.length; p++) {
      const old = I[p];
      let cand = [];
      for (let y = 0; y < w.rays.length; y++) if (!I.includes(y)) cand.push(y);
      if (cand.length > perPosition) {
        const picked = [];
        for (let t = 0; t < perPosition; t++) picked.push(cand[(ni * 5 + p * 3 + Math.floor((t * cand.length) / perPosition)) % cand.length]);
        cand = picked;
      }
      for (const y of cand) {
        I[p] = y;
        emit(`node ${ni} I[${p}] ${old}->${y}`);
      }
      I[p] = old;
    }
  });
};
const genDropBasis = (w, emit) => {
  for (let bi = 0; bi < w.bases.length; bi++) {
    const [removed] = w.bases.splice(bi, 1);
    emit(`basis ${bi}`);
    w.bases.splice(bi, 0, removed);
  }
};
const genFlipAdj = (w, emit) => {
  for (let i = 0; i < w.adj.length; i++) {
    for (let j = 0; j < w.adj.length; j++) {
      if (i === j) continue;
      const row = w.adj[i];
      const p = row.indexOf(j);
      if (p >= 0) row.splice(p, 1);
      else row.push(j);
      emit(`adj[${i}] flip ${j}`);
      if (p >= 0) row.splice(p, 0, j);
      else row.pop();
    }
  }
};
const genTruncate = (w, emit) => {
  nodesOf(w).forEach((node, ni) => {
    if (node[1].length === 0) return;
    const saved = node[1];
    node[1] = [];
    emit(`node ${ni} loses all children`);
    node[1] = saved;
  });
};
const genSwapChildren = (w, emit) => {
  nodesOf(w).forEach((node, ni) => {
    const ch = node[1];
    for (let j = 0; j + 1 < ch.length; j++) {
      [ch[j], ch[j + 1]] = [ch[j + 1], ch[j]];
      emit(`node ${ni} children ${j}<->${j + 1}`);
      [ch[j], ch[j + 1]] = [ch[j + 1], ch[j]];
    }
  });
};

const cert4 = loaded['cert_box4_H1_k17.json'];
sweep('delete one child, every position (49-ray cert)', base49, genDeleteChild, 'tree');
sweep('remove all children of one internal node, every internal node (49-ray cert)', base49, genTruncate, 'tree');
sweep('swap two adjacent children, every position (49-ray cert)', base49, genSwapChildren, 'tree');
if (FULL) {
  sweep('change one ray index in an I to any ray outside that I, every position, exhaustive (49-ray cert)', base49, genChangeI(Infinity), 'tree', 25);
} else {
  sweep('change one ray index in an I to a ray outside that I, every position x 3 replacements (49-ray cert; --full = all replacements)', base49, genChangeI(3), 'tree', 10);
}
sweep('drop one basis from the list, every basis (49-ray cert)', base49, genDropBasis, 'all');
sweep('flip one adj entry, every ordered pair (49-ray cert)', base49, genFlipAdj, 'all');
sweep('delete one child, every position (40-ray d=4 cert)', cert4, genDeleteChild, 'tree');
sweep('drop one basis from the list, every basis (40-ray d=4 cert)', cert4, genDropBasis, 'all');

// The command line: exit status 0 only for a passing certificate / a KS set.
console.log('== (b) command line exit status ==');
{
  const dir = mkdtempSync(join(tmpdir(), 'verify_cert_test_'));
  try {
    const run = (...args) => spawnSync(process.execPath, [VERIFIER, ...args], { encoding: 'utf8' });
    const good = run(resultPath(CERTS[0].file));
    record(good.status === 0 && JSON.parse(good.stdout).verdict === 'PASS', 'CLI: valid certificate -> exit 0 and JSON verdict PASS');
    const bad = clone(base49);
    bad.k += 1;
    const badPath = join(dir, 'corrupt_k31.json');
    writeFileSync(badPath, JSON.stringify(bad));
    const r2 = run(badPath);
    record(r2.status === 1 && JSON.parse(r2.stdout).verdict === 'FAIL', 'CLI: corrupted certificate (k+1) -> exit 1 and JSON verdict FAIL');
    const junkPath = join(dir, 'junk.json');
    writeFileSync(junkPath, '{"d":3,');
    record(run(junkPath).status === 1, 'CLI: truncated JSON -> exit 1');
    record(run(join(dir, 'does_not_exist.json')).status === 1, 'CLI: missing file -> exit 1');
    const ksGood = run('--ks', '--require-critical', resultPath(KS_FILE));
    record(ksGood.status === 0 && JSON.parse(ksGood.stdout).colorable === false, 'CLI --ks: KS set -> exit 0');
    const ks31 = JSON.parse(readFileSync(resultPath(KS_FILE), 'utf8'));
    const colPath = join(dir, 'ks31_minus_one.json');
    writeFileSync(colPath, JSON.stringify({ d: ks31.d, rays: ks31.rays.slice(1) }));
    const ksBad = run('--ks', colPath);
    record(ksBad.status === 1 && JSON.parse(ksBad.stdout).colorable === true, 'CLI --ks: colorable set (KS-31 minus one ray) -> exit 1');
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

// ---------------------------------------------------------------------------
// (c) cross-checks of the colorability search
// ---------------------------------------------------------------------------
console.log('== (c) cross-checks ==');

/** Brute force over all 0/1 assignments (m <= 22). */
function bruteColorable(d, orth, subset) {
  const m = subset.length;
  if (m > 22) throw new Error('brute force limited to 22 rays');
  const bases = enumerateBases(d, orth, subset);
  const pos = new Map(subset.map((x, p) => [x, p]));
  const nbr = subset.map((x) => subset.reduce((acc, y, q) => (orth[x][y] ? acc | (1 << q) : acc), 0));
  const bmask = bases.map((b) => b.reduce((acc, x) => acc | (1 << pos.get(x)), 0));
  for (let mask = 0; mask < 1 << m; mask++) {
    let ok = true;
    for (let p = 0; p < m && ok; p++) if ((mask >> p) & 1 && nbr[p] & mask) ok = false;
    for (let t = 0; t < bmask.length && ok; t++) if (!(bmask[t] & mask)) ok = false;
    if (ok) return true;
  }
  return false;
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function randomSubset(rng, n, size) {
  const idx = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [idx[i], idx[j]] = [idx[j], idx[i]];
  }
  return idx.slice(0, size).sort((a, b) => a - b);
}
function crossCheck(label, ok, detail) {
  report.cross_checks.push({ check: label, ok, detail });
  record(ok, label, detail);
}

// Cabello-Estebaranz-Garcia-Alcaine 18-ray KS set in dimension 4 (9 bases, each ray in 2).
const KS18 = [
  [0, 0, 0, 1], [0, 0, 1, 0], [1, 1, 0, 0], [1, -1, 0, 0], [0, 1, 0, 0], [1, 0, 1, 0],
  [1, 0, -1, 0], [1, -1, 1, -1], [1, -1, -1, 1], [0, 0, 1, 1], [1, 1, 1, 1], [0, 1, 0, -1],
  [1, 0, 0, 1], [1, 0, 0, -1], [0, 1, -1, 0], [1, 1, -1, 1], [1, 1, 1, -1], [-1, 1, 1, 1],
];
{
  const res = analyseKSObject({ d: 4, rays: KS18 });
  const { orth } = analyseRays(4, KS18);
  const all = KS18.map((_, i) => i);
  const brute = bruteColorable(4, orth, all);
  crossCheck(
    'known KS-18 (d=4) is not colorable and is critical; brute force over 2^18 assignments agrees',
    res.colorable === false && res.critical === true && brute === false,
    `pairs=${res.orthogonal_pairs} bases=${res.bases} colorable=${res.colorable} critical=${res.critical} brute=${brute}`,
  );
}

/** Map each ray of `rays` to the index of the proportional ray of `pool` (or -1). */
function embed(rays, pool) {
  return rays.map((v) =>
    pool.findIndex((w) => {
      for (let a = 0; a < v.length; a++) for (let b = a + 1; b < v.length; b++) if (v[a] * w[b] !== v[b] * w[a]) return false;
      return true;
    }),
  );
}

// The KS sets live inside the pools, one ray above the certified k: the certified bound is tight.
{
  const ks31 = JSON.parse(readFileSync(resultPath(KS_FILE), 'utf8'));
  for (const file of ['cert_box3_H2_k30.json', 'cert_box3_H3_k30.json']) {
    const cert = loaded[file];
    const idx = embed(ks31.rays, cert.rays);
    const inside = idx.every((x) => x >= 0) && new Set(idx).size === idx.length;
    let colorable = null;
    if (inside) colorable = decideColorable(cert.d, analyseRays(cert.d, cert.rays).orth, idx).colorable;
    crossCheck(
      `${KS_FILE} is a ${idx.length}-ray subset of the pool of ${file} and is not colorable there (so k=${cert.k} is the largest certifiable k)`,
      inside && colorable === false && idx.length === cert.k + 1,
      `embedded=${inside} colorable=${colorable}`,
    );
  }
  const cert4 = loaded['cert_box4_H1_k17.json'];
  const idx = embed(KS18, cert4.rays);
  const inside = idx.every((x) => x >= 0) && new Set(idx).size === idx.length;
  const colorable = inside ? decideColorable(4, analyseRays(4, cert4.rays).orth, idx).colorable : null;
  crossCheck(
    `known KS-18 is an 18-ray subset of the pool of cert_box4_H1_k17.json and is not colorable there (so k=17 is the largest certifiable k)`,
    inside && colorable === false,
    `embedded=${inside} colorable=${colorable}`,
  );
}

// Backtracking (method A) vs ray-order search (method B) vs brute force on random subsets.
{
  const rng = mulberry32(20261109);
  let n = 0;
  let agree = 0;
  let nonColorable = 0;
  for (const file of ['cert_box4_H1_k17.json', 'cert_box3_H2_k30.json']) {
    const cert = loaded[file];
    const { orth } = analyseRays(cert.d, cert.rays);
    for (let t = 0; t < 60; t++) {
      const size = 12 + Math.floor(rng() * 9); // 12..20
      const sub = randomSubset(rng, cert.rays.length, size);
      const a = decideColorable(cert.d, orth, sub).colorable;
      const b = decideColorableByRayOrder(cert.d, orth, sub).colorable;
      const c = bruteColorable(cert.d, orth, sub);
      n++;
      if (a === b && b === c) agree++;
      if (!c) nonColorable++;
    }
  }
  // supersets of KS-18 inside the 40-ray pool: guaranteed non-colorable instances
  {
    const cert4 = loaded['cert_box4_H1_k17.json'];
    const { orth } = analyseRays(4, cert4.rays);
    const core = embed(KS18, cert4.rays);
    for (let t = 0; t < 20; t++) {
      const extra = randomSubset(rng, cert4.rays.length, 6).filter((x) => !core.includes(x)).slice(0, 3);
      const sub = [...core, ...extra].sort((x, y) => x - y);
      const a = decideColorable(4, orth, sub).colorable;
      const b = decideColorableByRayOrder(4, orth, sub).colorable;
      const c = bruteColorable(4, orth, sub);
      n++;
      if (a === b && b === c) agree++;
      if (!c) nonColorable++;
    }
  }
  crossCheck('backtracking = ray-order search = brute force on random subsets (12..21 rays)', agree === n, `${agree}/${n} agree, ${nonColorable} of them non-colorable`);
}

// Random subsets of size exactly k from each pool are colorable (consistent with the certified claims).
{
  const rng = mulberry32(31);
  for (const c of CERTS) {
    const cert = loaded[c.file];
    const { orth } = analyseRays(cert.d, cert.rays);
    const trials = 300;
    let col = 0;
    for (let t = 0; t < trials; t++) {
      if (decideColorable(cert.d, orth, randomSubset(rng, cert.rays.length, cert.k)).colorable) col++;
    }
    crossCheck(`random ${cert.k}-ray subsets of the pool of ${c.file} are colorable`, col === trials, `${col}/${trials}`);
  }
}

// ---------------------------------------------------------------------------
report.checks = checks;
report.verdict = report.failures.length === 0 ? 'PASS' : 'FAIL';
const summaryName = FULL ? 'verify_summary_full.json' : 'verify_summary.json';
report.mode = FULL ? 'full' : 'default';
writeFileSync(resultPath(summaryName), JSON.stringify(report, null, 2) + '\n');
console.log(`== ${report.verdict}: ${checks - report.failures.length}/${checks} checks passed; summary written to results/${summaryName} ==`);
process.exitCode = report.failures.length === 0 ? 0 : 1;
