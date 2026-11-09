"""Build 384, round 9: every hundo effect leaves the grade box the way the default (Confetti) does.
Madison, on Extinguisher beside Confetti: "The default Hundo effect is perfect. The others, the grade box still has some of the
old interface in it, and the borders is messed up? Notice how when the grade box for the default one is done the box doesn't
change color but the others do? Yeah they should be like that, so follow suite with the default way."
On a REAL results screen (a full-chapter / full-unit drill at 100%, summarize() and the results reveal), in both classes, for every effect:
 (1) while it plays and after it ends, the box gets no light of the effect's (no .hfx-tint wash layer on it);
 (2) after it ends the BOX reads exactly as Confetti's does (background, border, shadow), while the 100% and the unit bar carry
     the effect's own colours - his "This is how the sprinkler one should look" (Sprinklers' teal 100% and bar on the plain card);
 (3) while it plays, the effect's layer in the box covers the card's whole border box - its 1px border included, so no ring of
     plain card shows round whatever the effect lays in the box; and nothing washes the box in a colour mid-effect (ifxBoxWash);
 (4) the hand-off from the count's green into a far colour (Extinguisher's red) never shows a hue in between - every frame of the
     number's fill and the bar is near the green, near the red, or a pale light (his "odd colors ... the transition of them isn't
     adding up": it went green > khaki > red).
Run:  python3 tools/check-b384-hfxdefault.py   (--against OLD/index.html must FAIL)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lib_realrun as R
from playwright.sync_api import sync_playwright
cb = R.cb
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1]).read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
READ = r"""() => { const g = document.querySelector('.rs-grade'); if(!g) return null; const cs = getComputedStyle(g), r = g.getBoundingClientRect();
  const f = g.querySelector('.unit-breakdown-fill'), p = g.querySelector('.rs-pct'), bx = g.querySelector(':scope > .hfx-box');
  const br = bx && bx.getBoundingClientRect();
  return { tinted: !!g.querySelector(':scope > .hfx-tint'),
    look: [cs.backgroundColor, cs.backgroundImage, cs.borderTopWidth + ' ' + cs.borderTopColor, cs.boxShadow,
           f ? getComputedStyle(f).backgroundImage : '', p ? getComputedStyle(p).backgroundImage + ' ' + getComputedStyle(p).color : ''],
    box: br ? [br.left - r.left, br.top - r.top, r.right - br.right, r.bottom - br.bottom].map(v => Math.round(v * 10) / 10) : null }; }"""
import math
def oklch(rgb):
    lin = lambda v: v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    r, g, b = [lin(v / 255) for v in rgb]
    l = (.4122214708*r + .5363325363*g + .0514459929*b) ** (1/3); m = (.2119034982*r + .6806995451*g + .1073969566*b) ** (1/3); q = (.0883024619*r + .2817188376*g + .6299787005*b) ** (1/3)
    L = .2104542553*l + .793617785*m - .0040720468*q; A = 1.9779984951*l - 2.428592205*m + .4505937099*q; B = .0259040371*l + .7827717662*m - .808675766*q
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360
def hdist(a, b): d = abs(a - b) % 360; return min(d, 360 - d)
SAMPLE = r"""() => { const g = document.querySelector('.rs-grade'); if(!g) return null; const p = g.querySelector('.rs-pct'), f = g.querySelector('.unit-breakdown-fill');
  const cs = p ? getComputedStyle(p) : null; const fill = cs ? (cs.webkitTextFillColor && cs.webkitTextFillColor !== 'rgba(0, 0, 0, 0)' ? cs.webkitTextFillColor : cs.color) : '';
  return { pct: p ? p.textContent : '', fill, was: f ? f.style.getPropertyValue('--was') : '', wash: g.querySelectorAll('.hfx-box img, .hfx-box *').length }; }"""
WASH = r"""() => { const g = document.querySelector('.rs-grade'); if(!g) return 0; let n = 0;
  g.querySelectorAll('.hfx-box *').forEach(e => { const r = e.getBoundingClientRect(), gr = g.getBoundingClientRect(); const bi = getComputedStyle(e).backgroundImage + (e.src || '');
    if(r.width > gr.width * 1.3 && r.height > gr.height * 2 && +getComputedStyle(e).opacity > .05) n++; }); return n; }"""
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
with sync_playwright() as pw:
    br = pw.chromium.launch()
    for cls in ("ifc", "academy"):
        ref = None
        for fx in IDS:
            ctx, pg, errs = R.open_run(br, cls, 440, 956, fx, dpr=1)
            hand = []
            if cls == "ifc" and fx == "fireworks":
                for _ in range(90):
                    R.advance(pg, .05); v = pg.evaluate(SAMPLE)
                    if v and v["pct"].startswith("100"): hand.append(v)
                    if len(hand) > 26: break
            R.wait_fx(pg)
            washes = 0
            for _ in range(8):
                R.advance(pg, .5); washes = max(washes, pg.evaluate(WASH))
            mid = pg.evaluate(READ)
            R.advance(pg, 14)
            end = pg.evaluate(READ)
            ctx.close()
            tag = "%s %s" % (cls, fx)
            if not mid or not end:
                chk(tag + ": a results screen with a grade card", False, (mid, end)); continue
            if fx == "confetti":
                ref = end["look"]
                chk(tag + ": (1) the default's box is not tinted", not mid["tinted"] and not end["tinted"], (mid["tinted"], end["tinted"]))
                continue
            chk(tag + ": (1) no wash of the effect's colour on the box, while it plays or after", not mid["tinted"] and not end["tinted"], (mid["tinted"], end["tinted"]))
            chk(tag + ": (2) after it ends the box reads exactly as the default's", ref is not None and end["look"][:4] == ref[:4], json.dumps([end["look"][:4], ref[:4]]))
            chk(tag + ": (2) ...and the 100% and the bar are in the effect's colours, not the default's gold", ref is not None and end["look"][4] != ref[4] and end["look"][5] != ref[5], json.dumps([end["look"][4:], ref[4:]]))
            b = mid["box"]
            chk(tag + ": (3) the effect's layer covers the card's border box (offsets %s)" % b, b is None or all(v <= 0.05 for v in b), b)
            chk(tag + ": (3) nothing washes the box in a colour mid-effect (card-sized glows in the box: %d)" % washes, washes == 0, washes)
            if hand:
                import re as _re
                G = oklch((79, 190, 140)); T = oklch((255, 90, 79)); bad = []
                for v in hand:
                    for key in ("fill", "was"):
                        m = _re.match(r"rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?", v[key] or "")
                        if not m or (m.group(4) is not None and float(m.group(4)) < .05): continue
                        L, C, H = oklch(tuple(int(m.group(i)) for i in (1, 2, 3)))
                        if C > .07 and hdist(H, G[2]) > 35 and hdist(H, T[2]) > 35: bad.append((key, v[key], round(H)))
                chk(tag + ": (4) the green-to-red hand-off shows no hue in between (%d frames)" % len(hand), len(hand) >= 5 and not bad, bad[:6])
            if errs: chk(tag + ": no page errors", False, errs)
    br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
