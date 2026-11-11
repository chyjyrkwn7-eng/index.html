#!/usr/bin/env python3
"""384.35: THE PLANET SYSTEM KEEPS MOVING WHILE THE BOTTOM TAB IS TOUCHED, AND A SLIDE LANDS LIKE A TAP.

Madison, on two 384.34 recordings (iPhone 17 Pro Max, installed app): "when you leave the app and come back, it's like the planet system
restarts and lags ... also the bottom tab, when using it, it freezes the planet system stuff"; and on a third: "tapping looks really good ...
swiping/sliding on the bottom tab is not good to go ... should be cohesive for all the tabs ... on home and profile the bubble is there longer
before it drops compared to the others".
What the recordings and this page say:
  - He pressed the bar and slid across it for 11s: Home's orbit changed in 0 frames of whole half-second windows (8-10.5s, 12.5, 14.5, 16.5).
    The page paused Home's hero (~39 of its 41 loops) a frame after the finger landed (barUnderPause, SLIDE_HOLD_SEL: builds 376-384 r15) and
    played them again when the glass landed. Home's hero is nowhere near the bar (hero 102-482px, bar 855-934px), so it was held for the
    frames' sake, not because it was behind the glass.
  - A slide let go over another tab held its glass up until that tab's screen had been drawn (lensHoldFor, build 382), so release to rest
    was the screen's build time: at 4x CPU the median was 776ms on Home, 467 Profile, 396 Calendar, 374 Leaderboard (a 400ms spread).
  - The return from the app switcher: dots where the card had them, nothing faded in, nothing restarted (read off the recordings); what
    differs is the frame rate after a long absence (59fps before, 44 in the first second back). The resume log now says how long it lasts.

Counted on the page (nothing typed as a label, no frame-time threshold except where the sandbox is made to stand in for a slower phone):
 (1) A PRESS THAT STAYS DOWN: for 1.2s on a tab, no animation of Home's hero is paused, none was paused by the page (Animation.pause calls on
     the hero: 0), the reference loop's pose advances with the clock, and the flare sheets (the 7 flip-books) are running.
 (2) A SLIDE ACROSS THE BAR (Home to the last tab and back, finger down for 2.5s): the same, the whole way; and the glass is the glass:
     the bar's backdrop blur is what it is at rest (not none: no DRAG_SOLID), the lens is up.
 (3) A TAP: the press, and the screen it brings in. Tapping Home from another tab, Home's hero is running from the frame it is built to the
     glass landing (nothing paused, nothing played again), and its loops' poses go on from the loop clock.
 (4) A SLIDE LANDS ON ITS OWN CLOCK, THE SAME FOR EVERY TAB (4x CPU, the sandbox standing in for a slow build): the glass is told to land
     with the release (median within PLAN_MS; it was told when the screen had been drawn: 160-820ms here), and the page's own plan for
     release-to-glass-gone is within SPREAD_MS across the four targets (Home, Profile, Leaderboard, Calendar; 377ms apart before).
 (5) AFTER A HIDE AND A SHOW nothing restarts: every loop that ran runs again, none is back at an earlier pose than it was left in, none was
     cancelled or made again, and the poses against the reference loop are what they were.
 (6) THE RETURN'S LINE IN THE RESUME LOG carries the frames drawn in each half second of the first 6s (q) and the first 24 gaps (g), so the
     next report says how long a slow return lasts.     (7) no page error.

  python3 tools/check-b384-planetfreeze.py [--against index.html|REV] [--cpu 4] [--quick]
Phone = iPhone 17 Pro Max installed 440x956 at 3x, academy, all seven bubbles on their moving sheets. Chromium has no iOS compositor: what it
shows is what the page asks of the animations and when it asks; whether the glass is smoother with Home running is the phone's to say.
Against the 384.34 file (the live copy) (1), (2), (3), (4) and (6) FAIL; (5) holds on both (it guards what must not change)."""
import json, os, re, statistics, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
head = open(os.path.join(HERE, "check-b384-resume.py")).read().split("def scenario(")[0]
G = {"__file__": os.path.join(HERE, "check-b384-resume.py"), "__name__": "rh"}
exec(compile(head, "resume-head", "exec"), G)
g, sync_playwright, UA, init_for, body_for, url, VIS, INSTR, chk = (G[k] for k in ("g", "sync_playwright", "UA", "init_for", "body_for", "url", "VIS", "INSTR", "chk"))
args = sys.argv[1:]
CPU = float(args[args.index("--cpu") + 1]) if "--cpu" in args else 4.0
QUICK = "--quick" in args
SPREAD_MS = 40          # the four targets' release-to-rest medians, at CPU slowdown (was ~400 on 384.34)
PLAN_MS = 80            # the glass is told to land this soon after the release, median (it was 160-820)

