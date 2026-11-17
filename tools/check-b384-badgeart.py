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
srv, port = R.serve()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=R.CHROME, args=["--disable-dev-shm-usage"])
    ctx, pg, errs = R.open_page(br, port, R.SEED, 440, 956, 1, "ifc", BODY)
    r = pg.evaluate(PROBE)
    chk("(1) every groove on the %d pins stays on the part it is cut into (80%% of its length): %d run off" % (r["n"], len(r["grooves"])), r["n"] == 58 and not r["grooves"], r["grooves"][:8])
    chk("(2) the tent's door stops at least 2 units above the silhouette's foot under it (gap %s)" % (r["door"] and r["door"]["gap"]), bool(r["door"]) and r["door"]["gap"] >= 2, r["door"])
    chk("(3) the corrosive jug's acid is at least 3 units from its cap (%s)" % (r["leak"] and r["leak"]["dist"]), bool(r["leak"]) and r["leak"]["dist"] >= 3, r["leak"])
    real = [e for e in errs if "firebase" not in e.lower() and "gstatic" not in e.lower()]
    chk("(4) no page errors", not real, real[:3])
    br.close()
print("ALL PASS" if not fails else "FAILURES: %d" % len(fails))
sys.exit(1 if fails else 0)
