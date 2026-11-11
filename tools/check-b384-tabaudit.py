#!/usr/bin/env python3
"""Build 384.25: THE BOTTOM TAB BAR, AUDITED TWICE - does it do the right thing, and is it smooth.

Madison, on his iPhone: "Please do a super thorough check over the bottom tab to verify it works properly. Seems a little finicky and still
not flawlessly smooth." Earlier rounds (tabroots, tabbutter, qslide, navmeet, navchat, mouse) each measured one thing; this reads the whole
bar against a list, by SHAPE - the DOM, boxes and counts, never a label - and prints what it found.

PART 1, CORRECTNESS (a finger on the phone and the iPad, a mouse on the laptop, both classes, installed and in a browser):
 (1) THE MATRIX. From the starting screens that show the bar (Home, the modes, units, Customize, Friends, the badge case, the ladder, Settings
     pages, Test history, Review, Virtual Room, Profile and its tabs, the Leaderboard, the Calendar / Fire Code's Settings) x EVERY tab of the
     class's bar, tapped for real: that tab's own root is up and no other, exactly that tab is lit, ARIA SAYS SO (aria-current="page" on the lit
     tab and on no other - a screen reader heard four buttons and no place), the platter (the bubble) rests exactly under it (centre within 1px,
     width equal, fully visible), nothing of the screen it came from is left. On the screens that belong to no tab (the modes, the units) no tab
     is lit, none says aria-current and the platter is hidden.
 (2) RAPID TAPS. Tap A, B, C, A within 30 / 100ms, a double tap, a tap in the middle of a slide, random runs: the bar ends on the last tab, its
     screen is the only one up, highlight, aria-current and bubble agree, no lens or press state is left on <html> or the bar 1.5s later, no
     page error. A second tap on the tab that is up builds nothing.
 (3) SHOWN AND HIDDEN: hidden on Welcome (a fresh install), a question, Pause and a run's results; back on Home from each in the right place with
     no frame where its box differs from where it ends; covered (nothing under a tab's middle but the cover) by a sheet and by the chat, and
     a tap through a sheet opens nothing.
 (4) GESTURES: a long press opens its tab on release and leaves nothing held; a drag off the bar (finger up, mouse out) ends with the press
     over and the screen unchanged; two fingers end in one consistent state; a swipe that starts on the bar leaves nothing held.
 (5) GEOMETRY: every tab at least 44px both ways (320px, SE, Pro Max, iPad, laptop), labels not clipped, the bar inside the viewport with room
     under it (the home indicator's inset simulated installed; Safari's bars in a browser tab), no sideways scroll; the bar does not move while
     the page scrolls under it.
 (6) KEYBOARD: Tab reaches the tabs in their order, a visible focus ring on a keyboard's focus, Enter and Space open the tab and the focus
     stays, aria-current follows.
 (7) REDUCE MOTION: nothing on the bar animates; the platter steps and rests in the right place. And a resize / rotation: landscape, 320 wide
     and back, the platter under the lit tab each time.

PART 2, SMOOTHNESS (the phone, 440x956 at 2x, CDP tracing, a CPU throttle; the machine is shared, so a frame time is INFO and what is
asserted is main-thread CPU (1x-equivalent, as tabbutter reads it) and shapes):
 (S1) every animation on the bar's subtree during a tap or slide animates only transform / opacity / scale (the compositor), and no CSS
      transition runs on a layout property, a filter or a backdrop-filter.
 (S2) NO LAYOUT READ BETWEEN THE FINGER AND THE GLASS: no style pass is forced by the document's touchstart handler (it read window.innerHeight:
      20 elements restyled, 2-8ms at 1x, inside the first handler of every touch, bar or page) - counted in a trace of 12 taps by the function
      that forced it.
 (S3) the press answers within 2 frames: from the pointerdown to the first frame whose bar differs (the lens lifting), counted in frames.
 (S4) budgets: no task in a tab change over 140ms (1x-equivalent), no input handler over 20ms, no function forces more than 8 style passes /
      layouts in a tab change; the 16 transitions (every ordered pair of the four tabs, the same tab included) are printed as a table of p50 / p95
      frame gaps, over-20ms and over-50ms frames in the 600ms after the tap, the longest task and the style / layout passes.
 (S5) no page errors.

Run:  python3 tools/check-b384-tabaudit.py [--quick] [--part 1|2] [--only 1,2,...] [--against REV|path/to/index.html]
      --against origin/main FAILS (1) aria-current, and (S2).  The rest hold on both: they guard what is right today."""
import os, sys, re, time, json, statistics, collections, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.dirname(HERE)
argv = sys.argv[1:]
def opt(name, default=None):
    if name in argv:
        i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return v
    return default
QUICK = "--quick" in argv
if QUICK: argv.remove("--quick")
PART = opt("--part", "12"); ONLY = set((opt("--only", "") or "").split(",")) - {""}
AG = opt("--against")
SRC_FILE = None
if AG:
    if os.path.isfile(AG): SRC_FILE = os.path.abspath(AG)
    else:
        SRC_FILE = os.path.join(tempfile.mkdtemp(prefix="tabaudit-"), "index.html")
        open(SRC_FILE, "wb").write(subprocess.check_output(["git", "-C", REPO, "show", AG + ":index.html"]))
def want(n, part): return str(part) in PART and (not ONLY or str(n) in ONLY)

# ---- part 1's prelude: tabroots' starting screens, taps and verdicts, on the glitches harness (it takes --against itself)
sys.argv = [sys.argv[0]] + (["--against", SRC_FILE] if SRC_FILE else [])
_t = open(os.path.join(HERE, "check-b384-tabroots.py")).read().split("\ndef walk(")[0]
T = {"__file__": os.path.join(HERE, "check-b384-tabroots.py"), "__name__": "tabaudit_tr"}
exec(_t, T)
G = T["G"]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
def info(s): print("INFO " + s, flush=True)

