#!/usr/bin/env python3
"""Build 384.134: THE TOP OF EVERY SCREEN IS THE SCREEN'S OWN SKY - no band over the status bar's area.

Madison (Fire Code Enroll, a screenshot with the top strip circled): "the top banner thing here, it doesn't match the rest of the screen and
it doesn't look right." Since 384.80 #top-edge, the still top edge of an installed iPhone/iPad app, covers the whole safe area in ONE flat
colour (a model of the sky) while the sky beneath is three glows over the paper - a band the height of the inset, with a hard foot on the
inset line, 3-4 levels off the sky just under it on every screen.

Per device (installed Pro Max 440x956 inset 62, the Pro Max at 85% page zoom, an installed iPad Pro 11" both ways, a Pro Max Safari tab)
and class (academy, Fire Code), on 14 screens, at rest and scrolled 160px (where the screen scrolls), the screenshot is taken twice: as the
app paints it, and with #top-edge alone hidden (what the screen itself is up there). Read off the pixels, not the CSS:
 (1) SEAM   the median colour of the row just above the strip's foot against the row just under it (columns clear of ink): within SEAM_MAX
            levels. A flat strip over a glowing sky shows its foot as a step; the sky's own gradient moves well under a level in 4px.
 (2) SKY    the strip's area against the same area with the strip hidden (the sky beneath; at rest nothing of the page is up there):
            the median per-pixel difference within SKY_MED, the 95th percentile within SKY_P95.
 (3) STILL  the strip is still the 384.27/384.80 strip: the same node through every screen, fixed at y 0, full width, the inset's height,
            above everything, with a SOLID inline background-colour (what WebKit samples) - and absent from a Safari tab.
 (4) no page errors.
Run:  python3 tools/check-b384-topseam.py [--shots DIR]     --against fa11d79 must FAIL (1) and (2) on every installed screen.
"""
import importlib.util, io, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]
SHOTS = None
if "--shots" in argv:
    i = argv.index("--shots"); SHOTS = os.path.abspath(argv[i + 1]); del argv[i:i + 2]; os.makedirs(SHOTS, exist_ok=True)
sys.argv = [sys.argv[0]] + argv            # --against is read by the shared set-up
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

SEAM_MAX = 2.0
SKY_MED, SKY_P95 = 1, 3
DSF = 2
SCREENS = [
    ("Home", "()=>{ showHome(); }"),
    ("Enroll (Fire Code)", "()=>{ showIfcEnroll(); }"),
    ("Add a class", "()=>{ showClassCatalog('home'); }"),
    ("Choose your mode", "()=>{ showModeSelect(); }"),
    ("Units", "()=>{ cfg.mode='drill'; showSetup(); }"),
    ("Profile", "()=>{ showProfile(); }"),
    ("Stats", "()=>{ showStatsScreen(); }"),
    ("Settings", "()=>{ showAppearance(); }"),
    ("Advanced settings", "()=>{ showAdvancedSettings(); }"),
    ("Leaderboard", "()=>{ showLeaderboard(); }"),
    ("Calendar", "()=>{ showCalendarTab ? showCalendarTab() : showCalendar(); }"),
    ("Friends", "()=>{ showFriends(); }"),
    ("Ranks", "()=>{ showRanksScreen(); }"),
    ("Credits", "()=>{ showCredits(); }"),
]
DEVICES = ["promax", "pm85", "ipad", "ipad-land", "promax-tab"]
G.DEV["ipad-land"] = (1194, 834, 1194, 834, (24, 0, 20, 0), G.UA_IPAD, True, True)

HIDE = "()=>{ let s=document.getElementById('__seam'); if(!s){ s=document.createElement('style'); s.id='__seam'; document.body.appendChild(s); } s.textContent='#top-edge{visibility:hidden !important}'; }"
SHOW = "()=>{ const s=document.getElementById('__seam'); if(s) s.remove(); }"
QUIET = """()=>{ let s=document.getElementById('__q'); if(!s){ s=document.createElement('style'); s.id='__q'; document.body.appendChild(s); }
  s.textContent='*,*::before,*::after{animation-play-state:paused !important; caret-color:transparent !important}'
  + ' body::before, #top-edge{transition:none !important}'; }"""
EDGE = """()=>{ const e=document.getElementById('top-edge'); if(!e) return null; const cs=getComputedStyle(e); const r=e.getBoundingClientRect();
  return { disp: cs.display, pos: cs.position, top: r.top, left: r.left, w: r.width, h: r.height, z: cs.zIndex, inline: e.style.backgroundColor,
           bg: cs.backgroundColor, inW: innerWidth, inset: parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sat')) || null }; }"""
INK = """(foot)=>{ /* columns with ink (text, a button, an image) within 6px of the strip's foot are left out of the seam */
  const xs=[]; for(let x=6; x<innerWidth-6; x+=6) xs.push(x);
  return xs.filter(x => { for(const y of [foot-4, foot-1, foot+1, foot+4]){ if(y<0) continue;
     const hit=document.elementsFromPoint(x, y).filter(e => e.id!=='top-edge' && e!==document.body && e!==document.documentElement && !e.matches('.wrap,#stage,.panel,section,.top'));
     if(hit.length) return false; } return true; }); }"""

results = []
def chk(ok, msg):
    results.append(ok); print(("PASS " if ok else "FAIL ") + msg); sys.stdout.flush()

def med_row(im, y, xs):
    vals = [im.getpixel((int(x * DSF), int(y * DSF))) for x in xs]
    return tuple(statistics.median(v[i] for v in vals) for i in range(3))

