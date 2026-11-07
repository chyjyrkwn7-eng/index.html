"""Build 384: the page viewer keeps its swipes, and a brand-new account's Nova meeting has nothing to count.
Madison: "Using zoom in page function, swiping on it will swipe to the next question accidentally, it seems like when looking at
the full page, and moving it, I'm touching what's behind the page which is causing the swipe to happen even when the page is up.."
/ "The introduction for a brand new account needs to be updated. Why is it telling me I have 0 badges? Like of course I would."
Read off the page (a touch phone, 440x956, Fire Code):
(1) a Fire Code drill question answered, the page viewer (ifcOpenViewer) up over it: a real touch swipe across the viewer leaves
    the question where it was;
(2) the same swipe with the viewer closed moves to the next question (the swipe still works - the control);
(3) Nova's recap for an account with nothing found says nothing about badges, flares or crew - no lines at all - and for an
    account that has found some, one line each for what it has (the counts read back off the lines);
(4) an account that has finished sign-up but has never answered a question meets Nova as a new player (playNovaIntro asked
    without "existing"); one with answers gets the returning player's meeting;
(5) no page errors;
(6) a laptop (1536x864, a mouse, no touch): with the mouse moving about over Home, the warm-ups waiting for a quiet moment
    (idle callbacks: badge art, the flare flip-books) still get done - at least half as many run as with the mouse still, in
    the same time on the same page. (A hovering mouse used to count as a finger, so on a laptop they never ran.)
Run:  python3 tools/check-b384-laptop.py   (--against OLD/index.html must FAIL)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b383-ifcsync.py")).read().split("\nwith sync_playwright() as pw:")[0]
G = {"__file__": os.path.join(HERE, "check-b383-ifcsync.py"), "__name__": "b384lap"}
exec(src, G)
if "--against" in sys.argv:
    OLD = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read(); IR = G["g"]["INSET_RE"]
    def _old(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], OLD)
    G["g"]["patched"] = _old
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:400], flush=True)
def swipe(cdp, x0, y0, dx, steps=10):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x0 + dx * i / steps, "y": y0 + 4 * i / steps}]})
        time.sleep(0.012)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
QID = "()=>({ qi: (typeof pos==='number') ? pos : null })"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
    errs_all = []
    ctx, pg, errs = G["page"](br, G["init"](G["ifc"]))
    cdp = ctx.new_cdp_session(pg)
    pg.evaluate("""()=>{ theme.swipeAdvance = true; const t=topicsIn(QUESTIONS)[0]; cfg.mode='drill'; cfg.units=[t]; cfg.source='all';
      beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i).slice(0,6), null, null); }""")
    for _ in range(30):
        if pg.evaluate("()=>!!document.querySelector('#stage .choice')"): break
        pg.wait_for_timeout(250)
    pg.wait_for_timeout(700)
    def answer():
        pg.evaluate("""async ()=>{ const n=document.getElementById('nextbtn');
          if(!n || n.hidden){ const all=[...document.querySelectorAll('#stage .choice')]; const q=order[pos], oo=optionOrder(q);
            all[oo.indexOf(QUESTIONS[q].answer)].click(); await new Promise(r=>setTimeout(r, 1300)); } }""")
    answer()
    before = pg.evaluate(QID)
    nextUp = pg.evaluate("()=>{ const n=document.getElementById('nextbtn'); return !!(n && !n.hidden && !n.disabled); }")
    # (1) the viewer up: a swipe across it
    pg.evaluate("""()=>{ ifcOpenViewer({ anchor: document.querySelector('#stage .panel') || document.body, title: 'Section 101', sub: 'Page 1',
      render: box => { const c=document.createElement('canvas'); c.width=1400; c.height=1800; c.style.width='1400px'; c.style.height='1800px'; box.appendChild(c); return Promise.resolve(); } }); }""")
    pg.wait_for_timeout(900)
    up = pg.evaluate("()=>!!document.querySelector('.ifc-vz')")
    swipe(cdp, 420, 520, -360); pg.wait_for_timeout(900)
    swipe(cdp, 420, 640, -380); pg.wait_for_timeout(900)
    during = pg.evaluate(QID)
    chk("(1) the page viewer up (%s), two swipes across it: the question stays (%s -> %s)" % (up, before["qi"], during["qi"]),
        up and nextUp and during == before, [nextUp, before, during])
    # (2) closed: the same swipe moves on
    pg.evaluate("()=>{ try{ ifcCloseViewer(); }catch(e){} document.querySelectorAll('.ifc-vz').forEach(e=>e.remove()); }"); pg.wait_for_timeout(700)
    swipe(cdp, 420, 640, -380); pg.wait_for_timeout(1200)
    after = pg.evaluate(QID)
    chk("(2) the viewer closed, the same swipe goes to the next question (%s -> %s)" % (before["qi"], after["qi"]), after != before, [before, after])
    # (3) the recap lines
    r3 = pg.evaluate("""()=>{ const say = st => novaRecapLines(st, 'Test').map(l => l.text);
      return { none: say({ badges: 0, flares: 0, rankIdx: -1, level: 3 }), some: say({ badges: 3, flares: 2, rankIdx: 1, level: 12, rank: TIER_ORDER_FULL[1] }),
        crew: novaCrewTally().have }; }""")
    import re as _re
    # the lines that report what you have found: "of my badges/flares", "my crew", or a "none/haven't" about them
    tally = lambda lines: [l for l in lines if _re.search(r"of my (badges|flares|secret flares)|my crew|haven.t (found|relit)|none of my", l, _re.I)]
    some = tally(r3["some"])
    # the crew comes from the account itself (novaCrewTally), not these counts: said only when this account has some home
    crewOk = lambda lines: len([l for l in lines if "crew" in l]) == (1 if r3["crew"] > 0 else 0)
    noneSaid = [l for l in tally(r3["none"]) if "crew" not in l]
    chk("(3) nothing found, nothing said (%s; crew home %d); some found, one line each with its count (%s)" % (noneSaid, r3["crew"], some),
        not noneSaid and crewOk(r3["none"]) and crewOk(r3["some"]) and len([l for l in some if "badges" in l and "3" in l]) == 1 and len([l for l in some if "flares" in l and "2" in l]) == 1, r3)
    # (4) who gets which meeting
    r4 = pg.evaluate("""()=>{ const out = {}; const real = playNovaIntro, keep = JSON.stringify({ l: store.lifetime, h: store.testHistory });
      const ask = (name, life, hist) => { store.lifetime = life; store.testHistory = hist; novaMeetOn = false;
        let got = null; playNovaIntro = (then, o) => { got = o || {}; }; try{ playNovaMeeting(); }catch(e){ got = { err: String(e) }; }
        out[name] = got; novaMeetOn = false; introPending = false; };
      ask('fresh', Object.assign({}, store.lifetime, { answered: 0, points: 0, correct: 0 }), []);
      const k = JSON.parse(keep); ask('used', Object.assign({}, k.l, { answered: 40, points: 900 }), k.h || []);
      playNovaIntro = real; store.lifetime = k.l; store.testHistory = k.h; return out; }""")
    chk("(4) never answered: the new player's meeting (existing %s); with answers: the returning one (existing %s)" % (r4["fresh"].get("existing"), r4["used"].get("existing")),
        r4["fresh"].get("existing") is False and r4["used"].get("existing") is True, r4)
    errs_all += errs; ctx.close()
    # (6) a laptop: the mouse moving, the warm-ups still run
    COUNT = "window.__ric=0; (function(){ const r=window.requestIdleCallback; if(r) window.requestIdleCallback=function(cb,o){ return r.call(window, function(d){ window.__ric++; return cb(d); }, o); }; })();"
    runs = {}
    for mode in ("still", "moving"):
        c2 = br.new_context(viewport={"width": 1536, "height": 864}, device_scale_factor=1.25)
        c2.add_init_script("window.__cloudSeed = {};"); c2.add_init_script(G["FAKE"]); c2.add_init_script(COUNT)
        c2.add_init_script(G["init"](G["academy"], active="academy"))
        p2 = c2.new_page(); e2 = []; p2.on("pageerror", lambda e: e2.append(str(e)[:160]))
        body = G["g"]["patched"]((0, 0, 0, 0))
        p2.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        p2.goto(G["serve_url"]); p2.wait_for_timeout(3000)
        p2.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); document.querySelectorAll('.intro-popup,.daily-alert,#intro-pop,.nova-talk,.app-banner').forEach(e=>e.remove()); showHome(); window.__ric = 0; }")
        for i in range(24):
            if mode == "moving": p2.mouse.move(500 + (i % 2) * 300, 300 + (i % 3) * 60, steps=3)
            p2.wait_for_timeout(500)
        runs[mode] = p2.evaluate("()=>window.__ric"); errs_all += e2; c2.close()
    chk("(6) laptop: the mouse moving over Home, the warm-ups still run (%d idle runs moving, %d still)" % (runs["moving"], runs["still"]),
        runs["still"] > 10 and runs["moving"] >= runs["still"] * .5, runs)
    chk("(5) no page errors", not errs_all, errs_all[:3])
    br.close()
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
