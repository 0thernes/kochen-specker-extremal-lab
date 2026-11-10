// viewer.js -- 3D view of a set of rays in dimension three on a 2D canvas.
// Own rotation matrix and perspective projection; no WebGL, no library.

const CAMERA = 4.2; // distance of the eye from the centre, in sphere radii

function norm(v) {
  const l = Math.hypot(v[0], v[1], v[2]);
  return [v[0] / l, v[1] / l, v[2] / l];
}

function mul(A, B) {
  const C = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) C[3 * i + j] = A[3 * i] * B[j] + A[3 * i + 1] * B[3 + j] + A[3 * i + 2] * B[6 + j];
  return C;
}

function rotX(a) {
  const c = Math.cos(a), s = Math.sin(a);
  return [1, 0, 0, 0, c, -s, 0, s, c];
}

function rotY(a) {
  const c = Math.cos(a), s = Math.sin(a);
  return [c, 0, s, 0, 1, 0, -s, 0, c];
}

function apply(R, v) {
  return [R[0] * v[0] + R[1] * v[1] + R[2] * v[2], R[3] * v[0] + R[4] * v[1] + R[5] * v[2], R[6] * v[0] + R[7] * v[1] + R[8] * v[2]];
}

const START = mul(rotX(-0.42), rotY(0.55));

export function formatRay(v) {
  return '(' + v.map((x) => (x < 0 ? '−' + -x : String(x))).join(', ') + ')';
}

/**
 * model: { rays: integer vectors (length 3), orth: 0/1 matrix, bases: triples of ray indices }
 * hooks: { onPick(index), onHover(index or -1) }
 * view (set with setView): { selected, partners:Set, ones:Set, zeros:Set, bad:Set, triangles:[{basis, kind}], dimOthers }
 */
