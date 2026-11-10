#!/usr/bin/env python3
"""Build 384 round 24: EVERY FIRE CODE BANNER MOVES.

Madison: "Some ifc banners issues: why barely any of them animate, and why do some of them not animate as you scroll through them?"
Measured on the build before: three Fire Code banners (Certified, Squared Away, Mutual Aid) were held completely still by the academy's
"first rung of each ladder is still" rule, six more ran three or four slow breathing glows (a few percent of scale, a fifth of their
opacity) that cannot be seen at the size a tile is drawn, and the busiest ran nine to nineteen.

The motion is judged on the page, by SHAPE, never by a label:

 (1) EVERY id in IFC_BANNER_ART, built by buildBannerArt in a strip at phone width (440) and tablet width (834) in the Fire Code class:
     not .is-still; at least 6 animations RUNNING; every running animation animates only transform and/or opacity (read from
     getAnimations()[i].effect.getKeyframes(): the compositor's, nothing repaints).
 (2) ...and it VISIBLY MOVES, from the first second: every animation in the strip is paused and set to a time (not waited for, so the picture
     is the same on a slow machine), and the strip is photographed 0.7 seconds apart in three windows - from the moment the banner appears
     (0.0 -> 0.7s: "within a second of appearing"), and 1.1 -> 1.8s, and 2.4 -> 3.1s. In EVERY window the share of pixels that changed
     (by more than 10 of 255 in any channel) is at least MOVE_MIN. One window is not enough: a banner whose only event is every seven
     seconds, or whose event layers are dark until a delay runs out, passes one window and is a still picture the rest of the time.
 (3) CUSTOMIZE > BANNER, scrolled through (all banners forced earned) at phone width: once the page has settled at each stop (the two
     observers have answered: nothing paused or idle has changed over four frames), every tile that is at least two-thirds in view (seen, not under a bar) and
     drawn has running animations, is neither .is-offscreen nor .rk-idle, and VISIBLY moves (photographed as it runs, five frames 0.7s
     apart, the best gap of the four over the tile's own box; nothing is paused or seeked here, because pause()/play() on a CSS animation makes the
     browser ignore the CSS's own play-state for it afterwards); every drawn tile more than half a screen away runs nothing, and one more
     than a screen and a tenth away is .rk-idle (the build 252 budget: only what can be seen, or is about to be, moves).
 (4) THE ACADEMY is untouched: in the academy class every banner that is not in BANNER_ANIMATED is still .is-still with nothing running -
     tests100, hundos100 and vr50 among them - and the three rank banners are not.

  python3 tools/check-b384-fcbanner-motion.py [--against OLD/index.html] [--table] [--skip-strips] [--vp 518x1126] [--cpu 4]

MOVE_MIN is 1% of the strip's pixels. On 9b0ee77 (build 384.17) the weak ones measured 0.04% (On Call), 0.3-0.4% (Inspection Team, After Hours),
0.5% (Plan Review, Clean Sweep), 0.7-0.9% (Fire Investigator, Nebula, Comet in one window) and the three still ones 0.00%, so the line sits between
them and the ~1.3-75% every banner shows now.
Fails on 9b0ee77 (build 384.17): (1) tests100, hundos100 and vr50 are .is-still, nine banners have fewer than 6 animations running, (2) eleven banners
are under MOVE_MIN in some window (Certified, Plan Review, Inspection Team, Squared Away, Mutual Aid, On Call, Fire Investigator, After Hours, Clean
Sweep, Nebula, Comet), (3) the still tiles do not run or move.
--table prints every banner's running count and its three window numbers, and how many frames each scroll stop took to settle.
"""
import json, os, sys, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops

args = sys.argv[1:]
BODY = open(args[args.index("--against") + 1], encoding="utf-8").read() if "--against" in args else None
TABLE = "--table" in args
SKIP_STRIPS = "--skip-strips" in args      # while iterating on the scroll lines
VPW, VPH = [int(v) for v in (args[args.index("--vp") + 1] if "--vp" in args else "440x956").split("x")]   # the Customize section's viewport (518x1126 is the page-zoom case)
CPU = float(args[args.index("--cpu") + 1]) if "--cpu" in args else 1     # --cpu 4: CDP CPU throttling while the list is scrolled. The STATE lines still hold (running, not
# idle, not paused, far ones stilled); the pixel line does not: a throttled, software-rendered frame here is seconds long, so five screenshots can be one frame.
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700])

MOVE_MIN = 0.01        # share of the strip's pixels that must change in every 0.7s window (1%; the build before had a banner at 0.04%, and four more under 0.6%)
MIN_RUNNING = 6
WINDOWS = [(0.0, 0.7), (1.1, 1.8), (2.4, 3.1)]
COMPOSITOR = {"transform", "opacity"}
NOT_PROPS = {"offset", "easing", "composite", "computedOffset"}

