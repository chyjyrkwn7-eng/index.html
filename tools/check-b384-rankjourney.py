#!/usr/bin/env python3
"""Build 384.55: the rank-up journey - aligned, smooth, faster, and it ends on Home.

  python3 tools/check-b384-rankjourney.py [--against FILE|REV] [--only A,B,C,D,E,F,G] [--cpu 4]

Madison (he/him), on a frame of the road map in the rank-up cutscene: "The rank up cutscene, the stuff isn't lined up right as
you can tell." / "Also, the entire cutscene was a smidge laggy." / "Let's try to speed up the beginning of it slightly, the
part after you hit the profile tab to trigger it." / "Ensure the rank ladder part isn't laggy and is good to go. I saw a good
amount of chopped parts." / "After it finishes the rank ladder part, make it go to Home Screen automatically instead of back
to Profile, and on Home Screen that's where it will show the rank up reward pops." / "When the profile shakes saying you gotta
click it, ensure that isn't laggy and it's smooth because it did seem a bit non smooth."

  A. THE SETTLED LADDER IS EXACT. Every stop of the road map (all seven ranks, the Up next and locked ones too), at a phone, a
     bigger phone, an iPad and an iPad Pro: each circle's centre on the road's centre (0.5px) and on the middle of its stop; each
     card's top on its circle's top, one rule for every rank; the two gaps between a circle and its card equal; and the same
     again with a card that asks for far more room than it has (a long unbreakable name, wide chips): the circles do not move.
     (This guards what must not change: the settled map was exact (0.01px) in Chromium before this build too. What he saw is
     not the settled map - see B.)
  B. NOTHING ON THE MAP IS SCALED OR OFF IT WHILE IT PLAYS. The journey on the page's clock, a frame every 1/30s from the map's
     first frame to the cutscene: no element the map is inside carries a scale, translate or rotate (the screen came up out of
     the dark as scale(1.045) -> 1, which is what his frame caught: the road at 50% of the screen and the circles' centres 4-6pt
     to the right of it), every circle's centre is on the road's (1px; a circle that is shaking by design is excused for that
     frame), and each card's top is its circle's (1px; the Up next box's own lift excused). Phone and iPad.
  C. THE JOURNEY ENDS ON HOME, AND THE REWARDS ARE GIVEN THERE. A real run that ranks up, an account whose rank rewards are
     all still unannounced: from the Profile tap the journey plays the ladder, the cutscene, goes to Home (data-screen "home",
     the ladder's rank counted shown only after), the rank's reward card is up on Home, it cannot be tapped away before
     1.6s, it counts as shown only once it has been up (unlocksShown), once and in order (theme / flare / character / banner on
     one card), the rank is counted shown after the card, Profile is never mounted during the journey, and nothing is
     owed afterwards. The app sent to the background in the middle of the cards: nothing plays twice and nothing is lost
     (a journey closed in the cards plays them again once, then never). "Skip celebrations and pop-ups" skips the card, counts
     it shown, and still lands on Home. Both classes.
  D. THE START IS SHORTER. From the Profile tap to the road map's first frame, on the page's own clock: at least 20% shorter
     than the build it is measured against (origin/main unless --against); the numbers are printed.
  E. IT IS COMPOSITOR WORK AND IT PACES. (1) The Profile tab's shake: the animations on the tab are transform and opacity only (not a
     box-shadow), on the tab's picture and a ring, not on the whole button; a nudge adds nothing to the page (a node added
     re-checks every :has() rule, ~35ms). (2) The ladder's animations (the map, the light, the circles, the cards) are
     transform / opacity only. (3) The ride's loop reads nothing it does not have to (no geometry read per frame: counted).
     (4) Real time, 4x CPU, a Home just opened, alternated with the baseline in the same minutes (the sandbox is shared: its load
     moves absolute frame times 3x), best of two each: the road map's ride has a mean frame at most 90% of the baseline's and no
     larger a share of frames over 33ms (384.48 ~45-110ms, 71-83% over; the flip-book recorders do not run in the journey).
  G. THE SPIN IS ONE SMOOTH CURVE (the cutscene's whirl): it leaves at ~0 deg/s (384.48: 166, a step on the first frame), is ONE
     transform animation on the orbit for the whole 12.6s (not two swapped), its speed only rises to the peak and only falls
     after it, no change of speed over 3% of the top between two 40ms samples, little corner at the peak, whole turns; the new
     planet's orbit (not seen until the flash) does not spin.
  F. REDUCE MOTION. The shake and its ring do not animate, the journey still lands on Home with the card and counts it shown.
  G. NO PAGE ERRORS in any of it.

Fails on 384.48 (origin/main) in B, C, D, E, F, G; A guards what has to stay.
"""
import json, math, os, re, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from b384_rankjourney_lib import *  # noqa: E402,F401

ROOT_ = ROOT


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


ONLY = set((arg("--only") or "A,B,C,D,E,F,G").split(","))
CPU = int(arg("--cpu") or 4)
AGAINST = arg("--against")
if AGAINST and not os.path.exists(AGAINST):
    # a git revision: its index.html
    tmp = os.path.join(tempfile.mkdtemp(), "index.html")
    open(tmp, "wb").write(subprocess.check_output(["git", "show", "%s:index.html" % AGAINST], cwd=ROOT_))
    AGAINST = tmp
SELF = Served(AGAINST)
FAILS = []
_BUF = None


def ck(name, ok, info=None):
    line = ("  PASS  " if ok else "  FAIL  ") + name + ("" if ok or info is None else "  -> " + str(info)[:600])
    if _BUF is not None:
        _BUF.append((line, ok, name))
        return
    print(line, flush=True)
    if not ok:
        FAILS.append(name)


