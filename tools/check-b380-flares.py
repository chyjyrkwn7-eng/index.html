"""Build 380: Home's rank bubbles keep moving on an iPad that comes back at another size.
Madison: "the iPads main menu, the rank flares, the stuff within them aren't moving".
The sheets come off while the app is away and only went back on for the window size
they were made at: an iPad turned while away (Split View, Stage Manager) came back with
every bubble on its still drawing until Home was built again.
Run:  python3 tools/check-b380-flares.py   (--against: copy the old index.html over first)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-0380');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = "pubtest0380f"; d["firstName"] = "Casey"; d["novaMet"] = 99
HIDE = """()=>{ Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'}); document.dispatchEvent(new Event('visibilitychange')); }"""
SHOW = """()=>{ delete document.hidden; delete document.visibilityState; document.dispatchEvent(new Event('visibilitychange')); }"""
COUNT = """async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const imgs=()=>[...document.querySelectorAll('#stage .cosmic-badge-rank .rk-frame img')];
 const snap=()=>imgs().map(i=>{const cs=getComputedStyle(i); return cs.left+'|'+cs.top+'|'+cs.transform;}); const a=snap(); await wait(800); const b=snap();
 const bs=[...document.querySelectorAll('#stage .cosmic-badge-rank')];
 return {bubbles:bs.length, moving:a.filter((x,k)=>x!==b[k]).length, standins:document.querySelectorAll('#stage .cosmic-rank-anim.is-standin').length,
   most:Math.max(0,...bs.map(x=>x.querySelectorAll(':scope > .cosmic-rank-anim').length))}; }"""
W, H = 834, 1194
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)
def home_ready(pg):
    t0 = time.time()
    while time.time() - t0 < 300:
        pg.wait_for_timeout(3000)
        k = pg.evaluate("()=>[document.querySelectorAll('#stage .cosmic-badge-rank').length, document.querySelectorAll('#stage .cosmic-badge-rank .cosmic-rank-anim').length]")
        if k[0] and k[1] >= k[0]: return True
    return False
def fresh(br):
    g["new_page"].w, g["new_page"].h = W, H
    ctx, pg = g["new_page"](br, (24, 0, 20, 0), True, False)
    pg.add_init_script(INIT % json.dumps(json.dumps(d)))
    pg.goto(url); pg.wait_for_timeout(3000); pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }")
    return ctx, pg
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # (1) back at the same size: as before, nothing stood in
    ctx, pg = fresh(br); home_ready(pg); pg.wait_for_timeout(1500)
    pg.evaluate(HIDE); pg.wait_for_timeout(800); pg.evaluate(SHOW); pg.wait_for_timeout(4000)
    r = pg.evaluate(COUNT)
    chk("back at the same size every bubble moves on its own sheet (%d of %d, stand-ins %d)" % (r["moving"], r["bubbles"], r["standins"]),
        r["bubbles"] >= 3 and r["moving"] == r["bubbles"] and r["standins"] == 0 and r["most"] == 1, r)
    # (2) turned while away: back on its side
    pg.evaluate(HIDE); pg.wait_for_timeout(800); pg.set_viewport_size({"width": H, "height": W}); pg.wait_for_timeout(400)
    pg.evaluate(SHOW); pg.wait_for_timeout(4000)
    r = pg.evaluate(COUNT)
    chk("turned while away, every bubble is moving 4s after coming back (%d of %d)" % (r["moving"], r["bubbles"]),
        r["bubbles"] >= 3 and r["moving"] == r["bubbles"] and r["most"] == 1, r)
    pg.wait_for_timeout(60000)
    r2 = pg.evaluate(COUNT)
    chk("and its own sheets for that size take over as they are made (stand-ins %d -> %d), one sheet a bubble (%d)" % (r["standins"], r2["standins"], r2["most"]),
        r2["standins"] < r["standins"] and r2["moving"] == r2["bubbles"] and r2["most"] == 1, [r, r2])
    ctx.close()
    # (3) turned, then Home built again at a size with no sheets yet
    ctx, pg = fresh(br); home_ready(pg); pg.wait_for_timeout(1500)
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
    pg.set_viewport_size({"width": H, "height": W}); pg.wait_for_timeout(800)
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(4500)
    r = pg.evaluate(COUNT)
    chk("turned, a new Home has every bubble moving 4.5s in (%d of %d)" % (r["moving"], r["bubbles"]),
        r["bubbles"] >= 3 and r["moving"] == r["bubbles"] and r["most"] == 1, r)
    ctx.close()
    br.close()
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
