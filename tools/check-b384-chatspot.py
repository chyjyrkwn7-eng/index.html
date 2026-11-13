#!/usr/bin/env python3
"""Build 384.93: THE ROUND CHAT BUTTON IS IN ONE PLACE ON EVERY SCREEN, AND DOES NOT MOVE AS THE SCREEN CHANGES.

Madison: "Ensure the chat button's position is consistent between screens, for example, when I hit Start Studying the chat button
moves." On 384.86 it sat at Home's corner (the safe area + .75rem, 1.5rem in) on the tab screens and moved on every pushed screen:
384 r8's alignNavChat() put it level with the round back button two frames after the mount (10px lower and 4px further right on
an installed Pro Max, 30px lower in a Safari tab), and Settings' pages lowered it .6rem by CSS. Now it never moves; the pushed
screen's nav row is brought to it (the back button's middle on the chat button's middle; on a phone the back button as far in from
the left as the chat button is from the right), before the screen's first frame.

Per device (installed Pro Max 440x956 59/34, installed SE 375x667 20/0, iPad Pro 11" 834x1194 and 1194x834 24/20, a Safari tab
440x797) and class (academy, Fire Code):
 (1) SAME PLACE: #chatdock-btn's rect (left, top, width, height) on Home, Choose your mode, test setup, Profile and its Stats,
     Badges (the badge case) and Rank tabs, the Leaderboard, the Calendar, Settings, Advanced, Customize, the rankings page,
     Contributors, Friends, and Home again - all within 0.5px of Home's;
 (2) LEVEL: on every screen with a round back button, its middle is on the chat button's middle (0.5px), and on a phone it is as
     far in from the left as the chat button is from the right (0.5px);
 (3) NO MOVE IN THE CHANGE: from Home, tapping Start Studying and then the back button, the button's rect read every frame for 1.2s
     never differs from Home's by more than 0.5px;
 (4) THE EXCEPTIONS, reported: on a question the button sits beside Pause (Pause owns the corner; centred on Pause's line, one gap
     to its left) - checked to be level with Pause; the end-of-run results screen (Pro Max and iPad, academy) is in Home's place;
 (5) no page errors.
  python3 tools/check-b384-chatspot.py [--against OLD/index.html] [--quick]   (384.92 must FAIL (1)-(3))
"""
import json, os, sys, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "record-cutscenes.py")).read().split("\nSCENES = [")[0]
rc = {"__file__": os.path.join(HERE, "record-cutscenes.py"), "__name__": "rc"}; exec(src, rc)
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
from playwright.sync_api import sync_playwright
RAW = open(sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else cb.SRC, encoding="utf-8").read()
QUICK = "--quick" in sys.argv
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.1 Mobile/15E148 Safari/604.1"
UA_PAD = UA.replace("iPhone; CPU iPhone OS", "iPad; CPU OS")
SEEN = ("['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted',"
        "'class26e.ifc.intro.seen','class26e.ifc.unithold.tip','class26e.ifc.daily.seen','class26e.ifc.savecode.asked','class26e.ifc.savecode.card','class26e.ifc.getstarted','class26e.ifc.freshstart',"
        "'class26e.penal55124.seen','class26e.penal124256.seen','class26e.penal256578.seen','class26e.a2hs'].forEach(k=>localStorage.setItem(k,'1'));"
        "localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.weekrecap.v1','9999-12-31');")
IFC = ("localStorage.setItem('class26e.ifc.drill.v1', localStorage.getItem('class26e.drill.v1')); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
       "localStorage.setItem('class26e.greet.ifc','done'); localStorage.setItem('class26e.activeclass','ifc');")
# name, w, h, inset top, inset bottom, installed, UA, phone
DEVS = [("Pro Max", 440, 956, 59, 34, True, UA, True), ("SE", 375, 667, 20, 0, True, UA, True), ("iPad 11 P", 834, 1194, 24, 20, True, UA_PAD, False),
        ("iPad 11 L", 1194, 834, 24, 20, True, UA_PAD, False), ("Safari tab", 440, 797, 0, 0, False, UA, True)]
