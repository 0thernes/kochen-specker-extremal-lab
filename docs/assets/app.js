// app.js -- page logic: loads and hashes the data files, renders the results table, drives the
// 3D explorer and runs the in-browser checks (verify.js). No dependencies, no network requests
// other than the files in data/.
import * as V from './verify.js';
import { createViewer, formatRay } from './viewer.js';

const $ = (id) => document.getElementById(id);

function el(tag, attrs, ...children) {
  const node = document.createElement(tag);
  if (attrs) {
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === 'class') node.className = v;
      else if (k === 'text') node.textContent = v;
      else node.setAttribute(k, v === true ? '' : v);
    }
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

const nf = new Intl.NumberFormat('en-US');
const plural = (n, one, many) => `${nf.format(n)} ${n === 1 ? one : many}`;
const nextFrame = () => new Promise((resolve) => setTimeout(resolve, 30));

// ---------------------------------------------------------------------------
// Data files: fetch, hash, compare with the manifest, parse
// ---------------------------------------------------------------------------

const DATA = 'data/';
/** name -> { bytes, sha256, expected, expectedBytes, matches, json, error } */
const files = new Map();
let manifestError = null;

async function fetchBytes(name) {
  const res = await fetch(DATA + name, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.arrayBuffer();
}

async function loadData() {
  let manifest;
  try {
    const buf = await fetchBytes('manifest.json');
    manifest = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(buf));
    if (!manifest || typeof manifest.files !== 'object') throw new Error('manifest.json has no "files" object');
  } catch (e) {
    manifestError = `data/manifest.json could not be loaded (${e.message})`;
    return;
  }
  await Promise.all(
    Object.entries(manifest.files).map(async ([name, info]) => {
      const rec = { bytes: null, sha256: null, expected: info.sha256, expectedBytes: info.bytes, matches: false, json: null, error: null };
      files.set(name, rec);
      try {
        const buf = await fetchBytes(name);
        rec.bytes = buf.byteLength;
        try {
          rec.sha256 = await V.sha256Hex(buf);
          rec.matches = rec.sha256 === info.sha256 && rec.bytes === info.bytes;
          if (!rec.matches) rec.error = 'does not match manifest.json';
        } catch (e) {
          rec.error = `hash not computed: ${e.message}`;
        }
        try {
          rec.json = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(buf));
        } catch (e) {
          rec.error = `${rec.error ? rec.error + '; ' : ''}not valid JSON (${e.message})`;
        }
      } catch (e) {
        rec.error = `could not be loaded (${e.message})`;
      }
    }),
  );
}

/** null if the file arrived and matches the manifest, otherwise a sentence saying what is wrong. */
function integrityProblem(name) {
  if (manifestError) return manifestError;
  const rec = files.get(name);
  if (!rec) return `data/${name} is not listed in manifest.json`;
  if (rec.matches) return null;
  if (rec.sha256 && rec.sha256 !== rec.expected) {
    return `data/${name} does not match manifest.json (SHA-256 of the file received: ${rec.sha256.slice(0, 16)}…, manifest: ${String(rec.expected).slice(0, 16)}…)`;
  }
  return `data/${name}: ${rec.error || 'integrity not confirmed'}`;
}

