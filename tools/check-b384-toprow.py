#!/usr/bin/env python3
"""Build 384.89: THE TOP ROW SITS ON ONE LINE UNDER THE SYSTEM'S TOP BLUR, THE CHAT BUTTON IN ONE PLACE, AND NOTHING JUMPS.

Madison (installed iPhone 17 Pro Max, iOS 26): "By scrolling down just a smidge, it removes the stuff from the blurry area ... the
chat button would need to be moved and synced ... we just need to ever so slightly bring it down outside of the blurred area. Like
literally just on the edge." and "Ensure the chat button's position is consistent between screens". His 15:35 recording calibrates
the line (index.html, --edge-e): a title's ink is blurred to 74pt, sharp from 78pt; E = the inset + 18pt (x --zc), only in the
installed iPhone held upright with a notch or island. Elsewhere E is the inset and nothing may move but the chat button's twins.

Per device (installed Pro Max 440x956 62/34; the same phone at his 85% page zoom 518x1125 73/40; an installed SE 375x667 20/0;
iPad Pro 11" portrait 834x1194 and landscape 1194x834, 24/20; a Safari tab 440x797) and class (academy, Fire Code), on every
screen with a top row (onboarding from a fresh install; the rest on a used account; the run screens from a real run):
 (1) LINE: where there is a band (the first two), the top of every piece of ink in the top 40% of the screen - every text line's
     glyphs (canvas-measured from its font), button, icon, image and progress dot that is the page's - is at or below E (0.5px);
     elsewhere E is the inset (nothing to clear);
 (2) CHAT: #chatdock-btn has one rect (left, top, size) on every screen it is shown on, Home's; on a question it sits beside Pause
     (Pause owns the corner) with its top on the same line;
 (3) BACK: a round back button's middle is the chat button's middle (1px), and on a phone it is as far in from the left as the
     chat button is from the right (1px);
 (4) FIT: no screen scrolls that did not scroll on the previous build (--base, default origin/main);
 (5) CAP: on a question scrolled 200px, the strip from y 0 to the foot of the header row (on a phone, Pause's foot: it is in the
     row; on a tablet Pause is a corner button like the chat button) is solid paper down the left edge (no question text shows
     through above or between the row's controls);
 (6) TRANSITIONS (frame by frame, every rAF for the whole change): the bottom tabs Home -> Profile -> Leaderboard -> Settings ->
     Home, push and back (Start Studying and back, Settings -> Advanced -> back, Profile's badge case and back, Choose your mode ->
     Drill's units -> back), Profile's segments, a question (start, answer, the slide to the next, pause and resume, the last
     answer -> results -> Main menu), the chat sheet open and shut: the chat button's top never leaves the line (and its left never
     moves except into and out of a question), the tab bar never moves while shown, and every title row, once on the screen, stays
     where it comes to rest in every frame;
 (7) no page errors.
  python3 tools/check-b384-toprow.py [--against FILE] [--base FILE] [--devices promax,zoom85,se,ipadP,ipadL,safari] [--classes academy,ifc]
                                     [--only REGEX] [--no-transitions] [--no-base] [--shots DIR]      (384.86 must FAIL (1)-(3), (6))
"""
import json, os, re, sys, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_toprow_lib as L
from playwright.sync_api import sync_playwright
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
RAW = open(arg("--against"), encoding="utf-8").read() if arg("--against") else open(os.path.join(L.ROOT, "index.html"), encoding="utf-8").read()
NOBASE = "--no-base" in sys.argv
BASE = None if NOBASE else (open(arg("--base"), encoding="utf-8").read() if arg("--base") else
        subprocess.run(["git", "-C", L.ROOT, "show", "origin/main:index.html"], capture_output=True, text=True).stdout)
DEVS = (arg("--devices") or "promax,zoom85,se,ipadP,ipadL,safari").split(",")
CLASSES = (arg("--classes") or "academy,ifc").split(",")
ONLY = re.compile(arg("--only"), re.I) if arg("--only") else None
SHOTS = arg("--shots")
TRANS = "--no-transitions" not in sys.argv
ok = True; table = {}
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
    return bool(cond)
