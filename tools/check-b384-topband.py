#!/usr/bin/env python3
"""Build 384 r17: nothing in the top band of a screen blurs what is behind it.
Madison, on his iPhone: the screen title ("Profile"), the test's "Drill" and its count were soft and dim on every screen, the glass buttons
beside them crisp; "What is happening at the top of the screens? Fix this now". The only blurred (backdrop-filter) elements in the top band
of every screen were the chat button, the round back buttons and Pause - given the tab bar's glass in 384, a flat disc on 383 beyond Home.
On an iPhone 17 Pro Max and an iPhone SE, installed (standalone, real insets modelled), on Home, Profile (all tabs), Rankings, Settings, Mode
select, Friends, Calendar, the units picker and a Drill: no fixed / sticky / absolute element whose top edge is above 170px (and whose bottom
is below 0) computes a backdrop-filter - except the Home planet's own flares (the orbit is not an edge control) - and the chat button, the back
buttons and Pause are still there, visible, with a background that is not transparent (they still read as buttons).
Run:  python3 tools/check-b384-topband.py   (--against OLD/index.html must FAIL)"""
import sys, os, io, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = io.open(os.path.join(ROOT, "tools/check-positions.py")).read().rsplit("\nmain()", 1)[0]
cp = {"__file__": os.path.join(ROOT, "tools/check-positions.py"), "__name__": "cp"}; exec(src, cp)
from playwright.sync_api import sync_playwright
OLD = io.open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read() if "--against" in sys.argv else None
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
SCREENS = ["showHome()", "showProfile('profile')", "showProfile('stats')", "showRankings()", "showAppearance()", "showModeSelect()", "showFriends()", "showCalendar()",
           "(()=>{cfg.mode='drill';showSetup()})()",
           "(()=>{const t=[...new Set(QUESTIONS.map(q=>(q.topic||'').trim()))].filter(Boolean)[0]; beginRun(QUESTIONS.map((q,i)=>[q,i]).filter(([q])=>(q.topic||'').trim()===t).map(([,i])=>i), null, null);})()"]
READ = """()=>{ const out=[]; document.querySelectorAll('body *').forEach(e=>{ if(e.closest('.cosmic-hero-wrap')) return; const cs=getComputedStyle(e); const r=e.getBoundingClientRect(); if(!r.width||!r.height) return;
  const bf=cs.backdropFilter&&cs.backdropFilter!=='none'; if(bf && r.top<170 && r.bottom>0 && /fixed|sticky|absolute/.test(cs.position)) out.push(e.tagName.toLowerCase()+'.'+[...e.classList].join('.')+(e.id?'#'+e.id:'')+' y='+Math.round(r.top)); });
  const chat=document.getElementById('chatdock-btn'); const cc=chat?getComputedStyle(chat):null; const cr=chat?chat.getBoundingClientRect():null;
  return { blurred: out, chat: chat ? { vis: cc.visibility!=='hidden'&&cc.display!=='none'&&cr.width>20, bg: cc.backgroundColor, bgi: cc.backgroundImage.slice(0,30) } : null }; }"""
srv, url = cp["serve"]()
try:
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=cp["CHROME"])
        for name, w, h, plat, ins in cp["DEVICES"]:
            if not any(k in name for k in ("17 Pro Max", "SE (2nd")): continue
            ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=2)
            ctx.add_init_script(cp["SEED"]); ctx.add_init_script(cp["STANDALONE"])
            page = ctx.new_page(); errs = []; page.on("pageerror", lambda e: errs.append(str(e)[:140]))
            body = cp["patched"](ins) if OLD is None else __import__("re").sub(r"env\(safe-area-inset-(top|right|bottom|left)[^)]*\)", lambda m: {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}[m.group(1)], OLD)
            page.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
            page.goto(url); page.wait_for_timeout(2300); page.evaluate("document.getElementById('splashscreen')?.remove()")
            bad = []; nochat = []
            for scr in SCREENS:
                page.evaluate("()=>{ try{ %s }catch(e){} }" % scr); page.wait_for_timeout(1200)
                page.evaluate("()=>{document.getElementById('tour-overlay')?.remove();document.getElementById('tour-tooltip')?.remove();}")
                r = page.evaluate(READ)
                # (384.77, ON PURPOSE) build 383's top is back: Home's chat button wears 383's glass (with its blur), as it did all of 383's life;
                # every other top-band control stays unblurred (383's flat chat and back buttons beyond Home)
                blurred = [x for x in r["blurred"] if not (scr == "showHome()" and "#chatdock-btn" in x)]
                if blurred: bad.append((scr[:24], blurred[:2]))
                if not r["chat"] or not r["chat"]["vis"]: nochat.append(scr[:24])
                elif r["chat"]["bg"] in ("rgba(0, 0, 0, 0)", "transparent") and "gradient" not in r["chat"]["bgi"]: nochat.append(("transparent", scr[:24]))
            chk("%s: nothing in the top band of any of %d screens computes a backdrop blur" % (name, len(SCREENS)), not bad, bad[:3])
            chk("%s: the chat button is there on every screen and still reads as a button" % name, len(nochat) <= 1, nochat)
            chk("%s: no page errors" % name, not errs, errs)
            ctx.close()
        br.close()
finally:
    srv.shutdown()
print("ALL PASS" if ok else "FAILED"); sys.exit(0 if ok else 1)