export function createViewer(canvas, model, hooks = {}) {
  const ctx = canvas.getContext('2d');
  const unit = model.rays.map(norm);
  let R = START.slice();
  let view = { selected: -1, partners: new Set(), ones: new Set(), zeros: new Set(), bad: new Set(), triangles: [], dimOthers: false };
  let hover = -1;
  let w = 300, h = 300, dpr = 1;
  let colours = {};
  let spinning = false;
  let raf = 0;
  let screen = []; // per ray: projected front and back end points

  function readColours() {
    const cs = getComputedStyle(canvas);
    const get = (name, fallback) => cs.getPropertyValue(name).trim() || fallback;
    colours = {
      ink: get('--ink', '#1b1f27'), muted: get('--muted', '#5b6370'), ray: get('--ray', '#59616d'),
      accent: get('--accent', '#0b6b57'), partner: get('--partner', '#a4520b'), one: get('--one', '#0b6b57'),
      bad: get('--bad', '#b3261e'), warn: get('--warn', '#8a6100'), sphere: get('--sphere', '#ece9df'),
      rule: get('--rule', '#d9d6cc'), bg: get('--surface', '#ffffff'),
    };
  }

  function resize() {
    const rect = canvas.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2.5);
    w = Math.max(120, rect.width);
    h = Math.max(120, rect.height);
    canvas.width = Math.round(w * dpr);
    canvas.height = Math.round(h * dpr);
    draw();
  }

  function project(p) {
    const q = apply(R, p);
    const f = CAMERA / (CAMERA - q[2]);
    const s = 0.4 * Math.min(w, h);
    return { x: w / 2 + s * f * q[0], y: h / 2 - s * f * q[1], z: q[2] };
  }

  function arc(a, b, steps) {
    const pts = [];
    for (let t = 0; t <= steps; t++) {
      const u = t / steps;
      pts.push(project(norm([a[0] * (1 - u) + b[0] * u, a[1] * (1 - u) + b[1] * u, a[2] * (1 - u) + b[2] * u])));
    }
    return pts;
  }

  function rayStyle(i) {
    if (view.bad.has(i)) return { colour: colours.bad, width: 2.6, alpha: 1, dot: 6.5, fill: true };
    if (i === view.selected) return { colour: colours.accent, width: 3, alpha: 1, dot: 7, fill: true };
    if (view.ones.has(i)) return { colour: colours.one, width: 3, alpha: 1, dot: 7, fill: true };
    if (view.partners.has(i)) return { colour: colours.partner, width: 2.2, alpha: 1, dot: 5.5, fill: true };
    if (view.zeros.has(i)) return { colour: colours.muted, width: 1, alpha: 0.5, dot: 4, fill: false };
    if (view.dimOthers) return { colour: colours.ray, width: 1, alpha: 0.3, dot: 3.5, fill: true };
    return { colour: colours.ray, width: 1.4, alpha: 0.9, dot: 4.5, fill: true };
  }

  function draw() {
    if (!colours.ink) readColours();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const s = 0.4 * Math.min(w, h);
    const rad = (s * CAMERA) / Math.sqrt(CAMERA * CAMERA - 1);
    const cx = w / 2, cy = h / 2;

    // the sphere
    const g = ctx.createRadialGradient(cx - rad * 0.35, cy - rad * 0.4, rad * 0.1, cx, cy, rad);
    g.addColorStop(0, colours.bg);
    g.addColorStop(1, colours.sphere);
    ctx.beginPath();
    ctx.arc(cx, cy, rad, 0, 2 * Math.PI);
    ctx.fillStyle = g;
    ctx.fill();
    ctx.lineWidth = 1;
    ctx.strokeStyle = colours.rule;
    ctx.stroke();

    // three faint great circles for orientation
    ctx.lineWidth = 1;
    for (const [a, b] of [[[1, 0, 0], [0, 1, 0]], [[0, 1, 0], [0, 0, 1]], [[0, 0, 1], [1, 0, 0]]]) {
      ctx.beginPath();
      for (let t = 0; t <= 72; t++) {
        const ang = (t / 72) * 2 * Math.PI;
        const p = project([a[0] * Math.cos(ang) + b[0] * Math.sin(ang), a[1] * Math.cos(ang) + b[1] * Math.sin(ang), a[2] * Math.cos(ang) + b[2] * Math.sin(ang)]);
        if (t === 0) ctx.moveTo(p.x, p.y);
        else ctx.lineTo(p.x, p.y);
      }
      ctx.globalAlpha = 0.55;
      ctx.strokeStyle = colours.rule;
      ctx.stroke();
      ctx.globalAlpha = 1;
    }

    // collect drawables with a depth key, then paint back to front
    const items = [];
    const origin = project([0, 0, 0]);
    screen = [];
    for (let i = 0; i < unit.length; i++) {
      const u = unit[i];
      const p = project(u);
      const q = project([-u[0], -u[1], -u[2]]);
      screen.push([p, q]);
      // layers: 0 back triangles, 1 back half-rays, 2 front triangles, 3 front half-rays
      items.push({ layer: p.z < 0 ? 1 : 3, z: p.z / 2, kind: 'half', i, a: origin, b: p });
      items.push({ layer: q.z < 0 ? 1 : 3, z: q.z / 2, kind: 'half', i, a: origin, b: q });
      items.push({ layer: p.z < 0 ? 1 : 3, z: p.z + 0.001, kind: 'dot', i, p });
      items.push({ layer: q.z < 0 ? 1 : 3, z: q.z + 0.001, kind: 'dot', i, p: q });
    }
    for (const tri of view.triangles) {
      const [a, b, c] = tri.basis.map((x) => unit[x]);
      for (const sgn of [1, -1]) {
        const A = a.map((x) => sgn * x), B = b.map((x) => sgn * x), C = c.map((x) => sgn * x);
        const pts = arc(A, B, 10).concat(arc(B, C, 10), arc(C, A, 10));
        const z = apply(R, norm([A[0] + B[0] + C[0], A[1] + B[1] + C[1], A[2] + B[2] + C[2]]))[2];
        items.push({ layer: z < 0 ? 0 : 2, z, kind: 'tri', pts, tri });
      }
    }
    items.sort((m, n) => m.layer - n.layer || m.z - n.z);

    for (const it of items) {
      const depth = 0.45 + 0.55 * Math.min(1, Math.max(0, (it.z + 1) / 2)); // back items are fainter
      if (it.kind === 'tri') {
        const colour = it.tri.kind === 'good' ? colours.one : it.tri.kind === 'bad' ? colours.bad : it.tri.kind === 'warn' ? colours.warn : it.tri.kind === 'focus' ? colours.accent : colours.muted;
        ctx.beginPath();
        it.pts.forEach((p, k) => (k ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y)));
        ctx.closePath();
        // only bases with a definite state are filled, and only on the near side; the rest are outlines
        const outlineOnly = it.tri.kind === 'plain' || it.tri.kind === 'warn';
        if (!outlineOnly && it.z >= 0) {
          ctx.globalAlpha = 0.11;
          ctx.fillStyle = colour;
          ctx.fill();
        }
        ctx.globalAlpha = (it.tri.kind === 'plain' ? 0.5 : 0.9) * (it.z >= 0 ? 1 : 0.35);
        ctx.lineWidth = it.tri.kind === 'plain' ? 1 : 1.6;
        ctx.strokeStyle = colour;
        if (it.tri.kind === 'warn') ctx.setLineDash([5, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1;
        continue;
      }
      const st = rayStyle(it.i);
      ctx.globalAlpha = st.alpha * depth;
      if (it.kind === 'half') {
        ctx.beginPath();
        ctx.moveTo(it.a.x, it.a.y);
        ctx.lineTo(it.b.x, it.b.y);
        ctx.lineWidth = st.width;
        ctx.strokeStyle = st.colour;
        ctx.stroke();
      } else {
        const r = st.dot * (it.p.z > 0 ? 1 : 0.8) * (it.i === hover ? 1.35 : 1);
        ctx.beginPath();
        ctx.arc(it.p.x, it.p.y, r, 0, 2 * Math.PI);
        if (st.fill) {
          ctx.fillStyle = st.colour;
          ctx.fill();
        } else {
          ctx.fillStyle = colours.bg;
          ctx.fill();
          ctx.lineWidth = 1.2;
          ctx.strokeStyle = st.colour;
          ctx.stroke();
        }
        if (it.i === hover) {
          ctx.globalAlpha = 1;
          ctx.lineWidth = 1.5;
          ctx.strokeStyle = colours.ink;
          ctx.beginPath();
          ctx.arc(it.p.x, it.p.y, r + 2.5, 0, 2 * Math.PI);
          ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;
    }

    // labels: value-1 rays get a "1", the selected or hovered ray its coordinates
    ctx.font = '600 12px ui-monospace, "Cascadia Mono", Consolas, Menlo, monospace';
    ctx.textBaseline = 'middle';
    const label = (i, text) => {
      const [p, q] = screen[i];
      const e = p.z >= q.z ? p : q;
      const tw = ctx.measureText(text).width;
      let x = e.x + 10;
      if (x + tw + 6 > w) x = e.x - 10 - tw;
      const y = Math.min(h - 10, Math.max(10, e.y - 12));
      ctx.fillStyle = colours.bg;
      ctx.globalAlpha = 0.85;
      ctx.fillRect(x - 3, y - 9, tw + 6, 18);
      ctx.globalAlpha = 1;
      ctx.fillStyle = colours.ink;
      ctx.fillText(text, x, y);
    };
    for (const i of view.ones) if (i !== hover) label(i, '1');
    if (view.selected >= 0 && view.selected !== hover) label(view.selected, formatRay(model.rays[view.selected]));
    if (hover >= 0) label(hover, formatRay(model.rays[hover]) + (view.ones.has(hover) ? ' = 1' : ''));
  }

  function pick(x, y, radius) {
    let best = -1, bestScore = Infinity;
    for (let i = 0; i < screen.length; i++) {
      for (const p of screen[i]) {
        const dist = Math.hypot(p.x - x, p.y - y);
        if (dist > radius) continue;
        const score = dist - 6 * p.z; // prefer the nearer (front) end point
        if (score < bestScore) {
          bestScore = score;
          best = i;
        }
      }
    }
    return best;
  }

  function rotate(dx, dy) {
    R = mul(mul(rotY(dx), rotX(dy)), R);
    draw();
  }

  function stopSpin() {
    spinning = false;
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
    if (hooks.onSpin) hooks.onSpin(false);
  }

  function spinStep() {
    if (!spinning) return;
    R = mul(rotY(0.006), R);
    draw();
    raf = requestAnimationFrame(spinStep);
  }

  // ---- pointer: drag rotates, a click (no movement) picks the nearest ray end point ----
  let drag = null;
  const local = (ev) => {
    const rect = canvas.getBoundingClientRect();
    return { x: ev.clientX - rect.left, y: ev.clientY - rect.top };
  };
  canvas.addEventListener('pointerdown', (ev) => {
    if (ev.button !== undefined && ev.button !== 0) return;
    const p = local(ev);
    drag = { id: ev.pointerId, x: p.x, y: p.y, moved: 0, touch: ev.pointerType === 'touch' };
    try { canvas.setPointerCapture(ev.pointerId); } catch (e) { /* synthetic events have no capture */ }
    if (spinning) stopSpin();
  });
  canvas.addEventListener('pointermove', (ev) => {
    const p = local(ev);
    if (drag && ev.pointerId === drag.id) {
      const dx = p.x - drag.x, dy = p.y - drag.y;
      drag.moved += Math.abs(dx) + Math.abs(dy);
      drag.x = p.x;
      drag.y = p.y;
      if (drag.moved > 4) {
        canvas.classList.add('dragging');
        rotate(dx * 0.0085, dy * 0.0085);
      }
      return;
    }
    const i = pick(p.x, p.y, 12);
    if (i !== hover) {
      hover = i;
      canvas.style.cursor = i >= 0 ? 'pointer' : '';
      if (hooks.onHover) hooks.onHover(i);
      draw();
    }
  });
  const endDrag = (ev, cancelled) => {
    if (!drag || ev.pointerId !== drag.id) return;
    const wasClick = !cancelled && drag.moved <= 4;
    const radius = drag.touch ? 22 : 14;
    const p = local(ev);
    drag = null;
    canvas.classList.remove('dragging');
    if (wasClick) {
      const i = pick(p.x, p.y, radius);
      if (i >= 0 && hooks.onPick) hooks.onPick(i);
    }
  };
  canvas.addEventListener('pointerup', (ev) => endDrag(ev, false));
  canvas.addEventListener('pointercancel', (ev) => endDrag(ev, true));
  canvas.addEventListener('pointerleave', () => {
    if (hover !== -1 && !drag) {
      hover = -1;
      if (hooks.onHover) hooks.onHover(-1);
      draw();
    }
  });
  canvas.addEventListener('keydown', (ev) => {
    const step = 0.16;
    const moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    if (moves[ev.key]) {
      ev.preventDefault();
      if (spinning) stopSpin();
      rotate(moves[ev.key][0], moves[ev.key][1]);
    } else if (ev.key === 'Home') {
      ev.preventDefault();
      api.reset();
    }
  });

  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(resize).observe(canvas);
  else window.addEventListener('resize', resize);
  const scheme = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;
  if (scheme && scheme.addEventListener) scheme.addEventListener('change', () => { readColours(); draw(); });

  const api = {
    setView(v) {
      view = Object.assign({ selected: -1, partners: new Set(), ones: new Set(), zeros: new Set(), bad: new Set(), triangles: [], dimOthers: false }, v);
      draw();
    },
    rotate,
    reset() {
      if (spinning) stopSpin();
      R = START.slice();
      draw();
    },
    setSpin(on) {
      if (on && !spinning) {
        spinning = true;
        if (hooks.onSpin) hooks.onSpin(true);
        raf = requestAnimationFrame(spinStep);
      } else if (!on && spinning) stopSpin();
    },
    isSpinning: () => spinning,
    redraw() { readColours(); draw(); },
    /** Screen position (CSS pixels, relative to the canvas) of the nearer end point of ray i: used by tests. */
    endPoint(i) {
      const [p, q] = screen[i];
      const e = p.z >= q.z ? p : q;
      return { x: e.x, y: e.y };
    },
  };
  readColours();
  resize();
  return api;
}
