#!/usr/bin/env python3
"""Build 384 r15: A TAP ON A TAB ALWAYS LANDS ON THAT TAB'S OWN ROOT.

Madison: "if I'm selecting a unit, go to settings, and then hit home it goes back to units?? Fix that and ensure none of it does that."
The cause: Profile, Calendar and the rank screens set a flag (returnToSetupAfterTabs) when the unit screen was the one being left, and
the next tap on the Home tab built the unit screen instead of Home. Removed. This walks the whole class of it.

THE MATRIX. For every STARTING SCREEN (the ones below: Home, the modes, the units in Drill and in Review with a unit ticked, Customize,
Friends, the badge case, the rank ladder, a Settings page, Test history, Review's list, flash cards, the Virtual Room's choice / setup /
lobby, the chat open, every tab root and Profile's other top tabs, and - where the bar is hidden by design - a run's question, its Pause,
a saved test, the daily question and a run's results, left by the screen's own exit) x EVERY TAB OF THE CLASS'S BAR (academy: Home, Profile,
Leaderboard, Calendar; Fire Code: Home, Profile, Leaderboard, Settings), each tapped for real (a finger's tap on the phone, a mouse's
click on the laptop):
  (1) the tab's own root is up (read off the page: its screen's class, not a label) and no other tab's root is;
  (2) exactly that tab is lit;
  (3) nothing of the screen it came from is in the page (no unit screen, no mode screen, no sheet, no resume card over it);
  (4) the Home tab, tapped next, lands on Home with Home lit, from every other tab - and a unit ticked and left behind is not brought back.
Plus: (5) a CHAIN, every tab in turn and back to Home, from each starting screen; (6) the TEST IN PROGRESS still behaves as designed:
the Home path (confirmMainMenu) on a running drill asks "Leave to main menu?" with Keep going and Leave, Keep going resumes it, Leave goes
Home, and the Home tab afterwards is Home; on the daily question it goes straight Home; Save and exit still keeps the test and Start
Studying still offers it ("Resume test" / "Start a new test"), while a Home tap goes to Home and not to the offer; (7) the units are
kept or dropped as before: arriving at the units by Start Studying shows none ticked, and a Home tap never builds that screen.

On a phone (an iPhone 17 Pro Max installed, 440x956) and a laptop (1536x864, a mouse), in both classes.
Run:  python3 tools/check-b384-tabroots.py [--quick] [--only STARTING-SCREEN-SUBSTRING] [academy|ifc] [--against REV|DIR|path/to/index.html]  [device ...]   (devices: promax laptop se)
      --against HEAD~1 / the build before r15 must FAIL (1)/(4) from the units screen, from Profile, Calendar, the rank screens.
"""
import importlib.util, os, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
argv = sys.argv[1:]
against = []
if "--against" in argv:
    i = argv.index("--against"); target = argv[i + 1]; del argv[i:i + 2]
    if os.path.isfile(target):   # a bare index.html: a copy of the repo's other files around it
        d = tempfile.mkdtemp(prefix="tabroots-")
        for n in ["ifc", "launch", "share"]:
            if os.path.isdir(os.path.join(REPO, n)): shutil.copytree(os.path.join(REPO, n), os.path.join(d, n))
        shutil.copy(os.path.join(REPO, "version.json"), d); shutil.copy(target, os.path.join(d, "index.html"))
        target = d
    against = ["--against", target]
QUICK = "--quick" in argv
if QUICK: argv.remove("--quick")
CLASSES = [c for c in ("academy", "ifc") if c in argv]
argv = [a for a in argv if a not in ("academy", "ifc")]
ONLY = None
if "--only" in argv:
    i = argv.index("--only"); ONLY = argv[i + 1].lower(); del argv[i:i + 2]
want = argv or ["promax", "laptop"]
sys.argv = [sys.argv[0]] + against
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from playwright.sync_api import sync_playwright
chk = G.chk

TABS = {"academy": ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-calendar"],
        "ifc": ["bottomtab-home", "bottomtab-profile", "bottomtab-rewards", "bottomtab-settings"]}
# the screen each tab's root is (read off the page, not a label); the Profile root is the first of Profile's top tabs
ROOT = {"bottomtab-home": ".screen-home-actual", "bottomtab-profile": ".screen-profile .profile-identity-tab", "bottomtab-rewards": ".screen-rankings",
        "bottomtab-calendar": ".screen-calendar-tab", "bottomtab-settings": ".screen-settings"}