def case(fn, *a, tries=6):
    """one self-contained case (its own browser): the sandbox's chromium now and then crashes a tab, so a case that dies on
    'crashed' / 'closed' is run again from the start and only the run that finished is reported"""
    global _BUF
    last = None
    for _ in range(tries):
        _BUF = []
        try:
            fn(*a)
            buf, _BUF = _BUF, None
            for line, ok, name in buf:
                print(line, flush=True)
                if not ok:
                    FAILS.append(name)
            return
        except Exception as e:
            last = e
            _BUF = None
            if not re.search(r"crash|closed|Target", str(e)):
                raise
    raise last


def launch(pw):
    return pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox", "--disable-dev-shm-usage"])


def page(br, served, cls="academy", w=440, h=956, dpr=1, clock=False, retries=3):
    last = None
    for _ in range(retries):
        try:
            return open_page(br, served, cls, w, h, dpr, clock)
        except Exception as e:  # a crashed tab on load: the sandbox's chromium does that now and then
            last = e
    raise last




# ---------------------------------------------------------------- A: the settled ladder
GEO = r"""() => {
  const rc = el => { const b = el.getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; };
  const out = [];
  document.querySelectorAll('.rankmap-stop').forEach((s, i) => {
    const n = s.querySelector('.rankmap-node'), c = s.querySelector('.rankmap-card'), rd = s.querySelector('.rankmap-road');
    const sb = rc(s), nb = rc(n), cb = rc(c), rb = rd ? rc(rd) : null, left = s.classList.contains('is-left');
    const ncx = nb[0] + nb[2] / 2;
    out.push({ i, left, cls: s.className.replace('rankmap-stop ', ''), nodeVsRoad: rb ? ncx - (rb[0] + rb[2] / 2) : null, nodeVsStop: ncx - (sb[0] + sb[2] / 2),
      cardTop: cb[1] - nb[1], gap: left ? nb[0] - (cb[0] + cb[2]) : cb[0] - (nb[0] + nb[2]), cw: cb[2] });
  });
  const mp = document.querySelector('.rankmap'), st = document.querySelector('.rankmap-stops');
  return { rows: out, mapW: rc(mp)[2], stopsW: rc(st)[2], docW: document.documentElement.scrollWidth, vw: innerWidth }; }"""
STRESS = [("", ""), ("a long unbreakable name", ".rankmap-name{white-space:nowrap} .rankmap-name::after{content:'MMMMMMMMMMMMMMMMMMMM'}"),
          ("wide chips", ".rankmap-gift{min-width:230px}")]


def a_case(pw, w, h, lab, stress, css, rank):
    br = launch(pw)
    ctx, pg, errs = page(br, SELF, "academy", w, h)
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": rank, "mode": "owed", "owe": 1})
    pg.evaluate("()=>{ showRanksScreen('ranks'); }")
    pg.wait_for_timeout(1200)
    if css:
        pg.evaluate("(c)=>{ const s = document.createElement('style'); s.textContent = c; document.body.appendChild(s); }", css)
        pg.wait_for_timeout(250)
    g = pg.evaluate(GEO)
    rows = g["rows"]
    road = [r["nodeVsRoad"] for r in rows if r["nodeVsRoad"] is not None]
    lab2 = "%s, %s%s" % (lab, "an account at " + RANK_NAME[rank], " + " + stress if stress else "")
    ck("A %s: all %d circles are on the road's centre (worst %.2fpx) and the middle of their stop (worst %.2fpx)" % (
       lab2, len(rows), max(abs(x) for x in road), max(abs(r["nodeVsStop"]) for r in rows)),
       len(rows) == 7 and max(abs(x) for x in road) <= .5 and max(abs(r["nodeVsStop"]) for r in rows) <= .5, rows)
    ck("A %s: every card's top is its circle's top (worst %.2fpx), both gaps equal (%s)" % (
       lab2, max(abs(r["cardTop"]) for r in rows), sorted(set(round(r["gap"], 1) for r in rows))),
       max(abs(r["cardTop"]) for r in rows) <= .5 and max(r["gap"] for r in rows) - min(r["gap"] for r in rows) <= .5, rows)
    ck("A %s: the stops are the map's width (%.1f of %.1f)" % (lab2, g["stopsW"], g["mapW"]), abs(g["stopsW"] - g["mapW"]) <= .5, g)
    ck("A %s: no page errors" % lab2, not errs, errs[:3])
    ctx.close(); br.close()


RANK_NAME = {"rookie": "no rank yet (Bronze next)", "titan": "Supernova (all seven reached)"}


def section_a(pw):
    for w, h, lab in [(393, 852, "iPhone 15"), (440, 956, "iPhone 17 Pro Max"), (834, 1194, "iPad Pro 11"), (1024, 1366, "iPad Pro 12.9")]:
        for stress, css in STRESS:
            if stress and w > 440:
                continue
            for rank in (("titan", "rookie") if not stress and w == 440 else ("titan",)):
                case(a_case, pw, w, h, lab, stress, css, rank)


# ---------------------------------------------------------------- the journey on the page's clock
INSTR = r"""() => {
  if(window.__rj) return true;
  const J = window.__rj = { tl: [], spots: [], marks: [], shownAt: null, screens: [], profile: 0 };
  const t0 = () => Math.round(performance.now());
  let lastPh = null, lastShown = rankUpShownCount(), lastUS = JSON.stringify((store.unlocksShown || {}).chars || []) + JSON.stringify((store.unlocksShown || {}).banners || []);
  const scr = () => { const f = stage.firstElementChild; return f ? f.className.split(' ').slice(0, 2).join('.') : null; };
  window.__rjtick = () => {
    const ph = rankUpScene ? rankUpScene.phase : null;
    if(ph !== lastPh){ J.tl.push([t0(), 'phase', ph, scr()]); lastPh = ph; }
    const sh = rankUpShownCount();
    if(sh !== lastShown){ J.tl.push([t0(), 'rankUpShown', sh, !!stage.querySelector('[data-screen="home"]')]); lastShown = sh; J.shownAt = t0(); }
    const us = JSON.stringify((store.unlocksShown || {}).chars || []) + JSON.stringify((store.unlocksShown || {}).banners || []);
    if(us !== lastUS){ J.marks.push([t0(), 'unlocksShown', !!stage.querySelector('[data-screen="home"]'), document.querySelectorAll('.rs-spot').length]); lastUS = us; }
    document.querySelectorAll('.rs-spot').forEach(sp => { if(!sp.__j){ sp.__j = 1; J.spots.push({ t: t0(), kind: sp.className.replace('rs-spot ', ''), home: !!stage.querySelector('[data-screen="home"]'), screen: scr(), phase: rankUpScene ? rankUpScene.phase : null }); } });
  };
  new MutationObserver(() => { const f = stage.firstElementChild; J.screens.push([t0(), scr()]); if(f && f.classList.contains('screen-profile') && !f.classList.contains('screen-ranks')) J.profile++; }).observe(stage, { childList: true });
  return true; }"""