sweep = open(os.path.join(HERE, "sweep-layout.py"), encoding="utf-8").read()
RESULTS_STAGE = re.search(r'RESULTS_STAGE = """(.*?)"""', sweep, re.S).group(1)
Q = "theme.autoAdvance=false; theme.reduceMotion=true; theme.muteBanners=true;"
def run_js(mode, unit_expr="pickUnit()"):
    return ("showHome(); " + Q + " cfg.mode='%s'; cfg.source='all'; cfg.size=0; cfg.timer='off'; cfg.flashcards=false; const u = %s; cfg.units=[u];"
            " beginRun(QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u));" % (mode, unit_expr))
PICK = """window.pickUnit = () => { const c = {}; QUESTIONS.forEach(q => { const t = (q.topic || '').trim(); c[t] = (c[t] || 0) + 1; });
  return Object.keys(c).filter(t => c[t] >= 6).sort((a, b) => c[a] - c[b])[0]; };"""
# name, js (null: a run screen set up by RUNS), needs: '' | 'q' (wait for a question)
USED = [
    ("Home", "showHome()"), ("Choose your mode", "showModeSelect()"),
    ("units: drill", "cfg.mode='drill'; showSetup()"), ("units: exam", "cfg.mode='exam'; showSetup()"),
    ("units: review", "cfg.mode='review'; showSetup()"), ("units: game", "cfg.mode='game'; showSetup()"),
    ("Virtual Room", "showVirtualRoomChoice()"), ("Virtual Room host", "showVirtualRoomSetup()"), ("Virtual Room join", "showRoomBrowser()"),
    ("Profile", "showProfile()"), ("Stats", "showProfile('stats')"), ("Profile: Settings", "showProfile('settings')"),
    ("Rank ladder", "showRanksScreen()"), ("badge case", "showRanksScreen('badges')"), ("rank lore", "showRankLore('vanguard')"),
    ("Customize", "showCustomize()"), ("Customize: character", "showCustomize('character')"), ("Customize: banner", "showCustomize('banner')"),
    ("Customize: theme", "showCustomize('theme')"), ("Customize: effects", "showCustomize('fx')"),
    ("Leaderboard", "showRankings()"), ("Leaderboard board 2", "showRankings((rankingBoardsFor()[1] || {}).key)"),
    ("Leaderboard board 3", "showRankings((rankingBoardsFor()[2] || rankingBoardsFor()[0]).key)"), ("Leaderboard (list)", "showLeaderboard()"),
    ("Calendar", "showCalendar()"), ("Calendar tab", "showCalendarTab()"), ("Friends", "showFriends()"),
    ("Test history", "showTestReviewList()"), ("Test history detail", "showTestHistoryDetail((store.testHistory || [])[0] || null)"),
    ("Settings", "showAppearance()"), ("Settings: sound", "showAppearance({page:'sound'})"), ("Settings: study", "showAppearance({page:'study'})"),
    ("Settings: motion", "showAppearance({page:'motion'})"), ("Settings: sync", "showAppearance({page:'sync'})"),
    ("Settings: share", "showAppearance({page:'share'})"), ("Settings: leaderboard", "showAppearance({page:'rankings'})"),
    ("Settings: account", "showAppearance({page:'account'})"), ("Settings: classes", "showAppearance({page:'classes'})"),
    ("Advanced", "showAdvancedSettings()"), ("Contributors", "showCredits()"), ("Legal", "showSettingsText('legal')"),
    ("Terms", "showSettingsText('terms')"), ("Privacy", "showSettingsText('privacy')"), ("Report a bug", "showBugReport()"),
    ("Release history", "showReleaseHistory()"), ("Reset warning", "showResetWarning()"), ("Class catalog", "showClassCatalog()"),
    ("install guide", "showHome(); showInstallGuide('ios')"), ("install picker", "showInstallPlatformPicker()"),
    ("Home Screen sheet", "showHomeScreenSheet({from:'settings',device:'apple'})"), ("save-code card", "showHome(); showSaveCodeCard()"),
    ("code viewer", "showHome(); ifcOpenViewer({ title: 'Section 101', sub: 'Scope' })"), ("chat", "showHome(); openChatDock()"),
    ("rank cutscene", "showHome(); playTierCutscene('vanguard')"),
    ("question: drill", run_js("drill"), "q"), ("question: exam", run_js("exam"), "q"), ("question: game", run_js("game"), "q"),
    ("paused", run_js("drill") + " setTimeout(()=>pauseRun(), 3600);", "p"),
    ("review list", "showHome(); " + Q + " showAnswerReview([pickUnit()], 'all')"), ("flashcards", "showHome(); " + Q + " showFlashcards([pickUnit()], 'all')"),
    ("daily question", "showHome(); " + Q + " startDailyQuestion()"),
    ("results", "showHome(); __sweepResults('drill')"), ("results: retake", "showHome(); __sweepResults('retake')"),
    ("Nova's meeting", "showHome(); store.novaMet = 0; playNovaMeeting()"),   # last: it holds the pop-ups while he talks
]
FRESH = [("Get Started", "showGetStarted()"), ("Welcome", "showWelcome()"), ("sign-up check", "showWelcome(); showSignUpCheck()"),
         ("intro", "showWelcome(); showWelcomeIntro()"), ("class pick", "showWelcome(); showClassSelection()"),
         ("username", "showWelcome(); showWelcomeNamePrompt()"), ("character", "showWelcome(); showWelcomeCharacterPrompt()"),
         ("sign in", "showWelcome(); showWelcomeCodeEntry()"), ("your code", "showWelcome(); showWelcomeCodeReveal()"),
         ("install first", "showInstallFirst({device:'apple',inapp:false})")]