# what the page asks of the animations: pause() calls on Home's hero, counted from the moment this is installed
PAUSES = """(()=>{ const P = Animation.prototype, op = P.pause; window.__pz = { hero: 0, all: 0 };
  P.pause = function(){ try{ __pz.all++; const t = this.effect && this.effect.target; if(t && t.closest && t.closest('.cosmic-hero-wrap')) __pz.hero++; }catch(e){} return op.apply(this, arguments); }; })()"""
# the landing's own track: the lens's opacity fade that ends at 0 is planned as [1, 1, 0] over (hold + shrink) ms the moment the page decides to
# land, so when it was asked for + its length is when the glass is gone BY THE PAGE'S PLAN - which a long build on the main thread cannot move
LANDS = """(()=>{ const oa = Element.prototype.animate; window.__LA = [];
  Element.prototype.animate = function(kf, o){ try{ if(this.id === 'bottomtabs-lens' && Array.isArray(kf) && kf.length >= 2){ const last = kf[kf.length - 1].opacity; if(String(last) === '0') __LA.push([performance.now(), Number(o && o.duration)]); } }catch(e){} return oa.apply(this, arguments); }; })()"""
HERO = """()=>{ const hero = document.querySelector('#stage .cosmic-hero-wrap'); if(!hero) return null;
  const L = __M.loops().filter(a => { try{ return hero.contains(a.effect.target); }catch(e){ return false; } });
  const ref = L.find(a => a.animationName === 'cosmic-orbit-spin');
  return { n: L.length, running: L.filter(a => a.playState === 'running').length, paused: L.filter(a => a.playState === 'paused').length,
           flips: L.filter(a => a.playState === 'running' && a.effect.target.closest('.rk-frame')).length,
           ref: ref ? ref.currentTime : null, t: performance.now(), pz: window.__pz ? window.__pz.hero : -1 }; }"""
REC = """()=>{
 const bar = document.querySelector('.bottomtabs'), lens = document.getElementById('bottomtabs-lens'), st = document.getElementById('stage');
 const R = window.__R = { ev: [], op: [] };
 const now = () => performance.now();
 new MutationObserver(() => R.ev.push([now(), 'bar', bar.className])).observe(bar, { attributes: true, attributeFilter: ['class'] });
 addEventListener('pointerup', () => R.ev.push([now(), 'up']), true);
 addEventListener('pointerdown', () => R.ev.push([now(), 'down']), true);
 (function f(t){ try{ R.op.push([t, parseFloat(getComputedStyle(lens).opacity)]); }catch(e){} requestAnimationFrame(f); })(now());
}"""
def touch(cdp, typ, x=None, y=None):
    cdp.send("Input.dispatchTouchEvent", {"type": typ, "touchPoints": [] if x is None else [{"x": x, "y": y}]})

