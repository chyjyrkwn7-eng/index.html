"""Build 349: the page viewer pinches, double-taps and pans on one transform; Gold, Sapphire and Supernova sit on the
outer ring; coming back from another app holds the optional work for a couple of seconds; the Leaderboard builds seven
rows in the tap's task; the class list is inert while closed and Start Studying answers on its left edge.
Run:  python3 tools/check-b349.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const n=AVATAR_CHARACTERS.length; const rows=[]; for(let i=0;i<42;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:AVATAR_CHARACTERS[i%n].id}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    # the viewer
    pg.evaluate("""()=>ifcOpenViewer({title:'t',sub:'s',render:async box=>{for(let i=0;i<3;i++){const c=document.createElement('canvas');c.width=800;c.height=1100;box.appendChild(c);}}})""")
    pg.wait_for_timeout(700)
    scale = lambda: pg.evaluate("()=>{ const m=/scale\\(([\\d.]+)\\)/.exec(document.querySelector('.ifc-vz-pages').style.transform||''); return m?+m[1]:null; }")
    ty = lambda: pg.evaluate("()=>{ const m=/translate3d\\([-\\d.]+px,\\s*([-\\d.]+)px/.exec(document.querySelector('.ifc-vz-pages').style.transform||''); return m?+m[1]:null; }")
    ev = lambda t, i, x, y: pg.dispatch_event(".ifc-vz-scroll", t, {"pointerId": i, "clientX": x, "clientY": y, "pointerType": "touch", "isPrimary": i == 1})
    chk("the viewer starts at 1x", scale() == 1, scale())
    ev("pointerdown", 1, 200, 400); ev("pointerup", 1, 200, 400); ev("pointerdown", 1, 200, 400); ev("pointerup", 1, 200, 400)
    pg.wait_for_timeout(400)
    z = scale(); chk("a double tap zooms in (%s)" % z, z and z > 1.5, z)
    y0 = ty(); ev("pointerdown", 1, 200, 500); ev("pointermove", 1, 200, 420); ev("pointermove", 1, 200, 300); ev("pointerup", 1, 200, 300); pg.wait_for_timeout(300)
    y1 = ty(); chk("one finger pans the zoomed page (%s -> %s)" % (y0, y1), y1 is not None and y0 is not None and y1 < y0 - 50, (y0, y1))
    ev("pointerdown", 1, 150, 400); ev("pointerdown", 2, 250, 400); ev("pointermove", 2, 330, 400); ev("pointermove", 2, 380, 400)
    z2 = scale(); chk("two fingers pinch it further (%s -> %s)" % (z, z2), z2 and z2 > z * 1.2, z2)
    ev("pointerup", 2, 380, 400); ev("pointerup", 1, 150, 400)
    ta = pg.evaluate("()=>getComputedStyle(document.querySelector('.ifc-vz-scroll')).touchAction")
    chk("the viewer takes the touches itself (touch-action none)", ta == "none", ta)
    pg.evaluate("()=>ifcCloseViewer()"); pg.wait_for_timeout(300)
    # Home's rank bubbles on the ring
    sp = pg.evaluate("()=>({ R: HOME_OUTER_R, spots: HOME_SPOTS.map(s=>s.R) })")
    n = sum(1 for r in sp["spots"] if abs(r - sp["R"]) < 1)
    m = sum(1 for r in sp["spots"] if abs(r - 108) < 1)
    chk("at least two rank bubbles sit on the outer ring (%d) and two on the inner (%d)" % (n, m), n >= 2 and m >= 2, sp)
    # coming back from another app
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1500)
    pg.evaluate("""()=>{ window.__u=0; window.__h=0; const cu=checkForUpdate, sh=sendHeartbeat; checkForUpdate=function(){ window.__u++; return cu.apply(this,arguments); }; try{ sendHeartbeat=function(){ window.__h++; return sh.apply(this,arguments); }; }catch(e){}
      Object.defineProperty(document,'hidden',{configurable:true,get:()=>window.__hid}); window.__hid=true; document.dispatchEvent(new Event('visibilitychange')); window.__hid=false; document.dispatchEvent(new Event('visibilitychange')); }""")
    pg.wait_for_timeout(400)
    early = pg.evaluate("()=>window.__u")
    chk("the update check does not run in the frames that wake the page (%s)" % early, early == 0, early)
    pg.wait_for_timeout(2600)
    late = pg.evaluate("()=>window.__u")
    chk("it still runs after a moment (%s)" % late, late >= 1, late)
    # leaderboard
    pg.evaluate(FILL)
    now = pg.evaluate("()=>{ showRankings(); return document.querySelectorAll('.rank-rows .rank-row').length; }")
    chk("the Leaderboard builds seven rows in the tap's own task (%d)" % now, 1 <= now <= 8, now)
    pg.wait_for_timeout(2500)
    full = pg.evaluate("()=>document.querySelectorAll('.rank-rows .rank-row').length")
    chk("and finishes the list (%d)" % full, full >= 42, full)
    # Start Studying left edge, class list inert while closed
    pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(1800)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    r = pg.evaluate("""()=>{ const b=document.querySelector('.screen-home-actual > .playbtn'); if(!b) return null; const q=b.getBoundingClientRect();
      const hit=(x)=>{ const e=document.elementFromPoint(x, q.top+q.height/2); return !!e && (e===b||b.contains(e)); };
      const st=document.querySelector('.class-bubble-wrap .class-stack'); return { left:hit(q.left+8), right:hit(q.right-8), stack: st? getComputedStyle(st).pointerEvents : 'none' }; }""")
    chk("Start Studying answers on its left and right edges", r and r["left"] and r["right"], r)
    chk("the closed class list takes no touches", r and r["stack"] == "none", r)
    ctx.close(); br.close()
sys.exit(0 if g["ok"] else 1)