TEST = {"question: drill", "question: exam", "question: game", "paused", "review list", "flashcards", "daily question"}
GEOM = """()=>{ const R = s => { const e = document.querySelector(s); if(!e || !e.getClientRects().length) return null; const st = getComputedStyle(e); if(st.visibility === 'hidden' || st.display === 'none') return null;
    const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top, r.width, r.height] : null; };
  const back = R('#stage .settings-nav > :is(.ios-nav-back, .settings-nav-back)');
  return { chat: (() => { const b = document.getElementById('chatdock-btn'); return b && !b.closest('[hidden]') ? R('#chatdock-btn') : null; })(), back, pause: R('#pausebtn:not([hidden])'),
    inTest: !!document.querySelector('.chatdock.in-test'), W: innerWidth, scr: ((document.querySelector('#stage > *') || {}).className || '') + '' }; }"""
CAP = """()=>{ const t = document.querySelector('.wrap.test-pinned > .top'); const p = document.querySelector('#pausebtn:not([hidden])');
  if(!t) return null; const r = t.getBoundingClientRect(); return { foot: Math.max(r.bottom, p && innerWidth < 640 ? p.getBoundingClientRect().bottom : 0), paper: getComputedStyle(document.documentElement).getPropertyValue('--paper').trim(), sy: scrollY }; }"""
REC = """(ms)=>{ let n = 0; const tag = e => { if(!e) return null; if(!e.dataset.trk) e.dataset.trk = 'k' + (++window.__trkN || (window.__trkN = 1)); return e.dataset.trk; };
  const R = e => { if(!e || !e.getClientRects().length) return null; const s = getComputedStyle(e); if(s.visibility === 'hidden' || s.display === 'none' || parseFloat(s.opacity) < .05) return null; const r = e.getBoundingClientRect(); return r.width ? [r.left, r.top] : null; };
  window.__frames = []; const t0 = performance.now();
  window.__recP = new Promise(res => { const f = () => {
    const b = document.getElementById('chatdock-btn'), bar = document.querySelector('.bottomtabs:not([hidden])');
    const title = document.querySelector('#stage .settings-nav') || [...document.querySelectorAll('.wrap > #count:not(:empty)')].find(e => parseFloat(getComputedStyle(e).fontSize) > 4) || document.querySelector('.wrap > .top:has(#pausebtn:not([hidden]))');
    let tl = R(title); const sy = title && /^(fixed|sticky)$/.test(getComputedStyle(title).position) ? 0 : scrollY;
    window.__frames.push({ t: Math.round(performance.now() - t0), chat: b && !b.closest('[hidden]') ? R(b) : null, bar: bar && R(bar) ? [bar.offsetLeft, bar.offsetTop] : null,
      title: tl ? [tag(title), tl[1] + sy, sy] : null, scr: (document.querySelector('#stage > *') || {}).className || '' });
    if(performance.now() - t0 < ms) requestAnimationFrame(f); else res(window.__frames); }; requestAnimationFrame(f); }); }"""
TAP = """(sel)=>{ const el = typeof sel === 'string' ? document.querySelector(sel) : null; if(!el) return false; const b = el.getBoundingClientRect(), x = b.left + b.width / 2, y = b.top + b.height / 2;
  const mk = t => new PointerEvent(t, { bubbles: true, cancelable: true, pointerType: 'touch', pointerId: 31, isPrimary: true, clientX: x, clientY: y });
  el.dispatchEvent(mk('pointerdown')); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, clientX: x, clientY: y })); return true; }"""