def shoot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")

def measure(pg, dev, cls, name, phase, node0):
    e = pg.evaluate(EDGE)
    installed = G.DEV[dev][7]
    if not installed:
        chk(not e or e["disp"] == "none", "%s %s %s %s: no strip in a Safari tab (%s)" % (dev, cls, name, phase, e and e["disp"]))
        return
    if e and e["disp"] == "none" and "Macintosh" in G.DEV[dev][5]:
        # iPadOS asks for the desktop site (a Mac user agent), and the head script's iOS test reads the user agent: no strip, nothing to match
        print("INFO %s %s %s %s: no strip (iPadOS's Mac user agent; html.top-edge-on is not set)" % (dev, cls, name, phase)); return
    same = pg.evaluate("(n)=>document.getElementById('top-edge') === window.__edge0", None)
    ok3 = e and e["disp"] == "block" and e["pos"] == "fixed" and e["top"] == 0 and e["left"] == 0 and abs(e["w"] - e["inW"]) < .5 \
        and abs(e["h"] - G.DEV[dev][4][0]) < .5 and e["z"] == "2147483647" and e["inline"] and same
    chk(bool(ok3), "%s %s %s %s: (3) the still strip - same node %s, fixed at %s,%s, %sx%s, z %s, inline colour %r" % (
        dev, cls, name, phase, same, e and e["top"], e and e["left"], e and e["w"], e and e["h"], e and e["z"], e and e["inline"]))
    foot = e["h"]
    xs = pg.evaluate(INK, foot)
    a = shoot(pg)
    pg.evaluate(HIDE); pg.wait_for_timeout(120); b = shoot(pg); pg.evaluate(SHOW); pg.wait_for_timeout(60)
    if SHOTS:
        a.save(os.path.join(SHOTS, "%s-%s-%s-%s.png" % (dev, cls, name.split(" ")[0].lower(), phase)))
    bar = pg.evaluate("()=>{ const b=document.getElementById('settings-bar'); return !!(b && b.classList.contains('is-on')); }")
    if phase == "scrolled" and (bar or len(xs) < 10):
        # scrolled, the page's own content (or Settings' frosted bar, which starts at the inset by design) is under the strip's foot
        print("INFO %s %s %s scrolled: seam not measured (%s)" % (dev, cls, name, "the frosted bar is up" if bar else "%d clear columns" % len(xs)))
        return
    if len(xs) < 10:
        chk(False, "%s %s %s %s: (1) too few clear columns at the strip's foot (%d)" % (dev, cls, name, phase, len(xs))); return
    above, below = med_row(a, foot - 2, xs), med_row(a, foot + 2, xs)
    step = max(abs(above[i] - below[i]) for i in range(3))
    chk(step <= SEAM_MAX, "%s %s %s %s: (1) seam at the strip's foot (y %g): %s over %s, %.1f levels (max %g)" % (
        dev, cls, name, phase, foot, tuple(int(v) for v in above), tuple(int(v) for v in below), step, SEAM_MAX))
    if phase == "rest":
        box = (0, 0, a.width, int(foot * DSF))
        d = ImageChops.difference(a.crop(box), b.crop(box)).convert("L")
        hist = d.histogram(); n = sum(hist); acc = 0; med = p95 = None
        for lv, c in enumerate(hist):
            acc += c
            if med is None and acc >= n * .5: med = lv
            if p95 is None and acc >= n * .95: p95 = lv; break
        chk(med <= SKY_MED and p95 <= SKY_P95, "%s %s %s rest: (2) the strip against the sky beneath it: median %d, p95 %d levels (max %d / %d)" % (
            dev, cls, name, med, p95, SKY_MED, SKY_P95))

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev in DEVICES:
        for cls in ("academy", "ifc"):
            pg = None
            for attempt in range(3):
                try:
                    pg = G.open_dev(br, dev, inits=[G.seed_init(cls), "try{localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));}catch(e){}"], dsf=DSF)
                    break
                except Exception as ex:
                    print("retry open", dev, cls, str(ex)[:120])
            pg.evaluate("()=>{ window.__edge0 = document.getElementById('top-edge'); }")
            for name, js in SCREENS:
                if name.startswith("Enroll") and cls == "ifc":
                    continue
                try:
                    pg.evaluate("()=>{ window.scrollTo(0,0); }")
                    pg.evaluate(js)
                except Exception as ex:
                    chk(False, "%s %s %s: could not open (%s)" % (dev, cls, name, str(ex)[:120])); continue
                pg.wait_for_timeout(1500); G.clear_popups(pg); pg.evaluate(QUIET); pg.wait_for_timeout(250)
                measure(pg, dev, cls, name, "rest", None)
                can = pg.evaluate("()=>document.documentElement.scrollHeight - innerHeight")
                if can > 200 and G.DEV[dev][7]:
                    pg.evaluate("()=>{ document.documentElement.style.scrollBehavior='auto'; window.scrollTo(0,160); }"); pg.wait_for_timeout(400)
                    measure(pg, dev, cls, name, "scrolled", None)
                    pg.evaluate("()=>{ window.scrollTo(0,0); document.documentElement.style.scrollBehavior=''; }"); pg.wait_for_timeout(200)
            chk(not pg.errs, "%s %s: (4) no page errors %s" % (dev, cls, pg.errs[:2]))
            pg.ctx.close()
    br.close()
bad = results.count(False)
print("\n%d checks, %d failed" % (len(results), bad))
print("ALL PASS" if not bad else "FAILED")
sys.exit(1 if bad else 0)
