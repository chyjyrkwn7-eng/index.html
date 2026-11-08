#!/usr/bin/env python3
"""check-b384-r2-connect.py - the base-art characters, every join checked (384 r2 connection audit).

Madison: "go through each character thoroughly to ensure all pieces connect right (another example, gold ranks crown sharp
parts aren't lined up) ... make them all right." Every character drawn by drawAvatarCharSVG was rendered at 4x and looked at.
What this holds, read off each drawing's own geometry (getBBox / getPointAtLength / point-in-fill), never off labels:

  (1) SOLAR  the crown's five spikes point away from the corona's own centre (20, 15.4) on the 22.5-degree lattice, are mirrored
             about x = 20 (tips at equal heights), and no corona ray stands behind them (11 rays remain, not 16).
  (2) LUNAR, TEMPEST, FROST, ORACLE  each side lock starts under the cap of hair (its first point is above y 12.5) and the two are
             mirrors, so no pointed start and no gap of background shows between cap, lock and face.
  (3) FORGE  the five crown ridges are mirrored about x = 20.
  (4) INFERNO  the mane ends inside the face: its lowest point is above y 25.5 (it was a flat cut at y 27).
  (5) CLOWN  each side point of the hat overlaps the brim by a unit or more in x (it hung free).
  (6) GHOST  the hem is the same at both ends (its lowest edge mirrored about x = 20) and the fold shading is clipped to the sheet.
  (7) DETECTIVE  the hat band is clipped to the crown and the crown's foot is as wide as the head's (wedge of skin).
  (8) VOID  where the hood's rim ends and the shoulder's rim starts, on the screen, is under 0.15 unit.
  (9) MASKED  the red lining on the tall top points is on both of them.
 (10) ORION  the upper-left rim light lies within 0.9 of the hood's own outline.
 (11) GENESIS  the collar's lit rim stays outside the planet (no ticks poking out beside it).
 (12) ZEUS  the hair's side tips come down to the ears (y 16 or more).
 (13) UMBRA  the inner rim ends in a round cap.
 (14) every character in AVATAR_CHARACTERS (not retired) still draws.

    python3 tools/check-b384-r2-connect.py [--against old-index.html]
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

SEED = {"onboardingComplete": True, "firstName": "Test", "avatarChar": "ghost", "tourRev": 99, "rankMapFx244": True,
        "classes": ["academy"], "publicId": "tstr2connect01",
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "gamePlays": 8,
                     "perfectTests": 64, "longestStreak": 44, "currentStreak": 12}}
FAILS = []


def check(name, ok, detail=""):
    print("  %s  %s%s" % ("PASS" if ok else "FAIL", name, "" if ok else "   -> " + str(detail)[:500]))
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


PROBE = r"""() => {
  document.getElementById('splashscreen')?.remove();
  const out = {};
  const host = document.createElement('div');
  host.style.cssText = 'position:fixed;left:0;top:0;width:400px;height:400px;z-index:99999';
  document.body.appendChild(host);
  const mount = (id, built) => { host.replaceChildren(); const s = (built ? buildAvatarCharSVG : drawAvatarCharSVG)(id); host.appendChild(s); return s; };
  const box = n => { try{ const b = n.getBBox(); return { x: b.x, y: b.y, w: b.width, h: b.height, r: b.x + b.width, b: b.y + b.height }; }catch(e){ return null; } };
  const paths = (root, sel) => [...root.querySelectorAll(sel || 'path')];
  const pts = (p, n) => { const L = p.getTotalLength(), a = []; for(let i = 0; i <= n; i++){ const q = p.getPointAtLength(L * i / n); a.push([q.x, q.y]); } return a; };
  const first = p => { const q = p.getPointAtLength(0); return [q.x, q.y]; };

  /* (1) solar: the crown group's five spikes */
  { const s = mount('solar'); const crown = s.querySelector('.cx-fx-crown');
    const sp = paths(crown).slice(0, 5);
    /* each spike is M base1 L tip L base2 Z: the tip is the second vertex */
    const tips = sp.map(p => { const n = (p.getAttribute('d').match(/-?\d+(\.\d+)?/g) || []).map(Number); return [n[2], n[3]]; });
    out.solarAngles = tips.map(t => +(Math.atan2(t[0] - 20, 15.4 - t[1]) * 180 / Math.PI).toFixed(2)).sort((a, b) => a - b);
    out.solarTipsY = tips.map(t => +t[1].toFixed(2));
    out.solarTipsX = tips.map(t => +t[0].toFixed(2));
    const corona = s.querySelector('.cx-fx-corona'); out.solarRays = corona ? paths(corona).length : 0; }

  /* (2) the four side-lock characters: the first path of the head group is the pair of locks (two subpaths) */
  out.locks = {};
  ['lunar', 'tempest', 'frost', 'oracle'].forEach(id => {
    const s = mount(id); const head = s.querySelector('.cx-head');
    /* the locks are one path with two subpaths, or (Tempest) two paths: collect every start point of the head group's first two
       paths */
    const starts = [];
    [...head.querySelectorAll(':scope > path')].slice(0, 2).forEach(p => p.getAttribute('d').split('M').filter(Boolean).forEach(t => starts.push(t.trim().split(/[\s,]+/).slice(0, 2).map(Number))));
    out.locks[id] = starts.slice(0, 2); });

  /* (3) forge: five ridge strokes (the M..L pairs of one path), mirrored */
  { const s = mount('forge'); const crown = s.querySelector('.cx-fx-crown');
    const ridge = paths(crown).find(p => p.getAttribute('stroke') === '#FFE9CC' && (p.getAttribute('d') || '').split('M').length > 3);
    const segs = ridge.getAttribute('d').split('M').filter(Boolean).map(t => t.trim().replace(/L/, ' ').split(/\s+/).map(Number));
    out.forgeRidges = segs; }

  /* (4) inferno: the mane (first path in cx-fx-flame) */
  { const s = mount('inferno'); const m = s.querySelector('.cx-fx-flame path'); const b = box(m); out.infernoManeBottom = +b.b.toFixed(2); }

  /* (5) clown: the first two paths of the hat group are the side points; the brim is the one with a violet stroke */
  { const s = mount('clown'); const hat = s.querySelector('.cx-fx-cl2hat'); const ps = paths(hat);
    const brim = ps.find(p => p.getAttribute('stroke') === '#9B5CFF'); const bb = box(brim);
    const ov = p => { const b = box(p); return +(Math.min(b.r, bb.r) - Math.max(b.x, bb.x)).toFixed(2); };
    out.clownOverlap = [ov(ps[0]), ov(ps[1])]; }

  /* (6) ghost: lowest filled y at x across the hem, mirrored; and a clip-path on the shading group */
  { const s = mount('ghost'); const head = s.querySelector('.cx-head');
    const sheet = paths(head).find(p => { const b = box(p); return b && b.w > 25 && b.h > 25; });
    const svgEl = s; const low = x => { let y = 34; const pt = svgEl.createSVGPoint(); for(; y > 26; y -= .05){ pt.x = x; pt.y = y; if(sheet.isPointInFill(pt)) return y; } return null; };
    const xs = []; for(let x = 8; x <= 20; x += .5) xs.push(x);
    out.ghostHem = xs.map(x => [x, +(low(x) || 0).toFixed(2), +(low(40 - x) || 0).toFixed(2)]);
    out.ghostClip = head.querySelectorAll('g[clip-path]').length; }

  /* (7) detective: crown path foot width and a clipped band */
  { const s = mount('detective'); const hat = s.querySelector('.cx-fx-hat');
    const crown = paths(hat)[0]; const b = box(crown);
    out.detectiveCrownW = +b.w.toFixed(2); out.detectiveBandClipped = hat.querySelectorAll('g[clip-path]').length; }

  /* (8) void: on the screen, the end of the hood's rim vs the start of the shoulder's rim */
  { const s = mount('voidwalker', true);
    const rims = paths(s).filter(p => p.getAttribute('stroke') === '#9FB8DC');
    const hood = rims.find(p => +p.getAttribute('opacity') === .7), body = rims.find(p => +p.getAttribute('opacity') === .6);
    const map = (p, t) => { const q = p.getPointAtLength(t === 0 ? 0 : p.getTotalLength()); const m = p.getScreenCTM(); return [m.a * q.x + m.c * q.y + m.e, m.b * q.x + m.d * q.y + m.f]; };
    const a = map(hood, 0), b2 = map(body, 0), scale = host.getBoundingClientRect().width / 34;
    out.voidGap = +(Math.hypot(a[0] - b2[0], a[1] - b2[1]) / scale).toFixed(3); }

  /* (9) masked: red hairlines on the mane (stroke red, opacity .55) */
  { const s = mount('masked'); const head = s.querySelector('.cx-head');
    out.maskedLining = paths(head, ':scope > path').filter(p => +p.getAttribute('opacity') === .55 && p.getAttribute('stroke-width') === '.35').length; }

  /* (10) orion: the rim at the upper left vs the hood outline (the largest hood-shaped fill) */
  { const s = mount('astronaut'); const head = s.querySelector('.cx-head');
    const rim = paths(head).find(p => p.getAttribute('stroke-width') === '.45' && +p.getAttribute('opacity') === .7);
    const hood = paths(head).find(p => { const b = box(p); return b && b.w > 17 && b.h > 22 && p.getAttribute('stroke') === '#03050C'; });
    const ring = pts(hood, 400); let worst = 0;
    pts(rim, 12).forEach(q => { const d = Math.min(...ring.map(r => Math.hypot(r[0] - q[0], r[1] - q[1]))); worst = Math.max(worst, d); });
    out.orionRim = +worst.toFixed(2); }

  /* (11) genesis: the collar rim path vs the planet circle (20, 19.4, r 7.6) */
  { const s = mount('genesis'); const head = s.querySelector('.cx-head');
    const rim = paths(s).find(p => p.getAttribute('stroke') === '#FF8FC0' && p.getAttribute('stroke-width') === '.4');
    let nearest = 99; pts(rim, 20).forEach(q => { nearest = Math.min(nearest, Math.hypot(q[0] - 20, q[1] - 19.4)); });
    out.genesisRimNearest = +nearest.toFixed(2); }

  /* (12) zeus: the hair's first point (its lowest tip) */
  { const s = mount('zeus'); const head = s.querySelector('.cx-head');
    const hair = paths(head).find(p => (p.getAttribute('d') || '').indexOf('Q11.8 9 14.2 8.2') > 0);
    out.zeusHairTip = +first(hair)[1].toFixed(2); }

  /* (13) umbra: the inner rim cap */
  { const s = mount('umbra'); const head = s.querySelector('.cx-head');
    const inner = paths(head).find(p => p.getAttribute('stroke') === '#7C3AED' && p.getAttribute('stroke-width') === '.5');
    out.umbraCap = inner ? inner.getAttribute('stroke-linecap') : null; }

  /* (14) every character draws */
  out.all = {};
  AVATAR_CHARACTERS.filter(c => !c.retired).forEach(c => {
    try{ const s = mount(c.id); const b = box(s.querySelector('.cx-fig') || s); out.all[c.id] = b ? 'ok' : 'empty'; }catch(e){ out.all[c.id] = 'ERR ' + e.message; } });
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
        print("\n384 r2: the base-art characters, every join")
        a = r["solarAngles"]
        lattice = len(a) == 5 and all(abs(a[i] - v) < .6 for i, v in enumerate([-45, -22.5, 0, 22.5, 45]))
        check("(1) Solar's five crown spikes point away from the corona's centre on the 22.5-degree lattice", lattice, a)
        tx, ty = r["solarTipsX"], r["solarTipsY"]
        pairs = sorted(zip(tx, ty))
        mirrored = len(pairs) == 5 and all(abs(pairs[i][0] + pairs[4 - i][0] - 40) < .1 and abs(pairs[i][1] - pairs[4 - i][1]) < .1 for i in range(2))
        check("(1) ... and mirrored about x = 20 (tips at the same heights)", mirrored, pairs)
        check("(1) ... with no corona ray standing behind them (11 rays, not 16)", r["solarRays"] == 11, r["solarRays"])
        for cid, subs in r["locks"].items():
            ok = len(subs) == 2 and all(s[1] <= 12.5 for s in subs) and abs(subs[0][0] + subs[1][0] - 40) < .2
            check("(2) %s: both side locks start under the cap of hair and mirror each other" % cid, ok, subs)
        rd = r["forgeRidges"]
        rd_ok = len(rd) == 5 and all(abs(rd[i][0] + rd[4 - i][0] - 40) < .25 and abs(rd[i][2] + rd[4 - i][2] - 40) < .25 and abs(rd[i][1] - rd[4 - i][1]) < .1 and abs(rd[i][3] - rd[4 - i][3]) < .1 for i in range(3))
        check("(3) Forge's five crown ridges are mirrored about x = 20", rd_ok, rd)
        check("(4) Inferno's mane ends inside the face (lowest point above 25.5)", r["infernoManeBottom"] < 25.5, r["infernoManeBottom"])
        check("(5) each side point of the Clown's hat overlaps the brim by a unit or more", all(v >= 1 for v in r["clownOverlap"]), r["clownOverlap"])
        hem = r["ghostHem"]
        check("(6) the Ghost's hem is the same at both ends (mirrored about x = 20 to 0.15)", all(abs(h[1] - h[2]) <= .15 and h[1] > 0 for h in hem), [h for h in hem if abs(h[1] - h[2]) > .15][:4])
        check("(6) ... and its fold shading is clipped to the sheet", r["ghostClip"] >= 1, r["ghostClip"])
        check("(7) the Detective's crown foot is as wide as the head (at least 16.4) and its band is clipped to the crown",
              r["detectiveCrownW"] >= 16.4 and r["detectiveBandClipped"] >= 1, [r["detectiveCrownW"], r["detectiveBandClipped"]])
        check("(8) Void: the hood's rim and the shoulder's rim meet (under 0.15 unit apart on the screen)", r["voidGap"] < .15, r["voidGap"])
        check("(9) the Masked One's red lining is on both tall top points (4 hairlines in all)", r["maskedLining"] == 4, r["maskedLining"])
        check("(10) Orion's upper-left rim light lies on the hood's outline (within 0.9)", r["orionRim"] <= .9, r["orionRim"])
        check("(11) Genesis' collar rim stays outside the planet (nearest point 7.55 or more from its centre)", r["genesisRimNearest"] >= 7.55, r["genesisRimNearest"])
        check("(12) Zeus' hair comes down to the ear at each temple (tip at y 16 or more)", r["zeusHairTip"] >= 16, r["zeusHairTip"])
        check("(13) Umbra's inner rim ends in a round cap", r["umbraCap"] == "round", r["umbraCap"])
        bad = {k: v for k, v in r["all"].items() if v != "ok"}
        check("(14) every character draws", not bad and len(r["all"]) >= 27, bad or len(r["all"]))
        check("no page errors", not errs, errs[:3])
        ctx.close(); br.close()
    srv.shutdown()
    print("\n%s  (%d failure(s))" % ("ALL PASS" if not FAILS else "FAILED", len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