SHOWING = "(s)=>[...document.querySelectorAll('#stage '+s)].some(e=>!e.closest('[hidden]') && e.getClientRects().length>0)"
# every tab root showing now, and what else of another screen is (a unit screen, the modes, a sheet, a resume card)
STATE = r"""(roots)=>{ const vis=e=>!e.closest('[hidden]') && e.getClientRects().length>0;
  const showing = Object.entries(roots).filter(([k,s])=>[...document.querySelectorAll('#stage '+s)].some(vis)).map(([k])=>k);
  const stray = ['.screen-setup', '.modeselect', '.screen-customize', '.screen-friends', '.screen-answerreview', '.screen-flashcards', '.screen-vroom',
                 '.resume-offer', '.unitdetail', '.pausepanel'].filter(s=>[...document.querySelectorAll(s)].some(vis));
  const lit=[...document.querySelectorAll('#bottomtabs .bottomtab.active')].map(t=>t.id);
  const tb=document.getElementById('bottomtabs');
  const top=[...document.querySelectorAll('#stage .navsegment .iconbtn, #stage .pf-tabs button, #stage [role=tab]')].filter(vis);
  const topOn=top.findIndex(b=>b.classList.contains('active')||b.getAttribute('aria-selected')==='true'||b.getAttribute('aria-pressed')==='true');
  return { showing, stray, lit, bar: !!tb && !tb.hidden && getComputedStyle(tb).display!=='none', topOn, nTop: top.length,
    cls: (document.querySelector('#stage > .panel')||{}).className||'' }; }"""
# a tab a person can tap: the bar is shown, the tab is in it and nothing else (the chat's dock, a loading screen) is on top of its middle
BAR_TAB_VISIBLE = """(i)=>{ const b=document.getElementById(i), bar=document.getElementById('bottomtabs');
  if(!b || b.hidden || !bar || bar.hidden || getComputedStyle(bar).display==='none' || b.getClientRects().length===0) return false;
  const r=b.getBoundingClientRect(); if(r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth) return false;
  const e=document.elementFromPoint(r.left+r.width/2, r.top+r.height/2); return !!e && b.contains(e); }"""

def stage_up(pg):   # the page has settled: one screen in the stage, nothing still sliding
    pg.wait_for_timeout(120)

def press(pg, tab_id, touch):
    """a finger's tap on a phone; on a laptop a real mouse (move, button down, a beat, button up - as check-b384-mouse does, not a script's click)"""
    sel = "#" + tab_id
    if touch: pg.tap(sel, timeout=20000); return
    c = pg.evaluate("(id)=>{ const b=document.getElementById(id); if(!b||b.hidden) return null; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }", tab_id)
    if not c: raise Exception("no such tab " + tab_id)
    pg.mouse.move(c[0], c[1], steps=4); pg.mouse.down(); pg.wait_for_timeout(60); pg.mouse.up()

def settle(pg, ms=450):
    pg.wait_for_timeout(ms); G.clear_popups(pg)

def land(pg, tab_id, touch, ms=2500):
    """tap the tab; wait for its root; return the state read a moment after"""
    press(pg, tab_id, touch)
    t = 0
    while t < ms:
        if pg.evaluate(SHOWING, ROOT[tab_id]): break
        pg.wait_for_timeout(50); t += 50
    pg.wait_for_timeout(300); G.clear_popups(pg)
    return pg.evaluate(STATE, ROOT)

def verdict(st, tab_id):
    bad = []
    if tab_id not in [k for k in st["showing"]]: bad.append("its root is not up (stage: %s; showing %s)" % (st["cls"][:50], st["showing"]))
    others = [k for k in st["showing"] if k != tab_id]
    if others: bad.append("another tab's root is up too: %s" % others)
    if st["lit"] != [tab_id]: bad.append("lit tabs %s, wanted [%s]" % (st["lit"], tab_id))
    if st["stray"]: bad.append("left over from another screen: %s" % st["stray"])
    if tab_id == "bottomtab-profile" and st["topOn"] > 0: bad.append("Profile's top tab %d is up, not the first" % st["topOn"])
    return bad

# ------------------------------------------------------------------------------------------------ the starting screens
def js(code):
    return lambda pg, cls, touch: pg.evaluate(code)

def tapc(pg, sel, touch, nth=0):
    loc = pg.locator(sel).nth(nth)
    loc.scroll_into_view_if_needed(timeout=10000)
    if touch: loc.tap(timeout=20000); return
    c = loc.evaluate("e=>{ const r=e.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }")
    pg.mouse.move(c[0], c[1], steps=4); pg.mouse.down(); pg.wait_for_timeout(60); pg.mouse.up()