PUMP = r"""(o) => {
  window.__rjtick();
  const J = window.__rj, now = performance.now();
  /* what a person does: reads Nova's words, taps a reward card once it has been up a while (or at once, to try the 1.6s) */
  const sp = document.querySelector('.rs-spot.is-up');
  if(sp){
    if(!sp.__t0) sp.__t0 = now;
    if(o.hurry && !sp.__h){ sp.__h = 1; sp.__tapAt = now; sp.click(); }
    if(o.hurry && sp.__tapAt && now - sp.__tapAt > 1500 && !sp.__chk){ sp.__chk = 1; J.hurry = J.hurry || []; J.hurry.push({ stillUp1500: sp.isConnected && sp.classList.contains('is-up') }); }
    if(now - sp.__t0 > (o.hold || 2700)) sp.click();
  }
  for(const id of ['nova-rank', 'nova-intro']){ const el = document.getElementById(id); if(el && el.__nova){ const n = el.__nova;
    if(!el.__t0) el.__t0 = now; if(now - el.__t0 > 900){ el.__t0 = now; if(n.typing) n.advance(); else if(n.index < n.count - 1) n.advance(); else { const g = el.querySelector('.nt-go'); if(g) g.click(); } } } }
  if(document.body.classList.contains('rankup-lock') && stage.querySelector('[data-screen="home"]') && !rankUpScene){
    if(!J.lockAt) J.lockAt = now;
    if(now - J.lockAt > 2500 && !J.tapped){ J.tapped = now; document.getElementById('bottomtab-profile')?.click(); }
  }
  if(o.bg && rankUpScene && rankUpScene.phase === 'cards' && !J.bg){ J.bg = 1;
    Object.defineProperty(document, 'hidden', { configurable: true, get(){ return true; } });
    Object.defineProperty(document, 'visibilityState', { configurable: true, get(){ return 'hidden'; } });
    document.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('pagehide')); J.bgAt = now; }
  if(J.bg === 1 && now - J.bgAt > 4000){ J.bg = 2; delete document.hidden; delete document.visibilityState;
    document.dispatchEvent(new Event('visibilitychange')); window.dispatchEvent(new Event('pageshow')); }
  return { scene: !!rankUpScene, phase: rankUpScene ? rankUpScene.phase : null, spot: !!sp, owed: !!rankUpOwed(), lock: document.body.classList.contains('rankup-lock'),
    home: !!stage.querySelector('[data-screen="home"]'), cut: !!document.getElementById('supernova-cutscene'), tapped: J.tapped || 0 }; }"""


def drive(pg, secs, o=None, until=None, ms=100):
    st = None
    for _ in range(int(secs * 1000 / ms)):
        step(pg, ms)
        st = pg.evaluate(PUMP, o or {})
        if until and until(st):
            return st, True
    return st, False


def journey_setup(br, cls="academy", w=440, h=956, rank="rookie", fresh=True, mute=False, reduce=False):
    ctx, pg, errs = page(br, SELF, cls, w, h, clock=True)
    pg.evaluate("(a)=>{ theme.muteBanners = a.mute; theme.reduceMotion = a.reduce; applyTheme(); }", {"mute": mute, "reduce": reduce})
    seed = pg.evaluate(SEED_A, {"topic": TOPIC[cls], "rank": rank, "mode": "owed", "owe": 1, "fresh": fresh})
    pg.evaluate(INSTR)
    return ctx, pg, errs, seed


def done(s):
    return not s["scene"] and not s["spot"] and not s["owed"] and not s["cut"] and s["tapped"]


# ---------------------------------------------------------------- B: nothing is scaled, nothing is off, while it plays
SAMPLE_B = r"""() => {
  const rc = el => { const b = el.getBoundingClientRect(); return [b.left, b.top, b.width, b.height]; };
  const map = document.querySelector('.rankmap');
  if(!map) return null;
  const tf = [];
  for(let e = map; e && e !== document.documentElement; e = e.parentElement){
    const c = getComputedStyle(e);
    const m = c.transform;
    let scaled = false;
    if(m && m !== 'none'){ const v = m.match(/matrix\(([^)]+)\)/); if(v){ const a = v[1].split(',').map(Number); scaled = Math.abs(a[0] - 1) > .0005 || Math.abs(a[3] - 1) > .0005 || Math.abs(a[1]) > .0005 || Math.abs(a[2]) > .0005; } else scaled = true; }
    if(scaled || (c.scale && c.scale !== 'none') || (c.rotate && c.rotate !== 'none')) tf.push((e.className || e.tagName).toString().split(' ').slice(0, 2).join('.') + ' ' + m);
  }
  const rows = [];
  document.querySelectorAll('.rankmap-stop').forEach((s, i) => {
    const n = s.querySelector('.rankmap-node'), c = s.querySelector('.rankmap-card'), rd = s.querySelector('.rankmap-road');
    if(!n || !c) return;
    const nb = rc(n), cb = rc(c), rb = rd ? rc(rd) : null;
    const shaking = n.classList.contains('ru-shake') || n.classList.contains('is-popping') || s.classList.contains('is-celebrating') || s.classList.contains('ru-ghost');
    const lifting = s.classList.contains('ru-nextpop');
    rows.push({ i, off: rb ? (nb[0] + nb[2] / 2) - (rb[0] + rb[2] / 2) : null, top: cb[1] - nb[1], shaking, lifting, w: nb[2] });
  });
  return { ph: rankUpScene ? rankUpScene.phase : null, tf, rows }; }"""


