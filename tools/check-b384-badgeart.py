#!/usr/bin/env python3
"""Build 384.133 badgeart: Fire Code's pins, the art Madison named and the audit after it.

Madison, of the tyre stack: "The lines on the tires are messed up and come off the tires." Of the tent: "Why is the black tent opening
look like it's underneath it?" Of the corrosive jug: "The leak is coming out of the lid, the green leak." And then: "do a check on all of
them, to ensure they are perfect, ensure all edges and pieces are good to go."

  (1) EVERY GROOVE STAYS ON ITS PART, on all 58 pins: a cut line (a groove, `cut` with `paint: 0`) is cut into the part it lies on, so
      along at least 80% of its length (on the face) the part on top at that point is the SAME part - it does not run on under a part
      laid over it (a tyre's sidewall, a barrel's hoop, a yarn's over-wrap, a door) or across from one part onto the next. Round 9's
      tyre tread ran up into the top tyre's sidewall; the grain bin's corrugations ran across its door; the cask's staves through its
      hoops; the pallet's planks under its cartons. Measured on the parts' own paths at 3 px a unit.
  (2) THE TENT'S DOOR IS IN ITS WALL (Chapter 31): its darkest part (the door) stops at least 2 units above the foot of the silhouette
      under it, so the side wall below it is the tent's colour, not the door's (it ran to the foot: the wall under it was black too).
  (3) THE JUG'S LEAK IS NOT THE CAP (Chapter 54): every part in the greenest colour (the acid) is at least 3 units from the reddest
      part (the cap); round 9's drop hung from under the cap.
  (4) no page errors.

(384.133 art3, Madison's next round, each leg FAILS on fa11d79, the build before it, and reads its numbers off the drawing):
  (5) THE TYRES LOOK LIKE TYRES (Chapter 34: "this just doesn't look legit"): (a) the tread's cross grooves are laid ROUND each tyre -
      in every row the gap between neighbouring grooves at the sides is under 0.85 of the gap at the middle (the old slashes were evenly
      spaced, a flat strip: 1.0; grooves 15 degrees apart round a tyre seen to 60 degrees each side give about 0.78); (b) each tyre sits on the next: down the stack's middle the face shows a dark band (a contact shadow, under
      0.6 of the median light down that line) at each of the two joins; (c) the top tyre's hole is seen in perspective: inside the hole (the
      darkest plate in the stack's top quarter) a lighter plate (the far inside wall) lies over its upper part.
  (6) THE HARD HAT'S MARK IS CENTRED (Chapter 33: "the randomly placed star is not it"): every bright mark on the navy shell (a fill
      plate far lighter than the shell) is centred on the shell, within 2.5 units, at its own height (the star sat 12 to the front).
  (7) THE PENCIL IS ONE STRAIGHT PENCIL (Appendix H, his circle at the cone): the graphite (the last plate) and the sharpened wood (the
      plate before it) share their joining edge (both ends within .15 units) and their sides run on one line (within 1 degree) - the
      graphite was wider than the cone where it met it, on a different taper.
  (8) THE RACK IS SEEN IN 3/4 (Chapter 32: "hard to tell what that even is"): at least 4 painted parts (straight-sided pieces of 40+
      square units, so no snap sliver or rounded corner counts) carry a slanted edge (20-70 degrees, 5+ units long) - the loads' tops and the end frame going back into
      the rack - and the outline has one 8+ units long (the end frame's foot); straight on, every part and the outline were square.
  (9) THE OXYGEN CYLINDER HAS A NECK (Chapter 63: "a nice connection from that top piece to the actual tank"): the white shoulder runs
      up into a neck - 2 units below its top it is at most 16 units wide (it was the dome's cap, 23 wide, with the valve set on it).
 (10) THE LPG COLLAR'S FOOT MEETS THE TANK (Chapter 61: "Blue tank has the same issue"): the steel band at the collar's foot (the wide
      steel plate at the top) runs out to the tank's outline at both ends - each end within 0.8 units of the outline (its square ends
      stopped inside the dome, with blue between them and the edge).
  python3 tools/check-b384-badgeart.py [--against OLD/index.html]   (FAILS on 458b3c9, the build before)
Playwright + /opt/pw-browsers Chromium; Firebase is blocked here, which changes nothing measured."""
import sys, os, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("rcb", os.path.join(HERE, "render-chapter-badges.py"))
_sv = sys.argv[:]; sys.argv = [_sv[0]]; R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R); sys.argv = _sv
from playwright.sync_api import sync_playwright
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(os.path.join(os.path.dirname(HERE), "index.html"), encoding="utf-8").read()
fails = []
def chk(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "   -> %s" % (detail,)), flush=True)
    if not ok: fails.append(name)