errs = []
def boot(br, raw, dev, cls, fresh=False):
    ctx, pg, e = L.open_page(br, raw, dev, cls, fresh=fresh, settle=False)
    pg.add_init_script(RESULTS_STAGE)
    pg.add_init_script(PICK)
    pg.reload(); pg.wait_for_timeout(3200); pg.evaluate(L.QUIET); pg.wait_for_timeout(300)
    pg.evaluate("()=>{ " + RESULTS_STAGE + PICK + " }")
    return ctx, pg, e
def mount(pg, name, js, need=""):
    pg.evaluate(L.QUIET)
    pg.evaluate("()=>{ try{ ifcCloseViewer(); }catch(e){} try{ closeChatDock(); }catch(e){} document.querySelectorAll('.tier-cutscene,#supernova-cutscene,.installguide-overlay,.savecode-card').forEach(n=>n.remove()); }")
    pg.evaluate("()=>{ " + js + " }")
    if need == "q": pg.wait_for_selector(".qpanel .choice", timeout=30000); pg.wait_for_timeout(900)
    elif need == "p": pg.wait_for_selector("#stage .pausepanel", timeout=30000); pg.wait_for_timeout(900)
    else: pg.wait_for_timeout(1100)
    # at rest at the page's top (a screen that scrolls itself to something - the rank ladder to your rank - is put back)
    last, still = None, 0
    for _ in range(16):   # let a screen's own scroll finish first
        y = pg.evaluate("()=>scrollY")
        still = still + 1 if y == last else 0; last = y
        if still >= 2: break
        pg.wait_for_timeout(250)
    for _ in range(4):
        pg.evaluate("()=>{ document.querySelectorAll('#tour-overlay, #tour-tooltip, .intro-pop, #intro-pop, .update-banner, .daily-alert, .unlock-card').forEach(n=>n.remove()); window.scrollTo({ top: 0, behavior: 'instant' }); }")
        pg.wait_for_timeout(350)
        if pg.evaluate("()=>scrollY") < .5: break
def measure(br, raw, dev, cls, base=False):
    out = {}
    for fresh, lst in ((True, FRESH), (False, USED)):
        if fresh and cls != CLASSES[0]: continue
        lst = [s for s in lst if not ONLY or ONLY.search(s[0])]
        if not lst: continue
        for attempt in range(3):
            res = {}; crashed = False
            try:
                ctx, pg, e = boot(br, raw, dev, cls, fresh=fresh)
                for item in lst:
                    name, js = item[0], item[1]; need = item[2] if len(item) > 2 else ""
                    try:
                        mount(pg, name, js, need)
                        ink = pg.evaluate(L.INK); geo = pg.evaluate(GEOM)
                        res[name] = (ink, geo)
                        if SHOTS and not base: pg.screenshot(path=os.path.join(SHOTS, "%s_%s_%s.png" % (dev, cls, re.sub(r"\W+", "_", name))))
                        if name == "question: drill" and not base:
                            pg.evaluate("()=>{ const s = document.createElement('div'); s.id = '__pad'; s.style.height = '1600px'; document.getElementById('stage').appendChild(s); window.scrollTo({ top: 200, behavior: 'instant' }); }"); pg.wait_for_timeout(500)
                            cap = pg.evaluate(CAP); f = os.path.join(SHOTS or "/tmp", "toprow_cap_%s_%s.png" % (dev, cls)); pg.screenshot(path=f)
                            res["__cap"] = (cap, f); pg.evaluate("()=>{ document.getElementById('__pad')?.remove(); window.scrollTo({ top: 0, behavior: 'instant' }); }")
                    except Exception as ex:
                        if "rash" in str(ex): raise
                        res[name] = (None, str(ex)[:200])
                if not base: errs.extend("%s %s: %s" % (dev, cls, x) for x in e)
                ctx.close()
            except Exception as ex:
                crashed = True   # a crash, a page that never loads on a loaded machine: again (3 times), then it is reported
                try: ctx.close()
                except Exception: pass
                if not crashed: raise
            if not crashed: break
            print("    (renderer crashed or the page did not load on a loaded machine: again)", flush=True)
        if crashed:
            for item in lst: res.setdefault(item[0], (None, "the page never came up in 3 tries"))
        out.update(res)
    return out