def b_case(pw, w, h, lab):
    br = launch(pw)
    ctx, pg, errs, seed = journey_setup(br, "academy", w, h, fresh=False)
    # a phone where `#stage > *{animation:none}` does not take (his frame fits one): the map's own entrance runs there; Chromium
    # never plays it, so it is let play here
    pg.evaluate("() => { const s = document.createElement('style'); s.textContent = 'html body #stage > .screen-ranks.ru-mapin{ animation:ru-mapin 1.25s cubic-bezier(.2,.75,.25,1) backwards !important; }'; document.body.appendChild(s); }")
    pg.evaluate("()=>{ showHome(); }")
    st, ok = drive(pg, 60, {}, until=lambda s: s["phase"] in ("map", "road"), ms=33)
    samples = []
    for _ in range(int(11000 / (1000 / 30))):
        step(pg, 1000 / 30)
        pg.evaluate(PUMP, {})
        r = pg.evaluate(SAMPLE_B)
        if r is None:
            continue
        samples.append(r)
        if r["ph"] in ("handoff", "cutscene"):
            break
    kf = pg.evaluate("() => { const out = []; for(const sh of document.styleSheets){ let rules; try{ rules = sh.cssRules; }catch(e){ continue; } for(const r of rules){ if(r.type === 7 && r.name === 'ru-mapin') out.push(r.cssText.replace(/\\s+/g, ' ')); } } return out; }")
    ck("B %s: the map's entrance keyframes (ru-mapin) move nothing but opacity (%s)" % (lab, (kf or ['?'])[0][:90]), kf and not re.search(r"transform|scale|translate|rotate", " ".join(kf)), kf)
    scaled = [(s["ph"], s["tf"]) for s in samples if s["tf"]]
    ck("B %s: %d frames of the map, from its first frame to the hand-off: nothing it is inside is scaled, moved or turned (%s)" % (
       lab, len(samples), scaled[0] if scaled else "none"), len(samples) > 60 and not scaled, scaled[:2])
    off = [(s["ph"], r["i"], round(r["off"], 2)) for s in samples for r in s["rows"] if r["off"] is not None and not r["shaking"] and abs(r["off"]) > 1]
    ck("B %s: every circle stays on the road (1px; a circle shaking by design excused)%s" % (lab, "" if not off else " - worst " + str(off[0])), not off, off[:3])
    topoff = [(s["ph"], r["i"], round(r["top"], 2)) for s in samples for r in s["rows"] if abs(r["top"]) > 1 and not r["lifting"] and not r["shaking"]]
    ck("B %s: every card's top stays on its circle's top (1px; the Up next lift excused)" % lab, not topoff, topoff[:3])
    szs = [r["w"] for s in samples for r in s["rows"] if not r["shaking"]]
    ck("B %s: no circle changes size while it plays (%.1f-%.1f)" % (lab, min(szs), max(szs)), max(szs) - min(szs) <= 1.0, (min(szs), max(szs)))
    ck("B %s: no page errors" % lab, not errs, errs[:3])
    ctx.close(); br.close()


def section_b(pw):
    for w, h, lab in [(440, 956, "phone"), (834, 1194, "iPad")]:
        case(b_case, pw, w, h, lab)


# ---------------------------------------------------------------- C: it ends on Home, and the rewards are given there
FINAL = r"""() => ({ tl: __rj.tl, spots: __rj.spots, marks: __rj.marks, hurry: __rj.hurry || [], profile: __rj.profile, owed: !!rankUpOwed(), shown: rankUpShownCount(),
  home: !!stage.querySelector('[data-screen="home"]'), tabs: !!document.querySelector('.bottomtabs') && getComputedStyle(document.querySelector('.bottomtabs')).visibility !== 'hidden',
  lock: document.body.classList.contains('rankup-lock'), chars: ((store.unlocksShown || {}).chars || []).length, banners: ((store.unlocksShown || {}).banners || []).length,
  left: !!document.querySelector('.ru-blocker, .ru-curtain.is-on, .ru-veil, #supernova-cutscene, .rs-spot'), bg: __rj.bg || 0 })"""
BEFORE = r"""() => ({ chars: ((store.unlocksShown || {}).chars || []).length, banners: ((store.unlocksShown || {}).banners || []).length, shown: rankUpShownCount(),
  parts: rankRewardParts(TIER_ORDER_FULL[rankUpOwed().toIdx]).map(p => p.kind) })"""