function renderIntegrity() {
  const box = $('integrity');
  const head = $('integrity-summary');
  box.textContent = '';
  head.textContent = '';
  if (manifestError) {
    head.append(el('p', { class: 'error' }, el('span', { class: 'verdict fail', text: 'FAIL' }), ' ', manifestError + '. If you opened this page as a local file, serve the folder over http instead.'));
    return;
  }
  const names = [...files.keys()].sort();
  const bad = names.filter((n) => !files.get(n).matches);
  head.append(
    el('p', null,
      el('span', { class: `verdict ${bad.length ? 'fail' : 'pass'}`, text: bad.length ? 'FAIL' : 'PASS' }), ' ',
      bad.length
        ? `${plural(bad.length, 'data file does', 'data files do')} not match the manifest: ${bad.join(', ')}.`
        : `All ${names.length} data files match the manifest (SHA-256 computed in this browser).`),
  );
  const table = el('table', { class: 'files' },
    el('thead', null, el('tr', null, el('th', { scope: 'col', text: 'File' }), el('th', { scope: 'col', class: 'num', text: 'Bytes' }), el('th', { scope: 'col', class: 'hash', text: 'SHA-256 (computed here)' }), el('th', { scope: 'col', text: 'Status' }))));
  const body = el('tbody');
  for (const name of names) {
    const rec = files.get(name);
    body.append(el('tr', null,
      el('td', null, el('a', { href: DATA + name }, name)),
      el('td', { class: 'num', text: rec.bytes === null ? '' : nf.format(rec.bytes) }),
      el('td', { class: 'hash', text: rec.sha256 || '' }),
      el('td', null, rec.matches ? 'matches manifest' : el('strong', { class: 'bad-text' }, 'MISMATCH: ' + (rec.error || 'integrity not confirmed')))));
  }
  table.append(body);
  box.append(table);
}

// ---------------------------------------------------------------------------
// Results table (ARIA table, so that the stacked phone layout keeps its semantics)
// ---------------------------------------------------------------------------

function renderResults() {
  const box = $('results-table');
  const rec = files.get('results.json');
  box.textContent = '';
  box.removeAttribute('aria-busy');
  if (!rec || !rec.json || !Array.isArray(rec.json.rows)) {
    box.append(el('p', { class: 'error' }, 'The results table could not be loaded. ', el('a', { href: 'https://github.com/0thernes/kochen-specker-extremal-lab/blob/main/results/RESULTS.md' }, 'Read results/RESULTS.md in the repository.')));
    return;
  }
  const data = rec.json;
  if (!rec.matches) box.append(el('p', { class: 'error' }, el('span', { class: 'verdict fail', text: 'FAIL' }), ' ', integrityProblem('results.json') + '. The table below shows the file as received.'));
  const table = el('div', { class: 'rt', role: 'table', 'aria-label': 'Minimum Kochen-Specker set sizes inside pools' });
  table.append(el('div', { class: 'rt-row rt-head', role: 'row' },
    el('div', { role: 'columnheader', text: 'Pool' }),
    el('div', { role: 'columnheader', text: 'Rays' }),
    el('div', { role: 'columnheader', text: 'Bases' }),
    el('div', { role: 'columnheader', text: 'Minimum KS set' }),
    el('div', { role: 'columnheader', text: 'Status' })));
  for (const row of data.rows) {
    const badges = (row.status || []).map((s) => el('span', { class: 'badge' + (s === 'Lean' ? ' strong' : s === 'in progress' ? ' pending' : ''), text: s }));
    if (!row.final && !(row.status || []).includes('in progress')) badges.push(el('span', { class: 'badge pending', text: 'provisional' }));
    if (row.in_browser) badges.push(el('a', { class: 'badge here', href: '#verify', text: 're-check it below' }));
    const core = row.core && row.core !== row.rays ? el('span', { class: 'rt-sub', text: `${nf.format(row.core)} of the ${nf.format(row.rays)} rays remain after discarding rays that no minimal KS set can contain` }) : null;
    table.append(el('div', { class: 'rt-row' + (row.final ? '' : ' provisional'), role: 'row' },
      el('div', { class: 'rt-cell rt-pool', role: 'cell' }, el('span', { class: 'dim', text: `d = ${row.d}` }), row.pool, core),
      el('div', { class: 'rt-cell rt-inline', role: 'cell', 'data-label': 'Rays' }, nf.format(row.rays)),
      el('div', { class: 'rt-cell rt-inline', role: 'cell', 'data-label': 'Bases' }, nf.format(row.bases)),
      el('div', { class: 'rt-cell', role: 'cell', 'data-label': 'Minimum KS set' }, el('span', { class: 'rt-min', text: row.minimum })),
      el('div', { class: 'rt-cell', role: 'cell', 'data-label': 'Status' }, badges, row.note ? el('span', { class: 'rt-note', text: row.note }) : null)));
  }
  box.append(table);
  const legend = $('legend');
  legend.textContent = '';
  for (const [word, meaning] of data.status_legend || []) {
    legend.append(el('dt', null, el('span', { class: 'badge' + (word === 'Lean' ? ' strong' : word === 'in progress' ? ' pending' : ''), text: word })), el('dd', { text: meaning }));
  }
  legend.append(el('dt', null, el('span', { class: 'badge pending', text: 'provisional' })), el('dd', { text: 'part of the evidence for this row is still pending; the number may be corrected' }));
  const na = $('not-achieved');
  na.textContent = '';
  for (const line of data.not_achieved || []) na.append(el('li', { text: line }));
}