if QUICK: DEVS = DEVS[:1] + DEVS[2:3]
SCREENS = [("Home", "showHome()"), ("Choose your mode", "showModeSelect()"), ("test setup", "showSetup()"), ("Profile", "showProfile()"),
           ("Stats", "showProfile('stats')"), ("badge case", "showProfile('badges')"), ("Rank", "showProfile('ranks')"), ("Leaderboard", "showRankings()"),
           ("Calendar", "showCalendar()"), ("Settings", "showAppearance()"), ("Advanced", "showAdvancedSettings()"), ("Customize", "showCustomize()"),
           ("rankings page", "showAppearance({page:'rankings'})"), ("Contributors", "showCredits()"), ("Friends", "showFriends()"), ("Home again", "showHome()")]
RECT = """()=>{ const b = document.getElementById('chatdock-btn'); if(!b || b.closest('[hidden]')) return null; const r = b.getBoundingClientRect();
  const k = document.querySelector('#stage .settings-nav > :is(.ios-nav-back, .settings-nav-back)'); const q = k && k.getClientRects().length ? k.getBoundingClientRect() : null;
  const p = document.querySelector('#pausebtn:not([hidden])'); const pr = p && p.getClientRects().length ? p.getBoundingClientRect() : null;
  return { x: r.left, y: r.top, w: r.width, h: r.height, right: innerWidth - r.right, sy: scrollY,
    back: q ? { mid: q.top + q.height / 2, left: q.left } : null, pause: pr ? { mid: pr.top + pr.height / 2 } : null }; }"""
FRAMES = """(ms)=>new Promise(res=>{ const out = []; const t0 = performance.now(); const f = () => { const b = document.getElementById('chatdock-btn');
  const r = b && !b.closest('[hidden]') ? b.getBoundingClientRect() : null; out.push(r ? [r.left, r.top, r.width, r.height] : null);
  if(performance.now() - t0 < ms) requestAnimationFrame(f); else res(out); }; requestAnimationFrame(f); })"""
errs = []
def boot(br, dev, cls):
    name, W, H, it, ib, inst, ua, phone = dev
    ins = {"top": "%dpx" % it, "bottom": "%dpx" % ib, "left": "0px", "right": "0px"}
    body = cb.INSET_RE.sub(lambda m: ins[m.group(1)], RAW).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
    ctx = br.new_context(viewport={"width": W, "height": H}, screen={"width": W, "height": H}, device_scale_factor=2, has_touch=True, is_mobile=True, user_agent=ua)
    if inst: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    ctx.add_init_script("(()=>{ try{ if(localStorage.getItem('class26e.drill.v1')) return; localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3843'); %s %s }catch(e){} })();"
                        % (json.dumps(cb.USED_ACCOUNT), SEEN, IFC if cls == "ifc" else ""))
    pg = ctx.new_page()
    pg.route("**/index.html*", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=body))
    pg.route("**/version.json*", lambda r: r.abort())
    pg.on("pageerror", lambda e: errs.append("%s %s: %s" % (name, cls, str(e)[:160])))
    pg.goto("http://127.0.0.1:%d/index.html" % PORT); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); try{ homeUnlocksOwed=()=>false; }catch(e){} try{ store.novaMet = 99; }catch(e){}"
                " try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} document.querySelectorAll('#tour-overlay,#tour-tooltip,#nova-intro,.unlock-card').forEach(n=>n.remove()); }")
    pg.wait_for_timeout(600)
    return ctx, pg
CLEAR = ("()=>{ document.querySelectorAll('.intro-pop,#intro-pop,.update-banner,.daily-alert,.savecode-card,.unlock-card,.challenge-pop,#tour-overlay,#tour-tooltip').forEach(n=>n.remove());"
         " document.body.classList.remove('cutscene-focus','cutscene-return'); window.scrollTo(0, 0); }")