def c_case(pw, cls):
    br = launch(pw)
    name = "Fire Code" if cls == "ifc" else "academy"
    ctx, pg, errs, seed = journey_setup(br, cls, 440, 956, rank="rookie", fresh=True)
    before = pg.evaluate(BEFORE)
    pg.evaluate("()=>{ showHome(); }")
    st, ok = drive(pg, 330, {"hurry": cls == "academy"}, until=done)
    drive(pg, 4, {})
    J = pg.evaluate(FINAL)
    ph = [x for x in J["tl"] if x[1] == "phase"]
    names = [x[2] for x in ph]
    ck("C %s: the journey played to the end and nothing is owed (%s)" % (name, " > ".join(str(n) for n in names)), ok and not J["owed"] and J["shown"] == before["shown"] + 1, J)
    ck("C %s: after the ladder's last step (the card at the top) the journey goes Home - not back to Profile: %s" % (name, names[-4:]),
       "hero" in names and "home" in names and names.index("hero") < names.index("home") and "back" not in names and "return" not in names, names)
    ck("C %s: it ends on Home (data-screen home), the tab bar is back, Home is not locked, nothing of the journey is left" % name, J["home"] and J["tabs"] and not J["lock"] and not J["left"], J)
    ck("C %s: Profile was mounted once in all - by the tap that started it - and not again at the end (%d)" % (name, J["profile"]), J["profile"] == 1, J["profile"])
    sp = [s for s in J["spots"] if "rankrewards" in s["kind"]]
    other = [s["kind"] for s in J["spots"] if "rankrewards" not in s["kind"]]
    ck("C %s: the rank's reward card (%s) was given on Home, by the journey, after it had gone there (%s)" % (name, "+".join(before["parts"]), [(s["kind"].split()[0], s["home"], s["phase"]) for s in sp]),
       len(sp) == 1 and all(s["home"] and s["phase"] == "cards" for s in sp) and not other, J["spots"])
    first = sp[0]["t"] if sp else None
    ck("C %s: what it hands over counts as shown only after the card was up, never before it (card at %s, marks at %s; characters %d -> %d)" % (
       name, first, [m[0] for m in J["marks"]], before["chars"], J["chars"]),
       first is not None and J["marks"] and all(m[0] > first for m in J["marks"]) and J["chars"] > before["chars"] - (0 if True else 0), J)
    rs = [x for x in J["tl"] if x[1] == "rankUpShown"]
    ck("C %s: the rank is counted shown once, on Home, after the card (%s)" % (name, rs), len(rs) == 1 and rs[0][3] and first is not None and rs[0][0] > first, rs)
    if cls == "academy":
        hh = J["hurry"]
        ck("C %s: a card tapped the moment it is up is still up 1.5s later (%s)" % (name, hh), bool(hh) and all(h["stillUp1500"] for h in hh), hh)
    ck("C %s: no page errors" % name, not errs, errs[:3])
    ctx.close(); br.close()


def c_bg(pw):
    br = launch(pw)
    ctx, pg, errs, seed = journey_setup(br, "academy", 440, 956, fresh=True)
    pg.evaluate("()=>{ showHome(); }")
    st, ok = drive(pg, 330, {"bg": True, "hold": 4000}, until=done)
    drive(pg, 4, {})
    J = pg.evaluate(FINAL)
    sp = [s["kind"].split()[0] for s in J["spots"]]
    ck("C backgrounded in the cards: the journey carried on, each card once (%s), the rank counted shown once, nothing owed, on Home" % sp,
       ok and J["bg"] == 2 and len(sp) == 1 and not J["owed"] and J["home"] and len([x for x in J["tl"] if x[1] == "rankUpShown"]) == 1, J)
    ck("C backgrounded in the cards: no page errors", not errs, errs[:3])
    ctx.close(); br.close()


def c_closed(pw):
    """the app closed while the cards are up: the next launch owes the journey again, plays the cutscene no more, and gives the card once"""
    br = launch(pw)
    ctx, pg, errs, seed = journey_setup(br, "academy", 440, 956, fresh=True)
    pg.evaluate("()=>{ showHome(); }")
    st, ok = drive(pg, 330, {}, until=lambda s: s["phase"] == "cards" and s["spot"])
    drive(pg, 1.5, {})
    mid = pg.evaluate("()=>({ owed: !!rankUpOwed(), shown: rankUpShownCount(), spots: document.querySelectorAll('.rs-spot').length })")
    ck("C closed in the cards: the rank is still owed (nothing counted shown before the cards were given): %s" % mid, ok and mid["owed"], mid)
    pg.reload(); pg.wait_for_timeout(3200)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ __stub(); }catch(e){} theme.reduceMotion = false; theme.muteBanners = false; applyTheme(); }")
    pg.evaluate(CLOCK); pg.evaluate(INSTR)
    pg.evaluate("()=>{ window.__cuts = 0; const P = window.playRankUpScene; window.playRankUpScene = function(){ window.__cuts++; return P.apply(this, arguments); }; showHome(); }")
    st, ok2 = drive(pg, 330, {}, until=done)
    drive(pg, 4, {})
    J = pg.evaluate(FINAL)
    cuts = pg.evaluate("()=>window.__cuts")
    ck("C closed in the cards: the next launch plays the cutscene %d times (it had played), gives the card %d time(s) and ends on Home, owed no more" % (cuts, len([s for s in J["spots"] if 'rankrewards' in s["kind"]])),
       ok2 and cuts == 0 and len([s for s in J["spots"] if 'rankrewards' in s["kind"]]) == 1 and not J["owed"] and J["home"], J)
    ctx.close(); br.close()


def c_mute(pw):
    br = launch(pw)
    ctx, pg, errs, seed = journey_setup(br, "academy", 440, 956, fresh=True, mute=True)
    before = pg.evaluate(BEFORE)
    pg.evaluate("()=>{ showHome(); }")
    st, ok = drive(pg, 330, {}, until=done)
    drive(pg, 3, {})
    J = pg.evaluate(FINAL)
    ck("C Skip celebrations and pop-ups: no card (%d), what the rank hands over counted shown (characters %d -> %d), and it still lands on Home" % (len(J["spots"]), before["chars"], J["chars"]),
       ok and not J["spots"] and not J["owed"] and J["home"] and J["chars"] > before["chars"], J)
    ck("C Skip celebrations: no page errors", not errs, errs[:3])
    ctx.close(); br.close()


def section_c(pw):
    case(c_case, pw, "academy")
    case(c_case, pw, "ifc")
    case(c_bg, pw)
    case(c_closed, pw)
    case(c_mute, pw)