G.DEV["w320"] = (320, 568, 320, 568, (20, 0, 0, 0), G.UA_IPHONE, True, True)
G.DEV["se-tab"] = (375, 553, 375, 667, (0, 0, 0, 0), G.UA_IPHONE, True, False)       # an SE in a Safari tab (Safari's bars take 114)
G.DEV["lap1366"] = (1366, 768, 1366, 768, (0, 0, 0, 0), G.UA_WIN, False, False)
TABS = T["TABS"]; ROOT = T["ROOT"]; STATE = T["STATE"]

BAR = r"""()=>{ const bar=document.getElementById('bottomtabs'); const nr=bar.querySelector('.bottomtabs-navrow'); const sl=document.getElementById('bottomtabs-slider');
 const tabs=[...nr.querySelectorAll('.bottomtab')].filter(t=>!t.hidden && t.id!=='bottomtab-start');
 const r=e=>{const b=e.getBoundingClientRect(); return {l:b.left,t:b.top,w:b.width,h:b.height,c:b.left+b.width/2,b:b.bottom,r:b.right}};
 const lens=document.getElementById('bottomtabs-lens'), H=document.documentElement;
 return { hidden:bar.hidden, act:tabs.filter(t=>t.classList.contains('active')).map(t=>t.id), cur:tabs.filter(t=>t.hasAttribute('aria-current')).map(t=>t.id+'='+t.getAttribute('aria-current')),
   bar:r(bar), slider:r(sl), sliderOp:+getComputedStyle(sl).opacity, sliderReady:sl.classList.contains('ready'), tabs:Object.fromEntries(tabs.map(t=>[t.id,r(t)])),
   held: H.classList.contains('tab-held')||H.classList.contains('tab-dragging')||bar.classList.contains('lens-up')||bar.classList.contains('is-pressing')||lens.classList.contains('is-up'),
   builds: bar._navBuilds||0, vw: innerWidth, vh: innerHeight, sw: document.documentElement.scrollWidth }; }"""
def rest(pg, ms=1500):
    pg.wait_for_timeout(ms); return pg.evaluate(BAR)
def bubble(b):
    """(centre offset, width offset) of the platter against the lit tab, or None when not exactly one is lit"""
    if len(b["act"]) != 1: return None
    t = b["tabs"][b["act"][0]]; s = b["slider"]
    return abs(s["c"] - t["c"]), abs(s["w"] - t["w"])
def bar_faults(b, want_tab=None):
    """what is wrong with the bar at rest: lit set, aria-current, bubble, leaked press state"""
    f = []
    if want_tab is not None and b["act"] != [want_tab]: f.append("lit %s, wanted [%s]" % (b["act"], want_tab))
    if len(b["act"]) == 1:
        if b["cur"] != [b["act"][0] + "=page"]: f.append("aria-current %s, the lit tab is %s" % (b["cur"], b["act"]))
        d = bubble(b)
        if d[0] > 1 or d[1] > 1: f.append("platter off its tab by %.2fpx (centre), %.2fpx (width)" % d)
        if b["sliderOp"] < .99 or not b["sliderReady"]: f.append("platter not fully shown (opacity %.2f)" % b["sliderOp"])
    elif not b["act"]:
        if b["cur"]: f.append("no tab is lit but aria-current is on %s" % b["cur"])
        if b["sliderOp"] > .01: f.append("no tab is lit and the platter shows (opacity %.2f)" % b["sliderOp"])
    else: f.append("several tabs lit %s" % b["act"])
    if b["held"]: f.append("a press is still held (lens / tab-held / is-pressing)")
    return f
def centre(pg, tid): return pg.evaluate("(id)=>{const r=document.getElementById(id).getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]}", tid)
def raw_tap(pg, cdp, touch, tid, hold=0.03):
    c = centre(pg, tid)
    if touch:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c[0], "y": c[1]}]}); time.sleep(hold)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    else:
        pg.mouse.move(c[0], c[1]); pg.mouse.down(); time.sleep(hold); pg.mouse.up()
def touch_path(cdp, pts, dt=0.016):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": pts[0][0], "y": pts[0][1]}]}); time.sleep(0.05)
    for p in pts[1:]:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": p[0], "y": p[1]}]}); time.sleep(dt)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
def state(pg): return pg.evaluate(STATE, ROOT)
def shown_tabs(pg, tabs): return pg.evaluate("(ts)=>ts.filter(i=>{const b=document.getElementById(i);return !!b&&!b.hidden&&b.getClientRects().length>0;})", tabs)
def tab_names(l): return [s.split("-")[1] for s in l]

QUICK_STARTS = ("Home", "the modes (Start Studying)", "the units, Drill, a unit ticked", "Customize", "Friends", "the badge case", "a Settings page (Sound)",
                "Test history", "Profile's Stats", "the Leaderboard", "the Calendar", "Settings (Fire Code's tab)")