def same(a, b, tol=.5): return a and b and all(abs(a[k] - b[k]) <= tol for k in ("x", "y", "w", "h"))
def fmt(r): return "(%.1f, %.1f) %.0fx%.0f" % (r["x"], r["y"], r["w"], r["h"]) if r else "none"
srv, PORT = rc["serve"]()
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=rc["CHROME"])
    def run_one(dev, cls):
        res = []
        def chk(n, c, i=""): res.append((n, c, i))
        e0 = len(errs)
        name, phone = dev[0], dev[7]
        tag = "%s, %s" % (name, "Fire Code" if cls == "ifc" else "academy")
        try:
            ctx, pg = boot(br, dev, cls)
        except Exception as e:
            chk("%s: booted" % tag, False, str(e)[:200]); return res, "rash" in str(e)
        home = None; bad = []; lvl = []; seen = []
        for scr, js in SCREENS:
            try:
                pg.evaluate(CLEAR); pg.evaluate("()=>{ " + js + " }"); pg.wait_for_timeout(900); pg.evaluate(CLEAR); pg.wait_for_timeout(150)
                r = pg.evaluate(RECT)
            except Exception as e:
                r = None; errs.append("%s %s: %s" % (tag, scr, str(e)[:120]))
            if scr == "Home": home = r
            seen.append("%s %s" % (scr, fmt(r)))
            if not same(r, home): bad.append((scr, fmt(r)))
            if r and r["back"]:
                mid = r["y"] + r["h"] / 2
                off = abs(r["back"]["mid"] - mid)
                offx = abs(r["back"]["left"] - r["right"]) if phone else 0
                if off > .5 or offx > .5: lvl.append((scr, "back mid %.1f vs chat mid %.1f, back left %.1f vs chat right %.1f" % (r["back"]["mid"], mid, r["back"]["left"], r["right"])))
        chk("%s (1): the chat button is in Home's place %s on all %d screens" % (tag, fmt(home), len(SCREENS)), home and not bad, bad)
        chk("%s (2): every round back button is level with it%s" % (tag, " and as far in from the left as it is from the right" if phone else ""), home and not lvl, lvl)
        # (3) through the change: Start Studying, then back
        try:
            pg.evaluate(CLEAR); pg.evaluate("()=>showHome()"); pg.wait_for_timeout(900); pg.evaluate(CLEAR)
            h0 = pg.evaluate(RECT)
            pg.evaluate("()=>{ const b = document.querySelector('#stage .playbtn') || document.getElementById('nextbtn'); b.click(); }")
            fr = pg.evaluate(FRAMES, 1200)
            pg.evaluate("()=>{ const k = document.querySelector('#stage .settings-nav > :is(.ios-nav-back, .settings-nav-back)'); if(k) k.click(); }")
            fr2 = pg.evaluate(FRAMES, 1200)
            key = (h0["x"], h0["y"], h0["w"], h0["h"]) if h0 else None
            moved = [f for f in fr + fr2 if not f or max(abs(a - b) for a, b in zip(f, key)) > .5] if key else ["no Home rect"]
            chk("%s (3): Home -> Start Studying -> back: the button stays put in every frame (%d frames, %d off: %s)" % (tag, len(fr) + len(fr2), len(moved), moved[:3]), key and not moved, moved[:4])
        except Exception as e:
            chk("%s (3): the change ran" % tag, False, str(e)[:200])
        # (4) a question and the results, Pro Max and iPad (academy)
        if cls == "academy" and name in ("Pro Max", "iPad 11 P"):
            try:
                pg.evaluate(CLEAR); pg.evaluate("()=>{ theme.autoAdvance=false; theme.reduceMotion=true; }")
                rc["start_unit_run"](pg, "Identity Crimes")
                pg.wait_for_selector(".choice", timeout=25000); pg.wait_for_timeout(900)
                q = pg.evaluate(RECT)
                lv = q and q["pause"] and abs(q["pause"]["mid"] - (q["y"] + q["h"] / 2)) <= 1
                chk("%s (4): on a question the button sits beside Pause, level with it (Pause owns the corner): %s, Pause's middle %s" % (tag, fmt(q), q and q["pause"]), lv, q)
                rc["answer_all"](pg); pg.wait_for_timeout(1800); pg.evaluate(CLEAR); pg.wait_for_timeout(300)
                rr = pg.evaluate(RECT); onres = pg.evaluate("()=>!document.querySelector('.choice')")
                chk("%s (4): the results screen: the button in Home's place (%s)" % (tag, fmt(rr)), onres and (rr is None or same(rr, home)), (rr, home))
            except Exception as e:
                chk("%s (4): a run" % tag, False, str(e)[:200])
        print("   ", tag, "|", "; ".join(seen), flush=True)
        try: ctx.close()
        except Exception: pass
        return res, any("rash" in e for e in errs[e0:]) or any("rash" in str(r[2]) for r in res)

    for dev in DEVS:
        for cls in ("academy", "ifc"):
            for attempt in range(3):
                n0 = len(errs)
                res, crashed = run_one(dev, cls)
                if not crashed or attempt == 2: break
                del errs[n0:]; print("    (renderer crashed on a loaded machine: again)", flush=True)
            for r in res: globals()["chk"](*r)
    br.close()
chk("(5) no page errors", not errs, errs[:6])
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
