#!/usr/bin/env node
/* Fire Code chapter objects, part 2 (Chapters 22-31): the outlines that are organic unions - a hand of bananas, a beetle and its legs, a
   stack of logs, a grain bin, a fuel dispenser's hose loop, a paint can and its run of paint - built from signed distance fields and
   written into tools/chapter-objects/part-2.js as plain path strings (between its @@P2_SHAPES markers), so the page never traces anything
   (traced at load, the ten took most of a second).
     node tools/chapter-objects/gen-part-2.js            rewrite the block
     node tools/chapter-objects/gen-part-2.js --check    exit 1 if the block is stale
   The parts are capsules, tapered capsules, circles, ellipses, boxes and polygons, joined with a smooth minimum (every join filleted,
   never a hard notch); the zero line is traced by marching squares on a half-unit grid (linear edge points), simplified to 0.04 units,
   into ONE closed M L .. Z path (and, with trace(), any holes as their own paths). Not a part file (the merge reads part-*.js only). */
const fs = require("fs"), path = require("path");
const len = (x, y) => Math.sqrt(x * x + y * y);
/* signed distances: negative inside */
const circle = (cx, cy, r) => (x, y) => len(x - cx, y - cy) - r;
const ellipse = (cx, cy, rx, ry) => (x, y) => { const u = (x - cx) / rx, v = (y - cy) / ry; return (len(u, v) - 1) * Math.min(rx, ry); };
const capsule = (ax, ay, bx, by, r) => (x, y) => {
  const px = x - ax, py = y - ay, ux = bx - ax, uy = by - ay, h = Math.max(0, Math.min(1, (px * ux + py * uy) / (ux * ux + uy * uy || 1)));
  return len(px - ux * h, py - uy * h) - r; };
/* a capsule whose ends have different radii (the exact 2D "uneven capsule") */
const cone = (ax, ay, bx, by, ra, rb) => (x, y) => {
  const px = x - ax, py = y - ay, qx0 = bx - ax, qy0 = by - ay, h = qx0 * qx0 + qy0 * qy0;
  if(h < 1e-9) return len(px, py) - Math.max(ra, rb);
  const qx = Math.abs((px * qy0 - py * qx0) / h), qy = (px * qx0 + py * qy0) / h;
  const b = ra - rb, cx = Math.sqrt(Math.max(1e-9, h - b * b)), cy = b;
  const k = cx * qy - cy * qx, m = cx * qx + cy * qy, n = qx * qx + qy * qy;
  if(k < 0) return Math.sqrt(h * n) - ra;
  if(k > cx) return Math.sqrt(h * (n + 1 - 2 * qy)) - rb;
  return m - ra; };
const box = (x0, y0, w, h, r) => (x, y) => {
  const hx = w / 2, hy = h / 2, qx = Math.abs(x - x0 - hx) - hx + r, qy = Math.abs(y - y0 - hy) - hy + r;
  return len(Math.max(qx, 0), Math.max(qy, 0)) + Math.min(Math.max(qx, qy), 0) - r; };
/* an exact polygon distance */
const poly = pts => (x, y) => {
  let d = Infinity, s = 1;
  for(let i = 0, j = pts.length - 1; i < pts.length; j = i++){
    const ax = pts[j][0], ay = pts[j][1], bx = pts[i][0], by = pts[i][1], ex = bx - ax, ey = by - ay, wx = x - ax, wy = y - ay;
    const t = Math.max(0, Math.min(1, (wx * ex + wy * ey) / (ex * ex + ey * ey || 1))), dx = wx - ex * t, dy = wy - ey * t;
    d = Math.min(d, dx * dx + dy * dy);
    const c1 = y >= ay, c2 = y < by, c3 = ex * wy > ey * wx;
    if((c1 && c2 && c3) || (!c1 && !c2 && !c3)) s = -s;
  }
  return s * Math.sqrt(d); };
/* a tapered tube along a quadratic curve: radius rf(t) */
const tube = (p0, p1, p2, rf, n) => {
  const N = n || 18, pt = t => [(1 - t) * (1 - t) * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) * (1 - t) * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]];
  const segs = []; for(let i = 0; i < N; i++){ const a = pt(i / N), b = pt((i + 1) / N); segs.push(cone(a[0], a[1], b[0], b[1], rf(i / N), rf((i + 1) / N))); }
  return (x, y) => { let d = Infinity; for(const f of segs){ const v = f(x, y); if(v < d) d = v; } return d; }; };