PROBE = r"""() => {
  const N = 300, SC = N / 100;
  const cv = document.createElement('canvas'); cv.width = cv.height = N; const c = cv.getContext('2d', { willReadFrequently: true });
  const mask = fn => { c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, N, N); c.setTransform(SC, 0, 0, SC, 0, 0); c.fillStyle = c.strokeStyle = '#000'; fn(c);
    const d = c.getImageData(0, 0, N, N).data, m = new Uint8Array(N * N); for(let i = 0; i < N * N; i++) m[i] = d[i * 4 + 3] > 127 ? 1 : 0; return m; };
  const hex = h => [1, 3, 5].map(k => parseInt(h.slice(k, k + 2), 16));
  const res = { grooves: [], door: null, leak: null, n: 0 };
  for(const u of Object.keys(CHAPTER_OBJ)){
    const e = CHAPTER_OBJ[u], pl = e.plates || [], pal = chapterObjPalette(u, false); res.n++;
    const face = mask(c => { const p = new Path2D(e.d); (e.holes || []).forEach(h => p.addPath(new Path2D(h))); c.fill(p, 'evenodd'); });
    const fills = pl.map((q, k) => { const o = q[2] || {}; if(o.ln || o.paint === 0) return null;
      return { k, m: mask(c => c.fill(new Path2D(q[1]))), rgb: hex((o.col && /^#[0-9a-f]{6}$/i.test(o.col)) ? o.col : (pal[q[0]] || pal.field)) }; });
    /* (1) */
    pl.forEach((q, k) => { const o = q[2] || {}; if(!(o.cut && o.paint === 0 && o.ln)) return;
      q[1].split(/(?=M)/).forEach(sp => { const m = mask(c => { c.lineWidth = .3; c.lineCap = 'butt'; c.stroke(new Path2D(sp)); });
        let host, n = 0, off = 0;
        for(let i = 0; i < N * N; i++){ if(!m[i] || !face[i]) continue; n++;
          let top = null; for(let j = fills.length - 1; j >= 0; j--){ const f = fills[j]; if(f && f.m[i]){ top = f; break; } }
          if(host === undefined) host = top; if(top !== host) off++; }
        if(n && off / n > .2) res.grooves.push([u.slice(0, 26), k, sp.slice(0, 34), +(off / n).toFixed(2)]); }); });
    const lum = f => .2126 * f.rgb[0] + .7152 * f.rgb[1] + .0722 * f.rgb[2];
    const box = m => { let x0 = N, x1 = -1, y1 = -1; for(let y = 0; y < N; y++) for(let x = 0; x < N; x++) if(m[y * N + x]){ if(x < x0) x0 = x; if(x > x1) x1 = x; if(y > y1) y1 = y; } return [x0, x1, y1]; };
    /* (2) */
    if(u.startsWith('Chapter 31:')){
      const dark = fills.filter(Boolean).reduce((a, f) => (!a || lum(f) < lum(a)) ? f : a, null), [x0, x1, y1] = box(dark.m);
      let foot = -1; for(let x = x0; x <= x1; x++) for(let y = N - 1; y >= 0; y--) if(face[y * N + x]){ foot = Math.max(foot, y); break; }
      res.door = { gap: +((foot - y1) / SC).toFixed(2), plate: dark.k };
    }
    /* (3) */
    if(u.startsWith('Chapter 54:')){
      const F = fills.filter(Boolean), g = f => f.rgb[1] - (f.rgb[0] + f.rgb[2]) / 2, r = f => f.rgb[0] - (f.rgb[1] + f.rgb[2]) / 2;
      const gmax = Math.max(...F.map(g)), acid = F.filter(f => g(f) >= gmax - 1), cap = F.reduce((a, f) => (!a || r(f) > r(a)) ? f : a, null);
      let best = 1e9; const cp = []; for(let i = 0; i < N * N; i++) if(cap.m[i]) cp.push(i);
      acid.forEach(a => { for(let i = 0; i < N * N; i++) if(a.m[i]){ const x = i % N, y = (i / N) | 0; for(const j of cp){ const d = Math.hypot(x - j % N, y - ((j / N) | 0)); if(d < best) best = d; } } });
      res.leak = { dist: +(best / SC).toFixed(2), acid: acid.map(a => a.k), cap: cap.k };
    }
  }
  return res;
}"""
PROBE2 = r"""() => {
  const N = 400, SC = N / 100, out = {};
  const cv = document.createElement('canvas'); cv.width = cv.height = N; const c = cv.getContext('2d', { willReadFrequently: true });
  const mask = fn => { c.setTransform(1, 0, 0, 1, 0, 0); c.clearRect(0, 0, N, N); c.setTransform(SC, 0, 0, SC, 0, 0); c.fillStyle = c.strokeStyle = '#000'; fn(c);
    const d = c.getImageData(0, 0, N, N).data, m = new Uint8Array(N * N); for(let i = 0; i < N * N; i++) m[i] = d[i * 4 + 3] > 127 ? 1 : 0; return m; };
  const hex = h => [1, 3, 5].map(k => parseInt(h.slice(k, k + 2), 16));
  const lum = rgb => .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2];
  const find = pre => Object.keys(CHAPTER_OBJ).find(u => u.indexOf(pre) === 0);
  const fillsOf = u => { const e = CHAPTER_OBJ[u], pal = chapterObjPalette(u, false);
    return (e.plates || []).map((q, k) => { const o = q[2] || {}; if(o.ln || o.paint === 0) return null;
      return { k, d: q[1], m: mask(c => c.fill(new Path2D(q[1]))), rgb: hex((o.col && /^#[0-9a-f]{6}$/i.test(o.col)) ? o.col : (pal[q[0]] || pal.field)) }; }); };
  const faceOf = u => { const e = CHAPTER_OBJ[u]; return mask(c => { const p = new Path2D(e.d); (e.holes || []).forEach(h => p.addPath(new Path2D(h))); c.fill(p, 'evenodd'); }); };
  const topAt = (F, i) => { for(let j = F.length - 1; j >= 0; j--) if(F[j] && F[j].m[i]) return F[j]; return null; };
  const bbox = m => { let x0 = N, x1 = -1, y0 = N, y1 = -1; for(let y = 0; y < N; y++) for(let x = 0; x < N; x++) if(m[y * N + x]){ if(x < x0) x0 = x; if(x > x1) x1 = x; if(y < y0) y0 = y; if(y > y1) y1 = y; } return { x0, x1, y0, y1 }; };
  const subs = d => d.split(/(?=M)/).map(sp => (sp.match(/-?\d*\.?\d+/g) || []).map(Number)).map(a => { const p = []; for(let i = 0; i + 1 < a.length; i += 2) p.push([a[i], a[i + 1]]); return p; });
  /* (5) the tyres */
  { const u = find('Chapter 34:'), e = CHAPTER_OBJ[u], F = fillsOf(u), face = faceOf(u);
    let worst = 0, rows = 0;
    (e.plates || []).forEach(q => { const o = q[2] || {}; if(!o.ln) return;
      const segs = subs(q[1]).filter(p => p.length === 2 && Math.abs(p[1][1] - p[0][1]) > Math.abs(p[1][0] - p[0][0]));
      const byRow = {}; segs.forEach(p => { const k = Math.round((p[0][1] + p[1][1]) / 2 / 3); (byRow[k] = byRow[k] || []).push((p[0][0] + p[1][0]) / 2); });
      Object.values(byRow).forEach(xs => { if(xs.length < 5) return; xs.sort((a, b) => a - b); const g = xs.slice(1).map((x, i) => x - xs[i]);
        const mid = Math.max(...g), side = Math.min(g[0], g[g.length - 1]); rows++; worst = Math.max(worst, side / mid); }); });
    const bb = bbox(face), cx = Math.round((bb.x0 + bb.x1) / 2);
    const col = []; for(let y = bb.y0; y <= bb.y1; y++){ const i = y * N + cx; col.push(face[i] ? topAt(F, i) : null); }
    const ls = col.filter(Boolean).map(f => lum(f.rgb)).sort((p, q) => p - q), tyreL = ls[ls.length >> 1];
    let darkRuns = 0, inRun = false; const y3 = Math.floor(col.length * .3);
    col.forEach((f, j) => { const dk = j > y3 && f && lum(f.rgb) < .6 * tyreL && j < col.length - 6; if(dk && !inRun) darkRuns++; inRun = dk; });
    const upper = F.filter(f => { if(!f) return false; const b = bbox(f.m); return b.x1 >= 0 && (b.y0 + b.y1) / 2 < bb.y0 + (bb.y1 - bb.y0) * .25; });
    const hole = upper.reduce((a, f) => (!a || lum(f.rgb) < lum(a.rgb)) ? f : a, null), hb = bbox(hole.m);
    const wall = F.filter(f => f && f.k > hole.k && lum(f.rgb) > lum(hole.rgb) + 8).find(f => { let n = 0, up = 0; for(let i = 0; i < N * N; i++) if(f.m[i] && hole.m[i]){ n++; if(((i / N) | 0) < (hb.y0 + hb.y1) / 2) up++; } return n > 20 && up / n > .6; });
    out.tyres = { rows, ratio: +worst.toFixed(2), darkRuns, wall: !!wall };
  }
  /* (6) the hard hat */
  { const u = find('Chapter 33:'), F = fillsOf(u).filter(Boolean), face = faceOf(u);
    const shell = F.reduce((a, f) => { const n = f.m.reduce((s, v) => s + v, 0); return (!a || n > a.n) ? Object.assign(f, { n }) : a; }, null);
    const marks = F.filter(f => lum(f.rgb) > lum(shell.rgb) + 60);
    out.hat = marks.map(f => { const b = bbox(f.m), ym = Math.round((b.y0 + b.y1) / 2); let x0 = N, x1 = -1;
      for(let x = 0; x < N; x++) if(shell.m[ym * N + x]){ if(x < x0) x0 = x; if(x > x1) x1 = x; }
      return +(Math.abs((b.x0 + b.x1) / 2 - (x0 + x1) / 2) / SC).toFixed(2); });
  }
  /* (7) the pencil */
  { const u = find('Appendix H'), pl = CHAPTER_OBJ[u].plates, byCol = c => pl.filter(q => (q[2] || {}).col === c);
    /* (384.136 art6 round 4, changed on purpose: the pencil is three faces now, its wood in three tones) the graphite is its own plate,
       the wood the two outer tones, whose outer edges run to the point */
    const g = subs(byCol('#3A3D42')[0][1])[0], wl = subs(byCol('#E6C08E')[0][1])[0], wr = subs(byCol('#B5844F')[0][1])[0], w = [wl[0], wl[1], wr[2], wr[3]];   /* the outer edges (the cone's own sides) */
    /* (384.136 art7, changed on purpose: the lead is longer and its point rounded) each side: the wood's outer edge (its far corner to the
       corner it shares with the lead) and the lead's outer edge (that corner to the lead's last point on the same side) run on one line */
    const near = (p, P) => Math.min(...P.map(q => Math.hypot(p[0] - q[0], p[1] - q[1])));
    const uniq = P => P.filter((p, k) => P.findIndex(q => Math.hypot(q[0] - p[0], q[1] - p[1]) < .01) === k);
    const G = uniq(g), Wd = uniq(w), cx = (Math.min(...G.map(p => p[0])) + Math.max(...G.map(p => p[0]))) / 2;
    const gs = G.slice().sort((a, b) => near(a, Wd) - near(b, Wd)).slice(0, 2), shared = Math.max(...gs.map(p => near(p, Wd)));
    const ang = (a, b) => Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI;
    let worst = 0; gs.forEach(p => { const side = Math.sign(p[0] - cx);
      const far = Wd.filter(q => Math.sign(q[0] - cx) === side && Math.hypot(q[0] - p[0], q[1] - p[1]) > 3).sort((a, b) => Math.hypot(a[0] - p[0], a[1] - p[1]) - Math.hypot(b[0] - p[0], b[1] - p[1]))[0];
      const tip = G.filter(q => Math.sign(q[0] - cx) === side && Math.hypot(q[0] - p[0], q[1] - p[1]) > 3).sort((a, b) => Math.hypot(b[0] - p[0], b[1] - p[1]) - Math.hypot(a[0] - p[0], a[1] - p[1]))[0];
      if(far && tip){ let d = Math.abs(ang(far, p) - ang(p, tip)); if(d > 180) d = 360 - d; worst = Math.max(worst, d); } });
    out.pencil = { shared: +shared.toFixed(2), angle: +worst.toFixed(2) };
  }
  /* (8) the rack: a part's own subpaths of 40+ square units (the snaps' slivers are thinner), and the outline */
  const area = p => { let A = 0; for(let i = 0; i < p.length; i++){ const a = p[i], b = p[(i + 1) % p.length]; A += a[0] * b[1] - b[0] * a[1]; } return A / 2; };
  const slant = (p, min) => { for(let i = 0; i < p.length; i++){ const a = p[i], b = p[(i + 1) % p.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
    const t = Math.abs(Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI) % 90; if(L >= min && t >= 20 && t <= 70) return true; } return false; };
  { const u = find('Chapter 32:'); let n = 0;
    (CHAPTER_OBJ[u].plates || []).forEach(q => { const o = q[2] || {}; if(o.ln || o.paint === 0) return;
      q[1].split(/(?=M)/).filter(sp => !/[^MLZ0-9.\s,-]/i.test(sp)).map(sp => subs(sp)[0]).forEach(p => { if(p && Math.abs(area(p)) >= 40 && slant(p, 5)) n++; }); });
    out.rack = { parts: n, outline: slant(subs(CHAPTER_OBJ[u].d)[0], 8) };
  }
  /* (9) the oxygen cylinder */
  { const u = find('Chapter 63:'), F = fillsOf(u).filter(Boolean);
    const white = F.filter(f => Math.min(...f.rgb) > 215).reduce((a, f) => { const n = f.m.reduce((s, v) => s + v, 0); return (!a || n > a.n) ? Object.assign(f, { n }) : a; }, null);
    const b = bbox(white.m), y = b.y0 + 2 * SC; let x0 = N, x1 = -1; for(let x = 0; x < N; x++) if(white.m[y * N + x]){ if(x < x0) x0 = x; if(x > x1) x1 = x; }
    out.neck = +((x1 - x0 + 1) / SC).toFixed(2);
  }
  /* (10) the LPG collar's foot */
  { const u = find('Chapter 61:'), e = CHAPTER_OBJ[u], pal = chapterObjPalette(u, false), face = faceOf(u);
    const steel = (e.plates || []).map(q => { const o = q[2] || {}; if(q[0] !== 'steel' || o.ln || o.paint === 0) return null; const m = mask(c => c.fill(new Path2D(q[1]))); return { m, b: bbox(m) }; })
      .filter(f => f && f.b.y1 < N * .5 && (f.b.x1 - f.b.x0) > N * .3);   /* (384.136 art6, changed on purpose: the foot is the collar's own plate now - Madison: the band read as a separate piece - so the steel part measured is the collar, whose widest columns are its foot's ends) */
    const dOut = (x, y) => { let best = 1e9; for(let yy = Math.max(0, y - 40); yy < Math.min(N, y + 40); yy++) for(let xx = Math.max(0, x - 40); xx < Math.min(N, x + 40); xx++) if(!face[yy * N + xx]){ const d = Math.hypot(xx - x, yy - y); if(d < best) best = d; } return best / SC; };
    out.collar = steel.map(f => { const ends = []; [f.b.x0, f.b.x1].forEach(x => { let ys = []; for(let y = 0; y < N; y++) if(f.m[y * N + x]) ys.push(y); ends.push(+dOut(x, ys[ys.length >> 1]).toFixed(2)); }); return ends; });
  }
  return out;
}"""
srv, port = R.serve()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    ctx, pg, errs = R.open_page(br, port, R.SEED, 440, 956, 1, "ifc", BODY)
    r = pg.evaluate(PROBE)
    # (384.136) RE-PINNED: the pins are Fire Code's 58 and, since Madison asked for the academy's badges to be pins "just as great", the
    # academy's 24 (tools/chapter-objects/academy-units.json); every groove on all of them is held to the same rule
    NPINS = 58 + len(__import__("json").load(open(os.path.join(HERE, "chapter-objects", "academy-units.json"), encoding="utf-8")))
    chk("(1) every groove on the %d pins stays on the part it is cut into (80%% of its length): %d run off" % (r["n"], len(r["grooves"])), r["n"] == NPINS and not r["grooves"], r["grooves"][:8])
    chk("(2) the tent's door stops at least 2 units above the silhouette's foot under it (gap %s)" % (r["door"] and r["door"]["gap"]), bool(r["door"]) and r["door"]["gap"] >= 2, r["door"])
    chk("(3) the corrosive jug's acid is at least 3 units from its cap (%s)" % (r["leak"] and r["leak"]["dist"]), bool(r["leak"]) and r["leak"]["dist"] >= 3, r["leak"])
    q = pg.evaluate(PROBE2); print("     art3:", q, flush=True)
    t = q["tyres"]
    chk("(5a) Chapter 34: the tread's cross grooves close up toward each tyre's sides (side gap / middle gap %s over %d rows, under 0.85)" % (t["ratio"], t["rows"]), t["rows"] >= 3 and t["ratio"] < .85, t)
    chk("(5b) Chapter 34: a contact shadow at each of the two joins down the stack's middle (%d dark bands)" % t["darkRuns"], t["darkRuns"] >= 2, t)
    chk("(5c) Chapter 34: the top tyre's hole shows its far inside wall over its upper part", t["wall"], t)
    chk("(6) Chapter 33: every bright mark on the shell is centred on it, within 2.5 units (%s off)" % q["hat"], bool(q["hat"]) and max(q["hat"]) <= 2.5, q["hat"])
    chk("(7) Appendix H: the graphite and the wood share their edge (%s apart) and run on one taper (%s degrees)" % (q["pencil"]["shared"], q["pencil"]["angle"]), q["pencil"]["shared"] <= .15 and q["pencil"]["angle"] <= 1, q["pencil"])
    chk("(8) Chapter 32: at least 4 parts carry a slanted edge going back into the rack (%d), and so does the outline (%s)" % (q["rack"]["parts"], q["rack"]["outline"]), q["rack"]["parts"] >= 4 and q["rack"]["outline"], q["rack"])
    # (384.136 art6 round 4, changed on purpose: Madison, "the silver part, it doesn't wrap around, not sure why the sides are white") no
    # neck stands beside the collar any more: the collar sits on the shoulder, so the white's first rows are the shoulder's, wider than it
    chk("(9) Chapter 63: the white starts at the shoulder under the collar, no neck beside it (%s units wide 2 below its top)" % q["neck"], q["neck"] >= 17, q["neck"])
    # (384.136 art4, changed on purpose: Madison circled both ends of the foot band where it ran out into the outline - a notch and a stray
    # line at each side) the band now ends rounded a little inside the dome's outline, clear of it at both ends
    chk("(10) Chapter 61: the collar's foot band ends inside the tank's outline at both ends, clear of it by 1 to 4 units (%s)" % q["collar"], bool(q["collar"]) and all(1 <= min(c) and max(c) <= 4 for c in q["collar"]), q["collar"])
    real = [e for e in errs if "firebase" not in e.lower() and "gstatic" not in e.lower()]
    chk("(4) no page errors", not real, real[:3])
    br.close()
print("ALL PASS" if not fails else "FAILURES: %d" % len(fails))
sys.exit(1 if fails else 0)
