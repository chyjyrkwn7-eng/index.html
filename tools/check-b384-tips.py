#!/usr/bin/env python3
"""check-b384-tips.py - are the tips true, and do they point where they say? (384.137, "ensure all the tool tips are accurate and
updated ... a good thing for any new user")

check-tours.py asks whether every step renders and stays on screen, in the academy, for a returning account. This asks what a
new account in EITHER class is shown, on the iPhone 17 Pro Max (440x956) and the iPad Pro 11" (834x1194), installed:

  geometry  every step of every first-time tour (Home's tips, Profile, the Leaderboard, Settings, Choose your mode, Choose your
            units, a Virtual Room's units, the hold tip, the first results): the target is shown, the bubble is on screen, its
            dot is on its target, and
            the bubble does not cover the target it explains (a target taller than half the screen excepted). A tour that
            scrolls its target into view is where this broke: the bubble is fixed and was placed with window.scrollY added.
  order     Profile's and Settings' tips go down the page in the order the page reads (each target below the last).
  coverage  Settings' tips point at the same rows in both classes (Fire Code has Leaderboard & Privacy too).
  claims    what a tip says it is pointing at is there: the unit tip's "bar" is a bar you can see on that card; the hold tip
            names only parts the unit card has (no Most missed since 284); the first results tip on a 100% run does not talk
            about what was missed; the Leaderboard tip says Overall the way the board itself does (by rank); Stats' empty line
            names only modes the class has; Home's planet tip promises only what a tap does at that rank.
  launch    a Fire Code sign-up that reaches Nova inside 25 seconds is not covered by "Nova is taking too long to open".

Steps are read off the page (the steps handed to startSimpleTour, and the rendered bubble), never from this file.

  python3 tools/check-b384-tips.py
  python3 tools/check-b384-tips.py --against /path/to/old-index.html     (must FAIL)
  ONLY=profile,settings python3 tools/check-b384-tips.py
"""
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import b384_flow_lib as L
from playwright.sync_api import sync_playwright

AGAINST = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else None
SRC = L.load_src(AGAINST)
BUILD = re.search(r'const APP_BUILD = "([^"]+)"', SRC).group(1)
ONLY = set(x for x in os.environ.get("ONLY", "").split(",") if x)
DEVICES = [("iPhone 17 Pro Max", "iphone-safari", 440, 956, (62, 0, 34, 0)), ("iPad Pro 11", "ipad-safari", 834, 1194, (24, 0, 20, 0))]
if os.environ.get("TIPS_DEV"): DEVICES = [d for d in DEVICES if re.search(os.environ["TIPS_DEV"], d[0], re.I)]

fails = []
def ck(name, cond, info=""):
    print(("  PASS " if cond else "  FAIL ") + name + ("" if cond else "  -> " + str(info)[:500]), flush=True)
    if not cond: fails.append(name)

FLAGS = ["seenModeSelectTour", "seenUnitSelectTour", "seenSettingsTour", "seenProfileTour", "seenRewardsTour", "seenFirstResultsTour",
         "seenUnitOptionsTour", "seenClassTip"]
def seed(flag):
    d = {"firstName": "Casey", "username": "Casey", "avatarChar": "ghost", "onboardingComplete": True, "publicId": "tipgate38413",
         "classes": ["academy", "ifc"], "leaderboardOptIn": True, "lastModified": 1790500000000, "tourRev": 99, "novaMet": 99,
         "novaHeard": {"@recap": 99991231}, "savedCodeSaved": True, "badgeBandsVersion": 99, "rankMapFx244": True,
         "vrRetroDone": True, "vrTop3RetroDone": True, "lifetime": {"points": 100, "answered": 0, "correct": 0}}
    for f in FLAGS: d[f] = f != flag
    return d
SEEN = ("['class26e.freshstart','class26e.unithold.tip','class26e.getstarted','class26e.daily.seen','class26e.savecode.card',"
        "'class26e.savecode.asked','class26e.a2hs','class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen']"
        ".forEach(k=>{ localStorage.setItem(k,'1'); localStorage.setItem(k.replace('class26e.','class26e.ifc.'),'1'); });"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','99'); localStorage.setItem('class26e.ifc.intro.seen','99');"
        "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));")