const smin = (a, b, k) => { if(!k) return Math.min(a, b); const h = Math.max(k - Math.abs(a - b), 0) / k; return Math.min(a, b) - h * h * k / 4; };
const union = (fs, k) => (x, y) => { let d = fs[0](x, y); for(let i = 1; i < fs.length; i++) d = smin(d, fs[i](x, y), k); return d; };
const minus = (a, b) => (x, y) => Math.max(a(x, y), -b(x, y));
const inter = (a, b) => (x, y) => Math.max(a(x, y), b(x, y));
const grow = (a, r) => (x, y) => a(x, y) - r;
/* the zero line of f over a box [x0, y0, x1, y1], as closed loops (largest first); step 0.5, the grid nudged off the whole and half
   units so no sample lands exactly on an edge that sits on them (a zero there made a segment's direction ambiguous and broke its loop) */
const loops = (f, bb) => {
  const s = .5, x0 = Math.floor(bb[0]) - 1 + .0137, y0 = Math.floor(bb[1]) - 1 + .0119, nx = Math.ceil((bb[2] - bb[0] + 2) / s) + 1, ny = Math.ceil((bb[3] - bb[1] + 2) / s) + 1;
  const v = new Float64Array(nx * ny);
  for(let j = 0; j < ny; j++) for(let i = 0; i < nx; i++){ let q = f(x0 + i * s, y0 + j * s); if(q === 0) q = 1e-7; v[j * nx + i] = (i === 0 || j === 0 || i === nx - 1 || j === ny - 1) ? Math.max(q, 1e-3) : q; }
  /* an edge point: key = cell index * 2 (+1 for the vertical edge below the cell's corner) */
  const ept = key => { const e = key & 1, c = key >> 1, i = c % nx, j = (c - i) / nx;
    const a = v[j * nx + i], b = e ? v[(j + 1) * nx + i] : v[j * nx + i + 1], t = a / (a - b), px = x0 + i * s, py = y0 + j * s;
    return e ? [px, py + t * s] : [px + t * s, py]; };
  const next = new Map(), shared = { TL: "a", LT: "a", TR: "b", RT: "b", RB: "c", BR: "c", BL: "d", LB: "d", TB: "a", BT: "a", LR: "a", RL: "a" };
  for(let j = 0; j < ny - 1; j++) for(let i = 0; i < nx - 1; i++){
    const A = v[j * nx + i] < 0, B = v[j * nx + i + 1] < 0, C = v[(j + 1) * nx + i + 1] < 0, D = v[(j + 1) * nx + i] < 0;
    if(A === B && B === C && C === D) continue;
    const K = { T: (j * nx + i) << 1, B: ((j + 1) * nx + i) << 1, L: ((j * nx + i) << 1) | 1, R: ((j * nx + i + 1) << 1) | 1 };
    const corner = { a: [i, j, A], b: [i + 1, j, B], c: [i + 1, j + 1, C], d: [i, j + 1, D] }, pairs = [], crossed = [];
    if(A !== B) crossed.push("T"); if(B !== C) crossed.push("R"); if(C !== D) crossed.push("B"); if(D !== A) crossed.push("L");
    if(crossed.length === 2) pairs.push(crossed);
    else { const ctr = (v[j * nx + i] + v[j * nx + i + 1] + v[(j + 1) * nx + i + 1] + v[(j + 1) * nx + i]) / 4 < 0;
      if(ctr === A) pairs.push(["T", "R"], ["B", "L"]); else pairs.push(["T", "L"], ["R", "B"]); }
    for(const pr of pairs){
      let k1 = K[pr[0]], k2 = K[pr[1]]; const cn = corner[shared[pr[0] + pr[1]]];
      const p = ept(k1), q = ept(k2), kx = x0 + cn[0] * s, ky = y0 + cn[1] * s;
      const cr = (q[0] - p[0]) * (ky - p[1]) - (q[1] - p[1]) * (kx - p[0]);
      if((cr > 0) !== cn[2]){ const t = k1; k1 = k2; k2 = t; }
      next.set(k1, k2);
    }
  }
  const out = [], seen = new Set();
  for(const k of next.keys()){
    if(seen.has(k)) continue;
    const lp = []; let c = k;
    while(c !== undefined && !seen.has(c)){ seen.add(c); lp.push(ept(c)); c = next.get(c); }
    if(lp.length > 4) out.push(lp);
  }
  const area = l => { let a = 0; for(let i = 0, j = l.length - 1; i < l.length; j = i++) a += (l[j][0] * l[i][1] - l[i][0] * l[j][1]); return a / 2; };
  out.sort((a, b) => Math.abs(area(b)) - Math.abs(area(a)));
  return out; };