# ---------------------------------------------------------------- D: the start
def start_ms(pw, served):
    br = launch(pw)
    ctx, pg, errs = page(br, served, "academy", 440, 956, clock=True)
    pg.evaluate("(a)=>{ theme.muteBanners = false; theme.reduceMotion = false; applyTheme(); }", {})
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "rookie", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate("()=>{ window.__ph = []; setInterval(() => { const p = rankUpScene ? rankUpScene.phase : null; if(!window.__ph.length || window.__ph[window.__ph.length - 1][1] !== p) window.__ph.push([Math.round(performance.now()), p]); }, 16); showHome(); }")
    tap = None
    for _ in range(1200):
        step(pg, 50)
        s = pg.evaluate("()=>({ lock: document.body.classList.contains('rankup-lock'), sc: !!rankUpScene, ph: window.__ph })")
        if s["lock"] and not s["sc"] and tap is None:
            tap = pg.evaluate("()=>{ const t = Math.round(performance.now()); document.getElementById('bottomtab-profile').click(); return t; }")
        if tap is not None and any(p[1] == "road" for p in s["ph"] if p[0] >= tap):
            break
    ph = pg.evaluate("()=>window.__ph")
    first = lambda name: [p[0] for p in ph if p[1] == name and p[0] >= tap][0] - tap
    out = {"road": first("road"), "tick": first("tick"), "tomap": first("tomap"), "map": first("map")}
    ctx.close(); br.close()
    return out


def d_case(pw):
    base_src = arg("--baseline") or "origin/main"
    tmp = os.path.join(tempfile.mkdtemp(), "index.html")
    try:
        open(tmp, "wb").write(subprocess.check_output(["git", "show", "%s:index.html" % base_src], cwd=ROOT_, stderr=subprocess.DEVNULL))
        base = Served(tmp)
    except Exception:
        ck("D the baseline (git %s) could not be read" % base_src, False)
        return
    now = start_ms(pw, SELF)
    old = start_ms(pw, base)
    pct = 100.0 * (old["road"] - now["road"]) / old["road"]
    print("  D  tap -> the road map's first frame: %dms now, %dms on %s (%.1f%% shorter); the challenge rows %d -> %d, the dive %d -> %d" % (
        now["road"], old["road"], base_src, pct, old["tomap"] - old["tick"], now["tomap"] - now["tick"], old["road"] - old["tomap"], now["road"] - now["tomap"]))
    ck("D from the Profile tap to the road map's first frame is at least 20%% shorter than %s (%.1f%%)" % (base_src, pct), pct >= 20.0, (now, old))
    ck("D ...and not abrupt: the challenge rows still take at least 3s (%dms from the first tick to the dive)" % (now["tomap"] - now["tick"]), now["tomap"] - now["tick"] >= 3000, now)


def section_d(pw):
    case(d_case, pw)


# ---------------------------------------------------------------- E: compositor work, and it paces
ANIMS = r"""(sel) => {
  const root = document.querySelector(sel); if(!root) return null;
  const out = [];
  root.getAnimations({ subtree: true }).forEach(a => {
    if(a.playState === 'idle' || a.playState === 'finished') return;
    if(typeof CSSTransition !== 'undefined' && a instanceof CSSTransition) return;   /* a one-off colour change on one small box (a chip lighting, a card's rim) */
    let kf = []; try{ kf = a.effect.getKeyframes(); }catch(e){}
    const ps = new Set(); kf.forEach(k => Object.keys(k).forEach(p => { if(!['offset', 'computedOffset', 'easing', 'composite'].includes(p)) ps.add(p); }));
    const t = a.effect && a.effect.target;
    out.push({ n: a.animationName || a.transitionProperty || 'waapi', props: [...ps], tgt: t ? (t.id || (t.className && t.className.baseVal !== undefined ? t.className.baseVal : t.className) || t.tagName) : '?', pe: a.effect.pseudoElement || '' });
  });
  return out; }"""
OK_PROPS = {"transform", "opacity", "rotate", "scale", "translate"}


def wait_lock(pg):
    for _ in range(60):
        pg.wait_for_timeout(250)
        if pg.evaluate("()=>document.body.classList.contains('rankup-lock')"):
            break


def e_shake(pw):
    br = launch(pw)
    ctx, pg, errs = page(br, SELF, "academy", 440, 956, dpr=2)
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "rookie", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate("()=>{ showHome(); }")
    wait_lock(pg)
    pg.wait_for_timeout(2500)
    pg.evaluate("()=>{ window.__added = 0; new MutationObserver(ms => ms.forEach(m => { window.__added += m.addedNodes.length + m.removedNodes.length; })).observe(document.querySelector('.bottomtabs'), { childList: true, subtree: true }); }")
    ra = None
    for _ in range(5):
        pg.evaluate("()=>rankUpNudge()")
        pg.wait_for_timeout(250)
        if ra is None:
            ra = pg.evaluate(ANIMS, "#bottomtab-profile")
        pg.wait_for_timeout(1200)
    added = pg.evaluate("()=>window.__added")
    bad = [a for a in (ra or []) if not set(a["props"]) <= OK_PROPS]
    ck("E the Profile tab's shake runs %d animations (%s), all transform / opacity, none a box-shadow" % (len(ra or []), sorted(set(p for a in (ra or []) for p in a["props"]))), bool(ra) and not bad, bad or ra)
    whole = [a for a in (ra or []) if a["n"] == "ru-nudge" and "bottomtab-icon" not in str(a["tgt"])]
    ck("E the swing is on the tab's picture (its own layer), not the whole button with its label (%s)" % [a["tgt"] for a in (ra or [])], not whole and bool(ra), ra)
    ck("E five nudges added or removed %d nodes in the tab bar (a node added re-checks every :has() rule on the page: ~35ms)" % added, added == 0, added)
    ck("E no page errors (shake)", not errs, errs[:3])
    ctx.close(); br.close()


