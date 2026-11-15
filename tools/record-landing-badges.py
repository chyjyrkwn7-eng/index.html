#!/usr/bin/env python3
"""Records the badges clip on the Get Started page: landing/badges.mp4 and landing/badges.jpg (its FIRST frame, the poster).

  python3 tools/record-landing-badges.py            (LANDING_OUT=<dir> to write somewhere else)

BUILD 384.124 (startup). Madison: "Badges should be a little video in the start up screen. So update the start up, remove the
badges from the thing on the bottom, make badges a badge but only show a few of the ifc ones. Like 10 max."

What the clip is: a Fire Code chapter badge being found and going into the badge case, in the app's own scene
(playBadgeCaseScene: BADGE FOUND, the pin turning, its name; the case comes up, unlatches, opens with the badges already in it
lit; the new pin flies into its slot and seats). It runs over Fire Code's Home and ends back on it, so the loop's dissolve
joins Home to Home.

AT MOST TEN DISTINCT BADGES (CLIP_UNITS, Madison's "Like 10 max"). The real Fire Code case holds every chapter (58), and its
empty slots are drawn as recesses in each object's outline - 58 shapes. For the clip only, the case is given these ten chapters
(BADGE_CASES[0].units, set in the recording page; nothing in the app changes): nine are held when it opens (eight already in
it and the new one), one stays empty. The count line under the case ("Found N of M missing badges") would read the clip's
ten, not the real 58, so it is hidden in the recording (the badge's name stays). Chosen to read well at the case's size and
to look varied (red, brass, green, yellow, cream, blue, teal, white):
  Chapter 3 extinguisher, Chapter 5 hydrant, Chapter 9 sprinkler (the one found), Chapter 10 exit door, Chapter 20 airplane,
  Chapter 33 hard hat, Chapter 35 torch, Chapter 54 jug, Chapter 59 matches, Chapter 62 cooler.

Capture and encoding are record-landing.py's (780x1690 from a 390px page at 2x, the page in slow motion, a true 30 fps clock,
the last half second dissolved into the first frame, H.264 High 4.1 yuv420p, faststart, no audio, under 3 MB). The account is
record-landing-ifc.py's fixture ("Alex"; the Fire Code class needs the publicId it uses, never on screen); sound off. The
Firebase CDN is blocked in the sandbox, so the app runs on its local copy as every recorder here does."""
import importlib.util, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("record_landing_ifc", os.path.join(HERE, "record-landing-ifc.py"))
ri = importlib.util.module_from_spec(spec); spec.loader.exec_module(ri)
rl = ri.rl
from playwright.sync_api import sync_playwright

# the case in the clip, in the case's own (teaching) order; at most ten - check-b384-startup.py reads this list
CLIP_UNITS = [
    "Chapter 3: General Requirements",
    "Chapter 5: Fire Service Features",
    "Chapter 9: Fire Protection and Life Safety Systems",
    "Chapter 10: Means of Egress",
    "Chapter 20: Aviation Facilities",
    "Chapter 33: Fire Safety During Construction and Demolition",
    "Chapter 35: Welding and Other Hot Work",
    "Chapter 54: Corrosive Materials",
    "Chapter 59: Flammable Solids",
    "Chapter 62: Organic Peroxides",
]
FOUND = "Chapter 9: Fire Protection and Life Safety Systems"
EMPTY = "Chapter 59: Flammable Solids"
assert len(CLIP_UNITS) <= 10 and FOUND in CLIP_UNITS and EMPTY in CLIP_UNITS
# the wait while the case comes up and opens (6.0-12.1s of the scene) plays 1.5x faster, uniformly (never skips)
SPEED = [(6.6, 12.9, 1.5)]

SETUP = r"""([units, found, empty])=>{
  const have = units.filter(u => u !== empty);
  const missing = units.filter(u => !unitsInTeachingOrder().includes(u));
  if(missing.length) return 'not in the bank: ' + missing.join(', ');
  BADGE_CASES[0].units = units.slice();
  store.unitPerfects = {};
  have.forEach(u => { store.unitPerfects[u] = badgeThresholdFor(u); });
  try{ markBadgeScenesPlayed(have); }catch(e){}
  store.pendingBadgeUnlocks = [];
  store.seenUnlockedTiers = TIER_ORDER_FULL.slice();
  saveStore();
  const s = document.createElement('style');
  s.textContent = '.bc-scene .bc-words .bc-sub{ visibility:hidden !important; }';
  document.body.appendChild(s);
  return 'ok';
}"""


def scene_badges(br, port):
    ctx, pg = rl.new_page(br, port, ri.SEED, ri.IN_IFC)
    cls = pg.evaluate("()=>window.NOVA_CLASS")
    if cls != "ifc": raise SystemExit("badges: the page is not in Fire Code (%s)" % cls)
    got = pg.evaluate(SETUP, [CLIP_UNITS, FOUND, EMPTY])
    if got != "ok": raise SystemExit("badges: " + got)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    rl.settle(pg)
    pg.wait_for_timeout(1200)
    rec = rl.Recorder(pg); rec.start(rate=.12)
    rl.wait(pg, 900)
    pg.evaluate("(u)=>{ window.__bcDone = false; playBadgeCaseScene([u], () => { window.__bcDone = true; }, [], {}); }", FOUND)
    # the scene runs ~17s of its own clock; then Home again for a beat (the loop's join)
    for _ in range(2400):
        rl.wait(pg, 250)
        if pg.evaluate("()=>window.__bcDone === true && !document.querySelector('.bc-scene')"): break
    rl.wait(pg, 700)
    frames = rec.stop(); ctx.close()
    rl.encode(frames, "badges", speed=SPEED)


if __name__ == "__main__":
    srv, port = rl.serve()
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=rl.CHROME)
        scene_badges(br, port)
        br.close()
    srv.shutdown()
