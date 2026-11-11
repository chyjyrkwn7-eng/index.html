"""Build 384.37: a badge's cutscene is not tappable away, and neither is a rank-up or a find.
The owner: "You shouldn't be able to skip the badge cutscene, it says tap to skip, you shouldn't be able to skip those rewards though, unless
you have the setting on in settings though. Also, badge cutscenes ARENT SHOWING UP ... there are people who are already unlocking badges."

THE CAUSE, played in Chromium on the build before: the results' "Tap to skip" line (384 r6) has a person tapping through the grade and the XP
box, and each tap brings the next step in at once (build 380's rule) - the one that brings the badge's case in is followed by the next, and
the case's own click handler ended it: on a screen it was up for about 0.3s ("not showing up"). Taps on a rank-up scene (once its title was
up) and on a secret flare's scene ended them the same way. The setting the owner means is the one that is already there, "Skip celebrations
and pop-ups" (theme.muteBanners): with it on, none of these play at all; with it off, a tap does nothing. Read off the page, no label.

(A) THE ACADEMY, A REAL FULL-UNIT RUN (the unit's hundos one short of its badge, then answered right through the page's own buttons), and
    from the moment the results are up a person taps the screen about four times a second: the badge case's scene comes in and stays up
    - at least MIN_UP seconds, never with its ending (bc-out) begun - while the taps go on
(B) the same in Fire Code (its chapter, the first 100% is the badge)
(C) REDUCE MOTION (the still scene, BC_STILL_MS long): taps all over it end nothing for the first half of its time
(D) THE RANK-UP SCENE (a tier, and Supernova) as Reduce motion plays it, a tap once its title is up: no ending begins (rank-outro); and it does
    end by itself, handing over (onDone)
(E) A FIND'S SCENE (playFlareFoundScene), still: a tap once its title is up ends nothing (sf-end), and it ends by itself
(F) THE HOME BADGE CUTSCENE (an old build's queue, played on Home): a tap does not end it (badge-cutscene-out)
(G) "Skip celebrations and pop-ups" ON: the badge's scene is not played at all (no .bc-scene, done() at once) - the other half of the rule
(H) no scene carries a tap-to-skip line of its own (their text has no 'skip' and no 'tap')
(I) no page errors

Run:  python3 tools/check-b384-badgecut.py   (--against OLD/index.html must FAIL (A, B, C, D, E, F); ONLY=A,D runs those)"""
import json, os, re, sys, time, functools, http.server, socket, threading, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    CHROME = (sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
BODY = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else open(ROOT + "/index.html", encoding="utf-8").read()
ONLY = set(os.environ.get("ONLY", "").split(",")) - {""}
def want(n): return not ONLY or n in ONLY
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()
_m = re.search(r'const APP_BUILD = "([^"]+)"', BODY)
SERVED = _m.group(1) if _m else ""
# an existing, up-to-date account (tours seen, Nova met, everything it holds announced): nothing lands over what is measured
SEED = {"onboardingComplete": True, "firstName": "Maddog", "avatarChar": "ninja", "publicId": "xph5b57jbp5a", "novaMet": 99,
        "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True, "seenModeSelectTour": True, "seenUnitSelectTour": True,
        "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231},
        "lifetime": {"points": 9000, "answered": 900, "correct": 860, "drillPlays": 30, "examPlays": 4, "perfectTests": 30,
                     "longestStreak": 20, "currentStreak": 3}}
SEEN = ["freshstart", "unithold.tip", "savecode.asked", "savecode.card", "getstarted"]
def init_js(cls):
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.intro.seen','9'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    if cls == "ifc":
        s += "localStorage.setItem('class26e.activeclass','ifc'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.greet.ifc','done');"
        for k in SEEN: s += "localStorage.setItem('class26e.ifc.%s','1');" % k
        s += "localStorage.setItem('class26e.ifc.drill.v1', %s);" % json.dumps(json.dumps(SEED))
    return s + " }catch(e){} })()"
def page(br, cls, reduce=False, w=440, h=956):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=1, has_touch=True, reduced_motion="reduce" if reduce else "no-preference")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});")
    pg.add_init_script(init_js(cls))
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=BODY))
    # the page's own build, whatever the repo's version.json says (under --against the update check would reload the page mid-walk)
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"}, body='{"build":"%s","frameId":"","note":""}' % SERVED))
    pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(3500)
    pg.evaluate("()=>document.getElementById('splashscreen')?.remove()")
    return ctx, pg, errs
