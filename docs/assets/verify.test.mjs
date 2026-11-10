// verify.test.mjs -- checks the browser port (verify.js) against the original verifier
// (verify/verify_cert.mjs) on the files of docs/data and on corrupted copies of the certificates.
// Not loaded by the page.  Run from the repository:   node docs/assets/verify.test.mjs
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import * as port from './verify.js';
import * as orig from '../../verify/verify_cert.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const data = (name) => readFileSync(join(here, '..', 'data', name));
let failures = 0;
let checks = 0;
const check = (name, ok, detail = '') => {
  checks++;
  if (!ok) failures++;
  console.log(`${ok ? 'ok  ' : 'FAIL'} ${name}${detail ? ' -- ' + detail : ''}`);
};
const same = (a, b, keys) => keys.every((k) => JSON.stringify(a[k]) === JSON.stringify(b[k]));
const CERT_KEYS = ['d', 'k', 'rays', 'orthogonal_pairs', 'bases', 'nodes', 'nodes_visited', 'nodes_accepted_by_rule0', 'max_depth', 'checks', 'claim', 'verdict', 'error'];
const KS_KEYS = ['d', 'rays', 'orthogonal_pairs', 'bases', 'colorable', 'search_nodes', 'cross_check', 'critical', 'removals_colorable', 'removals_not_colorable', 'verdict', 'error'];

const manifest = JSON.parse(data('manifest.json').toString('utf8'));
for (const [name, info] of Object.entries(manifest.files)) {
  const buf = data(name);
  const h = await port.sha256Hex(buf);
  check(`sha256 ${name}`, h === info.sha256 && h === orig.sha256Hex(buf) && buf.length === info.bytes, h.slice(0, 16));
}

const certs = {};
for (const name of ['cert_box3_H2_k30.json', 'cert_box4_H1_k17.json']) {
  const cert = JSON.parse(data(name).toString('utf8'));
  certs[name] = cert;
  const a = port.verifyCertObject(cert);
  const b = orig.verifyCertObject(cert);
  check(`${name}: port = original, PASS`, a.verdict === 'PASS' && same(a, b, CERT_KEYS), `${a.nodes_visited} nodes, max depth ${a.max_depth}`);
  const p = port.verifyCertObject(cert, { treeReplay: false });
  check(`${name}: pool-only check`, p.verdict === 'PASS' && p.checks.bases && !p.checks.tree && p.claim === null, `${p.rays} rays, ${p.orthogonal_pairs} pairs, ${p.bases} bases`);
}

// Corrupted copies: the port must reject what the original rejects, with the same message.
const clone = (x) => JSON.parse(JSON.stringify(x));
const mutants = [];
for (const [name, cert] of Object.entries(certs)) {
  let m = clone(cert); m.k += 1; mutants.push([`${name}: k raised by one`, m, true]);
  m = clone(cert); m.tree[1].shift(); mutants.push([`${name}: first child of the root deleted`, m, true]);
  m = clone(cert); m.bases.pop(); mutants.push([`${name}: last basis dropped`, m, true]);
  m = clone(cert); m.adj[0].pop(); mutants.push([`${name}: one adj entry removed`, m, true]);
  m = clone(cert); m.rays[1][m.d - 1] += 1; mutants.push([`${name}: one ray coordinate changed`, m, true]);
  m = clone(cert); m.rays[2] = m.rays[3].map((x) => 2 * x); mutants.push([`${name}: proportional rays`, m, true]);
  m = clone(cert); m.tree = [[], []]; mutants.push([`${name}: empty tree`, m, true]);
  m = clone(cert); delete m.tree; mutants.push([`${name}: missing key`, m, true]);
  // every single child deleted, every position
  let count = 0;
  let agree = 0;
  const walk = (node, path) => {
    node[1].forEach((c, j) => {
      const mm = clone(cert);
      let t = mm.tree;
      for (const p of path) t = t[1][p][1];
      t[1].splice(j, 1);
      const a = port.verifyCertObject(mm);
      const b = orig.verifyCertObject(mm);
      count++;
      if (a.verdict === 'FAIL' && b.verdict === 'FAIL' && a.error === b.error) agree++;
      walk(c[1], path.concat(j));
    });
  };
  walk(cert.tree, []);
  check(`${name}: every single child deleted is rejected, same message as the original`, agree === count, `${agree}/${count}`);
}
for (const [label, m, mustFail] of mutants) {
  const a = port.verifyCertObject(m);
  const b = orig.verifyCertObject(m);
  check(label, (a.verdict === 'FAIL') === mustFail && a.verdict === b.verdict && a.error === b.error, (a.error || '').slice(0, 70));
}

for (const [name, certName] of [['ks31_box3_H2.json', 'cert_box3_H2_k30.json'], ['ks18_box4_H1.json', 'cert_box4_H1_k17.json']]) {
  const obj = JSON.parse(data(name).toString('utf8'));
  const a = port.analyseKSObject(obj);
  const b = orig.analyseKSObject(obj);
  check(`${name}: port = original, critical KS set`, a.colorable === false && a.critical === true && same(a, b, KS_KEYS), `${a.rays} rays, ${a.orthogonal_pairs} pairs, ${a.bases} bases, ${a.search_nodes} nodes`);
  const cert = certs[certName];
  const e = port.embedInPool(obj.d, obj.rays, cert.rays);
  check(`${name}: subset of the pool of ${certName}, size k + 1`, e.embedded && obj.rays.length === cert.k + 1);
  // the same set, decided inside the pool by index
  const { orth } = port.analyseRays(cert.d, cert.rays);
  check(`${name}: not colorable as a subset of the pool`, port.decideColorable(cert.d, orth, e.indices).colorable === false);
  // a colorable set must be reported colorable: drop one ray
  const less = { d: obj.d, rays: obj.rays.slice(1) };
  check(`${name} minus one ray: colorable in both`, port.analyseKSObject(less).colorable === true && orig.analyseKSObject(less).colorable === true);
}
check('embedInPool rejects a ray outside the pool', port.embedInPool(3, [[1, 3, 5]], certs['cert_box3_H2_k30.json'].rays).embedded === false);

console.log(`${checks} checks, ${failures} failed`);
process.exitCode = failures ? 1 : 0;