// ---------------------------------------------------------------------------
// Explorer: the 31-ray set
// ---------------------------------------------------------------------------

/**
 * Among all labellings with no two perpendicular rays both 1 (rule 1), the largest number of bases
 * that contain a 1.  Plain enumeration of every such labelling.
 */
function bestLabelling(n, orth, bases) {
  const later = Array.from({ length: n }, (_, i) => { const out = []; for (let j = i + 1; j < n; j++) if (orth[i][j]) out.push(j); return out; });
  const inBases = Array.from({ length: n }, () => []);
  bases.forEach((b, bi) => b.forEach((x) => inBases[x].push(bi)));
  const blocked = new Int16Array(n);
  const cnt = new Uint8Array(bases.length);
  const cur = [];
  let sat = 0, max = -1, attaining = 0, total = 0, example = [];
  const rec = (i) => {
    if (i === n) {
      total++;
      if (sat > max) { max = sat; attaining = 1; example = cur.slice(); }
      else if (sat === max) attaining++;
      return;
    }
    rec(i + 1);
    if (blocked[i]) return;
    for (const j of later[i]) blocked[j]++;
    for (const b of inBases[i]) if (cnt[b]++ === 0) sat++;
    cur.push(i);
    rec(i + 1);
    cur.pop();
    for (const b of inBases[i]) if (--cnt[b] === 0) sat--;
    for (const j of later[i]) blocked[j]--;
  };
  rec(0);
  return { max, attaining, total, example };
}

