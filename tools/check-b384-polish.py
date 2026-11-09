#!/usr/bin/env python3
"""Build 384 polish: the rank-up cutscene and the results screen's grade box, after Madison watched the videos.

  python3 tools/check-b384-polish.py [--against FILE] [--only A,B,C,D,E]

Madison (he/him): "The rank up cutscene, double check that this only forms up during that entire rank up ladder
cutscene. And ensure that problem we talked about a while ago is fixed where you couldn't leave it because it kept going
in circles going it again and again is fixed." / "The rank up cutscene, when the large planet changes color, there's
like a weird lag that happens in the video, ensure it's smooth transitions." / "The result screen, the grade box, it
says 'right in first try' before the numbers above it appear, shouldn't that be fixed?" / "Also, still ensure when it
changes from red to green that it's a smooth transition. Don't put in other colors just ensure it's smooth." / "could
the bottom of it [the XP box] with your level and character and stuff, could that all look better?"

Both classes (Police Academy, Fire Code); an iPhone 17 Pro Max, an iPad Pro 11" and a laptop window.

A. THE RANK-UP CUTSCENE PLAYS ONLY IN THE RANK-UP JOURNEY, ONCE A RANK, AND IT ALWAYS ENDS. Every call of the
   cutscene (playRankUpScene) is counted, with where it was called from. Walked on the page's own clock (the recorders':
   timers, frames and every animation stepped), each class: a real 100% that ranks up -> its results -> Main menu ->
   Home locks and calls -> the Profile tab -> the journey (road map, cutscene, reward card) -> Home and Profile again
   for a while; a relaunch after it; a relaunch in the middle of the cutscene (it plays the rest - the cutscene once more
   - and then never again); two ranks owed (two journeys, one cutscene each, then nothing); taps all through the
   cutscene and the app sent to the background in the middle of it; a forced update held for the whole journey. Every
   cutscene is inside a journey (rankUpScene, phase "cutscene"), each rank's cutscene finishes and is played at most once
   per journey, nothing is owed at the end, the tab bar comes back, and Home and Profile stay free (no lock, no journey,
   no cutscene) for 25s after. A copy with rankUpMarkShown taken out (the journey owes itself again - "going in circles")
   fails this section: --sabotage-loop runs that copy (A_CLASSES=academy runs one class).
B. THE PLANET CHANGES COLOUR SMOOTHLY. The tier cutscene on the page's clock, 1/30s a frame: (1) the flash's scale and
   brightness, read every frame from the start of the flash to the title, never stop dead and lurch on (no frame's step
   more than 4x the frame before while it moves - the keyframes used to ease out one by one: a stop at 14% and at 35%,
   where the planet swaps, then a jump of ~100x); (2) from the flash to the title nothing is added to the page or taken
   off it, and neither <html> nor the overlay is re-themed (each was a whole-document style pass, 30-40ms here, as the
   planet changed colour); (3) the theme is still set when the scene ends; (4) the overlay's words come up in the new
   rank's colours. Real-time frame gaps around the swap are printed (not gated: the machine is shared).
C. THE WORDS UNDER THE GRADE NEVER COME BEFORE ITS NUMBERS. Real results (summarize()) on the page's clock: in every
   frame "right on the first try" (.rs-grade-sub) is no more visible than "10 / 12" (.rs-grade-frac) above it, and it
   is fully there once the grade has landed.
D. RED INTO GREEN, SMOOTH, NO OTHER COLOUR, NEVER COLOURLESS. Same runs, every frame, off the pixels: the number's glyphs
   and each unit bar are only ever the red or the green (over the dark card) - no hue between them (orange, yellow, olive)
   with any colour in it, and no green brighter or more saturated than the landed one; a fail never takes any green; a
   pass ends on the landed green. REVISED IN 384 r7 (Madison: "When the grade transition turns from red to green, it's
   like no color when that happens"): the 384-polish fade to 12% opacity WAS that colourless moment, so the turn is a
   FLIP - the number and each bar keep their full colour in every frame (chroma never under 60% of the weaker landed
   colour), the number's colour changes only while it is edge-on (its height at that frame under 30% of its full height),
   and the flip is a movement over several frames (3+ frames under 90% height), not a cut.
E. THE XP BOX'S FOOT (the level, the character, the bar under them): its parts in one row and in order, the level
   chip and the bar's line legible, nothing clipped or overflowing, at every size, both classes.

Every section fails on 185cc5c (A only with --sabotage-loop: the loop it guards against was fixed in build 331).
"""
import functools, http.server, io, json, math, os, re, socket, sys, threading, time, glob
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


SRC = arg("--against") or os.path.join(ROOT, "index.html")
ONLY = set((arg("--only") or "A,B,C,D,E").split(","))
_rs = open(os.path.join(ROOT, "tools", "record-sound.py"), encoding="utf-8").read()
CLOCK = re.search(r'CLOCK = r"""(.*?)"""', _rs, re.S).group(1)
STUB = re.search(r'FIRESTORE_STUB = """(.*?)"""', _rs, re.S).group(1)
RAW = open(SRC, encoding="utf-8").read()
if "--sabotage-loop" in sys.argv:
    # the journey that never counts itself shown: what "kept going in circles" would be
    RAW = RAW.replace("function rankUpMarkShown(toIdx){\n  try{", "function rankUpMarkShown(toIdx){ return;\n  try{", 1)
BODY = RAW.replace("let fbDb = null;", "let fbDb = null;" + STUB, 1)
BUILD = (re.search(r'APP_BUILD\s*=\s*"([^"]+)"', BODY) or [None, "x"])[1]
s = socket.socket(); s.bind(("127.0.0.1", 0)); PORT = s.getsockname()[1]; s.close()


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass


SRV = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
threading.Thread(target=SRV.serve_forever, daemon=True).start()

FAILS = []