def eq(a, b, tol=.5): return a is not None and b is not None and all(abs(x - y) <= tol for x, y in zip(a, b))
def check_screens(dev, cls, M, B):
    name, W, H, ins, installed, ua, gated = L.DEVICES[dev]
    tag = "%s, %s" % (name, "Fire Code" if cls == "ifc" else "academy")
    below = []; chat_off = []; back_off = []; newscroll = []; failed = []
    home = M.get("Home", (None, {}))[1] or {}
    hc = home.get("chat") if isinstance(home, dict) else None
    phone = W < 640
    for scr, (ink, geo) in M.items():
        if scr.startswith("__"): continue
        if ink is None: failed.append((scr, geo)); continue
        row = table.setdefault(scr, {})
        # the line is the gate's own (his recording: the inset + 16pt, + 2pt, in points: x the page zoom), not the page's word for it
        zc = (W / 440.0) if dev == "zoom85" else 1.0
        E = ins[0] + (18 * zc if gated else 0); mn = ink["min"]
        if ink["E"] is None or abs(ink["E"] - E) > .5: below.append((scr, "the page's line (--top-e) is %s, not %.1f" % (ink["E"], E))); good = False
        good = True
        if gated and mn is not None and mn < E - .5:
            below.append((scr, "E %.1f" % E, [(i["what"], i["top"]) for i in ink["items"] if i["top"] < E - .5][:4])); good = False
        c = geo["chat"]
        if c and hc and scr not in ("rank cutscene",):   # a cutscene flies the corner buttons away on purpose
            if scr in TEST and geo["inTest"]:
                # beside Pause, centred on Pause's line (Pause owns the corner): under the band that line IS the chat button's (E);
                # where there is no band (an SE, an iPad, a Safari tab) the test row stays on the page's own floor, as before
                p = geo["pause"]
                if gated and abs(c[1] - hc[1]) > .5: chat_off.append((scr, "in test, off the line", [round(v, 1) for v in c])); good = False
                elif p and abs((c[1] + c[3] / 2) - (p[1] + p[3] / 2)) > 1: chat_off.append((scr, "in test, not level with Pause", [round(v, 1) for v in c], [round(v, 1) for v in p])); good = False
            elif not eq(c, hc): chat_off.append((scr, [round(v, 1) for v in c], "Home", [round(v, 1) for v in hc])); good = False
        if c and geo["back"] and not geo["inTest"]:
            bk = geo["back"]; d = abs((bk[1] + bk[3] / 2) - (c[1] + c[3] / 2)); dx = abs(bk[0] - (geo["W"] - c[0] - c[2])) if phone else 0
            if d > 1 or dx > 1: back_off.append((scr, "mid %.1f vs %.1f, left %.1f vs right %.1f" % (bk[1] + bk[3] / 2, c[1] + c[3] / 2, bk[0], geo["W"] - c[0] - c[2]))); good = False
        if B is not None and scr in B and B[scr][0] is not None and isinstance(B[scr][1], dict) and B[scr][1].get("scr") == geo.get("scr"):   # the same screen on both builds
            if B[scr][0]["scroll"] <= 1 and ink["scroll"] > 1: newscroll.append((scr, "%d (was %d)" % (ink["scroll"], B[scr][0]["scroll"]))); good = False
        row[(dev, cls)] = "ok" if good else "FAIL"
    n = len([k for k in M if not k.startswith("__")])
    for lst, what in ((below, "above E"), (chat_off, "chat"), (back_off, "back"), (newscroll, "scroll")):
        for x in lst: print("      %s: %s" % (what, x), flush=True)
    chk("%s (1): %s on all %d screens" % (tag, "every top row's ink is at or below E (the inset + 18pt) and the page's line is E" if gated else
        "no band here - the page's line is the inset (%s) and nothing has to clear it" % ins[0], n), not below, below)
    chk("%s (2): the chat button is in Home's place (%s) on every screen it shows on, beside Pause on its line in a question" % (tag, hc and [round(v, 1) for v in hc]), hc and not chat_off, chat_off)
    chk("%s (3): every round back button is level with the chat button%s" % (tag, " and mirrors its inset" if phone else ""), not back_off, back_off)
    if B is not None: chk("%s (4): no screen scrolls that did not before" % tag, not newscroll, newscroll)
    chk("%s: every screen mounted" % tag, not failed, failed)
    if "__cap" in M and M["__cap"][0]:
        from PIL import Image
        cap, f = M["__cap"]; im = Image.open(f).convert("RGB"); sc = im.size[0] / W
        pap = cap["paper"]; m = re.match(r"#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})", pap.strip(), re.I)
        pc = tuple(int(x, 16) for x in m.groups()) if m else None
        top_strip = int(max(ins[0], 12) * sc)
        ys = range(top_strip + 2, int((cap["foot"] - 1) * sc))
        bad = [(round(y / sc, 1), im.getpixel((int(6 * sc), y))) for y in ys if pc and max(abs(a - b) for a, b in zip(im.getpixel((int(6 * sc), y)), pc)) > 3]
        chk("%s (5): a question scrolled %dpx: the header is solid paper %s from the strip to its foot (y %.0f) - nothing shows through" % (tag, cap["sy"], pap, cap["foot"]), cap["sy"] >= 150 and not bad, bad[:5])