def open_home(br):
    w, h, dpr = 440, 956, 3
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA, reduced_motion="no-preference")
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    ctx.add_init_script(VIS); ctx.add_init_script(INSTR); ctx.add_init_script(PAUSES); ctx.add_init_script(LANDS)
    pg = ctx.new_page(); body = body_for((62, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(init_for(False))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(4000)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(300)
    pg.evaluate("()=>{ try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} }")
    t0 = time.time(); n = [0, 0]
    while time.time() - t0 < 240:
        pg.wait_for_timeout(3000)
        n = pg.evaluate("()=>[document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank').length, document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank > .cosmic-rank-anim').length]")
        if n[0] and n[1] >= n[0]: break
    pg.wait_for_timeout(2500)
    return ctx, pg, ctx.new_cdp_session(pg), errs, n

def tab_centres(pg):
    d = pg.evaluate("()=>{ const o = {}; document.querySelectorAll('.bottomtabs .bottomtab').forEach(t => { const r = t.getBoundingClientRect(); if(r.width > 0) o[t.id.replace('bottomtab-', '')] = [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; }); return o; }")
    return d

def sample(pg, ms, every=150):
    out = []; t0 = time.time()
    while (time.time() - t0) * 1000 < ms or len(out) < 6:     # a busy host can make one read slow: always at least six reads
        out.append(pg.evaluate(HERO)); pg.wait_for_timeout(every)
    return out

def advancing(S, label):
    """the reference loop's pose moves with the clock across the samples (>= 80% of the wall time between first and last)"""
    S = [s for s in S if s and s["ref"] is not None]
    if len(S) < 3: return False, "no reference loop"
    dpose = S[-1]["ref"] - S[0]["ref"]; dwall = S[-1]["t"] - S[0]["t"]
    return dpose >= 0.8 * dwall, "%s pose +%.0fms over %.0fms of clock" % (label, dpose, dwall)

def scenario(br):
    ctx, pg, cdp, errs, sheets = open_home(br)
    out = dict(errs=errs, sheets=sheets)
    tabs = tab_centres(pg); out["tabs"] = sorted(tabs)
    order = [t for t in ("home", "profile", "rewards", "calendar") if t in tabs]
    y = tabs["home"][1]
    pg.evaluate(REC)
    restBF = pg.evaluate("()=>{ const cs = getComputedStyle(document.querySelector('.bottomtabs')); return cs.backdropFilter || cs.webkitBackdropFilter || 'none'; }")
    out["restBF"] = restBF
    H0 = pg.evaluate(HERO); out["hero0"] = H0
    # (1) a press that stays down on Home's own tab
    touch(cdp, "touchStart", tabs["home"][0], y); pg.wait_for_timeout(250)
    S1 = sample(pg, 1200)
    glass1 = pg.evaluate("()=>{ const b = document.querySelector('.bottomtabs'), l = document.getElementById('bottomtabs-lens'); const cs = getComputedStyle(b); return { barLens: b.classList.contains('lens-up'), lensUp: l.classList.contains('is-up'), bf: cs.backdropFilter || cs.webkitBackdropFilter || 'none', solid: [...document.querySelectorAll('style')].some(s => /\\.bottomtabs\\.lens-up\\{backdrop-filter:none/.test(s.textContent)) }; }")
    touch(cdp, "touchEnd"); pg.wait_for_timeout(900)
    out["S1"] = S1; out["glass1"] = glass1
    # (2) a slide across the whole bar and back, finger down
    xa, xb = tabs[order[0]][0], tabs[order[-1]][0]
    touch(cdp, "touchStart", xa, y); pg.wait_for_timeout(120)
    S2 = []; glass2 = None
    for rep in range(2):
        for k in range(1, 21):
            ph = k / 20; x = xa + (xb - xa) * (ph if rep == 0 else 1 - ph)
            touch(cdp, "touchMove", x, y); pg.wait_for_timeout(30)
            if k % 5 == 0: S2.append(pg.evaluate(HERO))
        S2.extend(sample(pg, 500, 125))
        if glass2 is None:
            glass2 = pg.evaluate("()=>{ const b = document.querySelector('.bottomtabs'), l = document.getElementById('bottomtabs-lens'); const cs = getComputedStyle(b); return { barLens: b.classList.contains('lens-up'), lensUp: l.classList.contains('is-up'), dragging: document.documentElement.classList.contains('tab-dragging'), bf: cs.backdropFilter || cs.webkitBackdropFilter || 'none' }; }")
    touch(cdp, "touchEnd"); pg.wait_for_timeout(1200)
    out["S2"] = S2; out["glass2"] = glass2
    # land on Home again whatever the slide ended over
    for _ in range(2):
        touch(cdp, "touchStart", tabs["home"][0], y); pg.wait_for_timeout(60); touch(cdp, "touchEnd"); pg.wait_for_timeout(1500)
    # (3) tap another tab, then tap Home: Home's hero is running from the frame it is built to the landing
    touch(cdp, "touchStart", tabs["profile"][0], y); pg.wait_for_timeout(60); touch(cdp, "touchEnd"); pg.wait_for_timeout(1800)
    pg.evaluate("()=>{ window.__pz.hero = 0; window.__seen = []; window.__wt = setInterval(() => { const h = document.querySelector('#stage .cosmic-hero-wrap'); if(h){ const L = __M.loops().filter(a => h.contains(a.effect.target)); __seen.push([Math.round(performance.now()), L.length, L.filter(a => a.playState === 'paused').length, L.filter(a => a.playState === 'running').length]); } }, 25); }")
    touch(cdp, "touchStart", tabs["home"][0], y); pg.wait_for_timeout(60); touch(cdp, "touchEnd"); pg.wait_for_timeout(1800)
    out["S3"] = pg.evaluate("()=>{ clearInterval(window.__wt); return { seen: window.__seen, pz: window.__pz.hero }; }")
    # (4) release to rest, a slide from each other tab to each target, at CPU slowdown
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": CPU})
    rows = []
    pairs = [(a, b) for b in order for a in order if a != b]
    if QUICK: pairs = [p for p in pairs if (p[1] == "home" and p[0] == "calendar") or (p[1] == "profile" and p[0] == "rewards") or (p[1] == "rewards" and p[0] == "calendar") or (p[1] == "calendar" and p[0] == "rewards")]
    for a, b in pairs:
        for _ in range(2):
            touch(cdp, "touchStart", tabs[a][0], y); pg.wait_for_timeout(80); touch(cdp, "touchEnd"); pg.wait_for_timeout(1400)
        pg.evaluate("()=>{ __R.ev.length = 0; __R.op.length = 0; __LA.length = 0; }")
        touch(cdp, "touchStart", tabs[a][0], y); pg.wait_for_timeout(100)
        for k in range(1, 15):
            touch(cdp, "touchMove", tabs[a][0] + (tabs[b][0] - tabs[a][0]) * k / 14, y); time.sleep(0.016)
        time.sleep(.12); touch(cdp, "touchEnd")
        pg.wait_for_timeout(1300)
        d = pg.evaluate("()=>({ ev: __R.ev, op: __R.op, la: __LA })")
        ev = d["ev"]; up = next((e[0] for e in ev if e[1] == "up"), None)
        plan = next((e[0] for e in ev if e[1] == "bar" and up and e[0] > up and "is-pressing" not in e[2]), None)
        vis = next((p for p, o in d["op"] if up and p > up + 60 and o < 0.05), None)
        land = [x for x in d["la"] if up and x[0] >= up - 5 and x[1] > 100]
        hand = round(land[-1][0] - up + land[-1][1]) if land and up else None
        rows.append(dict(a=a, b=b, plan=round(plan - up) if plan and up else None, vis=round(vis - up) if vis and up else None, hand=hand))
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    out["rows"] = rows
    # (5) a hide and a show
    touch(cdp, "touchStart", tabs["home"][0], y); pg.wait_for_timeout(60); touch(cdp, "touchEnd"); pg.wait_for_timeout(2500)
    pre = pg.evaluate("()=>{ window.__M.ev.length = 0; window.__M.RT = 0; return __M.poses().map(p => [p[0], p[1], p[2]]); }")
    pg.evaluate("()=>{ window.__M.RT = performance.now(); __setHidden(true); window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true })); }")
    pg.wait_for_timeout(1500)
    pg.evaluate("()=>{ window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })); __setHidden(false); window.dispatchEvent(new Event('focus')); }")
    t1 = time.time(); Q = None
    while time.time() - t1 < 9:
        pg.wait_for_timeout(300)
        Q = pg.evaluate("()=>__M.poses()")
        if len([q for q in Q if q[1] == 'running']) >= len([p for p in pre if p[1] == 'running']): break
    pg.wait_for_timeout(2000)
    Q = pg.evaluate("()=>__M.poses()")
    out["pre"] = pre; out["Q"] = Q
    out["evs"] = pg.evaluate("()=>({ cancel: __M.ev.filter(e => e.k === 'cancel').length, animate: __M.ev.filter(e => e.k === 'animate').length })")
    # (6) the return's line in the resume log, once the 6s are over
    pg.wait_for_timeout(5500)
    out["log"] = pg.evaluate("()=>JSON.parse(localStorage.getItem('class26e.resumelog') || '[]')")
    ctx.close()
    return out

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    s = scenario(br)
    print("   tabs %s  sheets %s  backdrop at rest %r  hero at rest %s" % (s["tabs"], s["sheets"], s["restBF"][:40], {k: v for k, v in (s["hero0"] or {}).items() if k not in ("ref", "t")}))
    # (1)
    S1 = s["S1"]; ok1, msg1 = advancing(S1, "press")
    pz1 = max([x["pz"] for x in S1 if x] + [0])
    chk("(1) a press that stays down: none of Home's hero loops paused (most paused in a sample: %d of %d), none paused by the page (%d calls), flip-books running (%d), %s" % (
        max([x["paused"] for x in S1 if x] + [0]), (S1[0] or {}).get("n", 0), pz1, min([x["flips"] for x in S1 if x] or [0]), msg1),
        S1 and all(x and x["n"] >= 30 and x["paused"] == 0 for x in S1) and pz1 - (s["hero0"] or {}).get("pz", 0) == 0 and min(x["flips"] for x in S1) >= 5 and ok1, S1[:3])
    # (2)
    S2 = s["S2"]; ok2, msg2 = advancing(S2, "slide")
    pz2 = max([x["pz"] for x in S2 if x] + [0])
    chk("(2) a slide across the bar and back: none of Home's hero loops paused (most: %d), none paused by the page (%d calls), %s" % (max([x["paused"] for x in S2 if x] + [0]), pz2 - pz1, msg2),
        S2 and all(x and x["paused"] == 0 for x in S2) and pz2 - pz1 == 0 and ok2, S2[:3])
    g1, g2 = s["glass1"], s["glass2"] or {}
    chk("(2) ...and the glass is the glass: lens up on a press and a slide, the bar's backdrop blur as at rest (%r), no solid stand-in style" % s["restBF"][:30],
        g1.get("barLens") and g1.get("lensUp") and g2.get("barLens") and g2.get("lensUp") and s["restBF"] != "none" and g1.get("bf") == s["restBF"] and g2.get("bf") == s["restBF"] and not g1.get("solid"), [g1, g2])
    # (3)
    seen = s["S3"]["seen"]
    built = [x for x in seen if x[1] >= 30]
    chk("(3) a tap that brings Home in: its hero is built in %d samples and none shows a loop paused (most %d), no pause() call on it (%d)" % (len(built), max([x[2] for x in built] + [0]), s["S3"]["pz"]),
        len(built) >= 5 and all(x[2] == 0 for x in built) and s["S3"]["pz"] == 0, [built[:4], s["S3"]["pz"]])
    # (4)
    rows = s["rows"]
    bt = {}; bv = {}
    for r in rows:
        if r["hand"] is not None: bt.setdefault(r["b"], []).append(r["hand"])
        if r["vis"] is not None: bv.setdefault(r["b"], []).append(r["vis"])
    meds = {k: round(statistics.median(v)) for k, v in bt.items()}
    visd = {k: round(statistics.median(v)) for k, v in bv.items()}
    spread = (max(meds.values()) - min(meds.values())) if meds else 9999
    plans = [r["plan"] for r in rows if r["plan"] is not None]
    print("   release to the glass gone BY THE PAGE'S PLAN, median ms (%gx CPU): %s   told to land (ms after release): %s" % (CPU, meds, sorted(plans)))
    info = "   INFO: first frame the page could draw it gone (a long build on the main thread delays this one): %s" % visd
    print(info)
    # the landing is a spring simulated in script at the release (~25ms at 1x, 100 at 4x, more on a loaded host), so the MEDIAN is held, not the worst
    mplan = statistics.median(plans) if plans else None
    chk("(4a) the glass is told to land with the release, not with the screen: median %s ms after it, within %dms (latest %s, %d slides)" % (mplan, PLAN_MS, max(plans) if plans else None, len(rows)),
        plans and len(plans) == len(rows) and mplan <= PLAN_MS, plans)
    chk("(4b) release to the glass gone, by the page's plan, across the four targets is within %dms of each other (spread %d)" % (SPREAD_MS, spread), len(meds) >= (3 if QUICK else 4) and spread <= SPREAD_MS, meds)
    # (5)
    pre, Q = s["pre"], s["Q"]
    ref = next((i for i, p in enumerate(pre) if p[0] == "cosmic-orbit-spin"), 0)
    ran = [i for i, p in enumerate(pre) if p[1] == "running"]
    back = len([q for q in Q if q[1] == "running"])
    early = [pre[i][0] for i in ran if len(Q) == len(pre) and Q[i][2] is not None and pre[i][2] is not None and Q[i][2] < pre[i][2] - 50]
    skew = []
    if len(Q) == len(pre) and pre:
        for i in ran:
            if Q[i][1] == "running" and abs((Q[i][2] - Q[ref][2]) - (pre[i][2] - pre[ref][2])) > 150: skew.append(pre[i][0])
    chk("(5) a hide and a show: %d of %d loops run again, none at an earlier pose (%d), none cancelled or made again (%s), none skewed against the reference (%d)" % (
        back, len(ran), len(early), s["evs"], len(skew)),
        len(ran) >= 30 and back >= len(ran) and not early and s["evs"]["cancel"] == 0 and s["evs"]["animate"] == 0 and not skew, [early[:4], skew[:4], s["evs"]])
    # (6)
    line = next((x for x in reversed(s["log"]) if x.startswith("told")), "")
    mq = re.search(r" q((?:\d+,){11}\d+) g((?:\d+,){0,23}\d+)", line)
    chk("(6) the return's line in the resume log carries the frames per half second for 6s and the first gaps (%s)" % (("q" + mq.group(1) + " g" + mq.group(2)[:40]) if mq else line[:80]),
        bool(mq) and sum(int(v) for v in mq.group(1).split(",")) > 10 and len(mq.group(2).split(",")) == 24, s["log"])
    chk("(7) no page error", not s["errs"], s["errs"])
    print("\n" + ("ALL PASS" if G["ok"] else "FAILED"))
    br.close()
sys.exit(0 if G["ok"] else 1)