def r_home(pg, cls, touch): pg.evaluate("()=>showHome()")
def start_studying(pg, touch):
    """Start Studying as the screen has it: Home's own button, or the bar's Start tab where the bar carries one (a laptop's)"""
    vis = pg.evaluate("()=>{ const b=document.querySelector('.panel.home.screen-home-actual .playbtn'); return !!b && b.getClientRects().length>0 && getComputedStyle(b).visibility!=='hidden'; }")
    if vis: tapc(pg, ".panel.home.screen-home-actual .playbtn", touch)
    else: press(pg, "bottomtab-start", touch)
def r_modes(pg, cls, touch):
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(500); G.clear_popups(pg)
    start_studying(pg, touch); pg.wait_for_timeout(700)
def r_units(mode, ticked):
    def f(pg, cls, touch):
        r_modes(pg, cls, touch); tapc(pg, ".modecard[data-mode=%s]" % mode, touch); pg.wait_for_timeout(800); G.clear_popups(pg)
        if ticked:
            tapc(pg, "#stage .pick", touch, 1); pg.wait_for_timeout(300)
    return f
def begin(pg):
    """a drill, started as the app starts one, and waited for on the page: LOADING TEST (about 3s), then the first question"""
    pg.evaluate(G.START_DRILL)
    for _ in range(200):
        if pg.evaluate("()=>!document.getElementById('teststart-overlay') && !!document.querySelector('#stage .choice')"): break
        pg.wait_for_timeout(50)
    pg.wait_for_timeout(500)
def r_pause(pg, cls, touch):
    begin(pg); pg.evaluate("()=>pauseRun()"); pg.wait_for_timeout(500)
def r_question(pg, cls, touch):
    begin(pg)
def r_daily(pg, cls, touch):
    pg.evaluate("()=>startDailyQuestion()"); pg.wait_for_timeout(1500)
def r_results(pg, cls, touch):
    begin(pg)
    pg.evaluate("""async ()=>{ theme.reduceMotion = true; theme.muteBanners = true;
      order.forEach((qi, k) => { attempts[qi] = k < 2 ? 2 : 1; picked[qi] = optionOrder(qi).indexOf(QUESTIONS[qi].answer); });
      stopQuestionTimer(); summarize(); await new Promise(r=>setTimeout(r,1500)); }""")
    pg.wait_for_timeout(600)
def r_vlobby(pg, cls, touch):
    pg.evaluate("""()=>{ const me=publicIdOf(); const parts={}; parts[me]={name:'Casey',avatarChar:'ghost',level:41,badges:6,joinedAt:1,seen:9e15,ready:false};
      window.__cloud.vrooms['ROOM384']={hostCode:me,hostName:'Casey',units:['Identity Crimes'],versions:{},game:'race',open:false,status:'waiting',mode:'exam',createdAt:1,count:null,participants:parts};
      vroomCode='ROOM384'; vroomMyKey=me; vroomIsHost=true; vroomIsOpen=false; vroomUnits=['Identity Crimes'];
      vroomLastDoc={code:'ROOM384',data:JSON.parse(JSON.stringify(window.__cloud.vrooms.ROOM384))}; showVirtualRoomLobby(); }""")