def ck(name, ok, info=None):
    print(("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:500]), flush=True)
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------- the account (an existing one: everything seen)
ALL_CHARS = ["detective", "masked", "zeus", "poseidon", "clown", "valkyrie", "marksman", "astronaut", "hacker", "timekeeper", "ronin", "hive",
             "voidwalker", "umbra", "singularity", "genesis", "lunar", "solar", "tempest", "frost", "oracle", "inferno", "astral", "celestial", "zenith"]
ALL_BANNERS = ["tests100", "tests250", "tests500", "hundos100", "hundos250", "vr50", "study50", "study60", "correct5000", "correct10000", "level80",
               "early10", "exam100", "adept_rank", "elite_rank", "titan_rank", "flare_void", "flare_umbra", "flare_horizon", "flare_genesis",
               "astral", "celestial", "zenith"]
SEED = {"onboardingComplete": True, "firstName": "Alex", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "seenFirstResultsTour": True, "seenRewardsTour": True, "seenSettingsTour": True, "seenUnitOptionsTour": True, "seenRanksTour": True,
        "seenBadgesTour": True,
        "lifetime": {"points": 41000, "answered": 2100, "correct": 1980, "drillPlays": 60, "examPlays": 12, "perfectTests": 64,
                     "longestStreak": 44, "currentStreak": 12},
        "unitPerfects": {},
        "unlocksShown": {"chars": ALL_CHARS, "banners": ALL_BANNERS, "fx": ["fireworks", "underwater", "bubbles", "ufo"]},
        "flareHintsShown": ["umbra", "singularity", "genesis"]}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen",
        "soundon.327"]


def init_js(cls):
    s = ("(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1');"
         "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9');"
         "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');")
    for k in SEEN:
        s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    if cls == "ifc":
        s += ("localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
              "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.ifc.weekrecap.v1','9999-12-31');"
              "localStorage.setItem('class26e.ifc.intro.seen','9');")
        for k in SEEN:
            s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"


def open_page(br, cls, w=440, h=956, dpr=1):
    """(the account is the class owner's public id - the one account that can open another class today, as check-b384-cutscenes)"""
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True)
    ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    ctx.add_init_script(init_js(cls))
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
    pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    pg.route("**/version.json*", lambda r: r.fulfill(status=200, headers={"content-type": "application/json"},
                                                     body='{"build":"%s","frameId":"","force":false}' % BUILD))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT)
    pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ __stub(); }catch(e){} theme.reduceMotion = false; theme.muteBanners = false; applyTheme(); }")
    return ctx, pg, errs


def step(pg, ms=1000 / 30):
    return pg.evaluate("async (d) => await __clk.advance(d)", ms)


# ---------------------------------------------------------------- colour
def lin(v):
    v /= 255.0
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4


def oklab(c):
    r, g, b = [lin(v) for v in c[:3]]
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s_,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s_,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s_)


def lch(c):
    L, a, b = oklab(c)
    return L, math.hypot(a, b), (math.degrees(math.atan2(b, a)) + 360) % 360


