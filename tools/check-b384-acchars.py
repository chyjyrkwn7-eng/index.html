#!/usr/bin/env python3
"""check-b384-acchars.py - the academy's characters, touched up (384 r6).

Madison: "I think the characters (every single one of them) could be touched up ... ensure none of them have weird
disconnections or just out of place things". What was found, going through every academy character at 3x:

  (N) the six crowned rulers (Forge, Lunar, Solar, Frost, Oracle, Tempest) had a head ending in a point at y 27.6 and
      shoulders starting at 28.8 with only dark robe between: a head resting on a ledge. Each has a neck now, in its body
      group, a skin-coloured shape that runs from under the chin into the collar.
  (G) the Ghost's folds were two round-capped strokes 2.6 wide from shoulder to hem (grey pillars), its arms pointed flaps.
  (M) the Marksman's camo paint was three bands across the whole face, one through the open eye.
  (H) the Hive stood on the shoulders with no sill under the dome.
  (R) the Ronin's two neon streaks were bare lines that ended in mid-air; they fade along their length now.
  (T) the Tempest's wind-blown hair was one ragged outline that ran into the bolt beside it.
  (A) every academy character still draws, with no page error (the frame is check-behaviour's b314 section).

Read off the drawing's own geometry (getBBox), not off label strings. Every check was written against bb7eb94 and fails
there; `--against old-index.html` runs it on another build.

    python3 tools/check-b384-acchars.py [--against old-index.html]
"""
import json
import socket
import sys
import threading
import http.server
import functools

from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ROOT = __file__.rsplit("/tools/", 1)[0]
AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None

SEED = {"onboardingComplete": True, "firstName": "Test", "avatarChar": "ninja", "tourRev": 99, "rankMapFx244": True,
        "classes": ["academy"], "publicId": "tstacchars001",
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "gamePlays": 8,
                     "perfectTests": 64, "longestStreak": 44, "currentStreak": 12}}
FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "   -> " + str(detail)[:400]))
    if not ok:
        FAILS.append(name)


def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, port


