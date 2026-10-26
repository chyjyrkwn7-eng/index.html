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
want = [a for a in sys.argv[1:]] or ["bubble", "new", "se", "flare"]
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
    br.close()
print("\nALL PASS" if ok else "\nFAILED"); sys.exit(0 if ok else 1)