def e_ladder(pw):
    br = launch(pw)
    ctx, pg, errs, seed = journey_setup(br, "academy", 440, 956, rank="ranger", fresh=False)
    pg.evaluate("()=>{ showHome(); }")
    pg.evaluate("""()=>{ window.__reads = 0; const g = Element.prototype.getBoundingClientRect; Element.prototype.getBoundingClientRect = function(){ if(rankUpScene && rankUpScene.phase === 'road' && this.classList && this.classList.contains('rankmap-road')) window.__reads++; return g.apply(this, arguments); }; }""")
    st, ok = drive(pg, 60, {}, until=lambda s: s["phase"] == "road")
    ladder = []
    for _ in range(int(14000 / 100)):
        step(pg, 100)
        pg.evaluate(PUMP, {})
        a = pg.evaluate(ANIMS, ".screen-ranks")
        if a:
            ladder.extend(a)
        if pg.evaluate("()=>rankUpScene ? rankUpScene.phase : null") in ("handoff", "cutscene"):
            break
    reads = pg.evaluate("()=>window.__reads")
    props = sorted(set(p for a in ladder for p in a["props"]))
    bad = sorted(set((a["n"], tuple(a["props"])) for a in ladder if not set(a["props"]) <= OK_PROPS))
    ck("E the ladder: %d animations (not one-off transitions) seen on the road map (%s): transform / opacity only" % (len(ladder), props), bool(ladder) and not bad, bad[:6])
    ck("E the ride reads the road's box %d times in its whole run (once, then the same number every frame: a layout flush a frame on a page of 3,400 elements)" % reads, reads <= 12, reads)
    ck("E no page errors (ladder)", not errs, errs[:3])
    ctx.close(); br.close()


def pace_once(pw, served):
    br = launch(pw)
    ctx, pg, errs = page(br, served, "academy", 440, 956)
    cdp = ctx.new_cdp_session(pg)
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": False})
    fr, ev, lt, tap = run_journey(pg, cdp, CPU, home_wait=4, timeout=90, settle=0, stop_after="handoff")
    road = pacing(fr, lo=tap).get("road")
    ctx.close(); br.close()
    if not road:
        raise RuntimeError("the road map's ride was not seen (crash)")
    road["secs"] = sum(f["dt"] for f in fr if f["ph"] == "road" and f["t"] >= tap) / 1000.0
    return road, errs


def e_pace(pw):
    """real time, 4x CPU, a Home just opened. The sandbox is shared and its load changes the absolute numbers 3x, so the build is
    measured AGAINST the baseline (origin/main) in the same minutes, best of two each, alternating"""
    base_src = arg("--baseline") or "origin/main"
    tmp = os.path.join(tempfile.mkdtemp(), "index.html")
    try:
        open(tmp, "wb").write(subprocess.check_output(["git", "show", "%s:index.html" % base_src], cwd=ROOT_, stderr=subprocess.DEVNULL))
        base = Served(tmp)
    except Exception:
        ck("E the baseline (git %s) could not be read" % base_src, False)
        return
    mine, theirs, errs = [], [], []
    for _ in range(2):
        r, e = pace_once(pw, SELF); mine.append(r); errs += e
        r, e = pace_once(pw, base); theirs.append(r)
    m = min(mine, key=lambda r: r["mean"]); o = min(theirs, key=lambda r: r["mean"])
    print("  E  %dx CPU, the road map's ride (best of 2): %d frames in %.1fs, mean %.1fms, %.0f%% over 33ms - on %s: %d frames in %.1fs, mean %.1fms, %.0f%% over 33ms" % (
        CPU, m["n"], m["secs"], m["mean"], 100 * m["gt33"] / m["n"], base_src, o["n"], o["secs"], o["mean"], 100 * o["gt33"] / o["n"]))
    ck("E the road map's ride at %dx CPU, a Home just opened: mean frame %.1fms against %.1fms on %s (at most 90%% of it)" % (CPU, m["mean"], o["mean"], base_src), m["mean"] <= .9 * o["mean"], (m, o))
    ck("E ...and a share of frames over 33ms of %.0f%% against %.0f%%" % (100 * m["gt33"] / m["n"], 100 * o["gt33"] / o["n"]), m["gt33"] / m["n"] <= o["gt33"] / o["n"] + .02, (m, o))
    ck("E no page errors (real time)", not errs, errs[:3])


def section_e(pw):
    case(e_shake, pw)
    case(e_ladder, pw)
    case(e_pace, pw)


# ---------------------------------------------------------------- F: reduce motion
def f_shake(pw):
    br = launch(pw)
    ctx, pg, errs = page(br, SELF, "academy", 440, 956, dpr=2)
    pg.evaluate("()=>{ theme.reduceMotion = true; applyTheme(); }")
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "rookie", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate("()=>{ showHome(); }")
    wait_lock(pg)
    pg.evaluate("()=>rankUpNudge()")
    pg.wait_for_timeout(300)
    ra = pg.evaluate(ANIMS, "#bottomtab-profile")
    ck("F Reduce motion: the shake and its ring run no animation (%s)" % (ra,), not ra, ra)
    ctx.close(); br.close()


def f_journey(pw):
    br = launch(pw)
    ctx, pg, errs, seed = journey_setup(br, "academy", 440, 956, fresh=True, reduce=True)
    pg.evaluate("()=>{ showHome(); }")
    st, ok = drive(pg, 200, {}, until=done)
    drive(pg, 3, {})
    J = pg.evaluate(FINAL)
    sp = [(s["kind"].split()[0], s["home"]) for s in J["spots"]]
    ck("F Reduce motion: the journey still lands on Home, with the card (%s) given there and the rank counted shown" % (sp,),
       ok and J["home"] and not J["owed"] and len(sp) == 1 and all(s[1] for s in sp) and J["chars"] > 0, J)
    ck("F Reduce motion: no page errors", not errs, errs[:3])
    ctx.close(); br.close()


def section_f(pw):
    case(f_shake, pw)
    case(f_journey, pw)