/* Douglas-Peucker on a closed loop, then a path */
const simp = (pts, tol) => {
  const dp = (a, b, keep) => { let m = -1, mi = -1; const ax = pts[a][0], ay = pts[a][1], ex = pts[b][0] - ax, ey = pts[b][1] - ay, L = len(ex, ey) || 1;
    for(let i = a + 1; i < b; i++){ const dd = Math.abs((pts[i][0] - ax) * ey - (pts[i][1] - ay) * ex) / L; if(dd > m){ m = dd; mi = i; } }
    if(m > tol){ keep[mi] = 1; dp(a, mi, keep); dp(mi, b, keep); } };
  const n = pts.length, h = n >> 1, keep = new Uint8Array(n); keep[0] = keep[h] = keep[n - 1] = 1;
  dp(0, h, keep); dp(h, n - 1, keep);
  return pts.filter((p, i) => keep[i]); };
const pathOf = l => { const q = simp(l, .04), f = v => String(Math.round(v * 100) / 100); return "M" + q.map(p => f(p[0]) + " " + f(p[1])).join("L") + "Z"; };
/* the outline of f (its largest loop) and its holes (every other loop) */
const trace = (f, bb) => { const ls = loops(f, bb); return { d: pathOf(ls[0]), holes: ls.slice(1).map(pathOf) }; };
const shape = (f, bb) => pathOf(loops(f, bb)[0]);
const OUT = {};