function setupExplorer() {
  const status = $('status');
  const rec = files.get('ks31_box3_H2.json');
  if (!rec || !rec.json) {
    status.textContent = 'The 31-ray set could not be loaded: ' + (integrityProblem('ks31_box3_H2.json') || 'unknown error') + '.';
    return;
  }
  let geo;
  try {
    if (rec.json.d !== 3) throw new Error('the picture needs rays in dimension three');
    geo = V.analyseRays(rec.json.d, rec.json.rays);
  } catch (e) {
    status.textContent = 'The 31-ray set could not be drawn: ' + e.message + '.';
    return;
  }
  const rays = rec.json.rays;
  const n = rays.length;
  const orth = geo.orth;
  const bases = V.enumerateBases(3, orth);
  const model = { rays, orth, bases };
  const neighbours = rays.map((_, i) => rays.map((__, j) => j).filter((j) => orth[i][j]));
  const basesOf = rays.map((_, i) => bases.map((b, bi) => (b.includes(i) ? bi : -1)).filter((x) => x >= 0));
  const name = (i) => formatRay(rays[i]);

  $('x-pairs').textContent = String(geo.pairs);
  $('x-bases').textContent = String(bases.length);
  for (const s of document.querySelectorAll('.n-bases')) s.textContent = String(bases.length);
  const problem = integrityProblem('ks31_box3_H2.json');
  if (problem) $('explorer').querySelector('.prose').after(el('p', { class: 'error' }, el('span', { class: 'verdict fail', text: 'FAIL' }), ' ', problem + '. The picture shows the file as received.'));

  const state = { mode: 'explore', selected: -1, ones: new Set(), showBases: false };
  const best = n <= 40 ? bestLabelling(n, orth, bases) : null;

  const viewer = createViewer($('sphere'), model, {
    onPick: (i) => pick(i),
    onSpin: (on) => $('btn-spin').setAttribute('aria-pressed', on ? 'true' : 'false'),
  });

  // ray buttons and basis chips
  const rayButtons = rays.map((_, i) => {
    const b = el('button', { type: 'button', 'aria-pressed': 'false', text: name(i) });
    b.addEventListener('click', () => pick(i));
    $('ray-list').append(b);
    return b;
  });
  const basisChips = bases.map((b, bi) => {
    const li = el('li', { text: `B${bi + 1}`, title: b.map(name).join('  ') });
    $('basis-list').append(li);
    return li;
  });

  function pick(i) {
    if (state.mode === 'explore') state.selected = state.selected === i ? -1 : i;
    else if (state.ones.has(i)) state.ones.delete(i);
    else state.ones.add(i);
    update();
  }

  function analyse() {
    const ones = [...state.ones].sort((a, b) => a - b);
    const conflicts = [];
    for (let a = 0; a < ones.length; a++) for (let b = a + 1; b < ones.length; b++) if (orth[ones[a]][ones[b]]) conflicts.push([ones[a], ones[b]]);
    const bad = new Set(conflicts.flat());
    const zeros = new Set();
    for (const x of ones) for (const y of neighbours[x]) if (!state.ones.has(y)) zeros.add(y);
    const kinds = bases.map((b) => {
      const c = b.filter((x) => state.ones.has(x)).length;
      if (c === 1) return 'good';
      if (c >= 2) return 'bad';
      return b.every((x) => zeros.has(x)) ? 'blocked' : 'warn';
    });
    return { ones, conflicts, bad, zeros, kinds, satisfied: kinds.filter((k) => k === 'good').length };
  }

  function update() {
    const colour = state.mode === 'colour';
    $('colour-tools').hidden = !colour;
    status.textContent = '';
    if (!colour) {
      const s = state.selected;
      const partners = new Set(s >= 0 ? neighbours[s] : []);
      const focus = new Set(s >= 0 ? basesOf[s] : []);
      const triangles = [];
      bases.forEach((b, bi) => {
        if (focus.has(bi)) triangles.push({ basis: b, kind: 'focus' });
        else if (state.showBases) triangles.push({ basis: b, kind: 'plain' });
      });
      viewer.setView({ selected: s, partners, triangles, dimOthers: s >= 0 });
      rayButtons.forEach((b, i) => {
        b.setAttribute('aria-pressed', i === s ? 'true' : 'false');
        b.className = partners.has(i) ? 'partner' : '';
        b.textContent = name(i);
        b.title = partners.has(i) ? 'perpendicular to the selected ray' : '';
      });
      basisChips.forEach((li, bi) => {
        li.className = focus.has(bi) ? 'focus' : '';
        li.textContent = `B${bi + 1}`;
      });
      if (s < 0) {
        status.append('Pick a ray, in the picture or with a button below, to see the rays perpendicular to it and the bases it belongs to.');
      } else {
        status.append(el('p', null, 'Ray ', el('code', { text: name(s) }), ` is perpendicular to ${partners.size} of the other ${n - 1} rays (thicker lines in the picture, outlined buttons below) and lies in ${plural(focus.size, 'basis', 'bases')}` + (focus.size ? ':' : '.')));
        if (focus.size) status.append(el('ul', null, [...focus].map((bi) => el('li', null, `B${bi + 1}: `, el('code', { text: bases[bi].map(name).join('  ') })))));
      }
      return;
    }
    const a = analyse();
    const triangles = state.showBases ? bases.map((b, bi) => ({ basis: b, kind: a.kinds[bi] === 'blocked' ? 'bad' : a.kinds[bi] })) : [];
    viewer.setView({ ones: state.ones, zeros: a.zeros, bad: a.bad, triangles });
    rayButtons.forEach((b, i) => {
      const one = state.ones.has(i);
      b.setAttribute('aria-pressed', one ? 'true' : 'false');
      b.className = a.bad.has(i) ? 'conflict' : a.zeros.has(i) ? 'zero' : '';
      b.textContent = name(i) + (one ? ' = 1' : '');
      b.title = a.bad.has(i) ? 'breaks rule 1' : a.zeros.has(i) ? 'perpendicular to a ray labelled 1, so it must be 0' : '';
    });
    const words = { good: '✓ has its 1', bad: '✗ two 1s', blocked: '✗ blocked', warn: '○ no 1 yet' };
    basisChips.forEach((li, bi) => {
      li.className = a.kinds[bi] === 'blocked' ? 'bad' : a.kinds[bi];
      li.textContent = `B${bi + 1} ${words[a.kinds[bi]]}`;
    });
    $('count-ok').textContent = String(a.satisfied);
    const lacking = a.kinds.filter((k) => k === 'warn' || k === 'blocked').length;
    const blocked = a.kinds.filter((k) => k === 'blocked').length;
    const list = el('ul');
    if (a.ones.length === 0) {
      status.append('Pick rays to label them 1; every other ray counts as 0. A basis is satisfied when exactly one of its rays is 1.');
    } else {
      if (a.conflicts.length) {
        list.append(el('li', { class: 'bad' }, `Rule 1 is broken: ${plural(a.conflicts.length, 'perpendicular pair is', 'perpendicular pairs are')} both 1 (${a.conflicts.slice(0, 3).map(([x, y]) => `${name(x)} and ${name(y)}`).join('; ')}${a.conflicts.length > 3 ? '; …' : ''}).`));
      } else {
        list.append(el('li', { class: 'ok' }, 'Rule 1 holds: no two perpendicular rays are both 1.'));
      }
      if (lacking) {
        list.append(el('li', null, `Rule 2 fails: ${plural(lacking, 'basis has', 'bases have')} no 1.` + (blocked ? ` Blocked: ${blocked}. Every ray of a blocked basis is perpendicular to a ray already labelled 1, so the basis cannot receive a 1.` : '')));
      }
      if (!a.conflicts.length && best && a.satisfied === best.max) {
        list.append(el('li', { class: 'ok' }, best.max < bases.length
          ? `This is as good as it gets: ${best.max} of ${bases.length}. No labelling satisfies them all, which is what makes this a Kochen-Specker set.`
          : `All ${bases.length} bases are satisfied and rule 1 holds: this is a colouring, so the set shown is not a Kochen-Specker set.`));
      }
      status.append(list);
    }
  }

  for (const radio of document.querySelectorAll('input[name="mode"]')) {
    radio.addEventListener('change', () => {
      if (radio.checked) {
        state.mode = radio.value;
        update();
      }
    });
    if (radio.checked) state.mode = radio.value;
  }
  $('chk-bases').addEventListener('change', (ev) => { state.showBases = ev.target.checked; update(); });
  state.showBases = $('chk-bases').checked;
  $('btn-reset').addEventListener('click', () => viewer.reset());
  $('btn-spin').addEventListener('click', () => viewer.setSpin(!viewer.isSpinning()));
  $('btn-clear').addEventListener('click', () => { state.ones.clear(); update(); });
  $('btn-best').addEventListener('click', () => { if (best) { state.ones = new Set(best.example); update(); } });

  if (best) {
    const text = [`Best possible when rule 1 is respected: ${best.max} of ${bases.length}. Your browser has just tried all ${nf.format(best.total)} labellings that respect rule 1; ${nf.format(best.attaining)} of them reach ${best.max}` + (best.max < bases.length ? `, none reaches ${bases.length}.` : '. Since that is every basis, the set shown is colourable: it is not a Kochen-Specker set.')];
    const stack = files.get('stack_demo.json');
    const key = stack && stack.json && stack.json.key_numbers;
    if (key && stack.matches) {
      const same = key.classical_max_M === best.max && key.admissible_assignments === best.total && key.assignments_attaining_M === best.attaining;
      text.push(same ? ' The same three numbers are recorded in results/stack_demo.json.' : ' Warning: results/stack_demo.json records different numbers.');
    }
    $('best').textContent = text.join('');
  } else {
    $('btn-best').hidden = true;
  }
  renderStackNote(bases.length);
  update();
  window.ksExplorer = { viewer, state, pick, model }; // for tests and the curious
}