def transitions(br, dev, cls, qtop=None):
    name, W, H, ins, installed, ua, gated = L.DEVICES[dev]
    tag = "%s, %s" % (name, "Fire Code" if cls == "ifc" else "academy")
    for attempt in range(3):
        try:
            ctx, pg, e = boot(br, RAW, dev, cls)
            pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(900); pg.evaluate(L.QUIET)
            g0 = pg.evaluate(GEOM); hc = g0["chat"]
            results = []
            def step(label, action, ms=1300, test_move=False, wait_sel=None):
                pg.evaluate(REC, ms)
                if action.startswith("tap:"): pg.evaluate(TAP, action[4:])
                else: pg.evaluate("()=>{ " + action + " }")
                fr = pg.evaluate("()=>window.__recP")
                if wait_sel:
                    try: pg.wait_for_selector(wait_sel, timeout=20000)
                    except Exception: pass
                    pg.evaluate(REC, 900); fr += pg.evaluate("()=>window.__recP")
                pg.evaluate(L.QUIET)
                bad = []
                cs = [f["chat"] for f in fr if f["chat"]]
                if hc:
                    tops = sorted(set(round(c[1], 1) for c in cs))
                    # into and out of a question the button goes beside Pause: on the band's line that is the same top; elsewhere it is
                    # Pause's line (measured on the question screen), and nothing else
                    ok_tops = [hc[1]] + ([qtop] if (test_move and qtop is not None and not gated) else [])
                    if any(min(abs(t - o) for o in ok_tops) > .5 for t in tops): bad.append("chat top %s (line %.1f%s)" % (tops[:5], hc[1], "" if len(ok_tops) == 1 else ", Pause's %.1f" % qtop))
                    if not test_move:
                        lefts = sorted(set(round(c[0], 1) for c in cs))
                        if any(abs(x - hc[0]) > .5 for x in lefts): bad.append("chat left %s" % lefts[:5])
                # the bar is still on each screen (a screen may stand it elsewhere from its first frame: a unit picker stacks it
                # above its Start button, on main too) - so per screen, never moving within one
                bys = {}
                for f in fr:
                    if f["bar"]: bys.setdefault(f["scr"], set()).add(round(f["bar"][1], 1))
                for k, v in bys.items():
                    if max(v) - min(v) > .5: bad.append("tab bar top %s on %s" % (sorted(v)[:6], k[:30]))
                byk = {}
                for f in fr:
                    if f["title"]: byk.setdefault(f["title"][0] + '|' + f["scr"], []).append(f["title"][1])
                for k, ys in byk.items():
                    if max(ys) - min(ys) > .5: bad.append("title %s at %s; frames %s" % (k, sorted(set(round(y, 1) for y in ys))[:6], [(f["t"], round(f["title"][1], 1), f["title"][2], f["scr"][:30]) for f in fr if f["title"] and f["title"][0] == k][:3] + [(f["t"], round(f["title"][1], 1), f["title"][2], f["scr"][:30]) for f in fr if f["title"] and f["title"][0] == k][-2:]))
                results.append((label, len(fr), bad))
            step("Home -> Profile (tab)", "tap:#bottomtab-profile")
            step("Profile -> Stats (segment)", "tap:#stage .navsegment .iconbtn:nth-child(2)")
            step("Stats -> Profile (segment)", "tap:#stage .navsegment .iconbtn:nth-child(1)")
            step("Profile -> Leaderboard (tab)", "tap:#bottomtab-rewards")
            step("Leaderboard -> Settings (tab)", "tap:#bottomtab-settings")
            step("Settings -> Advanced (push)", "showAdvancedSettings()")
            step("Advanced -> back", "tap:#stage .settings-nav > .settings-nav-back")
            step("Settings -> Home (tab)", "tap:#bottomtab-home")
            step("Home -> Start Studying", "tap:#stage .playbtn")
            step("Choose your mode -> back", "tap:#stage .settings-nav > :is(.ios-nav-back, .settings-nav-back)")
            step("Home -> Start Studying (again)", "tap:#stage .playbtn")
            step("Choose your mode -> Drill's units", "tap:#stage .modecard")
            step("units -> back", "tap:#stage .settings-nav > :is(.ios-nav-back, .settings-nav-back)")
            step("-> Profile", "tap:#bottomtab-profile")
            step("Profile -> badge case (push)", "showRanksScreen('badges')")
            step("badge case -> back", "tap:#stage .settings-nav > :is(.ios-nav-back, .settings-nav-back)")
            step("Home: chat sheet open", "showHome(); openChatDock()")
            step("chat sheet shut", "closeChatDock()")
            step("Home -> a question", run_js("drill"), test_move=True, wait_sel=".qpanel .choice")
            step("answer", "const r = correctSlot(order[pos]); document.querySelector('.choice[data-index=\"' + r + '\"]').click();", 700, test_move=True)
            step("the slide to the next question", "document.getElementById('nextbtn').click();", 1300, test_move=True)
            step("Pause", "pauseRun()", 900, test_move=True)
            step("Resume", "const b = [...document.querySelectorAll('#stage button')].find(b => /resume|keep going|continue/i.test(b.textContent)); if(b) b.click();", 1100, test_move=True)
            pg.evaluate("()=>{ const go = () => { if(!document.querySelector('.choice')) return; const r = correctSlot(order[pos]); document.querySelector('.choice[data-index=\"' + r + '\"]').click(); if(pos < order.length - 1) setTimeout(()=>{ document.getElementById('nextbtn').click(); setTimeout(go, 500); }, 250); }; go(); }")
            pg.wait_for_function("()=>pos >= order.length - 1 && !!document.getElementById('nextbtn')", timeout=60000)
            step("last answer -> results", "document.getElementById('nextbtn').click();", 2400, test_move=True)
            step("results -> Main menu", "const b = [...document.querySelectorAll('#stage button')].find(b => /main menu/i.test(b.textContent)); if(b) b.click(); else showHome();", 1500, test_move=True)
            errs.extend("%s %s transitions: %s" % (dev, cls, x) for x in e)
            ctx.close()
            break
        except Exception as ex:
            try: ctx.close()
            except Exception: pass
            if "rash" not in str(ex) and "closed" not in str(ex) and attempt == 2: chk("%s (6): the transitions ran" % tag, False, str(ex)[:300]); return
            if attempt == 2: return
            print("    (again: %s)" % str(ex)[:120], flush=True)
    for label, n, bad in results:
        chk("%s (6) %s: %d frames, chat on its line, the tab bar and the title row still" % (tag, label, n), n >= 2 and not bad, bad)
        table.setdefault("transition: " + label, {})[(dev, cls)] = "ok" if (n >= 2 and not bad) else "FAIL"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    if SHOTS: os.makedirs(SHOTS, exist_ok=True)
    for dev in DEVS:
        for cls in CLASSES:
            t0 = time.time()
            M = measure(br, RAW, dev, cls)
            B = None if NOBASE else measure(br, BASE, dev, cls, base=True)
            check_screens(dev, cls, M, B)
            qg = M.get("question: drill", (None, None))[1]
            if TRANS: transitions(br, dev, cls, qg["chat"][1] if isinstance(qg, dict) and qg.get("chat") else None)
            print("    (%s %s: %.0fs)" % (dev, cls, time.time() - t0), flush=True)
    br.close()
chk("(7) no page errors", not errs, errs[:6])
cols = [(d, c) for d in DEVS for c in CLASSES]
print("\nTABLE (screen x device/class):\n" + "%-34s" % "" + " ".join("%-9s" % (d[:5] + "/" + c[:3]) for d, c in cols))
for scr, row in table.items():
    print("%-34s" % scr[:34] + " ".join("%-9s" % row.get(k, "-") for k in cols))
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