# (name, classes, reach, kind)  kind: "bar" = the bar is up here and every tab is tapped; "hidden" = the bar is hidden by design here
STARTS = [
    ("Home", "both", r_home, "bar"),
    ("the modes (Start Studying)", "both", r_modes, "bar"),
    ("the units, Drill, a unit ticked", "both", r_units("drill", True), "bar"),
    ("the units, Review, a unit ticked", "both", r_units("review", True), "bar"),
    ("Customize", "both", js("()=>showCustomize()"), "bar"),
    ("Friends", "both", js("()=>showFriends()"), "bar"),
    ("the badge case", "both", js("()=>showRanksScreen('badges')"), "bar"),
    ("the rank ladder", "both", js("()=>showRanksScreen()"), "bar"),
    ("a Settings page (Sound)", "both", js("()=>showAppearance({ page: 'sound' })"), "bar"),
    ("a Settings page (Account)", "both", js("()=>showAppearance({ page: 'account' })"), "bar"),
    ("Test history", "both", js("()=>showTestReviewList()"), "bar"),
    ("Review's list", "both", js("()=>{ cfg.mode='review'; showAnswerReview([topicsIn(QUESTIONS)[0]], 'all'); }"), "bar"),
    ("flash cards", "both", js("()=>{ cfg.mode='review'; showFlashcards([topicsIn(QUESTIONS)[0]], 'all'); }"), "bar"),
    ("the Virtual Room's choice", "both", js("()=>showVirtualRoomChoice()"), "bar"),
    ("the Virtual Room's setup", "both", js("()=>showVirtualRoomSetup()"), "bar"),
    ("the Virtual Room's lobby", "both", r_vlobby, "bar"),
    ("the chat, open on Home", "both", js("()=>{ showHome(); openChatDock(); }"), "bar"),
    ("Profile", "both", js("()=>showProfile()"), "bar"),
    ("Profile's Stats", "both", js("()=>showProfile('stats')"), "bar"),
    ("Profile's Settings tab", "academy", js("()=>showProfile('settings')"), "bar"),
    ("the Leaderboard", "both", js("()=>showRankings()"), "bar"),
    ("the Calendar", "academy", js("()=>showCalendarTab()"), "bar"),
    ("Settings (Fire Code's tab)", "ifc", js("()=>showAppearance()"), "bar"),
]
HIDDEN = [
    ("a question", "both", r_question),
    ("Pause", "both", r_pause),
    ("the daily question", "both", r_daily),
    ("a run's results", "both", r_results),
]
# where each hidden-bar screen is left by its own exit, as a person leaves it (read in the page, not by a tab)
LEAVE = {
    "a question": "()=>{ try{ confirmMainMenu(); }catch(e){} }",
    "Pause": "()=>{ const b=document.getElementById('pause-save') || document.getElementById('pause-exit'); b && b.click(); }",
    "the daily question": "()=>confirmMainMenu()",
    "a run's results": "()=>showHome()",
}

def reset(pg):
    pg.evaluate("""()=>{ try{ closeChatDock(); }catch(e){} try{ document.getElementById('resume-offer')?.remove(); }catch(e){}
      try{ testInProgress=false; paused=false; }catch(e){} try{ vroomCode=null; vroomMyKey=null; vroomIsHost=false; vroomUnits=[]; }catch(e){}
      window.forceHideBottomTabs=false; showHome(); }""")
    pg.wait_for_timeout(350); G.clear_popups(pg)

def reach_retry(pg, reach, cls, touch):
    """a machine under load can be slow to put a screen up: one more try from Home before a screen is called unreachable"""
    try: reach(pg, cls, touch)
    except Exception:
        reset(pg); pg.wait_for_timeout(1500); reach(pg, cls, touch)