function renderStackNote(nBases) {
  const stack = files.get('stack_demo.json');
  const key = stack && stack.json && stack.json.key_numbers;
  if (!key || !stack.matches) return;
  $('stack-note').textContent =
    `Why the count matters. In quantum theory, whatever the state, the probabilities of the outcomes in each basis add up to 1, so the ${nBases} bases total ${key.quantum_value_every_state}; a fixed 0/1 labelling that respects rule 1 reaches at most ${key.classical_max_M}. ` +
    `The repository contains a demonstration that recomputes these numbers with several independent programs (results/stack_demo.json, overall ${stack.json.overall}). One of them is a classical simulator of quantum states: for ${nf.format(key.n_states)} sampled states the basis sums differed from 1 by at most ${Number(key.max_basis_sum_deviation).toExponential(1)}. ` +
    'These are numerical simulations on an ordinary computer; nothing was run on quantum hardware.';
}

// ---------------------------------------------------------------------------
// Verify in your browser
// ---------------------------------------------------------------------------

function recordedCert(name) {
  const rec = files.get('verify_summary.json');
  if (!rec || !rec.json || !rec.matches || !Array.isArray(rec.json.certificates)) return null;
  return rec.json.certificates.find((c) => c.file === name) || null;
}

function compareRecorded(name, s, keys) {
  const r = recordedCert(name);
  if (!r) return { line: null, ok: true };
  const differ = keys.filter((k) => r[k] !== s[k]);
  if (differ.length === 0) return { line: 'Same counts as the recorded run of the original verifier under Node.js (results/verify_summary.json).', ok: true };
  return { line: `The counts differ from the recorded Node.js run in results/verify_summary.json (${differ.map((k) => `${k}: here ${s[k]}, recorded ${r[k]}`).join('; ')}).`, ok: false };
}