def seed_for(cls):
    seed = dict(rc["SEED"]); seed.update(seenClassTip=True, novaMet=99, publicId="tst4fc8banr1", classes=["academy", "ifc"])
    S = json.dumps(json.dumps(seed))
    base = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
            "localStorage.setItem('class26e.drill.v1',%s);") % S
    if cls == "ifc":
        return base + ("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));"
            "localStorage.setItem('class26e.greet.ifc','done');['class26e.ifc.freshstart','class26e.ifc.intro.seen','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
            "localStorage.setItem('class26e.ifc.drill.v1',%s);}catch(e){}") % S
    return base + "localStorage.setItem('class26e.activeclass','academy');localStorage.setItem('class26e.enrolled',JSON.stringify(['academy']));}catch(e){}"

def share(a, b, box=None):
    """the share of pixels that differ by more than 10 (of 255) in any channel"""
    if box: a, b = a.crop(box), b.crop(box)
    d = ImageChops.difference(a, b); r, g, bl = d.split()
    m = ImageChops.lighter(ImageChops.lighter(r, g), bl)
    return sum(m.histogram()[11:]) / float(m.size[0] * m.size[1])

SEEK = "(t) => { document.getAnimations().forEach(a => { try{ a.pause(); a.currentTime = t * 1000; }catch(e){} }); }"
def shot(pg, t, sel=None):
    pg.evaluate(SEEK, t); pg.wait_for_timeout(90)
    png = (pg.query_selector(sel).screenshot() if sel else pg.screenshot())
    return Image.open(io.BytesIO(png)).convert("RGB")

STATS = """(a) => { const [id, w, h] = a;
  document.getElementById('splashscreen')?.remove(); document.body.innerHTML = ''; document.body.style.cssText = 'background:#000;margin:0';
  const box = document.createElement('div'); box.id = 'strip'; box.style.cssText = 'position:fixed;left:0;top:0;width:' + w + 'px;height:' + h + 'px;overflow:hidden;z-index:99999;background:#000';
  const el = buildBannerArt(id); box.appendChild(el); document.body.appendChild(box);
  const an = el.getAnimations({ subtree: true }).filter(x => x.playState === 'running');
  const bad = []; an.forEach(x => { try{ Object.keys(x.effect.getKeyframes()[0]).forEach(k => { if(['offset','easing','composite','computedOffset'].indexOf(k) < 0 && k !== 'transform' && k !== 'opacity') bad.push(k); }); x.effect.getKeyframes().forEach(f => Object.keys(f).forEach(k => { if(['offset','easing','composite','computedOffset'].indexOf(k) < 0 && k !== 'transform' && k !== 'opacity') bad.push(k); })); }catch(e){ bad.push('?'); } });
  return { still: el.classList.contains('is-still'), running: an.length, bad: Array.from(new Set(bad)), layered: el.classList.contains('bnr-layered') }; }"""