# Every measurement is made on a live drawing mounted in the page (getBBox needs layout).
PROBE = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const out = {};
  const host = document.createElement('div');
  host.style.cssText = 'position:fixed;left:0;top:0;width:400px;height:400px;z-index:99999';
  document.body.appendChild(host);
  const mount = id => { host.replaceChildren(); const s = drawAvatarCharSVG(id); host.appendChild(s); return s; };
  const box = n => { try{ const b = n.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, b: b.y + b.height }; }catch(e){ return null; } };

  /* (N) a neck in the body group of each crowned ruler */
  out.neck = {};
  ['forge','lunar','solar','frost','oracle','tempest'].forEach(id => {
    const s = mount(id);
    const body = s.querySelector('.cx-body');
    const hit = [...body.querySelectorAll('path')].filter(p => { const b = box(p); return b && b.y <= 25.2 && b.b >= 29.8 && b.w >= 4.5 && b.w <= 10 && b.x >= 14 && b.r <= 26; });
    out.neck[id] = hit.length;
  });

  /* (G) the ghost: no round-capped stroke wider than 2 units in the sheet, and no arm that is a thin pointed flap */
  { const s = mount('ghost'); const head = s.querySelector('.cx-head');
    out.ghostFatStrokes = [...head.querySelectorAll('path')].filter(p => p.getAttribute('stroke-linecap') === 'round' && +p.getAttribute('stroke-width') >= 2).length;
    /* the arms are the two side shapes outside the sheet's edges (x < 7 or x > 33): each at least 1.8 across and 3 tall */
    const arms = [...head.querySelectorAll('path')].map(box).filter(b => b && (b.x < 6.6 || b.r > 33.4) && b.w < 4);
    out.ghostArms = arms.map(b => [+b.w.toFixed(2), +b.h.toFixed(2)]); }

  /* (M) the marksman: no paint stroke across the whole face (face is x 14.4..25.6, 11.2 wide) */
  { const s = mount('marksman');
    const clipped = [...s.querySelectorAll('g[clip-path]')].filter(g => g.querySelectorAll('path').length >= 3 && g.querySelector('rect'));
    const g = clipped[0];
    out.marksmanPaint = g ? [...g.querySelectorAll('path')].filter(p => p.getAttribute('fill') !== 'none').map(p => { const b = box(p); return b ? +b.w.toFixed(1) : 0; }) : null; }

  /* (H) the hive: something under the dome that is wider than the dome */
  { const s = mount('hive'); const head = s.querySelector('.cx-head');
    const ps = [...head.querySelectorAll(':scope > path')].map(box).filter(Boolean);
    const dome = ps.reduce((a, b) => (b.w * b.h > a.w * a.h ? b : a), ps[0]);
    out.hive = { domeW: +dome.w.toFixed(2), wider: ps.filter(b => b.w > dome.w + .6 && b.y > 26).length }; }

  /* (R) the ronin's neon streaks fade along their length: their stroke is a gradient, not a flat colour */
  { const s = mount('ronin'); const g = s.querySelector('.cx-fx-roninneon');
    out.ronin = [...g.querySelectorAll('path')].map(p => (p.getAttribute('stroke') || '').indexOf('url(') === 0); }

  /* (T) the tempest's wind-blown side is smooth: the hair paths on the right of the face have no sharp reversal. A reversal
     is a path whose points run out and back in more than twice in x (a ragged edge); smooth locks do it once. */
  { const s = mount('tempest'); const head = s.querySelector('.cx-head');
    const hair = [...head.querySelectorAll(':scope > path')].filter(p => { const b = box(p); return b && b.x > 24 && b.r > 29; });
    const turns = p => { const n = p.getTotalLength(); let last = null, dir = 0, t = 0;
      for(let i = 0; i <= 60; i++){ const pt = p.getPointAtLength(n * i / 60); if(last){ const d = Math.sign(+(pt.x - last).toFixed(2)); if(d && dir && d !== dir) t++; if(d) dir = d; } last = pt.x; }
      return t; };
    out.tempestHair = hair.map(turns); }

  /* (A) every academy character draws (the frame is check-behaviour's b314 section, which this build passes) */
  out.all = {};
  AVATAR_CHARACTERS.filter(c => !c.retired).forEach(c => {
    try{ const s = mount(c.id); const b = box(s.querySelector('.cx-fig') || s);
      out.all[c.id] = b ? 'ok' : 'empty'; }catch(e){ out.all[c.id] = 'ERR ' + e.message; } });
  return out;
}"""


def main():
    srv, port = serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=CHROME)
        ctx = br.new_context(viewport={"width": 900, "height": 900}, device_scale_factor=1)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        if AGAINST:
            body = open(AGAINST, encoding="utf-8").read()
            pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
        pg.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');"
                           "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.drill.v1',%s);}catch(e){}"
                           % json.dumps(json.dumps(SEED)))
        pg.goto("http://127.0.0.1:%d/index.html" % port)
        pg.wait_for_timeout(3000)
        r = pg.evaluate(PROBE)
        print("\n384 r6: the academy's characters")
        check("(N) each crowned ruler has a neck in its body group (Forge, Lunar, Solar, Frost, Oracle, Tempest)",
              all(v >= 1 for v in r["neck"].values()), r["neck"])
        check("(G) the Ghost has no round-capped stroke 2 wide or more in its sheet", r["ghostFatStrokes"] == 0, r["ghostFatStrokes"])
        check("(G) the Ghost has two arms, each 4 units tall or more (stubs hanging at the sides, not 3-unit pointed flaps)",
              len(r["ghostArms"]) == 2 and all(h >= 4 for w, h in r["ghostArms"]), r["ghostArms"])
        mp = r["marksmanPaint"]
        check("(M) no camo stroke on the Marksman's face runs across it (all under 8 units, face is 11 wide)",
              mp is not None and len(mp) >= 3 and max(mp) < 8, mp)
        check("(H) the Hive has a sill under its dome that is wider than the dome", r["hive"]["wider"] >= 1, r["hive"])
        check("(R) the Ronin's neon streaks fade along their length (gradient strokes)", r["ronin"] and all(r["ronin"][:2]), r["ronin"])
        check("(T) the Tempest's wind-blown hair on the right has no ragged edge (each piece turns in x at most twice)",
              r["tempestHair"] and max(r["tempestHair"]) <= 2, r["tempestHair"])
        bad = {k: v for k, v in r["all"].items() if v != "ok"}
        check("(A) every academy character draws", not bad and len(r["all"]) >= 25, bad or len(r["all"]))
        check("no page errors", not errs, errs[:3])
        ctx.close(); br.close()
    srv.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