ANSWER = r"""()=>{ if(!document.querySelector('.choice') || typeof order === 'undefined' || !order.length) return 'wait';
  const key = order.length + ':' + pos;
  if(window.__answered !== key){ if(performance.now() - (window.__nextAt || 0) < 700) return 'wait'; const c = document.querySelector('.choice[data-index="' + correctSlot(order[pos]) + '"]'); if(!c) return 'wait'; c.click(); window.__answered = key; window.__answeredAt = performance.now(); return 'answered'; }
  const n = document.getElementById('nextbtn'); if(n && !n.hidden && performance.now() - window.__answeredAt > 400){ n.click(); window.__nextAt = performance.now(); return 'next'; } return 'wait'; }"""
SCENE = r"""()=>{ const s = document.querySelector('.bc-scene'); return s ? { out: s.classList.contains('bc-out'), still: s.classList.contains('bc-still') } : null; }"""
MIN_UP = 4.0

def walk(pg, cls, tap_every=0.25, min_up=MIN_UP, limit=170):
    """a real full-unit run in the unit one hundo short of its badge; from the results on, a person taps the screen"""
    topic = pg.evaluate("()=>unitsInTeachingOrder().filter(u=>unitQuestionCount(u)>0).sort((a,b)=>unitQuestionCount(a)-unitQuestionCount(b))[0]")
    pg.evaluate(r"""(t) => { store.unitPerfects = {}; store.unitPerfects[t] = Math.max(0, badgeThresholdFor(t) - 1); saveStore(); showHome();
      cfg.source = 'all'; cfg.mode = 'drill'; cfg.units = [t];
      setTimeout(() => beginRun(QUESTIONS.map((q, i) => i).filter(i => (QUESTIONS[i].topic || '').trim() === t)), 1200); return true; }""", topic)
    t0 = time.time(); rs = first = last = None; out_seen = False; taps = 0; nxt = 0
    while time.time() - t0 < limit:
        try:
            if pg.evaluate("()=>!!document.querySelector('.rs-screen')"):
                if rs is None: rs = time.time()
                if time.time() >= nxt:
                    pg.mouse.click(220, 300); taps += 1; nxt = time.time() + tap_every
            else:
                pg.evaluate(ANSWER)
            s = pg.evaluate(SCENE)
            if s:
                if first is None: first = time.time()
                last = time.time(); out_seen = out_seen or s["out"]
                if time.time() - first >= min_up + 1.0: break
            elif first is not None: break
        except Exception as ex:
            print("   (walk: %s)" % str(ex)[:100])
        pg.wait_for_timeout(100)
    return {"unit": topic[:30], "resultsAt": None if rs is None else round(rs - t0, 1), "taps": taps, "up": None if first is None else round(last - first, 2), "outBegun": out_seen}

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    errs_all = []
    # ------------------------------------------------------------------ (A)(B) a real run, tapped through
    for key, cls in (("A", "academy"), ("B", "ifc")):
        if not want(key): continue
        ctx, pg, errs = page(br, cls)
        r = walk(pg, cls)
        errs_all += errs
        chk("(%s) %s, a real full-unit run tapped through (%d taps from the results on): the badge case's scene comes in and stays up at least %.0fs with no ending begun (%s)"
            % (key, "the academy" if cls == "academy" else "Fire Code", r["taps"], MIN_UP, r),
            r["up"] is not None and r["up"] >= MIN_UP and not r["outBegun"], r)
        ctx.close()
    # ------------------------------------------------------------------ (C) reduce motion: the still scene, tapped
    if want("C"):
        ctx, pg, errs = page(br, "academy", reduce=True)
        ms = pg.evaluate("()=>BC_STILL_MS")
        pg.evaluate("()=>{ window.__done = 0; const u = unitsInTeachingOrder()[0]; store.unitPerfects[u] = badgeThresholdFor(u); playBadgeCaseScene([u], () => { window.__done++; }, [], {}); }")
        pg.wait_for_timeout(900)
        s0 = pg.evaluate(SCENE)
        for _ in range(6):
            pg.mouse.click(220, 400); pg.wait_for_timeout(int(ms / 2 / 7))
        s1 = pg.evaluate(SCENE)
        chk("(C) Reduce motion: the still badge scene is up (still) and taps all over it, for half of its %dms, end nothing (no ending begun)" % ms,
            bool(s0) and s0["still"] and bool(s1) and not s1["out"] and pg.evaluate("()=>window.__done") == 0, (s0, s1))
        pg.wait_for_timeout(int(ms) + 1500)
        chk("(C) ... and it ends by itself, handing over (done called once)", pg.evaluate("()=>[!!document.querySelector('.bc-scene'), window.__done]") == [False, 1], pg.evaluate("()=>[!!document.querySelector('.bc-scene'), window.__done]"))
        errs_all += errs; ctx.close()
    # ------------------------------------------------------------------ (D) the rank-up scene, a tier and Supernova, still
    if want("D"):
        for label, fn in (("a tier", "playTierCutscene('vanguard', { from: 'veteran', onDone(){ window.__done = (window.__done || 0) + 1; } })"),
                          ("Supernova", "playSupernovaCutscene({ from: 'elite', onDone(){ window.__done = (window.__done || 0) + 1; } })")):
            ctx, pg, errs = page(br, "academy", reduce=True)
            pg.evaluate("()=>{ window.__done = 0; store.supernovaAchieved = false; saveStore(); showHome(); document.querySelectorAll('.rs-spot,.daily-alert,#tour-overlay,.update-banner,.toast').forEach(n => n.remove()); }")
            pg.wait_for_timeout(900)
            pg.evaluate("()=>{ " + fn + "; }")
            title_ms, end_at = pg.evaluate("()=>[RANK_STILL_TITLE_MS, RANK_STILL_END_AT]")
            pg.wait_for_timeout(title_ms + 700)
            pg.mouse.click(220, 478)
            pg.wait_for_timeout(700)
            st = pg.evaluate("()=>{ const o = document.getElementById('supernova-cutscene'); return o ? { outro: o.classList.contains('rank-outro') } : null; }")
            chk("(D) %s, Reduce motion: a tap once the title is up (%dms in) begins no ending - the scene is still up and plays on (its own end is at %dms)" % (label, title_ms + 700, end_at),
                bool(st) and not st["outro"], st)
            pg.wait_for_timeout(end_at + 2500)
            chk("(D) %s: ... and it ends by itself, handing over once" % label, pg.evaluate("()=>[!document.getElementById('supernova-cutscene'), window.__done]") == [True, 1],
                pg.evaluate("()=>[!document.getElementById('supernova-cutscene'), window.__done]"))
            errs_all += errs; ctx.close()
    # ------------------------------------------------------------------ (E) a find's scene, still
    if want("E"):
        ctx, pg, errs = page(br, "academy", reduce=True)
        pg.evaluate("()=>{ window.__done = 0; store.mysteryColorsFound = { red: true }; playFlareFoundScene('red', false, () => { window.__done++; }); }")
        t_ms, e_at = pg.evaluate("()=>[SF_STILL_TITLE_MS, SF_STILL_END_AT]")
        pg.wait_for_timeout(t_ms + 900)
        pg.mouse.click(220, 478)
        pg.wait_for_timeout(700)
        st = pg.evaluate("()=>{ const o = document.querySelector('.sf-scene'); return o ? { end: o.classList.contains('sf-end') } : null; }")
        chk("(E) a find's scene, Reduce motion: a tap once its title is up begins no ending (its own end is at %dms)" % e_at, bool(st) and not st["end"], st)
        pg.wait_for_timeout(e_at + 2500)
        chk("(E) ... and it ends by itself, handing over once", pg.evaluate("()=>[!document.querySelector('.sf-scene'), window.__done]") == [True, 1], pg.evaluate("()=>[!document.querySelector('.sf-scene'), window.__done]"))
        errs_all += errs; ctx.close()
    # ------------------------------------------------------------------ (F) the Home badge cutscene (an old build's queue)
    if want("F"):
        ctx, pg, errs = page(br, "academy")
        pg.evaluate("()=>{ const u = unitsInTeachingOrder()[0]; store.pendingBadgeUnlocks = [u]; saveStore(); showHome(); }")
        for _ in range(40):
            if pg.evaluate("()=>!!document.getElementById('badge-cutscene')"): break
            pg.wait_for_timeout(250)
        up = pg.evaluate("()=>!!document.getElementById('badge-cutscene')")
        pg.wait_for_timeout(600)
        pg.mouse.click(220, 478); pg.wait_for_timeout(250); pg.mouse.click(220, 478)
        pg.wait_for_timeout(700)
        st = pg.evaluate("()=>{ const o = document.getElementById('badge-cutscene'); return o ? { out: o.classList.contains('badge-cutscene-out') } : null; }")
        chk("(F) the Home badge cutscene (a queue an old build stored): taps do not end it (still up, flying out not begun)", up and bool(st) and not st["out"], (up, st))
        errs_all += errs; ctx.close()
    # ------------------------------------------------------------------ (G)(H) the setting, and no hint of its own
    if want("G"):
        ctx, pg, errs = page(br, "academy")
        r = pg.evaluate("""()=>{ const u = unitsInTeachingOrder()[0]; let done = 0; theme.muteBanners = true;
          const h = playBadgeCaseScene([u], () => { done++; }, [], {}); const n = !!document.querySelector('.bc-scene'); theme.muteBanners = false;
          return { done, scene: n, handle: h }; }""")
        chk("(G) 'Skip celebrations and pop-ups' on (theme.muteBanners): the badge's scene is not played - done() at once, no scene", r["done"] == 1 and not r["scene"] and r["handle"] is None, r)
        errs_all += errs; ctx.close()
    if want("H"):
        ctx, pg, errs = page(br, "academy", reduce=True)
        pg.evaluate("()=>{ const u = unitsInTeachingOrder()[0]; store.unitPerfects[u] = badgeThresholdFor(u); playBadgeCaseScene([u], () => {}, [], {}); }")
        pg.wait_for_timeout(1200)
        t1 = pg.evaluate("()=>(document.querySelector('.bc-scene') || {}).textContent || ''")
        pg.evaluate("()=>{ document.querySelectorAll('.bc-scene').forEach(n => n.__nova && n.__nova.skip()); playTierCutscene('vanguard', { from: 'veteran', onDone(){} }); }")
        pg.wait_for_timeout(1500)
        t2 = pg.evaluate("()=>(document.getElementById('supernova-cutscene') || {}).textContent || ''")
        chk("(H) neither the badge's scene nor a rank-up's carries a tap-to-skip line of its own", bool(t1) and bool(t2) and not re.search(r"skip|\btap\b", t1 + " " + t2, re.I), (t1[:80], t2[:80]))
        errs_all += errs; ctx.close()
    chk("(I) no page errors on any of it", not errs_all, errs_all[:4])
    br.close()
sys.exit(0 if ok else 1)