function poolCheck(certName) {
  const cert = files.get(certName).json;
  const s = V.verifyCertObject(cert, { treeReplay: false });
  if (s.verdict !== 'PASS') return { pass: false, headline: s.error, lines: [] };
  const cmp = compareRecorded(certName, s, ['rays', 'orthogonal_pairs', 'bases']);
  return {
    pass: cmp.ok,
    headline: `${s.rays} rays, ${s.orthogonal_pairs} perpendicular pairs and ${s.bases} bases recomputed from the integer coordinates; the tables in the file agree with them.`,
    lines: [cmp.line],
    summary: s,
  };
}

function treeCheck(certName, withPool) {
  const cert = files.get(certName).json;
  const s = V.verifyCertObject(cert);
  if (s.verdict !== 'PASS') return { pass: false, headline: s.error, lines: [], summary: s };
  const cmp = compareRecorded(certName, s, ['rays', 'orthogonal_pairs', 'bases', 'nodes', 'nodes_visited', 'nodes_accepted_by_rule0', 'max_depth']);
  const pool = withPool ? `Pool recomputed: ${s.rays} rays, ${s.orthogonal_pairs} perpendicular pairs, ${s.bases} bases; the tables in the file agree. ` : '';
  return {
    pass: cmp.ok,
    headline: `${pool}${nf.format(s.nodes_visited)} nodes checked, every one accepted (deepest level ${s.max_depth}). Every set of at most ${s.k} rays of this ${s.rays}-ray pool is colourable.`,
    lines: [cmp.line],
    summary: s,
  };
}