def dE(c1, c2):
    a, b = oklab(c1), oklab(c2)
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def hue_gap(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


# ---------------------------------------------------------------- C and D: the grade box, counted in
RUN = """([n, good, perfectFx]) => {
  const units = {}; QUESTIONS.forEach((q, i) => { if(typeof inWholeUnit === 'function' && !inWholeUnit(i)) return; const t = (q.topic || '').trim(); (units[t] = units[t] || []).push(i); });
  let unit = Object.keys(units).find(t => units[t].length === n) || Object.keys(units).find(t => units[t].length >= n);
  if(window.NOVA_CLASS !== 'ifc' && units['Identity Crimes'] && units['Identity Crimes'].length >= n) unit = 'Identity Crimes';
  store.lifetime = store.lifetime || {}; store.lifetime.perfectTests = 900;
  if(perfectFx) store.hundoFx = perfectFx;
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit]; cfg.size = 0;
  order = units[unit].slice(0, n);
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false;
  practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {};
  try{ firstPick = {}; }catch(e){}
  order.forEach((qi, k) => { const oo = optionOrder(qi), right = oo.indexOf(QUESTIONS[qi].answer);
    attempts[qi] = k < n - good ? 2 : 1; picked[qi] = right; try{ if(k < n - good) firstPick[qi] = (right + 1) % oo.length; }catch(e){} });
  runStartTime = Date.now() - 42000; testInProgress = true; pos = order.length - 1;
  summarize(); return unit; }"""

GREAD = r"""() => { const g = document.querySelector('.rs-card.rs-grade'); if(!g) return null;
  const r = g.getBoundingClientRect(), pe = g.querySelector('.rs-pct'), fr = g.querySelector('.rs-grade-frac'), sub = g.querySelector('.rs-grade-sub');
  const op = el => { if(!el) return null; let o = 1; for(let e = el; e && e !== document.body; e = e.parentElement) o *= +getComputedStyle(e).opacity; return +o.toFixed(3); };
  const box = el => { const b = el.getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; };
  const bars = [...g.querySelectorAll('.unit-breakdown-fill')].map(f => { const b = f.getBoundingClientRect(), t = (f.parentNode || f).getBoundingClientRect();
    return [Math.max(b.left, t.left), b.top, Math.min(b.right, t.right), b.bottom]; });
  return { t: performance.now(), cls: g.className, box: [r.left, r.top, r.right, r.bottom], pct: pe ? pe.textContent.trim() : null, gop: op(g),
    pbox: pe ? box(pe) : null, fop: op(fr), sop: op(sub), sub: sub ? sub.textContent.trim() : '', bars, vh: innerHeight }; }"""


def glyph_core(im, box):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    W, H = im.size
    px = [im.getpixel((x, y)) for x in range(max(0, x0), min(W, x1)) for y in range(max(0, y0), min(H, y1))]
    if len(px) < 20:
        return None
    srt = sorted(px, key=lambda p: p[0] + p[1] + p[2])
    bg = srt[len(srt) // 2]
    d = sorted(px, key=lambda p: -sum(abs(p[i] - bg[i]) for i in range(3)))
    core = d[:max(6, len(d) // 14)]
    return tuple(sum(p[i] for p in core) / len(core) for i in range(3))


def bar_colour(im, b):
    x0, y0, x1, y1 = [int(round(v)) for v in b]
    if x1 - x0 < 8 or y1 - y0 < 2:
        return None
    ym = (y0 + y1) // 2
    px = [im.getpixel((x, ym)) for x in range(x0 + 3, x1 - 3)]
    return tuple(sum(p[i] for p in px) / len(px) for i in range(3)) if px else None


def grade_case(pw, label, cls, size, n, good, fx=None, max_frames=420):
    from PIL import Image
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx, pg, errs = open_page(br, cls, size[0], size[1])
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(500)
    pg.evaluate(CLOCK)
    unit = pg.evaluate(RUN, [n, good, fx])
    rows, land = [], None
    for f in range(max_frames):
        step(pg)
        st = pg.evaluate(GREAD)
        if not st:
            continue
        st["f"] = f
        if st["box"][3] > 0 and st["box"][1] < st["vh"]:
            # the card only (a clip is a fraction of a whole-page shot); boxes moved into its frame
            x0, y0 = max(0, int(st["box"][0]) - 2), max(0, int(st["box"][1]) - 2)
            x1, y1 = min(size[0], int(st["box"][2]) + 3), min(st["vh"], int(st["box"][3]) + 3)
            im = Image.open(io.BytesIO(pg.screenshot(clip={"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}))).convert("RGB")
            mv = lambda b: [b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0]
            st["num"] = glyph_core(im, mv(st["pbox"])) if st["pbox"] else None
            st["barc"] = [bar_colour(im, mv(b)) for b in st["bars"]]
        rows.append(st)
        if "rs-graded" in st["cls"] and land is None:
            land = f
        if land is not None and f > land + 40:
            break
    br.close()
    return {"label": label, "rows": rows, "land": land, "errs": errs, "good": good, "n": n, "unit": unit, "cls": cls}


def section_c(c):
    lab = c["label"]
    rows = [r for r in c["rows"] if r.get("fop") is not None and r.get("sop") is not None]
    early = [(r["f"], r["fop"], r["sop"]) for r in rows if r["sop"] > r["fop"] + .02]
    ck("C %s: in every frame (%d) the words under the grade are no more visible than its numbers" % (lab, len(rows)), rows and not early, early[:6])
    before = [r for r in rows if c["land"] is not None and r["f"] < c["land"]]
    shown_before = [(r["f"], r["sop"]) for r in before if r["sop"] > .02]
    ck("C %s: '%s' is not on the card before the grade lands (%d frames before it)" % (lab, rows[-1]["sub"] if rows else "", len(before)),
       before and not shown_before, shown_before[:4])
    ck("C %s: both are fully there once it has landed" % lab, rows and rows[-1]["fop"] > .98 and rows[-1]["sop"] > .98,
       rows and (rows[-1]["fop"], rows[-1]["sop"]))


def section_d(c):
    lab = c["label"]
    perfect = c["good"] == c["n"]
    # from the card's arrival (fully in) to the landing - a 100 then hands to its effect, its own transition (rsHandoff,
    # by hue); a pass is read on past its landing, where a grade just over the pass mark turns
    end = (c["land"] if perfect else c["land"] + 30) if c["land"] is not None else 10 ** 6
    rows = [r for r in c["rows"] if r.get("num") and (r.get("gop") or 0) >= .98 and r["f"] <= end]
    if not rows:
        ck("D %s: frames read" % lab, False, "none")
        return
    red = rows[0]["num"]
    passes = c["good"] * 100 // c["n"] >= 70
    green = (rows[-2]["num"] if perfect and len(rows) > 1 else rows[-1]["num"]) if passes else None
    hR = lch(red)[2]
    hG = lch(green)[2] if green else None
    cG = lch(green)[1] if green else 0
    LG = lch(green)[0] if green else 0
    off, over = [], []
    for r in rows:
        L, C, h = lch(r["num"])
        if C > .035 and hue_gap(h, hR) > 30 and (hG is None or hue_gap(h, hG) > 30):
            off.append((r["f"], [round(v) for v in r["num"]], round(h)))
        if hG is not None and hue_gap(h, hG) <= 30 and (C > cG * 1.12 + .01 or L > LG + .04):
            over.append((r["f"], round(C, 3), round(cG, 3), round(L, 3), round(LG, 3)))
    ck("D %s: the number is only ever its red or its green - no colour between (%d frames)" % (lab, len(rows)), not off, off[:6])
    if not passes:
        gr = [r["f"] for r in rows if hue_gap(lch(r["num"])[2], hR) > 60 and lch(r["num"])[1] > .035]
        ck("D %s: a fail never takes any green" % lab, not gr, gr[:6])
    else:
        ck("D %s: no green brighter or richer than the landed one (no bloom)" % lab, not over, over[:6])
        # (r7) never colourless: every frame keeps its full colour
        cmin = .6 * min(lch(red)[1], lch(green)[1])
        dull = [(r["f"], round(lch(r["num"])[1], 3)) for r in rows if lch(r["num"])[1] < cmin]
        ck("D %s: never colourless - the number keeps its colour in every frame (chroma >= %.3f)" % (lab, cmin), not dull, dull[:6])
        # (r7) the colour changes edge-on, inside a flip of several frames
        hs = [(r["f"], r["pbox"][3] - r["pbox"][1], hue_gap(lch(r["num"])[2], hG) < hue_gap(lch(r["num"])[2], hR)) for r in rows if r.get("pbox")]
        full = max((h for _, h, _ in hs), default=0)
        sw = next((i for i in range(1, len(hs)) if hs[i][2] and not hs[i - 1][2]), None)
        at = min(hs[sw - 1][1], hs[sw][1]) if sw else None
        ck("D %s: the colour changes while the number is edge-on (height %s of %s)" % (lab, at and round(at, 1), round(full, 1)),
           sw is not None and full > 0 and at <= .3 * full, (sw and hs[sw - 1:sw + 1], full))
        low = sum(1 for _, h, _ in hs if full and h < .9 * full)
        ck("D %s: a flip over several frames, not a cut (%d frames under 90%% height)" % (lab, low), low >= 3, low)
    # the unit bars: their own red and green, same rules
    nb = max((len(r.get("barc") or []) for r in rows), default=0)
    for bi in range(nb):
        seq = [(r["f"], r["barc"][bi]) for r in rows if r.get("barc") and len(r["barc"]) > bi and r["barc"][bi] and (not perfect or r["f"] < c["land"])]
        if len(seq) < 5:
            continue
        b0 = seq[0][1]; bl = seq[-1][1]
        h0 = lch(b0)[2]; hl = lch(bl)[2]
        boff = [(f, [round(v) for v in col]) for f, col in seq if lch(col)[1] > .035 and hue_gap(lch(col)[2], h0) > 30 and hue_gap(lch(col)[2], hl) > 30]
        ck("D %s: unit bar %d is only ever its red or its green" % (lab, bi + 1), not boff, boff[:6])
        if passes and hue_gap(h0, hl) > 60:
            bmin = .6 * min(lch(b0)[1], lch(bl)[1])
            bd = [(f, round(lch(col)[1], 3)) for f, col in seq if lch(col)[1] < bmin]
            ck("D %s: unit bar %d keeps its colour through the turn (chroma >= %.3f)" % (lab, bi + 1, bmin), not bd, bd[:6])
    ck("D %s: no page errors" % lab, not c["errs"], c["errs"][:3])


# ---------------------------------------------------------------- B: the planet changes colour smoothly
SEED_RANK = r"""(k)=>{ const rule = TIER_UNLOCKS[k] || {}; const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  store.unitPerfects = {}; topics.slice(0, rule.badges || 0).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
  let pts = 500; while(levelProgress(pts).level < (rule.level || 0)) pts += 250; store.lifetime.points = pts;
  const i = TIER_ORDER_FULL.indexOf(k);
  store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, i + 1); store.rankUpShown = i + 1; store.rankMapSeen = i;
  theme.accent = TIER_ORDER_FULL[i - 1]; applyTheme(); saveTheme(); saveStore();
  return [rankOf(store), isLockedAccent(k)]; }"""
WATCH = r"""() => {
  const W = window.__fw = { muts: [], frames: [], done: null };
  const nm = n => n.nodeType !== 1 ? '#' + n.nodeName : (n.tagName.toLowerCase() + (n.id ? '#' + n.id : '') + (typeof n.className === 'string' && n.className ? '.' + n.className.trim().split(/\s+/).slice(0, 3).join('.') : ''));
  new MutationObserver(ms => ms.forEach(m => {
    const o = document.getElementById('supernova-cutscene');
    if(!o || !o.classList.contains('supernova-burst') || o.classList.contains('supernova-settle')) return;
    if(m.type === 'childList') [...m.addedNodes, ...m.removedNodes].forEach(n => { if(n.nodeType === 1) W.muts.push((m.addedNodes.length ? '+ ' : '- ') + nm(n) + ' in ' + nm(m.target)); });
    else if(m.target === document.documentElement || m.target === o) W.muts.push('@' + m.attributeName + ' on ' + nm(m.target) + ' -> ' + m.target.getAttribute(m.attributeName));
  })).observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['data-accent', 'data-theme'] });
  return true; }"""
FREAD = r"""() => { const o = document.getElementById('supernova-cutscene'); if(!o) return null;
  const f = o.querySelector('.supernova-flash'); if(!f) return null;
  const sc = t => { if(!t || t === 'none') return 1; const m = t.match(/matrix\(([^)]*)\)/); return m ? +m[1].split(',')[0] : 1; };
  const cs = getComputedStyle(f), cb = getComputedStyle(f, '::before');
  return { c: o.className, s: sc(cs.transform), o: +cs.opacity, ds: sc(cb.transform), do: +cb.opacity }; }"""


def lurches(vals):
    """frames where the motion all but stops and then jumps on: a step more than 4x the one before it, or a near-still
    step (under a fifth) after a moving one and before a moving one"""
    d = [vals[i + 1] - vals[i] for i in range(len(vals) - 1)]
    big = max((abs(x) for x in d), default=0)
    out = []
    for i in range(1, len(d)):
        a, b = abs(d[i - 1]), abs(d[i])
        if max(a, b) < .02 * big:
            continue
        if b > 4 * max(a, 1e-4) and b > .25 * big:
            out.append((i, round(a, 4), round(b, 4)))
    return out


def scene_flash(pw, cls, key, supernova=False):
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx, pg, errs = open_page(br, cls)
    pg.evaluate(SEED_RANK, key)
    pg.evaluate("()=>{ showProfile(); }"); pg.wait_for_timeout(1500)
    pg.evaluate(CLOCK); pg.evaluate(WATCH)
    call = ("()=>{ playSupernovaCutscene({ from: 'elite', onDone(){ window.__fw.done = performance.now(); } }); }" if supernova else
            "(k)=>{ const i = TIER_ORDER_FULL.indexOf(k); playTierCutscene(k, { from: TIER_ORDER_FULL[i - 1], onDone(){ window.__fw.done = performance.now(); } }); }")
    pg.evaluate(call, key) if not supernova else pg.evaluate(call)
    rows = []
    # on to the charge in big steps (timers still run in order), then frame by frame
    for _ in range(1200):
        if pg.evaluate("async () => { await __clk.advance(1000 / 15); const o = document.getElementById('supernova-cutscene'); return !o || o.classList.contains('is-cutrest'); }"):
            break
    for f in range(30 * 30):
        step(pg)
        st = pg.evaluate(FREAD)
        if st:
            st["f"] = f
            rows.append(st)
        if pg.evaluate("()=>window.__fw.done != null"):
            break
    out = pg.evaluate("""(k)=>{ const p = document.createElement('p'); p.className = 'supernova-kicker'; p.dataset.accent = k; p.dataset.theme = 'dark';
      document.body.appendChild(p); const want = getComputedStyle(p).color; p.remove();
      return { muts: window.__fw.muts, done: window.__fw.done != null, accent: theme.accent, root: document.documentElement.dataset.accent || '', want }; }""", key)
    br.close()
    return rows, out, errs


def section_b(pw):
    for cls, key in (("academy", "veteran"), ("ifc", "veteran")):
        rows, out, errs = scene_flash(pw, cls, key)
        lab = "%s, the %s rank-up" % ("Fire Code" if cls == "ifc" else "academy", key)
        burst = [r for r in rows if "supernova-burst" in r["c"]]
        win = [r for r in burst if "supernova-settle" not in r["c"]]
        ck("B %s: the scene played to its end (%d frames, %d from the flash to the title)" % (lab, len(rows), len(win)), out["done"] and len(win) > 30, (out["done"], len(win)))
        for k, nm in (("s", "the flash's size"), ("o", "the flash's light"), ("ds", "the deep bloom's size"), ("do", "the deep bloom's light")):
            lz = lurches([r[k] for r in win])
            ck("B %s: %s never stops dead and lurches on (%d frames)" % (lab, nm, len(win)), win and not lz, lz[:5])
        ck("B %s: from the flash to the title nothing is added to or taken off the page and nothing is re-themed" % lab, not out["muts"], out["muts"][:8])
        ck("B %s: the new theme is set when the scene ends (%s, <html> %s)" % (lab, out["accent"], out["root"]), out["accent"] == key and out["root"] == key, out)
        ck("B %s: no page errors" % lab, not errs, errs[:3])
    rows, out, errs = scene_flash(pw, "academy", "titan", supernova=True)
    win = [r for r in rows if "supernova-burst" in r["c"] and "supernova-settle" not in r["c"]]
    for k, nm in (("s", "the flash's size"), ("o", "the flash's light")):
        lz = lurches([r[k] for r in win])
        ck("B academy, Supernova: %s never stops dead and lurches on (%d frames)" % (nm, len(win)), win and not lz, lz[:5])
    ck("B academy, Supernova: played to its end, no page errors", out["done"] and not errs, (out["done"], errs[:2]))
    realtime_gaps(pw)


def realtime_gaps(pw):
    """Not gated (a shared machine): the real-time frame gaps from the flash to the title, printed for the notes."""
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    ctx, pg, errs = open_page(br, "academy")
    pg.evaluate(SEED_RANK, "veteran")
    pg.evaluate("()=>{ showProfile(); }"); pg.wait_for_timeout(1500)
    pg.evaluate("""()=>{ const M = window.__rt = { fr: [] }; const loop = t => { M.fr.push(t); if(!M.stop) requestAnimationFrame(loop); }; requestAnimationFrame(loop);
      new MutationObserver(() => { const o = document.getElementById('supernova-cutscene'); if(!o) return;
        if(o.classList.contains('supernova-burst') && M.b == null) M.b = performance.now(); if(o.classList.contains('is-swapped') && M.s == null) M.s = performance.now();
        if(o.classList.contains('supernova-settle') && M.e == null) M.e = performance.now(); }).observe(document.body, { subtree: true, attributes: true, attributeFilter: ['class'] });
      playTierCutscene('veteran', { from: 'ranger', onDone(){ M.done = 1; } }); }""")
    for _ in range(45):
        pg.wait_for_timeout(1000)
        if pg.evaluate("()=>!!window.__rt.done"):
            break
    m = pg.evaluate("()=>{ window.__rt.stop = 1; return window.__rt; }")
    br.close()
    if not m.get("b") or not m.get("e"):
        print("  (real time: the scene did not reach its title)")
        return
    fr = [t for t in m["fr"] if m["b"] - 50 <= t <= m["e"] + 50]
    gaps = [round(fr[i + 1] - fr[i]) for i in range(len(fr) - 1)]
    sw = [round(fr[i + 1] - fr[i]) for i in range(len(fr) - 1) if m["s"] - 120 <= fr[i] <= m["s"] + 400]
    print("  (real time, 1x CPU, not gated: flash to title %d frames, longest gap %dms, %d gaps over 50ms; around the swap %s)" % (
        len(gaps), max(gaps or [0]), sum(1 for x in gaps if x > 50), sw), flush=True)


# ---------------------------------------------------------------- A: only in the journey, once a rank, it always ends
INSTR_A = r"""() => {
  if(window.__ru) return true;
  const A = window.__ru = { cuts: [], ends: 0, journeys: 0, fub: [], phases: {}, hidden: 0 };
  const P = window.playRankUpScene;
  window.playRankUpScene = function(k){ A.cuts.push({ k, j: !!rankUpScene, ph: rankUpScene ? rankUpScene.phase : null, to: rankUpScene ? rankUpScene.to : null }); return P.apply(this, arguments); };
  const N = window.rankUpNewScene;
  window.rankUpNewScene = function(){ A.journeys++; return N.apply(this, arguments); };
  new MutationObserver(ms => ms.forEach(m => [...m.removedNodes].forEach(n => { if(n.id === 'supernova-cutscene') A.ends++; }))).observe(document.body, { childList: true });
  return true; }"""
# what a person does while it plays: taps a reward card once it has been up a while, reads Nova's words through, leaves
# the results by Main menu, answers the Profile tab's call - and, when asked to, taps all over the cutscene and puts the
# app in the background in the middle of it
PUMP = r"""(o) => {
  const A = window.__ru, now = performance.now();
  if(rankUpScene){ A.phases[rankUpScene.phase] = 1; try{ if(!forcedUpdateBlocked()) A.fub.push(rankUpScene.phase); }catch(e){} }
  const sp = document.querySelector('.rs-spot.is-up');
  if(sp){ if(!sp.__t0) sp.__t0 = now; if(now - sp.__t0 > 2600) sp.click(); }
  for(const id of ['nova-rank', 'nova-intro']){ const el = document.getElementById(id); if(el && el.__nova){ const n = el.__nova;
    if(!el.__t0) el.__t0 = now; if(now - el.__t0 > 900){ el.__t0 = now; if(n.typing) n.advance(); else if(n.index < n.count - 1) n.advance(); else { const g = el.querySelector('.nt-go'); if(g) g.click(); } } } }
  const rs = document.querySelector('.rs-screen');
  if(rs && o.menu){ if(!rs.__t0) rs.__t0 = now;
    if(!rs.__done && (document.querySelector('.rs-rewards.rs-done') || now - rs.__t0 > 70000)) rs.__done = now;
    /* Main menu's own action (showHome): its tap guard reads the event's real time against the page's stepped clock, so a
       click from here is refused as "a finger already down" (rsTapAt) - the walk is about what comes after it */
    if(rs.__done && now - rs.__done > 1800 && !rs.__left){ rs.__left = 1; showHome(); } }
  if(document.body.classList.contains('rankup-lock') && stage.querySelector('[data-screen="home"]')){
    if(!A.lockAt) A.lockAt = now;
    if(now - A.lockAt > 2500){ A.lockAt = 0; document.getElementById('bottomtab-profile')?.click(); }
  } else A.lockAt = 0;
  const cut = document.getElementById('supernova-cutscene');
  let tap = null;
  if(cut && o.rough){
    if(!cut.__t0) cut.__t0 = now;
    const el = now - cut.__t0;
    if(!cut.__k) cut.__k = 0;
    if(el > cut.__k * 700){ cut.__k++; tap = [[.5, .5], [.5, .97], [.1, .05], [.9, .6]][cut.__k % 4]; }
    if(el > 6000 && !cut.__hid){ cut.__hid = 1; A.hidden++;
      Object.defineProperty(document, 'hidden', { configurable: true, get(){ return true; } });
      Object.defineProperty(document, 'visibilityState', { configurable: true, get(){ return 'hidden'; } });
      document.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('pagehide')); }
    if(el > 9000 && cut.__hid === 1){ cut.__hid = 2;
      delete document.hidden; delete document.visibilityState;
      document.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('pageshow')); }
  }
  return { tap, scene: !!rankUpScene, cut: !!cut, owed: !!rankUpOwed(), lock: document.body.classList.contains('rankup-lock'),
    journey: document.body.classList.contains('ru-journey'), nova: !!document.getElementById('nova-rank'), home: !!stage.querySelector('[data-screen="home"]'),
    j: A.journeys, c: A.cuts.length }; }"""
STATE = r"""() => { const A = window.__ru; const shown = el => { if(!el) return false; const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
    return r.width > 0 && r.bottom > 0 && r.top < innerHeight && cs.display !== 'none' && cs.visibility !== 'hidden' && +cs.opacity > .5; };
  return { cuts: A.cuts, ends: A.ends, journeys: A.journeys, fub: A.fub, phases: Object.keys(A.phases), hidden: A.hidden,
    owed: rankUpOwed(), shown: store.rankUpShown, rank: rankOf(store), lock: document.body.classList.contains('rankup-lock'),
    focus: ['cutscene-focus', 'ru-journey'].filter(c => document.body.classList.contains(c)), tabs: shown(document.getElementById('bottomtabs')),
    left: !!document.querySelector('#supernova-cutscene, .ru-blocker, .ru-curtain.is-on, .ru-veil') }; }"""
SEED_A = r"""(a) => {
  const topics = [...new Set(QUESTIONS.map(q => (q.topic||'').trim()))].filter(Boolean);
  const unit = topics.includes(a.topic) ? a.topic : topics.find(t => QUESTIONS.filter(q => (q.topic || '').trim() === t).length >= 8);
  const rule = TIER_UNLOCKS[a.rank], ri = TIER_ORDER_FULL.indexOf(a.rank);
  const others = topics.filter(t => t !== unit);
  store.unitPerfects = {};
  if(a.mode === 'run'){
    others.slice(0, rule.badges - 1).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
    store.unitPerfects[unit] = badgeThresholdFor(unit) - 1;
  } else others.slice(0, rule.badges).forEach(t => { store.unitPerfects[t] = badgeThresholdFor(t); });
  let pts = 500; while(levelProgress(pts).level < rule.level) pts += 100;
  store.lifetime.points = pts + 300; store.lifetime.perfectTests = 900;
  const shown = a.mode === 'run' ? ri : ri - (a.owe || 1) + 1;
  store.rankUpShown = shown; store.rankUpFrom = null; store.rankMapSeen = shown - 1; store.seenUnlockedTiers = TIER_ORDER_FULL.slice(0, shown);
  saveStore();
  return { unit, rank: rankOf(store), owed: rankUpOwed() }; }"""
RUN_UNIT = r"""(unit) => {
  showHome();
  cfg.mode = 'drill'; cfg.source = 'all'; cfg.units = [unit]; cfg.size = 0;
  order = QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === unit && (typeof inWholeUnit !== 'function' || inWholeUnit(i)));
  runTrackable = true; timedOut = false; runMode = 'drill'; runLabel = null; isMissedRetake = false;
  practiceTestMinutes = null; inVirtualRoom = false; attempts = {}; picked = {}; timedOutSet = {};
  try{ firstPick = {}; }catch(e){}
  order.forEach(qi => { attempts[qi] = 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
  runStartTime = Date.now() - 60000; testInProgress = true; pos = order.length - 1;
  summarize(); return { owed: rankUpOwed(), n: order.length }; }"""
TOPIC = {"academy": "Identity Crimes", "ifc": "Appendix H: Hazardous Materials Management Plan (HMMP) and Hazardous Materials Inventory Statement (HMIS) Instructions"}


def a_page(br, cls):
    ctx, pg, errs = open_page(br, cls)
    pg.evaluate("()=>{ theme.muteBanners = false; theme.reduceMotion = false; applyTheme(); saveTheme(); }")
    pg.evaluate(CLOCK); pg.evaluate(INSTR_A)
    return ctx, pg, errs


def a_relaunch(pg):
    pg.reload()
    pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ __stub(); }catch(e){} }")
    pg.evaluate(CLOCK); pg.evaluate(INSTR_A)


def a_drive(pg, secs, o, until=None, ms=150):
    """the page's clock on by `secs` (virtual), a person's taps along the way; stops early when until(state) holds"""
    st = None
    for _ in range(int(secs * 1000 / ms)):
        step(pg, ms)
        st = pg.evaluate(PUMP, o)
        if st.get("tap"):
            vw = pg.viewport_size
            try: pg.mouse.click(vw["width"] * st["tap"][0], vw["height"] * st["tap"][1])
            except Exception: pass
        if until and until(st):
            return st, True
    return st, False


def journey_over(st):
    return not st["scene"] and not st["cut"] and not st["journey"] and not st["nova"] and not st["owed"]


def a_free(pg, lab):
    """Home, then Profile, 25s each on the page's clock - a person going back to both - and nothing may start again"""
    before = pg.evaluate("()=>({ j: __ru.journeys, c: __ru.cuts.length })")
    pg.evaluate("()=>{ showHome(); }")
    a_drive(pg, 25, {})
    pg.evaluate("()=>{ showProfile(); }")
    a_drive(pg, 25, {})
    pg.evaluate("()=>{ showHome(); }")
    a_drive(pg, 4, {})
    st = pg.evaluate(STATE)
    ck("A %s: afterwards Home and Profile stay free for 50s - no lock, no journey, no cutscene (journeys %d -> %d, cutscenes %d -> %d)" % (
        lab, before["j"], st["journeys"], before["c"], len(st["cuts"])),
       st["journeys"] == before["j"] and len(st["cuts"]) == before["c"] and not st["lock"] and not st["owed"], st)
    ck("A %s: nothing of the journey is left on the page, the tab bar is back (%s)" % (lab, st["focus"]), not st["left"] and not st["focus"] and st["tabs"], st)
    return st


def a_cuts_ok(lab, st, want):
    bad = [c for c in st["cuts"] if not c["j"] or c["ph"] != "cutscene" or c["k"] != c["to"]]
    ck("A %s: every cutscene was played by the journey, in its cutscene step, for the journey's own rank (%s)" % (lab, [(c["k"], c["ph"]) for c in st["cuts"]]),
       st["cuts"] and not bad, bad)
    ks = [c["k"] for c in st["cuts"]]
    ck("A %s: one cutscene a rank - %s" % (lab, ks), ks == want, (ks, want))
    ck("A %s: each one finished (%d of %d) and a forced update was held all through the journey (%s)" % (lab, st["ends"], len(st["cuts"]), st["fub"][:3]),
       st["ends"] == len(st["cuts"]) and not st["fub"], st)


def section_a(pw):
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    for cls in [c for c in ("academy", "ifc") if c in os.environ.get("A_CLASSES", "academy,ifc")]:
        name = "Fire Code" if cls == "ifc" else "academy"
        rank = "adept" if cls == "academy" else "ranger"
        # 1. a real 100% that ranks up -> results -> Main menu -> Home's call -> Profile -> the journey
        ctx, pg, errs = a_page(br, cls)
        seed = pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": rank, "mode": "run"})
        run = pg.evaluate(RUN_UNIT, seed["unit"])
        lab = "%s, from the results" % name
        ck("A %s: the run of %s ranks up to %s (owed %s)" % (lab, seed["unit"][:40], rank, run["owed"]), bool(run["owed"]), (seed, run))
        st, ok = a_drive(pg, 200, {"menu": True, "rough": cls == "academy"}, until=lambda s: s["j"] >= 1 and s["c"] >= 1 and journey_over(s) and s["home"] is not None and not s["lock"])
        ok = ok and a_drive(pg, 3, {})[0] is not None
        s1 = pg.evaluate(STATE)
        ck("A %s: the journey played and ended%s (%s)" % (lab, ", with taps all over the cutscene and the app sent away and back in the middle of it" if cls == "academy" else "", s1["phases"]),
           ok and s1["journeys"] == 1 and (cls != "academy" or s1["hidden"] == 1), s1)
        a_cuts_ok(lab, s1, [rank])
        a_free(pg, lab)
        a_relaunch(pg)
        a_free(pg, lab + ", relaunched")
        ck("A %s: no page errors" % lab, not errs, errs[:3])
        ctx.close()
        # 2. two ranks owed, from Home: two journeys, a cutscene each, then nothing
        ctx, pg, errs = a_page(br, cls)
        rank2 = TIER_ORDER_FULL_KEYS[TIER_ORDER_FULL_KEYS.index(rank) + 1]
        seed = pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": rank2, "mode": "owed", "owe": 2})
        lab = "%s, two ranks owed" % name
        pg.evaluate("()=>{ showHome(); }")
        st, ok = a_drive(pg, 320, {}, until=lambda s: s["j"] >= 2 and s["c"] >= 2 and journey_over(s))
        a_drive(pg, 3, {})
        s2 = pg.evaluate(STATE)
        ck("A %s (%s): Home called twice and two journeys played, then it stopped" % (lab, seed["owed"]), ok and s2["journeys"] == 2, s2)
        a_cuts_ok(lab, s2, [rank, rank2])
        a_free(pg, lab)
        ck("A %s: no page errors" % lab, not errs, errs[:3])
        ctx.close()
        if cls != "academy":
            continue
        # 3. closed in the middle of the cutscene: on the next launch the rest plays - the cutscene once more - and that's all
        ctx, pg, errs = a_page(br, cls)
        pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": rank, "mode": "owed", "owe": 1})
        lab = "%s, relaunched mid-cutscene" % name
        pg.evaluate("()=>{ showProfile(); }")
        st, ok = a_drive(pg, 120, {}, until=lambda s: s["cut"])
        a_drive(pg, 5, {})
        s3a = pg.evaluate(STATE)
        ck("A %s: the cutscene was up when the app closed" % lab, ok and len(s3a["cuts"]) == 1 and s3a["ends"] == 0, s3a)
        a_relaunch(pg)
        pg.evaluate("()=>{ showHome(); }")
        st, ok = a_drive(pg, 200, {}, until=lambda s: s["j"] >= 1 and s["c"] >= 1 and journey_over(s))
        a_drive(pg, 3, {})
        s3 = pg.evaluate(STATE)
        ck("A %s: next launch, the journey plays the rest once and ends" % lab, ok and s3["journeys"] == 1, s3)
        a_cuts_ok(lab, s3, [rank])
        a_free(pg, lab)
        a_relaunch(pg)
        a_free(pg, lab + ", and relaunched again")
        ck("A %s: no page errors" % lab, not errs, errs[:3])
        ctx.close()
    br.close()


TIER_ORDER_FULL_KEYS = ["rookie", "ranger", "veteran", "vanguard", "adept", "elite", "titan"]


# ---------------------------------------------------------------- E: the XP box's foot
EREAD = r"""() => { const x = document.querySelector('.rs-xp'), w = x && x.querySelector('.results-level'); if(!w) return null;
  const R = el => { if(!el) return null; const b = el.getBoundingClientRect(); return b.width || b.height ? [b.left, b.top, b.right, b.bottom] : null; };
  const vis = el => !!el && getComputedStyle(el).display !== 'none' && getComputedStyle(el).visibility !== 'hidden' && (el.textContent || '').trim() !== '';
  const nx = w.querySelector('.results-level-next');
  const fs = el => el ? parseFloat(getComputedStyle(el).fontSize) : 0;
  const kids = [...w.querySelectorAll('*')].filter(e => e.closest('svg') === null || e.tagName.toLowerCase() === 'svg').map(R).filter(Boolean);
  return { card: R(x), foot: R(w), av: R(w.querySelector('.results-level-avatar')), lvl: R(w.querySelector('.results-level-num')),
    rank: R(w.querySelector('.results-level-rank')), bar: R(w.querySelector('.results-level-track')), line: R(w.querySelector('.results-level-line')),
    next: vis(nx) ? R(nx) : null, nextText: nx ? nx.textContent.trim() : null, lvlText: (w.querySelector('.results-level-num') || {}).textContent,
    border: parseFloat(getComputedStyle(w).borderTopWidth) || 0, total: R(x.querySelector('.rs-xptotal')),
    fsLine: fs(w.querySelector('.results-level-line')), fsNext: fs(nx), fsRank: fs(w.querySelector('.results-level-rank')), kids,
    sw: document.documentElement.scrollWidth, vw: innerWidth }; }"""


def section_e(pw):
    br = pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    for cls in ("academy", "ifc"):
        for sz, (w, h) in (("an SE (320)", (320, 568)), ("a 17 Pro Max", (440, 956)), ("an iPad Pro 11\"", (834, 1194)), ("a laptop", (1440, 820))):
            ctx, pg, errs = open_page(br, cls, w, h)
            pg.evaluate("()=>{ theme.reduceMotion = true; applyTheme(); }")
            pg.evaluate(RUN, [12, 10, None])
            pg.wait_for_timeout(1500)
            pg.evaluate("()=>{ document.querySelector('.rs-xp')?.scrollIntoView({ block: 'center', behavior: 'instant' }); }")
            pg.wait_for_timeout(400)
            m = pg.evaluate(EREAD)
            ctx.close()
            lab = "%s, %s" % ("Fire Code" if cls == "ifc" else "academy", sz)
            if not m or not m["av"] or not m["bar"]:
                ck("E %s: the XP box's foot is there" % lab, False, m)
                continue
            col = m["lvl"][0]
            same = [k for k in ("rank", "bar", "line") if m[k] and abs(m[k][0] - col) > 1.5]
            ck("E %s: the level, the rank, the bar and its numbers are one column beside the character (left edges %s)" % (lab, [round(m[k][0]) for k in ("lvl", "rank", "bar", "line") if m[k]]),
               not same and col >= m["av"][2] + 8, same)
            top, bot = m["lvl"][1], (m["next"] or m["line"])[3]
            mid = (m["av"][1] + m["av"][3]) / 2
            ck("E %s: the character sits level with that column (centre %d, column %d-%d)" % (lab, mid, top, bot), abs(mid - (top + bot) / 2) <= 14 or (m["av"][1] >= top - 2 and m["av"][3] <= bot + 2), (mid, top, bot))
            ck("E %s: set off from the total by a hairline (%.1fpx), below it" % (lab, m["border"]), m["border"] >= 1 and m["foot"][1] >= m["total"][3] - 1, (m["border"], m["foot"], m["total"]))
            if w > 352:
                lv = re.sub(r"\D", "", m["lvlText"] or "")
                ok = m["next"] and m["nextText"] == "Level %d" % (int(lv) + 1) and abs(m["next"][2] - m["bar"][2]) <= 1.5 and m["next"][0] >= m["line"][2] + 4 \
                    and abs(m["next"][1] - m["line"][1]) <= 3
                ck("E %s: where the bar is going (%r) at its right end, on the numbers' line, clear of them" % (lab, m["nextText"]), ok, m)
            else:
                ck("E %s: the numbers have the column to themselves on a narrow phone" % lab, not m["next"] and m["line"][2] <= m["foot"][2] + 1, m)
            card = m["card"]
            out = [k for k in m["kids"] if k[0] < card[0] - .5 or k[2] > card[2] + .5]
            ck("E %s: nothing in it leaves the card, no sideways scroll" % lab, not out and m["sw"] <= m["vw"], (out[:3], m["sw"], m["vw"]))
            ck("E %s: the numbers and the rank legible (%.1f, %.1f, %.1fpx)" % (lab, m["fsLine"], m["fsNext"], m["fsRank"]), m["fsLine"] >= 12 and m["fsRank"] >= 10.5 and (not m["next"] or m["fsNext"] >= 12), m)
            ck("E %s: no page errors" % lab, not errs, errs[:3])
    br.close()


# ---------------------------------------------------------------- main (sections are appended above this line)
SIZES = {"phone": (440, 956), "ipad": (834, 1194), "laptop": (1440, 820)}
GRADE_CASES = [
    ("academy, phone, 10 of 12", "academy", "phone", 12, 10, None),
    ("Fire Code, phone, 10 of 12", "ifc", "phone", 12, 10, None),
    ("academy, iPad, 9 of 12", "academy", "ipad", 12, 9, None),
    ("Fire Code, laptop, 10 of 12", "ifc", "laptop", 12, 10, None),
    ("academy, phone, 7 of 10 (turns as it lands)", "academy", "phone", 10, 7, None),
    ("academy, phone, 6 of 12 (a fail)", "academy", "phone", 12, 6, None),
    ("Fire Code, phone, 12 of 12 (a 100)", "ifc", "phone", 12, 12, None),
]


def main():
    with sync_playwright() as pw:
        if "A" in ONLY and "section_a" in globals():
            print("\n  A. the rank-up cutscene: only in the journey, once a rank, and it always ends")
            section_a(pw)
        if "B" in ONLY and "section_b" in globals():
            print("\n  B. the planet changes colour smoothly")
            section_b(pw)
        if ("C" in ONLY or "D" in ONLY):
            cases = [c for c in GRADE_CASES if not os.environ.get("CASES") or any(k in c[0] for k in os.environ["CASES"].split(","))]
            got = []
            for lab, cls, sz, n, good, fx in cases:
                got.append(grade_case(pw, lab, cls, SIZES[sz], n, good, fx))
            if "C" in ONLY:
                print("\n  C. the words under the grade never come before its numbers")
                for c in got:
                    if c["good"] < c["n"] or True:
                        section_c(c)
            if "D" in ONLY:
                print("\n  D. red into green: smooth, and no other colour")
                for c in got:
                    section_d(c)
        if "E" in ONLY and "section_e" in globals():
            print("\n  E. the XP box's foot")
            section_e(pw)
    print("\n%s (%d failed)" % ("ALL PASS" if not FAILS else "FAILURES", len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
