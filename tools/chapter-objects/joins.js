async (only) => {
  /* (384.90) JOINS AND EDGES, per authored chapter, read off its own parts at ~5.6 px a unit:
     gaps   - a hairline (0.8 units or less) of a DIFFERENT colour between two parts, or between a part and the outline (a part that
              stops just short of the edge it should meet);
     fringe - along a boundary where two parts meet, the colour map's pixel must be a mix of those two colours, not pulled toward the
              base under them (the canvas's conflation seam);
     seams  - two parts of the same colour, both sculpted (z, dome, gem), that partly overlap: one piece drawn as two shapes leaves a
              doubled bevel and a seam inside it;
     spikes - on the outline (and every hole): within any 2 units of its length the path turns 150 degrees or more back and forth
              while netting under 60 - a nub or a notch, not a corner;
     sym    - a silhouette that is ALMOST mirror-symmetric (IoU with its mirror 0.975 to 0.995) was meant to be symmetric and is not. */
  const lin = v => { v /= 255; return v <= .04045 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); };
  const lab = c => { const R = lin(c[0]), G = lin(c[1]), B = lin(c[2]);
    const X = (R * .4124 + G * .3576 + B * .1805) / .95047, Y = R * .2126 + G * .7152 + B * .0722, Z = (R * .0193 + G * .1192 + B * .9505) / 1.08883;
    const t = v => v > .008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116; return [116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z))]; };
  const dE = (a, b) => { const p = lab(a), q = lab(b); return Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]); };
  const segDist = (c, a, b) => { const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ac = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const L = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]; let t = L ? (ac[0] * ab[0] + ac[1] * ab[1] + ac[2] * ab[2]) / L : 0; t = t < 0 ? 0 : t > 1 ? 1 : t;
    return Math.hypot(c[0] - a[0] - t * ab[0], c[1] - a[1] - t * ab[1], c[2] - a[2] - t * ab[2]); };
  const out = [];
  const units = Object.keys(CHAPTER_OBJ).filter(u => !only || only.some(o => u.indexOf(o) === 0));
  for(const u of units){
    const face = badgeFaceShapeFor(u), e = chapterObjFor(u), pls = chapterObjPlates(u).filter(p => p.paint), pal = chapterObjPalette(u);
    const vb = badgeViewBoxFor(face.d).split(/\s+/).map(Number), vx = vb[0], vy = vb[1], vw = vb[2], S = BADGE_GEOM.scale, cx = face.c[0], cy = face.c[1];
    const W = 840, N = W * W, pxPerF = W / vw, k = pxPerF * S;
    const setT = g => { g.setTransform(pxPerF, 0, 0, pxPerF, -vx * pxPerF, -vy * pxPerF); g.translate(cx, cy); g.scale(S, S); g.translate(-cx, -cy); };
    const toU = (x, y) => [Math.round(((x + .5) / pxPerF + vx - cx) / S + cx), Math.round(((y + .5) / pxPerF + vy - cy) / S + cy)];
    const sil = new Path2D(face.d);
    const cs = badgeCoverage(W, g => { setT(g); g.fillStyle = "#000"; g.fill(sil); });
    const L = new Int16Array(N); for(let i = 0; i < N; i++) L[i] = cs[i] >= .5 ? -1 : -2;
    const cov = pls.map((pl, idx) => { const P = new Path2D(pl.d);
      /* unclipped, as the colour map paints it (384.90): the outline is the face's own coverage */
      const c = badgeCoverage(W, g => { setT(g); g.fillStyle = g.strokeStyle = "#000";
        if(pl.ln){ g.lineWidth = pl.ln; g.lineCap = "round"; g.lineJoin = "round"; g.stroke(P); } else g.fill(P); });
      for(let i = 0; i < N; i++) if(c[i] >= .5 && L[i] !== -2) L[i] = idx;
      return c; });
    const colOf = pl => badgeHexRgb(pl.col || pal[pl.r] || pal.field), cols = pls.map(colOf), base = badgeHexRgb(pal[(e || {}).base] || pal.field);
    const name = i => i >= 0 ? i + ":" + pls[i].r : i === -1 ? "base" : "edge";
    /* gaps: every connected piece of base showing (4-connected), with its width at each pixel (the narrowest of four directions, out to
       2 units). A piece is a SLIVER if it is thin everywhere (no pixel wider than 0.8 units) or a speck (at most 1.5 square units and 2
       across); it counts if it borders a part whose colour it visibly is not (dE over 10). A big piece of base - the base the design
       shows, a line of mortar, the gap between two boxes - is wide somewhere, and an acute corner of it is part of it, not a sliver. */
    const R2 = Math.ceil(2 * k), wmin = new Float32Array(N).fill(Infinity);
    const dirs = [[1, 0, 1], [0, 1, 1], [1, 1, Math.SQRT2], [1, -1, Math.SQRT2]];
    for(let y = 1; y < W - 1; y++) for(let x = 1; x < W - 1; x++){
      const i = y * W + x; if(L[i] !== -1) continue;
      for(const [dx, dy, dl] of dirs){
        let sa = 0, sb = 0;
        for(let s = 1; s <= R2; s++){ const xx = x + dx * s, yy = y + dy * s; if(xx < 0 || yy < 0 || xx >= W || yy >= W) break; if(L[yy * W + xx] !== -1){ sa = s; break; } }
        if(!sa) continue;
        for(let s = 1; s <= R2; s++){ const xx = x - dx * s, yy = y - dy * s; if(xx < 0 || yy < 0 || xx >= W || yy >= W) break; if(L[yy * W + xx] !== -1){ sb = s; break; } }
        if(!sb) continue;
        const w = (sa + sb - 1) * dl / k; if(w < wmin[i]) wmin[i] = w;
      }
    }
    const comps = [], seen = new Uint8Array(N);
    for(let i0 = 0; i0 < N; i0++){
      if(seen[i0] || L[i0] !== -1) continue;
      const st = [i0]; seen[i0] = 1; let n = 0, sx = 0, sy = 0, x0 = W, x1 = 0, y0 = W, y1 = 0, maxW = 0; const touch = {}; let edge = false;
      while(st.length){ const q = st.pop(), qx = q % W, qy = (q - qx) / W; n++; sx += qx; sy += qy; if(wmin[q] > maxW) maxW = wmin[q];
        if(qx < x0) x0 = qx; if(qx > x1) x1 = qx; if(qy < y0) y0 = qy; if(qy > y1) y1 = qy;
        for(const r of [q - 1, q + 1, q - W, q + W]){ if(r < 0 || r >= N) continue; const l = L[r];
          if(l === -1){ if(!seen[r]){ seen[r] = 1; st.push(r); } } else if(l === -2) edge = true; else touch[l] = (touch[l] || 0) + 1; } }
      const area = n / (k * k), ext = Math.max(x1 - x0 + 1, y1 - y0 + 1) / k;
      if(area < .25) continue;   /* under a quarter of a square unit (2 x 2 device px at 400 CSS px): not a spot */
      const sliver = maxW <= .8 || (area <= 1.5 && ext <= 2);
      if(!sliver) continue;
      /* already the colour of a part it borders, it reads as that part (the fillet where a leg joins a body) */
      if(Object.keys(touch).some(t => dE(base, cols[+t]) <= 10)) continue;
      const vis = Object.keys(touch);
      if(!vis.length) continue;
      const main = vis.sort((p, q) => touch[q] - touch[p])[0];
      comps.push({ n, area: Math.round(area * 100) / 100, at: toU(sx / n, sy / n), pair: name(+main) + "|" + (edge ? "edge" : Object.keys(touch).filter(t => t !== main).map(t => name(+t))[0] || "-"), maxW: Math.round(maxW * 100) / 100 });
    }
    /* fringe */
    let CM = null; try{ CM = chapterObjColourMap(face, { vx, vy, vw, cx, cy, S }, W, u, false); }catch(err){}
    let frMax = 0, frN = 0, frAt = null;
    if(CM) for(let y = 1; y < W - 1; y++) for(let x = 1; x < W - 1; x++){
      const i = y * W + x, a = L[i]; if(a < 0) continue;
      for(const o of [1, W]){ const b = L[i + o]; if(b < 0 || b === a) continue;
        const A = cols[a], B = cols[b], D = Math.min(segDist(base, A, B), 255); if(D < 40) continue;
        for(const p of [i, i + o]){ const j = p * 4, c = [CM[j], CM[j + 1], CM[j + 2]]; /* how far the pixel is pulled toward the BASE (the conflation seam), as a fraction of the way from the two parts' mix to it */ const ab = [B[0] - A[0], B[1] - A[1], B[2] - A[2]], LL = ab[0] * ab[0] + ab[1] * ab[1] + ab[2] * ab[2]; let tq = LL ? ((c[0] - A[0]) * ab[0] + (c[1] - A[1]) * ab[1] + (c[2] - A[2]) * ab[2]) / LL : 0; tq = tq < 0 ? 0 : tq > 1 ? 1 : tq; const pq = [A[0] + tq * ab[0], A[1] + tq * ab[1], A[2] + tq * ab[2]], bb = [base[0] - pq[0], base[1] - pq[1], base[2] - pq[2]], b2 = bb[0] * bb[0] + bb[1] * bb[1] + bb[2] * bb[2]; const r = b2 ? Math.max(0, ((c[0] - pq[0]) * bb[0] + (c[1] - pq[1]) * bb[1] + (c[2] - pq[2]) * bb[2]) / b2) : 0;
          /* a pixel bordering a third part is a three-way corner, not a seam */
          let third = false; for(const q of [p - 1, p + 1, p - W, p + W]) if(L[q] !== a && L[q] !== b) third = true;
          /* ...or any other part's edge within the pixel's reach (under the two, or over them): its colour is in the mix by right */
          if(!third) for(let t = 0; t < pls.length && !third; t++){ if(t === a || t === b) continue; const ct = cov[t];
            for(const q of [p, p - 1, p + 1, p - W, p + W]) if(ct[q] > .02){ third = true; break; } }
          if(third) continue;
          if(r > frMax){ frMax = r; frAt = toU(p % W, (p - p % W) / W).concat([name(a), name(b)]); } if(r > .15) frN++; } }
    }
    /* seams: same colour, both sculpted, partial overlap */
    const seams = [];
    for(let a = 0; a < pls.length; a++) for(let b = a + 1; b < pls.length; b++){
      const A = pls[a], B = pls[b]; if(A.ln || B.ln) continue;
      const sa = A.z || A.dome || A.gem, sb = B.z || B.dome || B.gem; if(!sa || !sb) continue;
      if(dE(cols[a], cols[b]) > 3) continue;
      let ov = 0, onlyA = 0, onlyB = 0, bx = 0, by = 0, bn = 0; const ca = cov[a], cb = cov[b];
      for(let i = 0; i < N; i++){ const ia = ca[i] >= .5, ib = cb[i] >= .5; if(ia && ib) ov++; else if(ia) onlyA++; else if(ib) onlyB++; }
      if(ov > 4 && onlyA > .02 * (ov + onlyA) && onlyB > .02 * (ov + onlyB)){
        /* where the seam runs: the edge of B lying inside A, away from the outline */
        for(let y = 1; y < W - 1; y++) for(let x = 1; x < W - 1; x++){ const i = y * W + x; if(!(cb[i] >= .5 && ca[i] >= .5) || L[i] === -2) continue;
          if((cb[i - 1] < .5 && ca[i - 1] >= .5) || (cb[i + 1] < .5 && ca[i + 1] >= .5) || (cb[i - W] < .5 && ca[i - W] >= .5) || (cb[i + W] < .5 && ca[i + W] >= .5)){ bx += x; by += y; bn++; } }
        seams.push([name(a), name(b), Math.round(ov / (k * k)), bn ? toU(bx / bn, by / bn) : null]); }
    }
    /* spikes on the outline and its holes */
    const spikes = [];
    [e.d].concat(Array.isArray(e.holes) ? e.holes : []).forEach((d, hi) => {
      let pts = []; try{ pts = OBJ_walk(d, 24); }catch(err){ return; }
      const P = []; pts.forEach(p => { const q = P[P.length - 1]; if(!q || Math.hypot(p[0] - q[0], p[1] - q[1]) > 1e-3) P.push(p); });
      if(P.length > 2 && Math.hypot(P[0][0] - P[P.length - 1][0], P[0][1] - P[P.length - 1][1]) < 1e-3) P.pop();
      const n = P.length; if(n < 4) return;
      const turn = [], len = [];
      for(let i = 0; i < n; i++){ const a = P[(i - 1 + n) % n], b = P[i], c = P[(i + 1) % n];
        const t1 = Math.atan2(b[1] - a[1], b[0] - a[0]), t2 = Math.atan2(c[1] - b[1], c[0] - b[0]); let t = t2 - t1; while(t > Math.PI) t -= 2 * Math.PI; while(t < -Math.PI) t += 2 * Math.PI;
        turn.push(t * 180 / Math.PI); len.push(Math.hypot(c[0] - b[0], c[1] - b[1])); }
      for(let i = 0; i < n; i++){ let absT = 0, net = 0, s = 0;
        for(let j = 0; j < n && s <= 2; j++){ const q = (i + j) % n; absT += Math.abs(turn[q]); net += turn[q]; s += len[q];
          if(absT >= 150 && Math.abs(net) <= 60){ spikes.push([hi ? "hole" + hi : "outline", P[i].map(v => Math.round(v * 10) / 10), Math.round(absT), Math.round(net)]); break; } }
        if(spikes.length > 6) break; }
    });
    /* symmetry */
    let sx = 0, sw = 0; for(let i = 0; i < N; i++){ if(cs[i] > 0){ sx += (i % W + .5) * cs[i]; sw += cs[i]; } }
    const mx = sx / sw; let mn = 0, mxx = 0;
    for(let y = 0; y < W; y++) for(let x = 0; x < W; x++){ const fx = 2 * mx - (x + .5) - .5; if(fx < 0 || fx > W - 1){ mxx += cs[y * W + x]; continue; }
      const x0 = fx | 0, t = fx - x0, v = cs[y * W + x0] * (1 - t) + (x0 + 1 < W ? cs[y * W + x0 + 1] : 0) * t, c = cs[y * W + x]; mn += Math.min(v, c); mxx += Math.max(v, c); }
    const sym = mn / mxx;
    out.push({ u, gaps: comps.sort((p, q) => q.n - p.n).slice(0, 6), gapN: comps.length, fringe: [Math.round(frMax * 100) / 100, frN, frAt], seams, spikes: spikes.slice(0, 6), sym: Math.round(sym * 1000) / 1000 });
  }
  return out;
}