def boot(pw, cls, w, h):
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    ctx = br.new_context(viewport={"width": w, "height": h})
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    if BODY is not None:
        pg.route("**/index.html", lambda r, q: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.add_init_script(seed_for(cls))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_timeout(2500)
    pg.evaluate("() => document.getElementById('splashscreen')?.remove()")
    return br, ctx, pg, errs

srv, PORT = rc["serve"]()
try:
  with sync_playwright() as pw:
    # ---------------------------------------------------------------- (1) and (2): every Fire Code banner in a strip
    table = {}
    for (W, label) in ([] if SKIP_STRIPS else [(440, "phone"), (834, "tablet")]):
        br, ctx, pg, errs = boot(pw, "ifc", W, 700)
        ids = pg.evaluate("() => Object.keys(IFC_BANNER_ART)")
        chk("the Fire Code class has its own banner set (%d ids)" % len(ids), len(ids) >= 17, ids)
        H = round(W / 3.017)
        notstill, few, badprops, quiet = [], [], [], []
        for i in ids:
            st = pg.evaluate(STATS, [i, W, H]); pg.wait_for_timeout(250)
            nums = []
            for (t0, t1) in (WINDOWS if label == "phone" else WINDOWS[:2]):
                a = shot(pg, t0, "#strip"); b = shot(pg, t1, "#strip"); nums.append(share(a, b))
            table[(label, i)] = (st["running"], nums)
            if st["still"]: notstill.append(i)
            if st["running"] < MIN_RUNNING: few.append((i, st["running"]))
            if st["bad"]: badprops.append((i, st["bad"]))
            if min(nums) < MOVE_MIN: quiet.append((i, [round(n * 100, 2) for n in nums]))
        chk("(1) %s: no Fire Code banner is held still (.is-still)" % label, not notstill, notstill)
        chk("(1) %s: every Fire Code banner has at least %d animations running" % (label, MIN_RUNNING), not few, few)
        chk("(1) %s: every running animation is transform and/or opacity only" % label, not badprops, badprops)
        chk("(2) %s: every Fire Code banner visibly moves in EVERY 0.7s window, the first one from the moment it appears (>= %.2f%% of pixels)" % (label, MOVE_MIN * 100), not quiet, quiet)
        chk("(1) %s: no page error" % label, not errs, errs[:2])
        ctx.close(); br.close()
    if TABLE:
        for (label, i), (n, nums) in sorted(table.items()):
            print("   %-7s %-14s running %2d   moved %s" % (label, i, n, "  ".join("%.2f%%" % (x * 100) for x in nums)))

    # ---------------------------------------------------------------- (3): Customize > Banner, scrolled through
    br, ctx, pg, errs = boot(pw, "ifc", VPW, VPH)
    if CPU != 1: ctx.new_cdp_session(pg).send("Emulation.setCPUThrottlingRate", {"rate": CPU})
    pg.evaluate("() => { window.bannerEarned = () => true; showCustomize('banner'); }"); pg.wait_for_timeout(3500)
    maxy = pg.evaluate("() => document.scrollingElement.scrollHeight - innerHeight")
    chk("(3) the Customize banner page is taller than the screen (%d)" % maxy, maxy > 900, maxy)
    TILES = """() => { const vh = innerHeight; return Array.from(document.querySelectorAll('.banner-opt')).map(b => {
      const art = b.querySelector('.banner-opt-art'), r = art.getBoundingClientRect(), bn = art.querySelector('.bnr');
      /* how much of the tile can actually be SEEN: a 4 x 3 grid of points over it, each one the tile's own pixel and not the viewport's edge or a bar over it (the
         navigation bar sits over the top of whatever scrolls under it, and a tile half under it moves under it where nobody looks) */
      let seen = 0; for(let i = 0; i < 4; i++) for(let j = 0; j < 3; j++){ const px = r.left + r.width * (i + .5) / 4, py = r.top + r.height * (j + .5) / 3;
        if(px >= 0 && py >= 0 && px < innerWidth && py < vh){ const e = document.elementFromPoint(px, py); if(e && art.contains(e)) seen++; } }
      const vis = seen / 12;
      const dist = r.bottom < 0 ? -r.bottom : r.top > vh ? r.top - vh : 0;
      return { id: b.dataset.banner, x: r.left, y: r.top, w: r.width, h: r.height, vis, dist, vh, drawn: !!bn,
        off: b.classList.contains('is-offscreen'), idle: !!(bn && bn.classList.contains('rk-idle')), still: !!(bn && bn.classList.contains('is-still')),
        running: bn ? bn.getAnimations({ subtree: true }).filter(x => x.playState === 'running').length : 0 }; }); }"""
    SETTLE = """() => new Promise(done => { const t0 = performance.now(); let frames = 0, same = 0, last = '';
      const sig = () => Array.from(document.querySelectorAll('.banner-opt')).map(b => (b.classList.contains('is-offscreen') ? 'o' : '-') + (b.querySelector('.bnr.rk-idle') ? 'i' : '-') + (b.querySelector('.bnr') ? 'd' : '-')).join('');
      const tick = () => { frames++; const s = sig(); same = (s === last) ? same + 1 : 0; last = s;
        if(same >= 4 || performance.now() - t0 > 9000) done({ frames, ms: Math.round(performance.now() - t0) }); else requestAnimationFrame(tick); };
      requestAnimationFrame(tick); })"""
    frames_waited = []
    problems = {"idleInView": [], "pausedInView": [], "notRunning": [], "notMoving": [], "farRunning": [], "farNotIdle": []}
    seen_view = set(); checked = 0
    # NOTHING here pauses or seeks the page's animations: calling pause() or play() on a CSS animation makes the browser ignore the CSS's own play-state for it
    # from then on, which is exactly the thing being measured. The tiles are photographed as they run, 0.7s apart, and the best of the four gaps is the number (a software-rendered browser on a loaded machine can hand back the same composited frame twice, so one gap can read zero).
    for k, frac in enumerate([0, .22, .45, .7, 1.0]):
        pg.evaluate("(y) => document.scrollingElement.scrollTo({ top: y, behavior: 'instant' })", int(maxy * frac)); pg.wait_for_timeout(1000)
        # "settled": the two observers have answered - what is paused or idle has not changed over four frames (a page this heavy paints a frame a second or so in a
        # software-rendered browser, so a fixed wait is a wait for a number of frames nobody counted)
        info = pg.evaluate(SETTLE); frames_waited.append((frac, info["frames"], info["ms"]))
        tiles = pg.evaluate(TILES)
        fr = []
        for n in range(5):
            fr.append(Image.open(io.BytesIO(pg.screenshot())).convert("RGB"))
            if n < 4: pg.wait_for_timeout(700)
        for t in tiles:
            if not t["drawn"] or not t["id"]: continue
            if t["vis"] >= .65:
                checked += 1; seen_view.add(t["id"])
                if t["idle"]: problems["idleInView"].append((frac, t["id"]))
                if t["off"]: problems["pausedInView"].append((frac, t["id"]))
                if t["running"] == 0: problems["notRunning"].append((frac, t["id"]))
                box = (max(0, int(t["x"])), max(0, int(t["y"])), min(VPW, int(t["x"] + t["w"])), min(VPH, int(t["y"] + t["h"])))
                mv = max(share(fr[k], fr[k + 1], box) for k in range(4))
                if CPU == 1 and mv < MOVE_MIN: problems["notMoving"].append((frac, t["id"], round(mv * 100, 2)))
            elif t["dist"] > t["vh"] * .5:
                if t["running"]: problems["farRunning"].append((frac, t["id"], t["running"]))
                if t["dist"] > t["vh"] * 1.1 and not t["idle"]: problems["farNotIdle"].append((frac, t["id"]))
    if TABLE: print("   settle after each stop (frac, frames, ms):", frames_waited)
    chk("(3) %d in-view tiles looked at over five stops, %d different banners" % (checked, len(seen_view)), checked >= 20 and len(seen_view) >= 12, (checked, len(seen_view)))
    chk("(3) a tile in view is never .rk-idle", not problems["idleInView"], problems["idleInView"][:4])
    chk("(3) a tile in view is never held paused (.is-offscreen) after a one-second settle", not problems["pausedInView"], problems["pausedInView"][:4])
    chk("(3) every tile in view has running animations", not problems["notRunning"], problems["notRunning"][:6])
    chk("(3) every tile in view visibly moves (>= %.2f%% of its pixels over 0.7s)" % (MOVE_MIN * 100), not problems["notMoving"], problems["notMoving"][:6])
    chk("(3) a tile more than half a screen away runs nothing", not problems["farRunning"], problems["farRunning"][:4])
    chk("(3) a tile more than a screen and a tenth away is idle (.rk-idle)", not problems["farNotIdle"], problems["farNotIdle"][:4])
    chk("(3) no page error", not errs, errs[:2])
    ctx.close(); br.close()

    # ---------------------------------------------------------------- (4): the academy keeps its still first rungs
    br, ctx, pg, errs = boot(pw, "academy", 440, 700)
    info = pg.evaluate("""() => { const stillIds = BANNERS.filter(b => BANNER_ANIMATED.indexOf(b.id) < 0).map(b => b.id), res = {};
      document.body.innerHTML = ''; document.body.style.cssText = 'background:#000;margin:0';
      BANNERS.forEach(b => { const box = document.createElement('div'); box.style.cssText = 'position:fixed;left:0;top:0;width:440px;height:146px;overflow:hidden';
        const el = buildBannerArt(b.id); box.appendChild(el); document.body.appendChild(box);
        res[b.id] = { still: el.classList.contains('is-still'), running: el.getAnimations({ subtree: true }).filter(x => x.playState === 'running').length }; box.remove(); });
      return { cls: window.NOVA_CLASS, stillIds, res, anim: BANNER_ANIMATED.slice(), ranks: BANNERS.filter(b => b.rank).map(b => b.id) }; }""")
    chk("(4) this is the academy page (%s)" % info["cls"], info["cls"] != "ifc", info["cls"])
    wrong = [i for i in info["stillIds"] if not info["res"][i]["still"] or info["res"][i]["running"]]
    chk("(4) every academy banner outside BANNER_ANIMATED is still and runs nothing (%d of them)" % len(info["stillIds"]), info["stillIds"] and not wrong, wrong)
    chk("(4) tests100, hundos100 and vr50 are among the academy's still ones", all(i in info["stillIds"] and info["res"][i]["still"] for i in ("tests100", "hundos100", "vr50")), [i for i in ("tests100", "hundos100", "vr50") if i not in info["stillIds"]])
    chk("(4) the rank banners move", all(not info["res"][i]["still"] and info["res"][i]["running"] > 0 for i in info["ranks"]), info["ranks"])
    chk("(4) no page error", not errs, errs[:2])
    ctx.close(); br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