/* Chapter 22: the grain bin (a cylinder: a curved foot and a curved eave), its cone roof and cap, and on its RIGHT the elevator leg,
   head and boot, with the spout running down from the head into the cap (on the left, the leg's long side wall pulled the pin's wall
   up-left of its face) */
{
  const bin = union([box(12, 48, 54, 42, 0), ellipse(39, 90, 27, 5)], 0);
  const eave = ellipse(39, 47, 31, 4.5);
  const roof = poly([[46, 22], [32, 22], [9, 45], [69, 45]]);
  const cap = box(31, 14, 16, 9, 2);
  const leg = box(80, 12, 10, 72, 0), head = box(77, 4, 16, 10, 2), boot = box(75, 82, 20, 12, 2);
  const spout = poly([[78, 6.5], [46, 16], [46, 22.5], [78, 13.5]]);
  OUT.c22 = { d: shape(union([bin, eave, roof, cap, leg, head, boot, spout], 1.6), [2, 1, 98, 99]), bin: shape(bin, [8, 44, 70, 99]),
    eave: shape(eave, [4, 40, 74, 54]) };
}
/* Chapter 23: the dispenser, its plinth, the hose loop (a hole) and the nozzle hung in its holster */
{
  const hose = union([capsule(66, 71.5, 80, 71.5, 3.6), capsule(83.5, 40, 83.5, 64, 3.6), tube([78, 71.5], [83.5, 71.5], [83.5, 64], () => 3.6, 6)], 0);
  const nozzle = union([box(75, 22, 17, 11, 3), capsule(83.5, 30, 83.5, 41, 3.6), capsule(77, 26, 68, 33, 2.8)], 2);
  const body = union([box(20, 12, 48, 76, 3), box(15, 3, 58, 13, 4), box(14, 86, 60, 9, 2.5)], 1.5);
  const sil = trace(union([body, hose, nozzle], 2.4), [10, 2, 96, 98]);
  OUT.c23 = { d: sil.d, holes: sil.holes, hose: shape(hose, [60, 36, 90, 78]), nozzle: shape(nozzle, [58, 18, 94, 44]) };
}
/* Chapter 25: three fingers fanning from the crown */
{
  const rf = R => t => t < .1 ? 3 + 8 * t : 3.8 + (R - 3.8) * Math.pow(Math.sin(Math.PI * Math.min(1, (t - .1) / .95)), .55);
  const B1 = tube([20, 20], [56, 42], [92, 16], rf(9.4), 20), B2 = tube([18, 24], [46, 62], [88, 46], rf(10), 20), B3 = tube([16, 28], [28, 82], [70, 84], rf(10.6), 20);
  const crown = capsule(11, 12, 19, 23, 5), bb = [2, 2, 98, 98];
  OUT.c25 = { d: shape(union([B1, B2, B3, crown], 3), bb),
    b1: shape(minus(B1, grow(union([B2, B3, crown], 0), .4)), bb), b2: shape(minus(B2, grow(union([B3, crown], 0), .4)), bb),
    b3: shape(minus(B3, grow(crown, .4)), bb), crown: shape(crown, bb) };
}
/* Chapter 26: the beetle (legs and antennae as capsules; part-2.js strokes the same polylines, P2B, for their parts) */
{
  const legs = [[[37, 34], [26, 30], [20, 18]], [[30, 52], [16, 50], [9, 62]], [[32, 70], [20, 78], [16, 92]]], ant = [[45, 13], [40, 7], [32, 4]];
  const mir = p => [100 - p[0], p[1]], caps = [];
  const chain = (pts, r) => { for(let i = 0; i < pts.length - 1; i++) caps.push(capsule(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], r)); };
  legs.forEach(l => { chain(l, 2.7); chain(l.map(mir), 2.7); }); chain(ant, 2.5); chain(ant.map(mir), 2.5);
  OUT.c26 = { d: shape(union([ellipse(50, 62, 24, 31), box(33, 26, 34, 16, 6), ellipse(50, 18, 10, 8.5)].concat(caps), 2.6), [2, 0, 98, 98]) };
}
/* Chapter 27: the package and its sixteen pins */
{
  const pins = []; [31, 43, 57, 69].forEach(c => { pins.push(box(c - 3, 6, 6, 18, 1.5), box(c - 3, 76, 6, 18, 1.5), box(6, c - 3, 18, 6, 1.5), box(76, c - 3, 18, 6, 1.5)); });
  OUT.c27 = { d: shape(union([box(20, 20, 60, 60, 4)].concat(pins), 1.6), [2, 2, 98, 98]) };
}
/* Chapter 28: six log ends, three, two, one */
{
  const L = [[22, 78], [50, 78], [78, 78], [36, 53.75], [64, 53.75], [50, 29.5]];
  OUT.c28 = { d: shape(union(L.map(c => circle(c[0], c[1], 14)), 4), [4, 12, 96, 96]) };
}
/* Chapter 29: the can, the bail (a hole under it) and the paint run over the rim, down the side and into a pool */
{
  const can = union([box(18, 30, 64, 60, 5), box(14, 25, 72, 9, 3)], 1.2);
  const bail = minus(inter(ellipse(50, 30, 35, 27), (x, y) => y - 30), ellipse(50, 30, 29.5, 21.5));
  const paint = union([box(13, 24, 74, 11, 4), capsule(26, 30, 26, 52, 5), capsule(44, 30, 44, 44, 4.4), capsule(66, 30, 66, 58, 4.8),
    capsule(19, 30, 17, 88, 4.4), ellipse(30, 91, 22, 5)], 3);
  const all = union([can, bail, paint], 2), sil = trace(all, [4, 0, 96, 99]);
  OUT.c29 = { d: sil.d, holes: sil.holes, can: shape(can, [10, 20, 90, 94]), bail: shape(bail, [10, 0, 90, 34]),
    paint: shape(inter(paint, grow(all, -.01)), [4, 18, 96, 99]) };
}

const P = path.join(__dirname, "part-2.js"), src = fs.readFileSync(P, "utf8");
const B = "/* @@P2_SHAPES_BEGIN (generated by tools/chapter-objects/gen-part-2.js: never edit by hand) */", E = "/* @@P2_SHAPES_END */";
const i = src.indexOf(B), j = src.indexOf(E);
if(i < 0 || j < 0){ console.error("part-2.js has no @@P2_SHAPES block"); process.exit(2); }
const block = "\n  const P2S = {\n" + Object.keys(OUT).map(k => "    " + k + ": " + JSON.stringify(OUT[k]) + ",\n").join("") + "  };\n  ";
const out = src.slice(0, i + B.length) + block + src.slice(j);
if(process.argv.includes("--check")){ console.log(out === src ? "in step" : "part-2.js's shapes are stale (run node tools/chapter-objects/gen-part-2.js)"); process.exit(out === src ? 0 : 1); }
fs.writeFileSync(P, out); console.log("wrote", Object.keys(OUT).length, "shape sets,", block.length, "chars");
