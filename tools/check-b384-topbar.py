#!/usr/bin/env python3
"""Build 384.136: a scrolled screen's frosted bar runs from the top of the screen, so nothing of the page shows above it.

Madison (the review page's "scrolls under the clock" picture, Profile scrolled, the strip above the bar circled): "Massive problem???
What is happening here. FIX". 384.136 put the status bar's strip behind the page (content scrolls under the clock, as on 383), but
#settings-bar - the frosted bar that comes up with the inline title once a Profile / Stats / Settings / Leaderboard / Calendar page is
scrolled - began AT the inset, so the clock's area above it was open and the scrolled page showed there, over the bar's top edge (the
Profile / Stats / Settings switch peeking out above "Profile").
Checked, installed, on an iPhone 17 Pro Max, its 85% page zoom and an iPad (both classes), on every screen that has the bar, scrolled
160px and 400px: whenever the bar is up its box starts at y 0 and reaches its foot, and at every sampled point in the clock's area
(0 .. the inset) the page shows through only as the frosted bar's faint blur: the clock's area photographed with the page and with the
page hidden differs by at most a few levels on average (the page sharp in the open strip differs by tens); at rest the bar is down.
(The bar takes no taps, so a hit test cannot see it: this is measured in pixels.) Saves the scrolled Profile with --shots DIR.

  python3 tools/check-b384-topbar.py [--against OLD/index.html] [--shots DIR]   (must FAIL on the build before)
"""
import importlib.util, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[1:]; SHOTS = None
if "--shots" in argv:
    i = argv.index("--shots"); SHOTS = os.path.abspath(argv[i + 1]); del argv[i:i + 2]; os.makedirs(SHOTS, exist_ok=True)
sys.argv = [sys.argv[0]] + argv
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
import io
from PIL import Image, ImageChops, ImageStat
SCREENS = [("Profile", "()=>{ showProfile(); }"), ("Stats", "()=>{ showStatsScreen(); }"), ("Settings", "()=>{ showAppearance(); }"),
           ("Advanced settings", "()=>{ showAdvancedSettings(); }"), ("Sound settings", "()=>{ showAppearance({page:'sound'}); }"),
           ("Study settings", "()=>{ showAppearance({page:'study'}); }"), ("Account settings", "()=>{ showAppearance({page:'account'}); }"), ("Leaderboard", "()=>{ showLeaderboard(); }"),
           ("Calendar", "()=>{ showCalendarTab ? showCalendarTab() : showCalendar(); }"), ("Ranks", "()=>{ showRanksScreen(); }")]
DEVICES = ["promax", "pm85", "ipad"]
PROBE = """()=>{ const b = document.getElementById('settings-bar'); const on = !!(b && b.classList.contains('is-on'));
  const r = b ? b.getBoundingClientRect() : null; const sat = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sat')) || 0;
  return { on, top: r && r.top, bottom: r && r.bottom, sat, bad: [], nbad: 0 }; }"""
results = []
def chk(ok, msg):
    results.append(bool(ok)); print(("PASS " if ok else "FAIL ") + msg, flush=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev in DEVICES:
        for cls in ("academy", "ifc"):
            pg = G.open_dev(br, dev, inits=[G.seed_init(cls), "try{localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));}catch(e){}"], dsf=2 if SHOTS else 1)
            seen_bar = 0
            for name, js in SCREENS:
                try:
                    pg.evaluate("()=>{ window.scrollTo(0,0); }"); pg.evaluate(js)
                except Exception as ex:
                    chk(False, "%s %s %s: could not open (%s)" % (dev, cls, name, str(ex)[:100])); continue
                pg.wait_for_timeout(1400); G.clear_popups(pg); pg.wait_for_timeout(200)
                r0 = pg.evaluate(PROBE)
                chk(not r0["on"], "%s %s %s rest: the bar is down" % (dev, cls, name))
                can = pg.evaluate("()=>document.documentElement.scrollHeight - innerHeight")
                for y in (160, 400):
                    if can < y: continue
                    pg.evaluate("(y)=>{ document.documentElement.style.scrollBehavior='auto'; window.scrollTo(0,y); }", y); pg.wait_for_timeout(500)
                    r = pg.evaluate(PROBE)
                    if name in ("Profile", "Stats", "Settings"):
                        # (384.150) Madison: "Remove the bar thing" - the Profile tab's three segments scroll their big title away, no bar
                        chk(not r["on"], "%s %s %s scrolled %d: no bar on the Profile tab (384.150)" % (dev, cls, name, y)); continue
                    if not r["on"]:
                        print("INFO %s %s %s scrolled %d: no bar on this screen" % (dev, cls, name, y)); continue
                    seen_bar += 1
                    clip = {"x": 0, "y": 0, "width": pg.evaluate("()=>innerWidth"), "height": max(4, r["sat"] - 1)}
                    a_ = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("L")
                    pg.evaluate("()=>{ const s=document.getElementById('stage'); if(s) s.style.visibility='hidden'; }"); pg.wait_for_timeout(150)
                    b_ = Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("L")
                    pg.evaluate("()=>{ const s=document.getElementById('stage'); if(s) s.style.visibility=''; }"); pg.wait_for_timeout(100)
                    d = ImageChops.difference(a_, b_); st = ImageStat.Stat(d); mean = st.mean[0]; mx = max(d.getdata())
                    chk(abs(r["top"]) < .5 and r["bottom"] >= r["sat"] + 10 and mean <= 4 and mx <= 40,
                        "%s %s %s scrolled %d: the bar runs from y %s to %s (inset %s); the page in the clock's area: mean %.1f, max %d levels" % (
                            dev, cls, name, y, r["top"] is not None and round(r["top"], 1), round(r["bottom"], 1), r["sat"], mean, mx))
                    if SHOTS and name == "Profile" and y == 160:
                        pg.screenshot(path=os.path.join(SHOTS, "%s-%s-profile-scrolled.png" % (dev, cls)))
                pg.evaluate("()=>{ window.scrollTo(0,0); document.documentElement.style.scrollBehavior=''; }")
            # (384.150) the Profile tab no longer has the bar, and the Settings pages that keep it are too short here to scroll 160px; the
            # Profile checks above are what this gate measures now (they FAIL on 384.149, where the bar came up there)
            print("INFO %s %s: the bar came up on %d scrolled screens" % (dev, cls, seen_bar))
            chk(not pg.errs, "%s %s: no page errors %s" % (dev, cls, pg.errs[:2]))
            pg.ctx.close()
    br.close()
bad = results.count(False)
print("\n%d checks, %d failed" % (len(results), bad)); print("ALL PASS" if not bad else "FAILED"); sys.exit(1 if bad else 0)
