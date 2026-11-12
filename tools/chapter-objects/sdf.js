/* Fire Code chapter objects (384.68): OBJ_SDF, outlines built from signed distance fields - for any part file, at MERGE time.
   Lifted from part 2's generator (gen-part-2.js, which pre-traced its organic unions - a hand of bananas, a beetle, a stack of logs - so the
   page never traced anything). Since 384.67 the merge RUNS the part files under node and writes their entries into index.html as plain
   data (baked), so a part file may call these directly: they run once, at merge, and the page never sees them.
     const S = OBJ_SDF, f = S.union([S.circle(30, 40, 12), S.capsule(30, 40, 70, 60, 5)], 2);   // a filleted union
     CHAPTER_OBJ["..."] = { d: S.shape(f, [0, 0, 100, 100]), ... };                             // its outline, one closed M L .. Z path
     const t = S.trace(f, bb);  t.d, t.holes                                                      // the outline and its holes
   Primitives (negative inside): circle, ellipse, capsule, cone (an uneven capsule), box (rounded), poly (exact), tube (a tapered tube
   along a quadratic curve). Combinators: union(fs, k) (a smooth minimum with fillet k), minus, inter, grow. The zero line is traced by
   marching squares on a half-unit grid and simplified to 0.04 units. Loaded by tools/chapter-objects/measure.js before the part files;
   also require()-able (gen-part-2.js uses it). */
const OBJ_SDF = (() => {
const len = (x, y) => Math.sqrt(x * x + y * y);
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
return { len, circle, ellipse, capsule, cone, box, poly, tube, smin, union, minus, inter, grow, loops, simp, pathOf, trace, shape };
})();
if(typeof module !== "undefined" && module.exports) module.exports = OBJ_SDF;