function ksCheck(setName, certName) {
  const obj = files.get(setName).json;
  const cert = files.get(certName).json;
  const s = V.analyseKSObject(obj);
  if (s.error) return { pass: false, headline: s.error, lines: [] };
  if (s.colorable !== false) return { pass: false, headline: `A colouring was found: these ${s.rays} rays are not a KS set.`, lines: [], summary: s };
  if (s.cross_check_nodes === null) return { pass: false, headline: `No colouring found (${nf.format(s.search_nodes)} nodes), but the cross-check search did not finish.`, lines: [], summary: s };
  const emb = cert && Array.isArray(cert.rays) ? V.embedInPool(obj.d, obj.rays, cert.rays) : { embedded: false };
  let inPool = false;
  if (emb.embedded) {
    const { orth } = V.analyseRays(cert.d, cert.rays);
    inPool = V.decideColorable(cert.d, orth, emb.indices).colorable === false;
  }
  const lines = [
    `Exhaustive backtracking: ${nf.format(s.search_nodes)} nodes. Second search, rays taken one at a time in file order: ${nf.format(s.cross_check_nodes)} nodes, same answer.`,
    `The set has ${s.orthogonal_pairs} perpendicular pairs and ${s.bases} bases.`,
    s.critical ? `Removing any single ray leaves a colourable set (${s.removals_colorable} of ${s.rays} removals checked), so no ray is superfluous.` : `Removing a ray does not always make the set colourable (${s.removals_not_colorable.length} removals keep it a KS set).`,
  ];
  const rec = files.get('verify_summary.json');
  const r = rec && rec.matches && rec.json && rec.json.ks && rec.json.ks.file === setName ? rec.json.ks : null;
  let recordedOk = true;
  if (r) {
    recordedOk = r.search_nodes === s.search_nodes && r.orthogonal_pairs === s.orthogonal_pairs && r.bases === s.bases && r.colorable === s.colorable && r.critical === s.critical;
    lines.push(recordedOk ? 'Same counts as the recorded run of the original verifier under Node.js (results/verify_summary.json).' : 'The counts differ from the recorded Node.js run in results/verify_summary.json.');
  }
  if (!emb.embedded || !inPool) {
    return { pass: false, headline: `No colouring found, but the ${s.rays} rays are not all rays of the ${cert && cert.rays ? cert.rays.length : '?'}-ray pool, so this says nothing about the pool.`, lines, summary: s };
  }
  return {
    pass: recordedOk,
    headline: `No colouring found: the ${s.rays} rays form a Kochen-Specker set. All ${s.rays} rays belong to the ${cert.rays.length}-ray pool.`,
    lines,
    summary: s,
  };
}

const CHECKS = {
  pool3: { files: ['cert_box3_H2_k30.json'], run: () => poolCheck('cert_box3_H2_k30.json') },
  tree3: { files: ['cert_box3_H2_k30.json'], run: () => treeCheck('cert_box3_H2_k30.json', false) },
  ks31: { files: ['ks31_box3_H2.json', 'cert_box3_H2_k30.json'], run: () => ksCheck('ks31_box3_H2.json', 'cert_box3_H2_k30.json') },
  cert4: { files: ['cert_box4_H1_k17.json'], run: () => treeCheck('cert_box4_H1_k17.json', true) },
  ks18: { files: ['ks18_box4_H1.json', 'cert_box4_H1_k17.json'], run: () => ksCheck('ks18_box4_H1.json', 'cert_box4_H1_k17.json') },
};
const outcome = {}; // id -> { pass, summary, ms }

function formatMs(ms) {
  return ms < 10 ? `${ms.toFixed(1)} ms` : `${Math.round(ms)} ms`;
}

async function runCheck(id) {
  const def = CHECKS[id];
  const out = $('out-' + id);
  out.textContent = '';
  out.append(el('div', { class: 'box' }, el('span', { class: 'verdict run', text: 'RUNNING' })));
  await nextFrame();
  const problems = def.files.map(integrityProblem).filter(Boolean);
  const missing = def.files.some((f) => !files.get(f) || !files.get(f).json);
  let result = null;
  let ms = 0;
  if (!missing) {
    const t0 = performance.now();
    try {
      result = def.run();
    } catch (e) {
      result = { pass: false, headline: `the checker stopped with an error: ${e.message}`, lines: [] };
    }
    ms = performance.now() - t0;
  }
  const pass = !!result && result.pass && problems.length === 0;
  out.textContent = '';
  const box = el('div', { class: 'box ' + (pass ? 'pass' : 'fail') });
  const head = el('div', null, el('span', { class: 'verdict ' + (pass ? 'pass' : 'fail'), text: pass ? 'PASS' : 'FAIL' }), ' ');
  if (problems.length) {
    head.append(problems.join('; ') + '.');
    if (result) box.append(head, el('p', null, `The check was still run on the file as received and ${result.pass ? 'that file passes it' : 'it fails'}: ${result.headline}`));
    else box.append(head);
  } else {
    head.append(result.headline);
    box.append(head);
  }
  if (result) for (const line of result.lines.filter(Boolean)) box.append(el('p', { text: line }));
  if (result) box.append(el('p', { class: 'time', text: `Time: ${formatMs(ms)} in this browser.` }));
  out.append(box);
  outcome[id] = { pass, summary: result && result.summary, ms };
  renderConclusion();
  return pass;
}