def init_for(flag, cls):
    raw = json.dumps(json.dumps(seed(flag)))
    js = ("(()=>{ try{ if(sessionStorage.getItem('__s')) return; sessionStorage.setItem('__s','1');" + SEEN +
          "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.ifc.drill.v1', %s); localStorage.setItem('class26e.synccode','TIPS-3841');" % (raw, raw))
    if cls == "ifc": js += "localStorage.setItem('class26e.activeclass','ifc');"
    return js + " }catch(e){} })()"

HOOK = r"""(()=>{ window.__tours = []; const t = setInterval(() => {
  if(typeof window.startSimpleTour === 'function' && !window.startSimpleTour.__w){
    const o = window.startSimpleTour;
    const w = function(steps){ try{ if(!arguments[2]) window.__tours.push((steps||[]).map(s => ({ target: s.target || null, center: !!s.center, text: String(s.text || '') }))); }catch(e){}
      return o.apply(this, arguments); };
    w.__w = true; window.startSimpleTour = w; try{ startSimpleTour = w; }catch(e){}
  } }, 20); })()"""

STEP = r"""()=>{ const t=document.getElementById('tour-tooltip'); if(!t) return null;
  const txt=(document.getElementById('tour-text')||{}).textContent||'';
  const R = e => { if(!e) return null; const r=e.getBoundingClientRect(); return {x:r.left,y:r.top,w:r.width,h:r.height}; };
  const all=(window.__tours||[]).slice(-1)[0]||[];
  const norm = s => String(s).replace(/\bchapter(s?)\b/gi, 'unit$1').toLowerCase();
  const step = all.find(s => norm(s.text) === norm(txt)) || null;
  const el = step && step.target ? document.querySelector(step.target) : null;
  const tr=R(t), tg=R(el); const d=document.getElementById('tour-line-dot');
  const dr = d && getComputedStyle(d).display !== 'none' ? R(d) : null; const dc = dr ? {x:dr.x+dr.w/2, y:dr.y+dr.h/2} : null;
  const vw=innerWidth, vh=innerHeight;
  const ov = (a,b) => !!a && !!b && Math.min(a.x+a.w,b.x+b.w)-Math.max(a.x,b.x) > 2 && Math.min(a.y+a.h,b.y+b.h)-Math.max(a.y,b.y) > 2;
  return { text: txt, target: step ? step.target : null, center: !!(step && step.center), index: step ? all.indexOf(step) : -1, count: all.length,
    onScreen: tr.x>=-1 && tr.y>=-1 && tr.x+tr.w<=vw+1 && tr.y+tr.h<=vh+1,
    dotOn: !!(dc && tg) && dc.x>=tg.x-2 && dc.x<=tg.x+tg.w+2 && dc.y>=tg.y-2 && dc.y<=tg.y+tg.h+2,
    covers: !!tg && tg.h < vh*0.5 && ov(tr, tg), tall: !!tg && tg.h >= vh*0.5,
    docTop: tg ? tg.y + scrollY : null, found: !!el, shown: !!tg && tg.w > 0 && tg.h > 0 && getComputedStyle(el).visibility !== 'hidden', inView: !!tg && tg.y>=-1 && tg.y+tg.h<=vh+1 }; }"""

def open_page(br, dev, cls, flag, extra=""):
    name, ua, w, h, ins = dev
    ctx, pg = L.new_page(br, SRC, URL, ua=ua, w=w, h=h, installed=True, insets=ins, extra_init=(init_for(flag, cls), HOOK) + ((extra,) if extra else ()))
    pg.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "force": False, "frameId": ""})))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(URL); pg.wait_for_timeout(3500)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} "
                "try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} "
                "try{ const u = pendingHomeUnlocks(); markUnlocksShown(u.chars, u.banners, u.fx); }catch(e){} "
                "document.querySelectorAll('#tour-overlay, #tour-tooltip, #tour-line, #tour-line-dot, #nova-intro, .rs-spot, .unlock-card, .daily-alert').forEach(n=>n.remove()); }")
    pg.errs = errs
    return ctx, pg