# ---------------------------------------------------------------- G: the spin is one smooth curve
SPIN = r"""async (step) => {
  const ov = document.getElementById('supernova-cutscene');
  const orbit = ov.querySelector('.rank-before .rank-orbit'), orbitA = ov.querySelector('.rank-after .rank-orbit');
  const waapi = x => x.effect && x.effect.target && !(typeof CSSAnimation !== 'undefined' && x instanceof CSSAnimation) && !(typeof CSSTransition !== 'undefined' && x instanceof CSSTransition);
  const ans = document.getAnimations().filter(x => waapi(x) && x.effect.getComputedTiming().duration > 12000);
  const mine = ans.filter(x => x.effect.target === orbit && x.effect.getKeyframes().some(k => k.transform && k.transform !== 'none'));
  const after = document.getAnimations().filter(x => waapi(x) && orbitA && (x.effect.target === orbitA || orbitA.contains(x.effect.target)) && x.effect.getComputedTiming().duration > 12000 && x.effect.getKeyframes().some(k => k.transform && k.transform !== 'none'));
  const an = mine[0], total = an.effect.getComputedTiming().duration;
  document.getAnimations().forEach(x => { try{ x.pause(); }catch(e){} });
  const out = []; let prev = 0, acc = 0;
  for(let t = 0; t <= total; t += step){
    ans.forEach(x => { try{ x.currentTime = t; }catch(e){} });
    const m = getComputedStyle(orbit).transform; let ang = 0;
    if(m && m !== 'none'){ const v = m.match(/matrix\(([^)]+)\)/); const x = v[1].split(',').map(Number); ang = Math.atan2(x[1], x[0]) * 180 / Math.PI; }
    let d = ang - prev; while(d > 180) d -= 360; while(d < -180) d += 360;
    acc += d; prev = ang; out.push([t, acc]);
  }
  return { total, n: mine.length, after: after.length, kf: an.effect.getKeyframes().length, out }; }"""


def g_case(pw):
    br = launch(pw)
    ctx, pg, errs = page(br, SELF, "academy", 440, 956)
    pg.evaluate(SEED_A, {"topic": TOPIC["academy"], "rank": "ranger", "mode": "owed", "owe": 1, "fresh": False})
    pg.evaluate("()=>{ rankUpMarkShown(1); showHome(); }")
    pg.wait_for_timeout(5000)
    pg.evaluate("()=>{ playTierCutscene('ranger', { from: 'rookie', onDone: () => {} }); }")
    for _ in range(120):
        pg.wait_for_timeout(250)
        if pg.evaluate("()=>document.getElementById('supernova-cutscene')?.classList.contains('is-cutspin')"):
            break
    r = pg.evaluate(SPIN, 40)
    o = r["out"]
    v = [(o[i][0] / 1000, (o[i][1] - o[i - 1][1]) / ((o[i][0] - o[i - 1][0]) / 1000)) for i in range(1, len(o))]
    top = max(x[1] for x in v)
    pk = max(range(len(v)), key=lambda i: v[i][1])
    first = v[0][1]
    ck("G the whirl leaves at %.1f deg/s on its first frame (%.1f%% of its top speed of %.0f): no step in angular velocity" % (first, 100 * first / top, top), abs(first) < .03 * top, v[:3])
    ck("G it is ONE transform animation on the orbit for the whole %.1fs (%d of them, %d keys), and the new planet's orbit, which is not seen until the flash, has none (%d)" % (r["total"] / 1000, r["n"], r["kf"], r["after"]), r["n"] == 1 and r["after"] == 0, r)
    rise = all(v[i][1] >= v[i - 1][1] - .02 * top for i in range(1, pk + 1))
    fall = all(v[i][1] <= v[i - 1][1] + .02 * top for i in range(pk + 1, len(v)))
    ck("G the speed only rises to its peak (%.1fs) and only falls after it" % v[pk][0], rise and fall, v[pk])
    dv = max(abs(v[i][1] - v[i - 1][1]) for i in range(1, len(v)))
    ck("G the largest change of speed between two 40ms samples is %.0f deg/s (%.1f%% of the top speed)" % (dv, 100 * dv / top), dv < .03 * top, dv)
    w = 12
    a_before = (v[pk - 1][1] - v[pk - 1 - w][1]) / (v[pk - 1][0] - v[pk - 1 - w][0])
    a_after = (v[pk + 1 + w][1] - v[pk + 1][1]) / (v[pk + 1 + w][0] - v[pk + 1][0])
    ck("G little corner at the peak: the speed's rate of change over the half second either side is %.0f deg/s2 going in and %.0f coming out (a step of %.0f against %.0f for the top speed; a ramp that meets its peak is ~3x that)" % (a_before, a_after, abs(a_before - a_after), top), abs(a_before - a_after) < .13 * top, (a_before, a_after))
    ck("G it stops on a whole number of turns (%.2f), so the orbit ends where it started" % (o[-1][1] / 360), abs(o[-1][1] / 360 - round(o[-1][1] / 360)) < .01, o[-1])
    ck("G no page errors (spin)", not errs, errs[:3])
    ctx.close(); br.close()


def section_g(pw):
    case(g_case, pw)


def main():
    print("serving %s (build %s)" % (SELF.src, SELF.build))
    with sync_playwright() as pw:
        for key, title, fn in (("A", "the settled ladder is exact", section_a), ("B", "nothing on the map is scaled or off it while it plays", section_b),
                               ("C", "it ends on Home, and the rewards are given there", section_c), ("D", "the start is shorter", section_d),
                               ("E", "compositor work, and it paces", section_e), ("F", "reduce motion", section_f),
                               ("G", "the spin is one smooth curve", section_g)):
            if key in ONLY:
                print("\n  %s. %s" % (key, title))
                fn(pw)
    print("\n%s (%d failed)" % ("ALL PASS" if not FAILS else "FAILURES", len(FAILS)))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