function renderConclusion() {
  const box = $('conclusion');
  box.textContent = '';
  const pairs = [['tree3', 'ks31', 'Three dimensions'], ['cert4', 'ks18', 'Four dimensions']];
  for (const [t, k, label] of pairs) {
    const a = outcome[t], b = outcome[k];
    if (!a || !b || !a.pass || !b.pass || !a.summary || !b.summary) continue;
    if (b.summary.rays !== a.summary.k + 1) continue;
    box.append(el('p', null, el('strong', { text: `${label}, ${a.summary.rays}-ray pool. ` }),
      `A Kochen-Specker set with ${b.summary.rays} rays exists in the pool, and every set of at most ${a.summary.k} rays is colourable. So the smallest Kochen-Specker set made of rays of this pool has exactly ${b.summary.rays} rays. This is a statement about this pool only.`));
  }
}

function setupVerify() {
  const ids = Object.keys(CHECKS);
  const buttons = [...document.querySelectorAll('button[data-check]')];
  const all = $('run-all');
  const setBusy = (busy) => { for (const b of buttons.concat(all)) b.disabled = busy; };
  for (const b of buttons) {
    b.addEventListener('click', async () => {
      setBusy(true);
      try { await runCheck(b.dataset.check); } finally { setBusy(false); }
    });
  }
  all.addEventListener('click', async () => {
    setBusy(true);
    const summary = $('run-summary');
    summary.textContent = 'Running…';
    let passed = 0, total = 0;
    try {
      for (const id of ids) {
        if (await runCheck(id)) passed++;
        total += outcome[id].ms;
      }
    } finally {
      setBusy(false);
    }
    summary.textContent = '';
    summary.append(el('span', { class: 'verdict ' + (passed === ids.length ? 'pass' : 'fail'), text: passed === ids.length ? 'PASS' : 'FAIL' }), ' ',
      passed === ids.length ? `All ${ids.length} checks passed; ${formatMs(total)} of computation.` : `${ids.length - passed} of ${ids.length} checks failed.`);
  });
  setBusy(false);

  const c3 = files.get('cert_box3_H2_k30.json'), c4 = files.get('cert_box4_H1_k17.json');
  if (c3 && c3.json && Number.isInteger(c3.json.k)) for (const s of document.querySelectorAll('.k3')) s.textContent = String(c3.json.k);
  if (c4 && c4.json && Number.isInteger(c4.json.k)) for (const s of document.querySelectorAll('.k4')) s.textContent = String(c4.json.k);

  const rec = files.get('verify_summary.json');
  if (rec && rec.json && rec.matches) {
    const v = rec.json;
    const rejected = Array.isArray(v.negative_tests) ? v.negative_tests.filter((t) => t.rejected === true).length : 0;
    $('recorded').textContent =
      `For comparison, the repository records its own run of the original verifier (results/verify_summary.json): verdict ${v.verdict}, ${v.checks} checks, ${v.verifier} under Node ${v.node}` +
      (rejected ? `, including ${rejected} deliberately corrupted inputs that were rejected.` : '.');
  }
}

// ---------------------------------------------------------------------------

async function main() {
  await loadData();
  renderIntegrity();
  renderResults();
  try {
    setupExplorer();
  } catch (e) {
    $('status').textContent = 'The explorer could not start: ' + e.message;
  }
  if (!manifestError) setupVerify();
  document.documentElement.dataset.ready = 'true';
}

main();