def walk(br, dev, cls):
    touch = G.DEV[dev][6]
    pg = G.open_dev(br, dev, [G.seed_init(cls)])
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); G.clear_popups(pg)
    tabs = TABS[cls]
    bad = []; n = 0; barless = []; info = []
    def shown(): return pg.evaluate("(ts)=>ts.filter(i=>{const b=document.getElementById(i);return !!b&&!b.hidden&&b.getClientRects().length>0;})", tabs)
    for name, which, reach, kind in STARTS:
        if which not in ("both", cls): continue
        if ONLY and ONLY not in name.lower(): continue
        if QUICK and name not in ("Home", "the units, Drill, a unit ticked", "Profile", "Profile's Settings tab", "the badge case", "the Calendar", "Settings (Fire Code's tab)", "Friends"): continue
        for T in tabs:
            reset(pg)
            try:
                reach_retry(pg, reach, cls, touch); settle(pg, 450)
            except Exception as e:
                bad.append((name, "cannot be reached: %s" % str(e)[:100])); break
            if T == tabs[0]:
                info.append("%s: bar %s, lit %s" % (name, "up" if pg.evaluate(STATE, ROOT)["bar"] else "hidden", pg.evaluate(STATE, ROOT)["lit"]))
            if not pg.evaluate(BAR_TAB_VISIBLE, T):
                barless.append((name, T)); continue
            n += 1
            try:
                st = land(pg, T, touch)
            except Exception as e:
                bad.append((name + " > " + T, "tap failed: %s" % str(e)[:100])); continue
            v = verdict(st, T)
            if v: bad.append((name + " > " + T, v))
            if T != tabs[0]:   # and Home, tapped next, is Home
                n += 1
                try:
                    st = land(pg, tabs[0], touch)
                    v = verdict(st, tabs[0])
                    if v: bad.append((name + " > " + T + " > Home", v))
                except Exception as e:
                    bad.append((name + " > " + T + " > Home", "tap failed: %s" % str(e)[:100]))
    chk("%s %s: from %d starting screens x every tab (%d taps, %d with the bar hidden by design): the tab's own root, that tab lit, nothing left "
        "of the screen it came from, and Home from each tab is Home" % (dev, cls, sum(1 for s in STARTS if s[1] in ("both", cls)), n, len(barless)),
        not bad, bad[:6])
    for line in info[:30]: print("    INFO " + line, flush=True)
    if barless: print("    INFO bar hidden (so no tab to tap) on: %s" % sorted({b[0] for b in barless}), flush=True)

    # ---- (5) the chain: every tab in turn and back to Home, from each start where the bar is up
    cbad = []; cn = 0
    for name, which, reach, kind in STARTS:
        if which not in ("both", cls): continue
        if ONLY and ONLY not in name.lower(): continue
        if QUICK and name not in ("Home", "the units, Drill, a unit ticked", "Friends"): continue
        reset(pg)
        try: reach_retry(pg, reach, cls, touch); settle(pg, 450)
        except Exception: continue
        if not pg.evaluate(BAR_TAB_VISIBLE, tabs[1]): continue
        for T in tabs[1:] + tabs[:1] + tabs[2:3] + tabs[:1]:
            cn += 1
            try: st = land(pg, T, touch)
            except Exception as e: cbad.append((name + " > chain " + T, str(e)[:80])); break
            v = verdict(st, T)
            if v: cbad.append((name + " > chain " + T, v)); break
    chk("%s %s: a chain of %d taps through every tab and home from each start lands on each tab's own root" % (dev, cls, cn), not cbad, cbad[:4])

    # ---- (4)/(7) the reported case, with the units
    reset(pg); r_units("drill", True)(pg, cls, touch); settle(pg, 500)
    ticked = pg.evaluate("()=>document.querySelectorAll('#stage .pick input:checked').length")
    land(pg, tabs[1], touch)
    st = land(pg, tabs[0], touch)
    chk("%s %s: units ticked (%d), Profile, then Home: Home, and the unit screen is not built (%s)" % (dev, cls, ticked, st["cls"][:40]),
        ticked >= 1 and st["showing"] == ["bottomtab-home"] and not st["stray"], st)
    reset(pg); start_studying(pg, touch); pg.wait_for_timeout(700)
    tapc(pg, ".modecard[data-mode=drill]", touch); pg.wait_for_timeout(800); G.clear_popups(pg)
    after = pg.evaluate("()=>document.querySelectorAll('#stage .pick input:checked').length")
    chk("%s %s: the units reached again through Start Studying are as they always were: none ticked (%d)" % (dev, cls, after), after == 0, after)

    # ---- (6) a test in progress keeps its pause / resume behaviour
    reset(pg); begin(pg)
    pg.evaluate("()=>confirmMainMenu()"); pg.wait_for_timeout(700)
    ask = pg.evaluate("()=>({ title: (document.querySelector('.pausepanel .qnum')||{}).textContent||'', keep: [...document.querySelectorAll('.pausepanel button')].map(b=>b.textContent.trim()) })")
    chk("%s %s: the Home path on a running drill asks before leaving, with Keep going and Leave (%s)" % (dev, cls, ask["keep"]),
        len(ask["keep"]) == 2 and ask["title"] != "", ask)
    pg.evaluate("()=>{ const b=[...document.querySelectorAll('.pausepanel button')].find(x=>/Keep going/.test(x.textContent)); b && b.click(); }"); pg.wait_for_timeout(900)
    back = pg.evaluate("()=>({ q: !!document.querySelector('#stage .choice'), pausePanel: !!document.querySelector('.pausepanel'), tip: typeof testInProgress!=='undefined' && testInProgress })")
    chk("%s %s: Keep going puts the running question back (%s)" % (dev, cls, back), back["q"] and not back["pausePanel"] and back["tip"], back)
    pg.evaluate("()=>confirmMainMenu()"); pg.wait_for_timeout(700)
    pg.evaluate("()=>{ const b=[...document.querySelectorAll('.pausepanel button')].find(x=>/Leave/.test(x.textContent)); b && b.click(); }"); pg.wait_for_timeout(1100); G.clear_popups(pg)
    st = pg.evaluate(STATE, ROOT)
    chk("%s %s: Leave goes Home (%s)" % (dev, cls, st["showing"]), st["showing"] == ["bottomtab-home"] and not st["stray"], st)
    if pg.evaluate(BAR_TAB_VISIBLE, tabs[1]):
        land(pg, tabs[1], touch); st = land(pg, tabs[0], touch)
        chk("%s %s: and the Home tab after it is Home" % (dev, cls), verdict(st, tabs[0]) == [], verdict(st, tabs[0]))
    # the daily question: straight Home
    reset(pg); r_daily(pg, cls, touch)
    pg.evaluate("()=>confirmMainMenu()"); pg.wait_for_timeout(1000); G.clear_popups(pg)
    st = pg.evaluate(STATE, ROOT)
    chk("%s %s: the daily question's Home path goes straight Home, no question asked (%s)" % (dev, cls, st["showing"]),
        st["showing"] == ["bottomtab-home"] and not st["stray"], st)
    # Save and exit keeps the test; Start Studying offers it; Home is Home
    reset(pg); r_pause(pg, cls, touch)
    pg.evaluate("()=>saveAndExitTest()"); pg.wait_for_timeout(1400); G.clear_popups(pg)
    saved = pg.evaluate("()=>{ try{ const s=readRunSession(); return !!(s && s.saved); }catch(e){ return null; } }")
    st = pg.evaluate(STATE, ROOT)
    chk("%s %s: Save and exit keeps the test (%s) and lands on Home (%s)" % (dev, cls, saved, st["showing"]), saved and st["showing"] == ["bottomtab-home"], [saved, st])
    for T in tabs[1:]:
        if not pg.evaluate(BAR_TAB_VISIBLE, T): continue
        land(pg, T, touch); st = land(pg, tabs[0], touch)
        v = verdict(st, tabs[0])
        chk("%s %s: with a saved test, %s then Home is Home (no resume card, no unit screen)" % (dev, cls, T.split("-")[1]), not v and not pg.evaluate("()=>!!document.getElementById('resume-offer')"), v)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(700); G.clear_popups(pg)
    start_studying(pg, touch); pg.wait_for_timeout(1200)
    offer = pg.evaluate("()=>({ go: !!document.getElementById('resume-go'), fresh: !!document.getElementById('resume-new') })")
    chk("%s %s: Start Studying still offers the saved test: Resume test and Start a new test (%s)" % (dev, cls, offer), offer["go"] and offer["fresh"], offer)
    # the hidden-bar screens: the bar is hidden by design (so no tab is tapped there), and leaving each by its own exit lands on Home
    hb = []
    for name, which, reach in HIDDEN:
        reset(pg); pg.evaluate("()=>{ try{ clearRunSession(); }catch(e){} }")
        try: reach(pg, cls, touch)
        except Exception as e: hb.append((name, "cannot be reached: " + str(e)[:80])); continue
        pg.wait_for_timeout(300)
        shownNow = pg.evaluate(BAR_TAB_VISIBLE, tabs[0])
        if shownNow: hb.append((name, "the bar is up on a screen that hides it"))
        pg.evaluate(LEAVE[name]); pg.wait_for_timeout(900)
        # a running question asks first: Leave
        pg.evaluate("()=>{ const b=[...document.querySelectorAll('.pausepanel button')].find(x=>/Leave/.test(x.textContent)); b && b.click(); }"); pg.wait_for_timeout(1000); G.clear_popups(pg)
        st = pg.evaluate(STATE, ROOT)
        if st["showing"] != ["bottomtab-home"] or st["stray"]: hb.append((name, "left by its own exit it lands on %s %s" % (st["showing"], st["stray"])))
        elif pg.evaluate(BAR_TAB_VISIBLE, tabs[1]):
            land(pg, tabs[1], touch); st2 = land(pg, tabs[0], touch); v = verdict(st2, tabs[0])
            if v: hb.append((name + " > Profile > Home", v))
    chk("%s %s: the screens that hide the bar (question, Pause, the daily question, results): hidden, left by their own exit to Home, and Profile then Home is Home" % (dev, cls),
        not hb, hb[:4])
    chk("%s %s: no page errors" % (dev, cls), not pg.errs, pg.errs[:3])
    pg.ctx.close()

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    for dev in want:
        for cls in (CLASSES or ["academy", "ifc"]):
            print("\n%s %s" % (dev, cls), flush=True)
            walk(br, dev, cls)
    br.close()
print("\n" + ("ALL PASS" if not G.fails else "SOME FAILED: %d" % len(G.fails)))
sys.exit(0 if not G.fails else 1)