SHOTS = os.environ.get("TIPS_SHOTS")
def walk(pg, secs=12, tag=""):
    out = []
    t0 = time.time()
    while time.time() - t0 < secs and not pg.evaluate("()=>!!document.getElementById('tour-tooltip')"):
        pg.wait_for_timeout(200)
    for _ in range(14):
        if not pg.evaluate("()=>!!document.getElementById('tour-next')"): break
        pg.wait_for_timeout(450)
        pg.evaluate("()=>document.getElementById('tour-text')?.click()")
        pg.wait_for_timeout(650)
        s = pg.evaluate(STEP)
        if s: out.append(s)
        if SHOTS:
            os.makedirs(SHOTS, exist_ok=True); pg.screenshot(path=os.path.join(SHOTS, "%s-%d.png" % (tag, len(out))))
        pg.evaluate("()=>document.getElementById('tour-next')?.click()")
        pg.wait_for_timeout(500)
    return out

RUN = r"""(unit)=>{ cfg.mode='drill'; cfg.source='all'; cfg.units=[unit]; cfg.size=0;
  order=QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===unit);
  runTrackable=true; timedOut=false; runMode='drill'; runLabel=null; isMissedRetake=false; practiceTestMinutes=null; inVirtualRoom=false;
  attempts={}; picked={}; timedOutSet={}; try{ firstPick = {}; }catch(e){}
  order.forEach(qi=>{ const oo=optionOrder(qi); attempts[qi]=1; picked[qi]=oo.indexOf(QUESTIONS[qi].answer); });
  runStartTime=Date.now()-order.length*9000; testInProgress=true; pos=order.length-1; summarize(); return order.length; }"""

SCEN = [
    ("home", None, "showHome(); startMainMenuTour()", 6),
    ("profile", "seenProfileTour", "showProfile('profile')", 8),
    ("leaderboard", "seenRewardsTour", "showRankings()", 8),
    ("settings", "seenSettingsTour", "showAppearance()", 8),
    ("modes", "seenModeSelectTour", "showModeSelect()", 8),
    ("units", "seenUnitSelectTour", "cfg.mode='drill'; showSetup()", 8),
    ("roomunits", "seenUnitSelectTour", "showVirtualRoomSetup()", 8),
    ("unithold", None, "localStorage.removeItem('class26e.unithold.tip'); cfg.mode='drill'; showSetup(); setTimeout(()=>{ const r=document.querySelector('.pick:not(.pick-tba)'); if(r) r.click(); }, 500)", 8),
    ("results", "seenFirstResultsTour", None, 45),
]