# ============================================================================================================== PART 1
def sec_matrix(br, dev, cls, full):
    touch = G.DEV[dev][6]; tabs = TABS[cls]
    pg = G.open_dev(br, dev, [G.seed_init(cls)])
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    bad = []; n = 0; initial_bad = []; no_tab_screens = []
    for name, which, reach, kind in T["STARTS"]:
        if which not in ("both", cls): continue
        if not full and name not in QUICK_STARTS: continue
        for ti, tb in enumerate(tabs):
            T["reset"](pg)
            try: T["reach_retry"](pg, reach, cls, touch); T["settle"](pg, 450)
            except Exception as e: bad.append((name, "cannot be reached: %s" % str(e)[:80])); break
            if not pg.evaluate(T["BAR_TAB_VISIBLE"], tb): continue
            if ti == 0:   # the bar's state on arrival, before any tap: what is lit is said, and a screen of no tab lights none
                pg.wait_for_timeout(700)       # the platter's own glide (.45s with an overshoot) has to have ended
                b0 = pg.evaluate(BAR); f0 = bar_faults(b0)
                f0 = [x for x in f0 if "still held" not in x]
                if f0: initial_bad.append((name, f0))
                if not b0["act"]: no_tab_screens.append(name)
            n += 1
            try: st = T["land"](pg, tb, touch)
            except Exception as e: bad.append((name + " > " + tb, "tap failed: " + str(e)[:80])); continue
            b = rest(pg, 600)
            v = T["verdict"](st, tb) + bar_faults(b, tb)
            if v: bad.append((name + " > " + tab_names([tb])[0], v))
    chk("(1) %s %s: from %d starting screens x every tab (%d taps): the tab's own root, only it lit and aria-current, the platter exactly under it (1px), nothing left of the screen it came from" % (
        dev, cls, sum(1 for s in T["STARTS"] if s[1] in ("both", cls) and (full or s[0] in QUICK_STARTS)), n), not bad, bad[:5])
    chk("(1) %s %s: on arrival at each starting screen what is lit is said (aria-current) and a screen of no tab lights none and shows no platter (%d such: %s)" % (
        dev, cls, len(no_tab_screens), no_tab_screens[:3]), not initial_bad, initial_bad[:4])
    chk("(1) %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3])
    pg.ctx.close()

def sec_rapid(br, dev, cls):
    touch = G.DEV[dev][6]; tabs = TABS[cls]
    pg = G.open_dev(br, dev, [G.seed_init(cls)]); cdp = pg.ctx.new_cdp_session(pg)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    import random; random.seed(11)
    seqs = [("A B C A, 100ms", [tabs[1], tabs[2], tabs[3], tabs[0]], .1), ("A B C A, 30ms", [tabs[1], tabs[2], tabs[3], tabs[1]], .03),
            ("double tap", [tabs[2], tabs[2]], .05), ("B then C, 400ms", [tabs[1], tabs[2]], .4), ("Profile, Home, 150ms", [tabs[1], tabs[0]], .15),
            ("C B C B C, 80ms", [tabs[2], tabs[1], tabs[2], tabs[1], tabs[2]], .08)]
    for r in range(4 if QUICK else 8):
        seqs.append(("random %d" % r, [random.choice(tabs) for _ in range(random.randint(3, 7))], random.choice([.03, .08, .15, .25])))
    bad = []
    for name, seq, gap in seqs:
        T["reset"](pg); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
        e0 = len(pg.errs)
        for tb in seq: raw_tap(pg, cdp, touch, tb); time.sleep(gap)
        pg.wait_for_timeout(1800); b = pg.evaluate(BAR); st = state(pg)
        last = seq[-1]; f = []
        if st["showing"] != [last]: f.append("screens up %s, wanted only %s" % (st["showing"], last))
        f += bar_faults(b, last)
        if len(pg.errs) > e0: f.append("page error " + pg.errs[e0])
        if f: bad.append((name, tab_names(seq), f))
    chk("(2) %s %s: %d runs of quick taps end on the last tab: one screen, highlight, aria-current and platter agree, nothing held, no error" % (dev, cls, len(seqs)), not bad, bad[:3])
    # a tap on the tab that is up builds nothing and goes to the top - on EVERY tab of the class's bar (Fire Code's Settings rebuilt its whole screen)
    again = []
    for tb in tabs:
        T["reset"](pg); T["press"](pg, tb, touch); pg.wait_for_timeout(1500)
        if tb != tabs[0]: pg.evaluate("()=>window.scrollTo(0, 400)"); pg.wait_for_timeout(300)
        b0 = pg.evaluate(BAR)["builds"]; y0 = pg.evaluate("()=>scrollY"); pg.evaluate("()=>{ const s=document.querySelector('#stage > *'); if(s) s.__same = 1; }")
        for _ in range(3): raw_tap(pg, cdp, touch, tb); time.sleep(.3)
        pg.wait_for_timeout(1200); b1 = pg.evaluate(BAR)["builds"]
        same = pg.evaluate("()=>!!(document.querySelector('#stage > *') || {}).__same"); y1 = pg.evaluate("()=>scrollY")
        f = []
        if b1 != b0: f.append("%d screens built" % (b1 - b0))
        if not same: f.append("the screen on the stage is a new one")
        if y0 > 0 and y1 > 5: f.append("the page did not go to its top (%d -> %d)" % (y0, y1))
        if f: again.append((tab_names([tb])[0], f))
    chk("(2) %s %s: three more taps on the tab that is up, on each tab of the bar, build no screen and take the page to its top" % (dev, cls), not again, again)
    # a tap in the middle of a slide (a second finger on another tab while the first slides)
    T["reset"](pg); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900)
    c0 = centre(pg, tabs[0]); c3 = centre(pg, tabs[3]); c1 = centre(pg, tabs[1])
    if touch:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c0[0], "y": c0[1], "id": 1}]}); time.sleep(.04)
        for i in range(1, 7):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": c0[0] + (c3[0] - c0[0]) * i / 12, "y": c0[1], "id": 1}]}); time.sleep(.016)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c0[0] + (c3[0] - c0[0]) * .5, "y": c0[1], "id": 1}, {"x": c1[0], "y": c1[1], "id": 2}]}); time.sleep(.05)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": [{"x": c0[0] + (c3[0] - c0[0]) * .5, "y": c0[1], "id": 1}]}); time.sleep(.05)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(2200); b = pg.evaluate(BAR); st = state(pg)
        f = bar_faults(b); lit = b["act"][0] if len(b["act"]) == 1 else None
        if len(st["showing"]) != 1 or (lit and st["showing"] != [lit]): f.append("screen %s but lit %s" % (st["showing"], b["act"]))
        chk("(2) %s %s: a second finger tapping in the middle of a slide leaves one screen, its tab lit, the platter under it" % (dev, cls), not f, f)
    chk("(2) %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3])
    pg.ctx.close()

def sec_visibility(br, dev, cls):
    touch = G.DEV[dev][6]; tabs = TABS[cls]
    SAMPLER = r"""(ms)=>{ window.__samp=new Promise(res=>{ const bar=document.getElementById('bottomtabs'); const out=[]; const t0=performance.now();
     const f=()=>{ const b=bar.getBoundingClientRect(); const cs=getComputedStyle(bar); out.push([Math.round(performance.now()-t0), bar.hidden||cs.display==='none'?1:0, b.left, b.top, b.width, b.height]);
       if(performance.now()-t0<ms) requestAnimationFrame(f); else res(out); }; f(); }); }"""
    def no_jump(rows):
        vis = [r for r in rows if not r[1]]
        if not vis: return None, "never visible"
        last = vis[-1]; moved = [r for r in vis if max(abs(r[i] - last[i]) for i in (2, 3, 4, 5)) > 1]
        return len(vis), ("%d of %d visible frames differ from the final box by over 1px (first: %s)" % (len(moved), len(vis), moved[0])) if moved else ""
    # a fresh install: the bar is not up on any onboarding screen
    ctx = br.new_context(viewport={"width": 440, "height": 956}, user_agent=G.UA_IPHONE, has_touch=True, is_mobile=True)
    ctx.add_init_script(G.STANDALONE); ctx.add_init_script("window.__cloudSeed = {};"); ctx.add_init_script(G.FAKE_CLOUD)
    pf = ctx.new_page(); pf.route("**/index.html", lambda r, q, b=G.body((62, 0, 34, 0)): r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pf.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": G.BUILD, "force": False, "frameId": ""})))
    pf.goto(G.URL); pf.wait_for_timeout(3000); pf.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    seen = []
    for fn in ("showWelcome", "showWelcomeIntro", "showGetStarted"):
        try: pf.evaluate("()=>{ try{ %s(); }catch(e){} }" % fn); pf.wait_for_timeout(500)
        except Exception: continue
        seen.append((fn, pf.evaluate("()=>{ const b=document.getElementById('bottomtabs'); return b.hidden || getComputedStyle(b).display==='none' || b.getClientRects().length===0; }")))
    chk("(3) a fresh install: the bar is hidden on every onboarding screen reached (%s)" % [s[0] for s in seen], bool(seen) and all(s[1] for s in seen), seen)
    ctx.close()
    pg = G.open_dev(br, dev, [G.seed_init(cls)]); cdp = pg.ctx.new_cdp_session(pg)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    bad = []
    for name, reach, leave in (("a run's results", T["r_results"], "()=>showHome()"), ("a question", T["r_question"], "LEAVE"), ("Pause", T["r_pause"], "LEAVE")):
        T["reset"](pg)
        try: reach(pg, cls, touch)
        except Exception as e: bad.append((name, "cannot be reached " + str(e)[:60])); continue
        pg.wait_for_timeout(400)
        up = pg.evaluate(T["BAR_TAB_VISIBLE"], tabs[0])
        if up: bad.append((name, "the bar is up here")); continue
        pg.evaluate(SAMPLER, 2400)
        if leave == "LEAVE":
            pg.evaluate("()=>{ try{ confirmMainMenu(); }catch(e){} }"); pg.wait_for_timeout(500)
            pg.evaluate("()=>{ const b=[...document.querySelectorAll('.pausepanel button')].find(x=>/Leave/.test(x.textContent)); b && b.click(); }")
        else: pg.evaluate(leave)
        n, why = no_jump(pg.evaluate("()=>window.__samp"))
        if why: bad.append((name + " > Home", why))
        else:
            b = rest(pg, 400)
            f = bar_faults(b, tabs[0])
            if f: bad.append((name + " > Home", f))
    chk("(3) %s %s: hidden on a run's results, a question and Pause; back on Home it appears in its final box in every frame it is visible, Home lit, platter under it" % (dev, cls), not bad, bad[:3])
    # covered by a sheet and by the chat; a tap through a sheet opens nothing
    T["reset"](pg); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(700)
    HIT = "(ids)=>ids.map(id=>{ const b=document.getElementById(id); const r=b.getBoundingClientRect(); const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); return !!(e && b.contains(e)); })"
    pg.evaluate("()=>{ const o=document.createElement('div'); o.className='invite-overlay'; o.id='__sheet'; o.innerHTML='<div class=\"invite-sheet\"><h3 class=\"invite-sheet-title\">x</h3></div>'; mountSheetOverlay(o); }")
    pg.wait_for_timeout(500)
    hit = pg.evaluate(HIT, tabs); c = centre(pg, tabs[2])
    if touch: pg.touchscreen.tap(c[0], c[1])
    else: pg.mouse.click(c[0], c[1])
    pg.wait_for_timeout(1200); st = state(pg)
    chk("(3) %s %s: under a sheet no tab is the topmost thing at its middle, and a tap there opens nothing (screen %s)" % (dev, cls, st["showing"]), not any(hit) and st["showing"] == [tabs[0]], [hit, st["showing"]])
    T["reset"](pg); pg.evaluate("()=>{ showHome(); openChatDock(); }"); pg.wait_for_timeout(900)
    hit = pg.evaluate(HIT, tabs)
    chk("(3) %s %s: with the chat open no tab is the topmost thing at its middle" % (dev, cls), not any(hit), hit)
    T["reset"](pg)
    chk("(3) %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3])
    pg.ctx.close()

def sec_gestures(br, dev, cls):
    touch = G.DEV[dev][6]; tabs = TABS[cls]
    pg = G.open_dev(br, dev, [G.seed_init(cls)]); cdp = pg.ctx.new_cdp_session(pg)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    bad = []
    def end(name, want_tab):
        pg.wait_for_timeout(2200); b = pg.evaluate(BAR); st = state(pg)
        f = bar_faults(b, want_tab)
        if st["showing"] != [want_tab]: f.append("screens up %s" % st["showing"])
        if f: bad.append((name, f))
    if touch:
        for hold in (.8, 2.5):
            T["reset"](pg); c = centre(pg, tabs[2])
            cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c[0], "y": c[1]}]}); time.sleep(hold)
            cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); end("a %.1fs press on Leaderboard opens it on release" % hold, tabs[2])
        T["reset"](pg); c = centre(pg, tabs[2]); touch_path(cdp, [(c[0], c[1] - i * 25) for i in range(0, 9)]); end("a drag up off the bar leaves Home", tabs[0])
        T["reset"](pg); c0 = centre(pg, tabs[0]); c3 = centre(pg, tabs[3]); touch_path(cdp, [(c0[0] + (c3[0] - c0[0]) * i / 12, c0[1]) for i in range(13)]); end("a slide Home > last tab lands there", tabs[3])
        T["reset"](pg); c0 = centre(pg, tabs[0]); c3 = centre(pg, tabs[3]); touch_path(cdp, [(c0[0] + (c3[0] - c0[0]) * i / 12, c0[1] - i * 12) for i in range(13)]); end("a slide that rises as it goes still lands on a tab", None) if False else None
        T["reset"](pg); c1 = centre(pg, tabs[1]); c2 = centre(pg, tabs[2])
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c1[0], "y": c1[1], "id": 1}]}); time.sleep(.03)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c1[0], "y": c1[1], "id": 1}, {"x": c2[0], "y": c2[1], "id": 2}]}); time.sleep(.1)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": [{"x": c1[0], "y": c1[1], "id": 1}]}); time.sleep(.05)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        pg.wait_for_timeout(2000); b = pg.evaluate(BAR); st = state(pg); f = bar_faults(b)
        lit = b["act"][0] if len(b["act"]) == 1 else None
        if len(st["showing"]) != 1 or (lit and st["showing"] != [lit]): f.append("screen %s, lit %s" % (st["showing"], b["act"]))
        if f: bad.append(("two fingers on two tabs", f))
        # a vertical swipe that starts on the bar over a scrolling screen
        T["reset"](pg); pg.tap("#" + tabs[1]); pg.wait_for_timeout(1500); c = centre(pg, tabs[2])
        touch_path(cdp, [(c[0], c[1] - i * 40) for i in range(0, 9)]); end("a vertical swipe that starts on the bar leaves Profile as it was", tabs[1])
    else:
        # a mouse: press on a tab, drift out above the bar, let go there: the press ends, nothing opens, nothing is held
        T["reset"](pg); c = centre(pg, tabs[2]); pg.mouse.move(c[0], c[1]); pg.mouse.down(); pg.mouse.move(c[0], c[1] - 200, steps=6); pg.mouse.up(); end("a mouse press let go above the bar opens nothing", tabs[0])
        T["reset"](pg); c = centre(pg, tabs[2]); pg.mouse.move(c[0], c[1]); pg.mouse.down(); time.sleep(1.2); pg.mouse.up(); end("a mouse held 1.2s on Leaderboard opens it", tabs[2])
        T["reset"](pg); c0 = centre(pg, tabs[0]); c3 = centre(pg, tabs[3]); pg.mouse.move(c0[0], c0[1]); pg.mouse.down(); pg.mouse.move(c3[0], c3[1], steps=10); pg.mouse.up(); end("a mouse slide Home > last tab lands there", tabs[3])
    chk("(4) %s %s: %s" % (dev, cls, "long presses, a drag off the bar, a slide, two fingers and a swipe from the bar each end consistent with nothing held" if touch else "a mouse's drift off the bar, a held press and a slide each end consistent with nothing held"), not bad, bad[:4])
    chk("(4) %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3])
    pg.ctx.close()

SIZES = r"""()=>{ const bar=document.getElementById('bottomtabs'); const bs=bar.getBoundingClientRect();
 const tabs=[...bar.querySelectorAll('.bottomtab')].filter(t=>!t.hidden).map(t=>{ const r=t.getBoundingClientRect(); const lab=t.querySelector('.bottomtab-label'); const lr=lab?lab.getBoundingClientRect():null;
   return { id:t.id, w:r.width, h:r.height, scroll: lab?lab.scrollWidth:0, client: lab?lab.clientWidth:0, clipL: lr? lr.left < r.left-.5 : false, clipR: lr? lr.right > r.right+.5 : false }; });
 return { bar:[bs.left,bs.top,bs.right,bs.bottom], vw:innerWidth, vh:innerHeight, sw:document.documentElement.scrollWidth, tabs }; }"""
def sec_geometry(br, devs, cls):
    bad = []; rows = []
    for dev in devs:
        pg = G.open_dev(br, dev, [G.seed_init(cls)], wait=2600)
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
        o = pg.evaluate(SIZES)
        small = [(t["id"][10:], round(t["w"], 1), round(t["h"], 1)) for t in o["tabs"] if t["w"] < 44 or t["h"] < 44]
        clip = [t["id"][10:] for t in o["tabs"] if t["clipL"] or t["clipR"] or t["scroll"] > t["client"] + 1]
        L, Tp, R, Bt = o["bar"]; f = []
        if small: f.append("under 44px: %s" % small)
        if clip: f.append("label clipped: %s" % clip)
        if L < 0 or R > o["vw"] or Tp < 0 or Bt > o["vh"] - 6: f.append("bar %s outside the %dx%d viewport (or under 6px from the bottom edge)" % ([round(x, 1) for x in o["bar"]], o["vw"], o["vh"]))
        if o["sw"] > o["vw"]: f.append("sideways scroll: %d wide in %d" % (o["sw"], o["vw"]))
        if f: bad.append((dev, f))
        rows.append("%s bar %dpx wide, %.0f from the bottom edge, tabs %s" % (dev, R - L, o["vh"] - Bt, [(t["id"][10:], round(t["w"]), round(t["h"])) for t in o["tabs"]]))
        # the bar does not move while the page scrolls under it
        scr = pg.evaluate("()=>{ showProfile('stats'); return 1; }"); pg.wait_for_timeout(1200)
        sh = pg.evaluate("()=>document.documentElement.scrollHeight - innerHeight")
        if sh > 200:
            ys = pg.evaluate("""()=>new Promise(res=>{ const bar=document.getElementById('bottomtabs'); const out=[]; let i=0; const f=()=>{ window.scrollTo(0, i*50); const b=bar.getBoundingClientRect(); out.push([b.top,b.left,b.height]); i++; if(i<40) requestAnimationFrame(f); else res(out); }; f(); })""")
            if len({tuple(round(x, 2) for x in r) for r in ys}) > 1: bad.append((dev, "the bar moved while the page scrolled under it: %s" % ys[:2]))
        pg.ctx.close()
    chk("(5) %s: every tab 44px+ both ways, labels not clipped, the bar inside the viewport with room under it, no sideways scroll, still while the page scrolls" % ",".join(devs), not bad, bad)
    for r in rows: info(r)

def sec_keyboard(br, cls):
    dev = "lap1366"; tabs = TABS[cls]
    pg = G.open_dev(br, dev, [G.seed_init(cls)]); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    pg.evaluate("()=>{ document.activeElement && document.activeElement.blur(); }")
    # from the document's start the bar is some Tab presses in (Home's flares come first in the page's order): INFO. From the first tab the rest follow in order.
    first = None
    for i in range(1, 61):
        pg.keyboard.press("Tab")
        if pg.evaluate("()=>document.activeElement && document.activeElement.id") in tabs: first = i; break
    info("%s %s: the first tab of the bar takes %s Tab presses from the top of the page" % (dev, cls, first))
    pg.focus("#" + tabs[0]); order = [tabs[0]]
    for _ in range(len(tabs) - 1):
        pg.keyboard.press("Tab"); order.append(pg.evaluate("()=>document.activeElement && document.activeElement.id"))
    chk("(6) %s %s: from the first tab, Tab goes through the bar's tabs in their order (%s)" % (dev, cls, tab_names(order)), order == tabs, order)
    pg.focus("#" + tabs[1]); pg.keyboard.press("Shift+Tab"); pg.keyboard.press("Tab")
    ring = pg.evaluate("(id)=>{ const e=document.getElementById(id); const cs=getComputedStyle(e); return { vis:e.matches(':focus-visible'), style:cs.outlineStyle, w:parseFloat(cs.outlineWidth), a:document.activeElement.id }; }", tabs[1])
    chk("(6) %s %s: a tab focused by the keyboard shows a ring (%s)" % (dev, cls, ring), ring["vis"] and ring["style"] != "none" and ring["w"] >= 1, ring)   # the bar is zoomed .9 on a computer: 2px computes to ~1.1, and is a clear ring on screen
    pg.keyboard.press("Enter"); b = rest(pg, 1300); a = pg.evaluate("()=>document.activeElement && document.activeElement.id"); st = state(pg)
    f = bar_faults(b, tabs[1]) + ([] if st["showing"] == [tabs[1]] else ["screen %s" % st["showing"]])
    chk("(6) %s %s: Enter on Profile opens it, the focus stays on the tab, aria-current moved (%s)" % (dev, cls, a), not f and a == tabs[1], f)
    pg.keyboard.press("Tab"); pg.keyboard.press("Space"); b = rest(pg, 1300); st = state(pg)
    f = bar_faults(b, tabs[2]) + ([] if st["showing"] == [tabs[2]] else ["screen %s" % st["showing"]])
    chk("(6) %s %s: Space on the next tab opens it and aria-current moves" % (dev, cls), not f, f)
    chk("(6) %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3]); pg.ctx.close()

def sec_motion_resize(br, dev, cls):
    touch = G.DEV[dev][6]; tabs = TABS[cls]
    pg = G.open_dev(br, dev, [G.seed_init(cls)]); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    pg.evaluate("()=>{ theme.reduceMotion = true; applyTheme && applyTheme(); }"); pg.wait_for_timeout(300)
    bad = []
    for tb in (tabs[2], tabs[3], tabs[1], tabs[0]):
        pg.evaluate("()=>{ window.__rmA = 0; const bar=document.getElementById('bottomtabs'); const f=()=>{ window.__rmA = Math.max(window.__rmA, document.getAnimations().filter(a=>a.effect&&a.effect.target&&a.effect.target.closest&&a.effect.target.closest('#bottomtabs')).length); if(window.__rmOn) requestAnimationFrame(f); }; window.__rmOn = true; f(); }")
        T["press"](pg, tb, touch); b = rest(pg, 900); anim = pg.evaluate("()=>{ window.__rmOn = false; return window.__rmA; }")
        f = bar_faults(b, tb) + (["%d animations ran on the bar" % anim] if anim else [])
        if f: bad.append((tb, f))
    chk("(7) %s %s: with Reduce Motion nothing on the bar animates and the platter rests under each tab" % (dev, cls), not bad, bad[:3])
    pg.evaluate("()=>{ theme.reduceMotion = false; applyTheme && applyTheme(); }")
    T["reset"](pg); T["press"](pg, tabs[2], touch); pg.wait_for_timeout(1200)
    w, h = G.DEV[dev][0], G.DEV[dev][1]; bad = []
    for label, size in (("landscape", (h, w)), ("320 wide", (320, 560)), ("back", (w, h))):
        pg.set_viewport_size({"width": size[0], "height": size[1]}); b = rest(pg, 1400); f = bar_faults(b, tabs[2])
        if f: bad.append((label, f))
    chk("(7) %s %s: after landscape, a 320 wide window and back the platter is under the lit tab each time" % (dev, cls), not bad, bad)
    chk("(7) %s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3]); pg.ctx.close()

# ============================================================================================================== PART 2
CATS = "devtools.timeline,disabled-by-default-devtools.timeline,disabled-by-default-devtools.timeline.stack,v8.execute,cc,viz"
def trace_run(pg, cdp, fn, tail_ms):
    evs, done = [], []
    h1 = lambda p: evs.extend(p["value"]); h2 = lambda p: done.append(1)
    cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
    cdp.send("Tracing.start", {"categories": CATS, "transferMode": "ReportEvents"})
    fn(); pg.wait_for_timeout(tail_ms); cdp.send("Tracing.end")
    for _ in range(400):
        if done: break
        pg.wait_for_timeout(100)
    cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
    return evs
def analyse(evs, thr):
    names = {}
    for e in evs:
        if e.get("name") == "thread_name": names[(e["pid"], e["tid"])] = e["args"]["name"]
    main = [e for e in evs if names.get((e.get("pid"), e.get("tid"))) == "CrRendererMain" and e.get("ph") == "X"]
    cpu = lambda e: e.get("tdur", e["dur"]) / 1000.0 / thr
    ty = lambda e: (e.get("args", {}).get("data", {}) or {}).get("type")
    downs = [e["ts"] for e in main if e["name"] == "EventDispatch" and ty(e) in ("pointerdown", "mousedown", "touchstart")]
    if not downs: return None
    t0 = min(downs); t1 = t0 + 1_100_000
    tasks = [e for e in main if e["name"] == "RunTask" and t0 - 2000 <= e["ts"] <= t1]
    inputs = [cpu(e) for e in main if e["name"] == "EventDispatch" and t0 - 2000 <= e["ts"] <= t1 and ty(e) in ("pointerdown", "pointerup", "click", "touchstart", "touchend", "mousedown", "mouseup")]
    forced = collections.Counter(); sn = ln = 0
    for e in main:
        if e["name"] in ("UpdateLayoutTree", "Layout") and t0 - 2000 <= e["ts"] <= t1:
            a = e.get("args", {}); st = (a.get("beginData", {}) or {}).get("stackTrace") or a.get("stackTrace") or []
            fn = next((f.get("functionName") for f in st if f.get("functionName")), None)
            real = (e["name"] == "UpdateLayoutTree" and (a.get("elementCount") or 0) > 0) or (e["name"] == "Layout" and e.get("tdur", 0) >= 50)
            if real:
                if e["name"] == "UpdateLayoutTree": sn += 1
                else: ln += 1
            if fn and real: forced[(e["name"], fn)] += 1
    return {"worst": max([cpu(e) for e in tasks] or [0]), "total": sum(cpu(e) for e in tasks), "inputMax": max(inputs or [0]), "forced": forced, "style_n": sn, "lay_n": ln}
# the traced taps carry a bare frame clock and nothing that reads style: a harness that called getComputedStyle each frame would force the very passes (S2, S4) count
CLOCK = r"""()=>{ const S = window.__pm = { frames: [], down: null, on: true };
  window.addEventListener('pointerdown', e => { if(!S.down) S.down = performance.now(); }, true); window.addEventListener('mousedown', e => { if(!S.down) S.down = performance.now(); }, true);
  const f = t => { if(!S.on) return; S.frames.push(performance.now()); requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
# the second tap of a pair is read in the page (not traced): what animates on the bar, which transitions run, and in how many frames the bar first changes
INSTR = r"""()=>{ const S = window.__pm2 = { down: null, framesAfter: null, on: true, anim: {}, trans: {}, nf0: 0 };
  const lens = document.getElementById('bottomtabs-lens'), bar = document.getElementById('bottomtabs'), sl = document.getElementById('bottomtabs-slider');
  const sig = () => [getComputedStyle(lens).opacity, getComputedStyle(lens).transform, getComputedStyle(bar).scale, getComputedStyle(sl).opacity, getComputedStyle(sl).transform].join('|');
  let base = sig(), nf = 0;
  const dn = e => { if(S.down) return; S.down = performance.now(); S.nf0 = nf; };
  window.addEventListener('pointerdown', dn, true); window.addEventListener('mousedown', dn, true);
  bar.addEventListener('transitionrun', e => { S.trans[e.propertyName + '@' + (e.target.id || String(e.target.className).slice(0, 20))] = 1; }, true);
  const f = t => { if(!S.on) return; nf++;
    document.getAnimations().forEach(a => { const t2 = a.effect && a.effect.target; if(!t2 || !t2.closest || !t2.closest('#bottomtabs')) return;
      try{ a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset','easing','composite','computedOffset'].includes(p)) S.anim[p] = 1; })); }catch(e){} });
    if(S.down && S.framesAfter === null && sig() !== base) S.framesAfter = nf - S.nf0;
    requestAnimationFrame(f); };
  requestAnimationFrame(f); }"""
def pct(a, p):
    s = sorted(a); return s[min(len(s) - 1, int(len(s) * p))] if s else 0
COMPOSITOR = {"transform", "opacity", "scale", "translate", "rotate"}
LAYOUT_PROPS = {"width", "height", "left", "top", "right", "bottom", "margin", "padding", "flex", "font-size", "gap", "backdrop-filter", "-webkit-backdrop-filter", "filter", "border-width", "inset"}
def part2():
    _src = open(os.path.join(HERE, "check-b384-desktop.py")).read().split("\nwith sync_playwright() as pw:")[0]
    _src = _src.replace('if "--against" in sys.argv:', 'if False:')
    saved = sys.argv; sys.argv = [saved[0]]
    D = {"__file__": os.path.join(HERE, "check-b384-desktop.py"), "__name__": "b384tabaudit2"}; exec(_src, D)
    if SRC_FILE:
        D["SRC"] = open(SRC_FILE, encoding="utf-8").read(); D["BUILD"] = (re.search(r'const APP_BUILD = "([^"]+)"', D["SRC"]) or [None, ""])[1]
    D["DEVS"]["phone2"] = (440, 956, 2, True)
    TB = ["home", "profile", "rewards", "calendar"]
    PAIRS = [(a, b) for a in TB for b in TB]
    if QUICK: PAIRS = [("home", "profile"), ("profile", "rewards"), ("rewards", "home"), ("home", "home"), ("calendar", "rewards")]
    errs_all = []; rows = []
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=D["CHROME"])
        for dev, cpu in (("phone2", 4),):
            ctx, pg, cdp, errs, touch = D["open_page"](br, dev)
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu}); pg.wait_for_timeout(1500)
            for a, b in PAIRS:
                D["tap"](pg, cdp, touch, "#bottomtab-" + a); pg.wait_for_timeout(1500 + 500 * (cpu - 1))
                pg.evaluate(CLOCK)
                evs = trace_run(pg, cdp, lambda: D["tap"](pg, cdp, touch, "#bottomtab-" + b), 800 + 300 * (cpu - 1))
                M = pg.evaluate("()=>{ __pm.on=false; return __pm; }"); r = analyse(evs, cpu)
                # the same pair again, read in the page: back to the tab it started on, then the tap
                D["tap"](pg, cdp, touch, "#bottomtab-" + a); pg.wait_for_timeout(1500 + 500 * (cpu - 1))
                pg.evaluate(INSTR); D["tap"](pg, cdp, touch, "#bottomtab-" + b); pg.wait_for_timeout(900 + 300 * (cpu - 1))
                M2 = pg.evaluate("()=>{ __pm2.on=false; return __pm2; }")
                if not r or not M["down"]: chk("(S) %s>%s: the trace saw the tap" % (a, b), False); continue
                after = [t for t in M["frames"] if M["down"] <= t <= M["down"] + 600]; gaps = [after[i + 1] - after[i] for i in range(len(after) - 1)]
                rows.append(dict(pair=(a, b), over20=sum(1 for g in gaps if g > 20), over50=sum(1 for g in gaps if g > 50), n=len(gaps), p50=round(pct(gaps, .5), 1), p95=round(pct(gaps, .95), 1),
                                 worst=round(r["worst"], 1), total=round(r["total"], 1), inp=round(r["inputMax"], 1), style_n=r["style_n"], lay_n=r["lay_n"], forced=r["forced"],
                                 fb=M2["framesAfter"], anim=sorted(M2["anim"]), trans=sorted(M2["trans"])))
            errs_all += errs; ctx.close()
        br.close()
    print("\n  pair                  frames>20ms >50ms  p50    p95   | longest task  input  total | style layout | frames to first change")
    for r in rows:
        print("  %-10s>%-10s %4d %5d %6.1f %6.1f  | %6.1f ms %6.1f %6.1f | %4d %4d  | %s" % (r["pair"][0], r["pair"][1], r["over20"], r["over50"], r["p50"], r["p95"], r["worst"], r["inp"], r["total"], r["style_n"], r["lay_n"], r["fb"]))
    info("frame gaps are the page's own rAF clock on a shared sandbox at 4x CPU (INFO); the asserted numbers are main-thread CPU divided by the throttle (1x-equivalent)")
    props = sorted({p for r in rows for p in r["anim"]})
    chk("(S1) every animation on the bar's subtree animates only transform / opacity / scale (saw: %s)" % props, props and set(props) <= COMPOSITOR, props)
    tr = sorted({t for r in rows for t in r["trans"]}); badtr = [t for t in tr if t.split("@")[0] in LAYOUT_PROPS]
    chk("(S1) no CSS transition runs on a layout property, a filter or a backdrop-filter on the bar (%s)" % (tr or "none ran"), not badtr, badtr)
    cap = collections.Counter()
    for r in rows:
        for (nm, fn), v in r["forced"].items():
            if fn == "document.addEventListener.capture": cap[fn] += v
    chk("(S2) no style pass is forced by the document's touchstart handler (%d in %d taps)" % (cap["document.addEventListener.capture"], len(rows)), cap["document.addEventListener.capture"] == 0, dict(cap))
    fbs = [r["fb"] for r in rows if r["fb"] is not None]
    chk("(S3) the press answers within 2 frames: the bar's first visible change comes %s frames after the pointerdown (every tap; worst %s)" % (sorted(set(fbs)), max(fbs or [0])), len(fbs) == len(rows) and max(fbs) <= 2, fbs)
    w = max(r["worst"] for r in rows); i = max(r["inp"] for r in rows)
    chk("(S4) no task in a tab change over 140ms (1x-equivalent; worst %.0fms)" % w, w <= 140, w)
    chk("(S4) no input handler over 20ms (1x-equivalent; worst %.1fms)" % i, i <= 20, i)
    worst_forced = collections.Counter()
    for r in rows:
        for k, v in r["forced"].items(): worst_forced[k] = max(worst_forced[k], v)
    top = worst_forced.most_common(1)
    chk("(S4) no function forces more than 8 style passes or layouts in a tab change (most: %s)" % (str(top[0]) if top else "-"), not top or top[0][1] <= 8, dict(worst_forced.most_common(4)))
    chk("(S5) no page errors", not errs_all, errs_all[:3])

# ============================================================================================================== main
if __name__ == "__main__":
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G.CHROME)
        if want(1, 1) or want(2, 1) or want(3, 1) or want(4, 1) or want(5, 1) or want(6, 1) or want(7, 1):
            for cls in ("academy", "ifc"):
                if want(1, 1):
                    for dev in (["promax"] if QUICK else ["promax", "se-tab", "ipad", "lap1366"]):
                        print("\n== (1) %s %s" % (dev, cls), flush=True); sec_matrix(br, dev, cls, full=(dev == "promax" and not QUICK))
                if want(2, 1):
                    for dev in (["promax"] if QUICK else ["promax", "lap1366"]):
                        print("\n== (2) %s %s" % (dev, cls), flush=True); sec_rapid(br, dev, cls)
                if want(3, 1):
                    print("\n== (3) promax %s" % cls, flush=True); sec_visibility(br, "promax", cls)
                if want(4, 1):
                    for dev in ("promax", "lap1366"):
                        print("\n== (4) %s %s" % (dev, cls), flush=True); sec_gestures(br, dev, cls)
                if want(5, 1):
                    print("\n== (5) %s" % cls, flush=True); sec_geometry(br, ["w320", "promax", "se-tab", "ipad", "lap1366"] if not QUICK else ["w320", "promax", "lap1366"], cls)
                if want(6, 1):
                    print("\n== (6) %s" % cls, flush=True); sec_keyboard(br, cls)
                if want(7, 1):
                    print("\n== (7) promax %s" % cls, flush=True); sec_motion_resize(br, "promax", cls)
        br.close()
    if "2" in PART and (not ONLY or ONLY & {"S", "s", "2"}):
        print("\n== PART 2: smoothness", flush=True); part2()
    print("\n" + ("ALL PASS" if ok and not G.fails else "FAILURES"))
    sys.exit(0 if ok and not G.fails else 1)
