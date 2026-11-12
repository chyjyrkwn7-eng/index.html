async (args) => {
  /* (384.90) SNAP EVERY PART TO WHAT IT MEETS - run in the page by tools/chapter-objects/snap.py, baked by the merge.
     Madison: "I still see a few spots on some where the connections of pieces aren't right. Ensure all the edges are perfect." A part
     drawn to meet the outline or its neighbour but stopping a fraction short (a rounded corner inside a sharper one, a traced outline a
     tenth of a unit inside the union it came from, a panel ending half a unit before the edge) leaves a sliver of the base showing - in
     the base's colour and with the part's own bevel standing a hair inside the edge. This finds every such sliver, read off the parts at
     12 px a unit: a run of base 0.8 units wide or less between a part and the outline, or between two parts, and gives it to the part
     nearest it (between two, split down the middle). Each part's sliver is traced to a polygon in the part's own units, overlapping the
     part a little and wound the same way, so that appended to the part's path it is one shape with it: its colour, material, height and
     bevel all run to the edge it meets. Line parts (ln) never take a sliver; a sliver only a line borders is left (the gate reports it).
     args: { units: [...] | null }. Returns { unit: { sil, plates: { index: { h, add } } } }, h a hash of the part's path (the merge applies
     a snap only to the very path it was traced for). */
  const units = (args && args.units) || Object.keys(CHAPTER_OBJ);
  const hash = s => { let h = 2166136261 >>> 0; for(let i = 0; i < s.length; i++){ h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; } return h.toString(36); };
  const K_F = 12, WIDTH = .8;
  const out = {};
  for(const u of units){
    const e = CHAPTER_OBJ[u]; if(!e || !Array.isArray(e.plates)) continue;
    const face = badgeFaceShapeFor(u);
    const vb = badgeViewBoxFor(face.d).split(/\s+/).map(Number), vx = vb[0], vy = vb[1], vw = vb[2], S = BADGE_GEOM.scale, cx = face.c[0], cy = face.c[1];
    const W = Math.ceil(vw * K_F), N = W * W, pxPerF = W / vw, k = pxPerF * S;
    const setT = g => { g.setTransform(pxPerF, 0, 0, pxPerF, -vx * pxPerF, -vy * pxPerF); g.translate(cx, cy); g.scale(S, S); g.translate(-cx, -cy); };
    /* grid point (corner) coordinates: pixel (i, j) has its centre at i + .5; a grid value at (i, j) is that pixel */
    const toS = (px, py) => [((px + .5) / pxPerF + vx - cx) / S + cx, ((py + .5) / pxPerF + vy - cy) / S + cy];
    const sil = new Path2D(face.d);
    const cs = badgeCoverage(W, g => { setT(g); g.fillStyle = "#000"; g.fill(sil); });
    const L = new Int16Array(N); for(let i = 0; i < N; i++) L[i] = cs[i] >= .5 ? -1 : -2;
    const raw = e.plates, info = [];
    raw.forEach((q, idx) => {
      if(!Array.isArray(q) || typeof q[1] !== "string") return;
      const o = q[2] || {}; if(o.paint === 0) return;
      const P = new Path2D(q[1]), ln = +o.ln > 0 ? +o.ln : 0;
      const c = badgeCoverage(W, g => { setT(g); g.fillStyle = g.strokeStyle = "#000"; if(ln){ g.lineWidth = ln; g.lineCap = "round"; g.lineJoin = "round"; g.stroke(P); } else g.fill(P); });
      for(let i = 0; i < N; i++) if(c[i] >= .5 && L[i] !== -2) L[i] = idx;
      info[idx] = { ln, c };
    });
    /* the slivers, and whose they are */
    const R = Math.ceil(WIDTH * k), own = new Int16Array(N).fill(-1);
    const dirs = [[1, 0, 1], [0, 1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2]];
    const isFill = l => l >= 0 && info[l] && !info[l].ln;
    /* colours: a sliver already the colour of a part it borders reads as that part - it goes to that part if it can (its relief then
       runs to the edge too) and is otherwise left (a line's colour: the fillet where a leg joins a body) */
    const pal = chapterObjPalette(u), HEX = /^#[0-9a-fA-F]{6}$/;
    const rgb = c => badgeHexRgb(c), baseC = rgb(pal[e.base] || pal.field);
    const colOf = idx => { const q = raw[idx], o = q[2] || {}; return rgb(HEX.test(o.col || "") ? o.col : (pal[q[0]] || pal.field)); };
    const same = idx => { if(idx < 0 || !info[idx]) return false; const c = colOf(idx); return Math.hypot(c[0] - baseC[0], c[1] - baseC[1], c[2] - baseC[2]) < 6; };
    for(let y = 1; y < W - 1; y++) for(let x = 1; x < W - 1; x++){
      const i = y * W + x; if(L[i] !== -1) continue;
      let best = null;
      for(const [dx, dy, dl] of dirs){
        let a = null, sa = 0, b = null, sb = 0;
        for(let s = 1; s <= R; s++){ const xx = x + dx * s, yy = y + dy * s; if(xx < 0 || yy < 0 || xx >= W || yy >= W) break; const l = L[yy * W + xx]; if(l !== -1){ a = l; sa = s; break; } }
        if(a === null) continue;
        for(let s = 1; s <= R; s++){ const xx = x - dx * s, yy = y - dy * s; if(xx < 0 || yy < 0 || xx >= W || yy >= W) break; const l = L[yy * W + xx]; if(l !== -1){ b = l; sb = s; break; } }
        if(b === null) continue;
        const w = (sa + sb - 1) * dl / k; if(w > WIDTH) continue;
        /* already one of its neighbours' colour: that neighbour takes it if it is a fill; if it is a line, it is left */
        if(same(a) || same(b)){
          const t = same(a) && isFill(a) ? a : same(b) && isFill(b) ? b : null;
          if(t === null){ best = null; break; }
          if(!best || w < best.w) best = { w, t }; continue; }
        if(!isFill(a) && !isFill(b)) continue;
        /* the nearer fill part takes it (a line or the outline never does); between two fills, the nearer */
        let t; if(isFill(a) && isFill(b)) t = sa < sb ? a : sb < sa ? b : Math.max(a, b); else t = isFill(a) ? a : b;
        if(!best || w < best.w) best = { w, t };
      }
      if(best) own[i] = best.t;
    }
    /* PASS 2, the corner specks: where a part's rounded corner sits in a sharper corner of the outline (or of the step where two
       parts meet it), the base left in the corner is wider than 0.8 units across its diagonal but it is a speck, not a channel - a
       small piece of base (at most 3 units across, 3 square units) touching the outline, or at most 1.6 units across anywhere. It goes
       whole to the fill part it borders most. A channel (the gap between two boxes, a line of mortar) is long, and is left. */
    { const cseen = new Uint8Array(N);
      for(let i0 = 0; i0 < N; i0++){
        if(cseen[i0] || L[i0] !== -1 || own[i0] >= 0) continue;
        const st = [i0], comp = []; cseen[i0] = 1; let x0 = W, x1 = 0, y0 = W, y1 = 0, edge = false; const touch = {}, lineTouch = {};
        while(st.length && comp.length < 40000){ const q = st.pop(); comp.push(q); const qx = q % W, qy = (q - qx) / W;
          if(qx < x0) x0 = qx; if(qx > x1) x1 = qx; if(qy < y0) y0 = qy; if(qy > y1) y1 = qy;
          for(const r of [q - 1, q + 1, q - W, q + W]){ if(r < 0 || r >= N) continue;
            if(L[r] === -1 && own[r] < 0){ if(!cseen[r]){ cseen[r] = 1; st.push(r); } }
            else if(L[r] === -2) edge = true;
            else { const t = own[r] >= 0 ? own[r] : L[r]; if(isFill(t)) touch[t] = (touch[t] || 0) + 1; else if(t >= 0) lineTouch[t] = 1; } } }
        const ext = Math.max(x1 - x0 + 1, y1 - y0 + 1) / k, area = comp.length / (k * k);
        const keys = Object.keys(touch); if(!keys.length) continue;
        if((edge && ext <= 3 && area <= 3) || ext <= 1.6){
          /* a speck the colour of a part it borders reads as that part: it is left, unless that part is a fill (its relief then runs on) */
          const sameK = keys.filter(t => same(+t));
          if(Object.keys(lineTouch).some(t => same(+t)) && !sameK.length) continue;
          const t = sameK.length ? +sameK.sort((p, q) => touch[q] - touch[p])[0] : +keys.sort((p, q) => touch[q] - touch[p])[0];
          comp.forEach(q => { own[q] = t; }); }
      } }
    const res = {};
    const parts = [...new Set(Array.from(own).filter(v => v >= 0))];
    for(const a of parts){
      /* the part's sliver, grown 2 px into the part itself (an overlap, so the two are one shape with no seam) */
      const M = new Uint8Array(N); let n = 0;
      for(let i = 0; i < N; i++) if(own[i] === a){ M[i] = 1; n++; }
      if(n < 2) continue;
      /* grown 2 px into the part itself and past the outline (unseen out there: so the sliver's traced edge can never fall short of the
         outline), and 1 px into a neighbour's sliver (the two meet with an overlap, never a hairline) */
      const ca = info[a].c, M2 = M.slice();
      for(let pass = 0; pass < 2; pass++){ const M3 = M2.slice();
        for(let y = 1; y < W - 1; y++) for(let x = 1; x < W - 1; x++){ const i = y * W + x; if(M2[i]) continue;
          const ok = ca[i] >= .5 || L[i] === -2 || (pass === 0 && own[i] >= 0);
          if(ok && (M2[i - 1] || M2[i + 1] || M2[i - W] || M2[i + W])) M3[i] = 1; }
        M2.set(M3); }
      /* traced: marching squares on the pixel grid (edge points at the half-way crossing), each loop simplified to .03 units */
      const val = (i, j) => (i < 0 || j < 0 || i >= W || j >= W) ? .5 : (M2[j * W + i] ? -.5 : .5);
      const ST = W + 2, ept = (key) => { const ev = key & 1, cI = key >> 1, i = cI % ST, j = (cI - i) / ST;
        return ev ? [i, j + .5] : [i + .5, j]; };
      const next = new Map();
      const K = (i, j) => (j * ST + i);
      for(let j = -1; j < W; j++) for(let i = -1; i < W; i++){
        const A = val(i, j) < 0, B = val(i + 1, j) < 0, C = val(i + 1, j + 1) < 0, D = val(i, j + 1) < 0;
        if(A === B && B === C && C === D) continue;
        const ii = i + 1, jj = j + 1;   /* shift by one so keys stay non-negative */
        const KT = K(ii, jj) << 1, KB = K(ii, jj + 1) << 1, KL = (K(ii, jj) << 1) | 1, KR = (K(ii + 1, jj) << 1) | 1;
        const edges = { T: KT, B: KB, L: KL, R: KR };
        /* walk with the inside on the left: a segment from the edge where we enter to the edge where we leave */
        const segs = [];
        const code = (A ? 8 : 0) | (B ? 4 : 0) | (C ? 2 : 0) | (D ? 1 : 0);
        switch(code){
          case 1: segs.push(["L", "B"]); break; case 2: segs.push(["B", "R"]); break; case 3: segs.push(["L", "R"]); break;
          case 4: segs.push(["R", "T"]); break; case 5: segs.push(["R", "T"], ["L", "B"]); break; case 6: segs.push(["B", "T"]); break;
          case 7: segs.push(["L", "T"]); break; case 8: segs.push(["T", "L"]); break; case 9: segs.push(["T", "B"]); break;
          case 10: segs.push(["T", "L"], ["B", "R"]); break; case 11: segs.push(["T", "R"]); break; case 12: segs.push(["R", "L"]); break;
          case 13: segs.push(["R", "B"]); break; case 14: segs.push(["B", "L"]); break;
        }
        segs.forEach(([p, q]) => next.set(edges[p], edges[q]));
      }
      const loops = [], seen = new Set();
      for(const k0 of next.keys()){ if(seen.has(k0)) continue; const lp = []; let c = k0;
        while(c !== undefined && !seen.has(c)){ seen.add(c); const p = ept(c); lp.push([p[0] - 1, p[1] - 1]); c = next.get(c); }
        if(lp.length > 3) loops.push(lp); }
      const simp = (pts, tol) => { const n2 = pts.length; if(n2 < 4) return pts; const keep = new Uint8Array(n2); keep[0] = keep[n2 - 1] = 1; const h = n2 >> 1; keep[h] = 1;
        const dp = (a0, b0) => { let m = -1, mi = -1; const ax = pts[a0][0], ay = pts[a0][1], ex = pts[b0][0] - ax, ey = pts[b0][1] - ay, Ln = Math.hypot(ex, ey) || 1;
          for(let q = a0 + 1; q < b0; q++){ const dd = Math.abs((pts[q][0] - ax) * ey - (pts[q][1] - ay) * ex) / Ln; if(dd > m){ m = dd; mi = q; } }
          if(m > tol){ keep[mi] = 1; dp(a0, mi); dp(mi, b0); } };
        dp(0, h); dp(h, n2 - 1); return pts.filter((p, q) => keep[q]); };
      const f2 = v => String(Math.round(v * 100) / 100);
      /* the part's own winding at a point it covers: a sliver loop must not cut a hole where it overlaps the part */
      const cvT = document.createElement("canvas").getContext("2d");
      let add = "";
      loops.forEach(lp => {
        /* the loop's points are in sample (pixel-centre) coordinates, which toS takes */
        let pts = simp(lp.map(p => toS(p[0], p[1])), .03);
        if(pts.length < 3) return;
        let d = "M" + pts.map(p => f2(p[0]) + " " + f2(p[1])).join("L") + "Z";
        /* a point of the part that this loop overlaps: if part + loop does not cover it, the loop winds against the part - turn it round */
        let probe = null; const lpP = new Path2D(d);
        for(let i = 0, tries = 0; i < N && !probe && tries < 4000; i++) if(M2[i] && !M[i] && ca[i] > .99){ tries++; const x = i % W, q = toS(x, (i - x) / W);
          if(cvT.isPointInPath(lpP, q[0], q[1], "nonzero")) probe = q; }
        if(probe){ const both = new Path2D(raw[a][1] + " " + d); if(!cvT.isPointInPath(both, probe[0], probe[1], "nonzero")){
          pts = pts.slice().reverse(); d = "M" + pts.map(p => f2(p[0]) + " " + f2(p[1])).join("L") + "Z"; } }
        add += (add ? " " : "") + d;
      });
      if(add) res[a] = { h: hash(raw[a][1]), add, px: n };
    }
    out[u] = { sil: hash(e.d), plates: res };
  }
  return out;
}