srv, URL = L.serve()
print("check-b384-tips against", AGAINST or "index.html", "(build %s)" % BUILD)
got = {}
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME, args=["--autoplay-policy=no-user-gesture-required"])
        for dev in DEVICES:
            for cls in ("academy", "ifc"):
                print("\n%s, %s" % (dev[0], "Fire Code" if cls == "ifc" else "Police Academy"), flush=True)
                for key, flag, setup, secs in SCEN:
                    if ONLY and key not in ONLY and not (key == "results" and "results" in ONLY): continue
                    ctx, pg = open_page(br, dev, cls, flag)
                    try:
                        ck("%s %s %s: the page is the class's (%s)" % (dev[0], cls, key, pg.evaluate("()=>window.NOVA_CLASS")),
                           pg.evaluate("()=>window.NOVA_CLASS") == cls)
                        extra = {}
                        if key == "results":
                            unit = pg.evaluate("()=>{ const c={}; QUESTIONS.forEach(q=>{ const t=(q.topic||'').trim(); c[t]=(c[t]||0)+1; }); return Object.keys(c).sort((a,b)=>c[a]-c[b])[0]; }")
                            pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(600)
                            extra["n"] = pg.evaluate(RUN, unit)
                            # past the reveal: taps skip it, as a person's do
                            for _ in range(30):
                                if pg.evaluate("()=>!!document.getElementById('tour-tooltip')"): break
                                pg.evaluate("()=>{ const s=document.querySelector('.rs-skip, .rs-stage, .rs-reveal'); if(s) s.click(); }")
                                pg.wait_for_timeout(700)
                        else:
                            pg.evaluate("()=>{ %s }" % setup)
                        steps = walk(pg, secs, re.sub(r"\W+", "-", "%s-%s-%s" % (dev[0], cls, key)))
                        if key == "unithold":
                            # the card the tip describes
                            extra["card"] = pg.evaluate("""()=>{ const r=document.querySelector('.pick.unit-hold-tip-target, .pick.pick-checked') || document.querySelector('.pick:not(.pick-tba)');
                              const nm = r && (r.dataset.unit || (r.querySelector('.pname, .pick-name, .ptitle')||{}).textContent || '');
                              try{ openUnitDetail(r, nm, cfg.mode); }catch(e){}
                              const d=document.querySelector('.unitdetail'); if(!d) return null;
                              return { missedDoor: !!d.querySelector('.unitdetail-door.is-missed, [data-kind="missed"], .unitdetail-door-missed'),
                                       text: d.innerText }; }""")
                        if key == "units":
                            extra["bar"] = pg.evaluate("""()=>{ const c=document.querySelector('.pick'); const b=c && c.querySelector('.pick-bar-track');
                              if(!b) return false; const r=b.getBoundingClientRect(); return r.width>0 && r.height>0 && getComputedStyle(b).visibility!=='hidden'; }""")
                        if key == "leaderboard":
                            extra["blurb"] = pg.evaluate("()=>{ try{ return RANKING_BOARDS.find(b=>b.key==='overall').blurb; }catch(e){ return ''; } }")
                        if key == "settings":
                            extra["rows"] = pg.evaluate("()=>[...document.querySelectorAll('#stage .settings-cat[id]')].map(b=>b.id)")
                        if key == "home":
                            extra["modes"] = None
                        got[(dev[0], cls, key)] = (steps, extra)
                        n = len(steps)
                        asked = pg.evaluate("()=>((window.__tours||[])[0]||[]).length")
                        ck("%s %s %s: %d of %d steps shown" % (dev[0], cls, key, n, asked), n >= 1 and n == asked, [s["text"][:40] for s in steps])
                        bad = [(s["index"] + 1, s["text"][:44], "target hidden" if not s["shown"] else "off screen" if not s["onScreen"] else "dot off target" if not s["dotOn"] else "covers its target")
                               for s in steps if not s["center"] and (not s["shown"] or not s["onScreen"] or not s["dotOn"] or s["covers"])]
                        ck("%s %s %s: every bubble on screen, its dot on its target, not over it" % (dev[0], cls, key), not bad, bad)
                        if key in ("profile", "settings"):
                            tops = [s["docTop"] for s in steps if s["target"] and s["target"] != "#chatdock-btn" and ".profile-stats-tab-btn" not in s["target"]]
                            ck("%s %s %s: the tips go down the page in its order (%s)" % (dev[0], cls, key, [round(t) for t in tops]),
                               len(tops) >= 2 and all(b > a for a, b in zip(tops, tops[1:])), tops)
                        if key == "units":
                            says_bar = any(re.search(r"\bbar\b", s["text"], re.I) for s in steps)
                            ck("%s %s units: a tip that speaks of the card's bar has one to see (bar shown: %s)" % (dev[0], cls, extra["bar"]),
                               not says_bar or extra["bar"], [s["text"] for s in steps])
                        if key == "unithold":
                            card = extra.get("card") or {}
                            says_missed = any(re.search(r"miss", s["text"], re.I) for s in steps)
                            ck("%s %s unithold: the tip names only what the unit card holds (card has a Most missed part: %s)" % (dev[0], cls, card.get("missedDoor")),
                               bool(card) and (not says_missed or card.get("missedDoor")), [s["text"] for s in steps])
                        if key == "results":
                            says_missed = any(re.search(r"\bmissed\b", s["text"], re.I) for s in steps)
                            ck("%s %s results: on a 100%% run (%s questions) the tip does not speak of what was missed" % (dev[0], cls, extra.get("n")),
                               bool(steps) and not says_missed, [s["text"] for s in steps])
                        if key == "leaderboard" and cls == "academy":
                            ov = [re.search(r"Overall:([^.]*)\.", s["text"]) for s in steps]
                            ov = [m.group(1).strip() for m in ov if m]
                            by_rank = "rank" in (extra.get("blurb") or "").lower()
                            ck("%s leaderboard: Overall is said the board's way (tip %r, board %r)" % (dev[0], ov, (extra.get("blurb") or "")[:40]),
                               bool(ov) and (("rank" in ov[0].lower()) == by_rank), ov)
                        if key == "settings":
                            got_rows = sorted(s["target"] for s in steps if s["target"])
                            got[("rows", dev[0], cls)] = (got_rows, extra["rows"])
                    finally:
                        ctx.close()
                # coverage: the rows Settings' tips point at, alike in both classes (where both have the row)
            a = got.get(("rows", dev[0], "academy")); f = got.get(("rows", dev[0], "ifc"))
            if a and f:
                want_f = sorted(t for t in a[0] if t.lstrip("#") in f[1])
                ck("%s settings: Fire Code's tips point at every row the academy's do that Fire Code has (%s vs %s)" % (dev[0], f[0], want_f), f[0] == want_f, [a, f])

        if not ONLY or "claims" in ONLY:
            print("\nclaims read off the page", flush=True)
            dev = DEVICES[0]
            for cls in ("academy", "ifc"):
                ctx, pg = open_page(br, dev, cls, None)
                try:
                    modes = pg.evaluate("()=>{ showModeSelect(); return [...document.querySelectorAll('.modecard[data-mode]')].map(c=>(c.querySelector('.modecardtitlerow')||c).textContent.trim().split(/\\s/)[0]); }")
                    pg.wait_for_timeout(500)
                    stats = pg.evaluate("()=>{ showProfile('stats'); return [...document.querySelectorAll('#stage .info-note')].map(p=>p.textContent).join(' | '); }")
                    named = set(re.findall(r"\b(Drill|Mock|Review|Virtual Room)\b", stats))
                    ck("%s Stats: its empty line names only modes this class has (%s; modes %s)" % (cls, sorted(named), modes),
                       bool(stats) and all(any(m.startswith(n.split()[0]) for m in modes) for n in named), stats)
                    planet = pg.evaluate("()=>{ try{ const t=NOVA_NEW_TIPS_321.find(s=>/plasma/.test(s.target)); return t ? t.text : ''; }catch(e){ return ''; } }")
                    ck("%s Home's planet tip promises only what a tap does below Supernova (%r)" % (cls, planet[:70]), bool(planet) and not re.search(r"spin", planet, re.I), planet)
                finally:
                    ctx.close()

        if not ONLY or "launch" in ONLY:
            print("\nlaunch: a quick Fire Code sign-up reaches Nova inside 25 seconds", flush=True)
            name, ua, w, h, ins = DEVICES[0]
            ctx, pg = L.new_page(br, SRC, URL, ua=ua, w=w, h=h, installed=True, insets=ins)
            pg.goto(URL); pg.wait_for_timeout(2500)
            pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); stage.replaceChildren(); try{ signupPicks = ['ifc']; }catch(e){} signupInNova = true; signupPart = 1; playNovaIntro(()=>{}, { signup: true, part: 1 }); }")
            pg.wait_for_timeout(27500)
            st = pg.evaluate("()=>({ nova: !!document.getElementById('nova-intro'), trouble: !!document.getElementById('launch-trouble') })")
            ck("Nova's first half is up at 30s and nothing is over it (%s)" % st, st["nova"] and not st["trouble"], st)
            ctx.close()
        br.close()
finally:
    srv.shutdown()

print("\n%d failure(s)" % len(fails) if fails else "\nALL PASS")
for f in fails: print("  * " + f)
sys.exit(1 if fails else 0)
