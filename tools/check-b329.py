"""Build 329: the 'More fixes' round - class bubble size and the new-class cue, SE sizes, hunted flare gone.
Owner account (publicId xph5b57jbp5a). Run:  python3 tools/check-b329.py [section ...]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
DEV = {"se1": (320, 568, (20, 0, 0, 0), True), "se3": (375, 667, (20, 0, 0, 0), True), "15": (393, 852, (59, 0, 34, 0), True),
       "promax": (440, 956, (62, 0, 34, 0), True), "ipad11": (834, 1194, (24, 0, 20, 0), True), "mac": (1512, 982, (0, 0, 0, 0), False)}
def seed(pid="xph5b57jbp5a"):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = pid; d["firstName"] = "Maddog"; d["novaMet"] = 99
    return json.dumps(d)
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0001'); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));
 %s
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
def page_for(br, dev, extra="", pid="xph5b57jbp5a"):
    w, h, ins, inst = DEV[dev]; g["new_page"].w, g["new_page"].h = w, h
    ctx, page = g["new_page"](br, ins, inst, False)
    page.add_init_script(INIT % (json.dumps(seed(pid)), extra))
    page.goto(url); page.wait_for_timeout(3000)
    page.evaluate("document.getElementById('splashscreen')?.remove()")
    page.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); page.wait_for_timeout(1500)
    return ctx, page
R = "s=>{const e=document.querySelector(s); if(!e) return null; const b=e.getBoundingClientRect(); return {w:Math.round(b.width),h:Math.round(b.height),l:Math.round(b.left),t:Math.round(b.top)}}"
want = [a for a in sys.argv[1:]] or ["bubble", "new", "se", "flare", "copy", "flow", "xp"]
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    if "bubble" in want:
        for dev in ("se1", "se3", "15", "promax", "ipad11", "mac"):
            ctx, page = page_for(br, dev)
            r = page.evaluate("()=>{ const f=%s; return {dq:f('.daily-question-fab'), cb:f('.class-bubble')} }" % R)
            chk(dev + ": the class bubble is the daily question's size", r["dq"] and r["cb"] and abs(r["dq"]["w"] - r["cb"]["w"]) <= 1 and r["cb"]["w"] == r["cb"]["h"], r)
            ctx.close()
    if "new" in want:
        ctx, page = page_for(br, "15")
        chk("nothing is new today: no pulse, no banner", page.evaluate("()=>!document.querySelector('.class-bubble-wrap.has-new') && !document.getElementById('newclass-banner')"))
        ctx.close()
        ctx, page = page_for(br, "15", "localStorage.setItem('class26e.classseen','[\"academy\"]');")
        page.evaluate("()=>{ sessionStorage.clear(); showHome(); }"); page.wait_for_timeout(3800)
        r = page.evaluate("""()=>{ const b=document.querySelector('.class-bubble'); const cs=getComputedStyle(b,'::before');
          return {has:!!document.querySelector('.class-bubble-wrap.has-new'), ring:cs.animationName, banner:!!document.querySelector('#newclass-banner'),
                  txt:(document.querySelector('#newclass-banner')||{}).innerText||''} }""")
        chk("a class not yet seen: the bubble pulses (a ring animates)", r["has"] and r["ring"] == "cb-new", r)
        chk("a class not yet seen: one banner says so", r["banner"] and "Fire Code" in r["txt"], r)
        page.click(".class-bubble"); page.wait_for_timeout(400)
        r = page.evaluate("()=>({has:!!document.querySelector('.class-bubble-wrap.has-new'), seen:localStorage.getItem('class26e.classseen')})")
        chk("opening the classes marks them seen: pulse stops, list stored", not r["has"] and "ifc" in (r["seen"] or ""), r)
        ctx.close()
    if "se" in want:
        for dev in ("se1", "se3"):
            ctx, page = page_for(br, dev)
            r = page.evaluate("()=>{ const f=%s; return {chat:f('.chatdock-btn'), play:f('.panel.home.screen-home-actual > .playbtn'), dq:f('.daily-question-fab')} }" % R)
            chk(dev + ": the chat button is no bigger than 40px, and no bigger than the daily question's circle + 2", r["chat"] and r["chat"]["w"] <= 40 and r["chat"]["w"] <= r["dq"]["w"] + 2, r)
            chk(dev + ": Start Studying is no taller than 40px", r["play"] and r["play"]["h"] <= 40, r)
            h = page.evaluate("()=>{ const b=document.querySelector('.chatdock-btn'); const r=b.getBoundingClientRect(); const x=r.left-2, y=r.top+r.height/2; const hit=document.elementFromPoint(x,y); return !!hit && (hit===b||b.contains(hit)); }")
            chk(dev + ": the chat button still has a 44px touch area (2-3px outside its edge hits it)", h)
            ctx.close()
    if "flare" in want:
        ctx, page = page_for(br, "15")
        r = page.evaluate("()=>({marked:document.querySelectorAll('.cosmic-flare-dot.is-next, .cosmic-flare-dot.is-hunting').length, rings:[...document.querySelectorAll('.cof-ring')].filter(e=>getComputedStyle(e).animationName!=='none').length, states:MYSTERY_ORDER.map(flareHuntState)})")
        chk("no flare on Home is marked as hunted: no is-next, no pulsing ring, never a hunt state", r["marked"] == 0 and r["rings"] == 0 and not any(s in ("next", "hunting") for s in r["states"]), r)
        ctx.close()
    if "copy" in want:
        ctx, page = page_for(br, "15")
        r = page.evaluate("""()=>{ const t = l => typeof l.text === 'function' ? l.text() : l.text;
          const lines = novaIntroLines({signup:true}).map(t).join(' | ');
          const tips = mainMenuTourSteps(false);
          const cal = tips.find(x => /Calendar/.test(x.text)).text, daily = tips.find(x => /daily question/i.test(x.text)).text;
          const names = ['ninja','ghost','wizard','grizzly','alien'].map(k => AVATAR_DISPLAY_NAME[k]);
          return {lines, cal, daily, names, last: tips[tips.length-1].text} }""")
        chk("intro: nothing says 'my class' or 'class material' (he has several classes)", not __import__("re").search(r"my class|class material", r["lines"], __import__("re").I), r["lines"][:200])
        chk("intro: the storm, and the word adventure", "storm" in r["lines"] and "adventure" in r["lines"].lower(), r["lines"][:200])
        chk("intro: the sync code is said to be in Settings and to sign you in on other devices", "Settings" in r["lines"] and "other devices" in r["lines"], r["lines"][-600:])
        chk("intro: the modes get more than one box", "Drill is practice" in r["lines"] and "Review goes over" in r["lines"], r["lines"][-600:])
        chk("tips: the calendar tip names no class and the daily tip no XP", "26E" not in r["cal"] and "XP" not in r["daily"], [r["cal"], r["daily"]])
        chk("tips: the last tip points at ranking up and badges", "Rank up" in r["last"] and "badges" in r["last"], r["last"])
        chk("starters have names of their own, not what they literally are", not set(n.lower() for n in r["names"]) & {"ninja", "ghost", "wizard", "bear", "alien"} and len(set(r["names"])) == 5, r["names"])
        ctx.close()
    if "flow" in want:
        w, h, ins, inst = DEV["15"]; g["new_page"].w, g["new_page"].h = w, h
        ctx, page = g["new_page"](br, ins, inst, False)
        errs = []; page.on("pageerror", lambda e: errs.append(str(e)[:160]))
        page.goto(url); page.wait_for_timeout(3500)
        page.evaluate("document.getElementById('splashscreen')?.remove()"); page.wait_for_timeout(600)
        chk("first visit: the Get Started page, not Welcome", page.evaluate("()=>!!document.querySelector('.gs-page') && !document.querySelector('.cosmic-welcome')"))
        r = page.evaluate("()=>{ const v=[...document.querySelectorAll('.gs-page video')]; return {n:v.length, srcs:v.map(x=>x.getAttribute('src')), scenes:document.querySelectorAll('.gs-scene').length} }")
        chk("it has four clips beside its four scenes", r["n"] == 6 and r["scenes"] == 4 and all(x and x.startswith("landing/") for x in r["srcs"]), r)
        page.wait_for_timeout(2200)
        r = page.evaluate("()=>{ const b=document.querySelector('.gs-go').getBoundingClientRect(); return {w:Math.round(b.width), h:Math.round(b.height), bottom:Math.round(innerHeight-b.bottom)} }")
        chk("its button is on screen and at least 44px tall", r["h"] >= 44 and r["bottom"] >= 0, r)
        page.click(".gs-go"); page.wait_for_timeout(1200)
        chk("Let's get started leads to Welcome, and the page is gone", page.evaluate("()=>!!document.querySelector('.cosmic-welcome') && !document.querySelector('.gs-page')"))
        page.reload(); page.wait_for_timeout(3500); page.evaluate("document.getElementById('splashscreen')?.remove()"); page.wait_for_timeout(600)
        chk("a second visit goes straight to Welcome", page.evaluate("()=>!!document.querySelector('.cosmic-welcome') && !document.querySelector('.gs-page')"))
        page.click(".cosmic-welcome-btn.welcome-new"); page.wait_for_timeout(800)
        page.click(".signupcheck-panel .signupcheck-go"); page.wait_for_timeout(800)
        chk("sign-up: the check goes straight to the class screen (no What This Actually Is)", page.evaluate("()=>!!document.querySelector('.classselect-panel') && !document.querySelector('.welcomeintro-panel')"))
        r = page.evaluate("()=>({cards:document.querySelectorAll('.classselect-panel .class-card').length, soon:!!document.querySelector('.classselect-panel .class-card.is-soon'), ifc:!!document.querySelector('.classselect-panel .is-ifc')})")
        chk("class screen: the Classes screen's cards - Police Academy and 'More classes', no Fire Code", r["cards"] == 2 and r["soon"] and not r["ifc"], r)
        page.click(".classselect-panel .class-card.is-academy"); page.wait_for_timeout(300)
        chk("picking one marks it Selected and shows Continue", page.evaluate("()=>document.querySelector('.classselect-panel .cc-status.is-enrolled')?.textContent==='Selected' && !document.querySelector('.classselect-panel .next.playbtn').hidden"))
        page.click(".classselect-panel .next.playbtn")
        import time
        t0 = time.time()
        while not page.evaluate("()=>!!document.querySelector('#nova-intro .nt-ask-input')") and time.time() - t0 < 60:
            st = page.evaluate("()=>{const el=document.getElementById('nova-intro'); if(!el||!el.__nova) return null; return {typing:!!el.__nova.typing}}")
            if st and not st["typing"]: page.evaluate("()=>{const el=document.getElementById('nova-intro'); if(el&&el.__nova) el.__nova.advance();}")
            page.wait_for_timeout(450)
        page.wait_for_timeout(800)
        page.fill(".nt-ask-input", "Recruit"); page.wait_for_timeout(500)
        page.evaluate("()=>{const b=document.querySelector('#nova-intro .nt-ask-go'); if(b) b.hidden=false;}")
        page.evaluate("()=>{ boardFetchedAt = Date.now(); }")   # the board was asked for on Welcome and has come back
        page.click("#nova-intro .nt-ask-go"); t1 = time.time(); r = None
        while time.time() - t1 < 7 and not r:
            page.wait_for_timeout(60)
            r = page.evaluate("()=>{ const m=document.querySelector('#nova-intro .nt-ask-msg.is-verified'); return m ? {t:m.textContent, c:getComputedStyle(m).color} : null }")
        took = round(time.time() - t1, 2)
        chk("the username check says Verified, in green, a beat after the board is in (under 1.5s)", r and r["t"] == "Verified" and r["c"].startswith("rgb(107") and took < 1.5, [r, took])
        chk("no page errors through the flow", not errs, errs[:3])
        ctx.close()
    if "xp" in want:
        ctx, page = page_for(br, "15")
        page.evaluate("()=>showPointsFlyEffect('+100 XP for creating an account!')"); page.wait_for_timeout(500)
        r = page.evaluate("()=>{ const b=document.getElementById('welcomebonus-banner'); const cs=getComputedStyle(b); return {bf:cs.backdropFilter||cs.webkitBackdropFilter, rad:cs.borderTopLeftRadius, tag:!!b.querySelector('.wb-tag'), bar:cs.borderLeftWidth} }")
        chk("the +100 XP pop-up is the account banner's glass: 16px corners, a 3px bar, a tag", r["rad"] == "16px" and r["bar"] == "3px" and r["tag"], r)
        chk("...and nothing blurred moves with it (no backdrop filter)", r["bf"] in ("none", "", None), r)
        page.wait_for_timeout(700)
        r = page.evaluate("()=>{ const b=document.getElementById('welcomebonus-banner'); return b ? {fly:b.classList.contains('welcomebonus-fly'), tr:getComputedStyle(b).transitionDuration} : null }")
        chk("it flies to Profile over .8s (it was .55s)", r and r["fly"] and "0.8s" in r["tr"], r)
        ctx.close()
    br.close()
print("\nALL PASS" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
