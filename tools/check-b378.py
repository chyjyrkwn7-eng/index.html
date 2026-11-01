"""Build 378: the Leaderboard speed test and the two other ways a board loop can be played.
(1) Report a bug has "Test Leaderboard speed"; it runs every look (base, paint, hold, noloops, nofx, noglass, norows) three times and
reports each look's numbers, and leaves the page as it found it (no look's class or style left on);
(2) html.lb-paint: the board's loops are moved by left/top on the same clock - the board looks the same frame for frame, the loops still
move, and the board has at most half the layers it has as it is;
(3) html.lb-hold: the loops are moved on a linear clock that holds each frame - the board looks the same frame for frame and every loop
runs linear;
(4) a board built while a look is on comes up in that look (every loop in it, not only the ones there when the look was turned on).
Run:  python3 tools/check-b378.py   (--against: copy the old index.html and version.json over first)"""
import os, sys, time, io
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
FILL = """()=>{ const ids=['ninja','wizard','ghost']; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%3]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }"""
LOOPS = "'.screen-rankings .rank-rows .char-flip-play img, .screen-rankings .rank-rows .rk-frame img'"
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILL); pg.wait_for_timeout(300)
    pg.evaluate("()=>showRankings()")
    PROBE = "()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;}); return [vis.length, vis.filter(r=>r.querySelector('.char-flip-play')).length, vis.filter(r=>r.querySelector('.cosmic-rank-anim')).length]; }"
    t0 = time.time()
    while time.time() - t0 < 120:
        pg.wait_for_timeout(1000)
        n, k, f = pg.evaluate(PROBE)
        if k >= n - 1 and f >= n - 2: break
    pg.wait_for_timeout(1500)
    def shot(t):
        pg.evaluate("(t)=>{ document.getAnimations().forEach(a=>{ try{ const el=a.effect&&a.effect.target; if(el&&el.closest&&el.closest('.rank-rows')){ a.pause(); a.currentTime=t; } }catch(e){} }); }", t)
        pg.wait_for_timeout(300)
        return Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": 150, "width": 440, "height": 650}))).convert("RGB")
    def play(): pg.evaluate("()=>document.getAnimations().forEach(a=>{ try{ a.play(); }catch(e){} })")
    def layers():
        cdp = ctx.new_cdp_session(pg); cdp.send("LayerTree.enable"); got = []
        cdp.on("LayerTree.layerTreeDidChange", lambda e: got.append(e))
        pg.evaluate("()=>{document.body.style.outline=document.body.style.outline?'':'0px solid transparent'}"); pg.wait_for_timeout(600)
        L = (got[-1].get("layers") or []) if got else []; cdp.detach()
        return len(L)
    def differs(a, b):
        h = ImageChops.difference(a, b).convert("L").histogram(); return sum(h[25:])
    TIMES = (1010, 2345, 4111)
    base_layers = layers()
    A = [shot(t) for t in TIMES]; play()
    loops = pg.evaluate("()=>document.querySelectorAll(%s).length" % LOOPS)
    has = pg.evaluate("()=>typeof lbPaintAll === 'function'")
    # (2) paint
    pg.evaluate("()=>{ document.documentElement.classList.add('lb-paint'); if(typeof lbPaintAll==='function') lbPaintAll(document.querySelector('.screen-rankings .rank-rows')); }")
    pg.wait_for_timeout(500)
    paint_layers = layers()
    P = [shot(t) for t in TIMES]; play()
    pn = pg.evaluate("()=>[...new Set([...document.querySelectorAll(%s)].map(i=>getComputedStyle(i).animationName.replace(/-\\d.*/,'')))]" % LOOPS)
    pd = [differs(a, b) for a, b in zip(A, P)]
    moving = differs(P[0], P[1]) > 50
    chk("painted loops: the board looks the same frame for frame (%s px off), the loops move (%s), %s loops all on left/top (%s), layers %s -> %s" % (pd, moving, loops, pn, base_layers, paint_layers),
        has and loops >= 12 and max(pd) < 400 and moving and pn == ["rk-pos"] and paint_layers * 2 <= base_layers, [pd, moving, pn, base_layers, paint_layers])
    pg.evaluate("()=>document.documentElement.classList.remove('lb-paint')"); pg.wait_for_timeout(400)
    # (3) hold
    pg.evaluate("()=>{ document.documentElement.classList.add('lb-hold'); if(typeof lbPaintAll==='function') lbPaintAll(document.querySelector('.screen-rankings .rank-rows')); }")
    pg.wait_for_timeout(500)
    H = [shot(t) for t in TIMES]; play()
    hn = pg.evaluate("()=>[...new Set([...document.querySelectorAll(%s)].map(i=>getComputedStyle(i).animationName.replace(/-\\d.*/,'')+' '+getComputedStyle(i).animationTimingFunction))]" % LOOPS)
    hd = [differs(a, b) for a, b in zip(A, H)]
    chk("held-frame loops: the board looks the same frame for frame (%s px off) and every loop runs linear (%s)" % (hd, hn),
        has and max(hd) < 400 and hn == ["rk-hold linear"], [hd, hn])
    # (4) a board built in a look comes up in it
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(800)
    pg.evaluate("()=>showRankings()"); pg.wait_for_timeout(1500)
    built = pg.evaluate("()=>{ const a=[...document.querySelectorAll(%s)]; return [a.length, a.filter(i=>getComputedStyle(i).animationName.startsWith('rk-hold')).length]; }" % LOOPS)
    pg.evaluate("()=>{ document.querySelector('.screen-rankings .navsegment button:nth-child(2)') && document.querySelector('.screen-rankings .navsegment button:nth-child(2)').click(); }"); pg.wait_for_timeout(1200)
    switched = pg.evaluate("()=>{ const a=[...document.querySelectorAll(%s)]; return [a.length, a.filter(i=>getComputedStyle(i).animationName.startsWith('rk-hold')).length]; }" % LOOPS)
    chk("a board built (%s) or switched (%s) while a look is on comes up in it" % (built, switched), built[0] >= 10 and built[1] == built[0] and switched[0] >= 10 and switched[1] == switched[0], [built, switched])
    pg.evaluate("()=>document.documentElement.classList.remove('lb-hold')"); pg.wait_for_timeout(300)
    # (1) the test itself
    pg.evaluate("()=>showBugReport()"); pg.wait_for_timeout(500)
    btn = pg.evaluate("()=>[...document.querySelectorAll('.screen-bugreport button')].some(b=>/Leaderboard speed/i.test(b.textContent))")
    res = pg.evaluate("async()=>{ if(typeof runBoardTest!=='function') return null; document.documentElement.classList.add('lb-paint'); const r=await runBoardTest(); const c=document.documentElement.classList; return [r.text, c.contains('lb-paint'), c.contains('lb-hold'), !!document.getElementById('board-test-look')]; }")
    import re
    looks = re.findall(r"\[b:(\w+)\] r p(\d+) \(([\d,]+)\) idle w(\d+)/s(\d+)/n(\d+)/f(\d+) \| p p(\d+)", res[0]) if res else []
    names = [l[0] for l in looks]
    chk("Report a bug has the Leaderboard speed test (%s); it reports every look three times (%s) and leaves the page as it was (%s)" % (btn, names, res[1:] if res else res),
        btn and names == ["base", "paint", "hold", "noloops", "nofx", "noglass", "norows"] and all(len(l[2].split(",")) == 3 and int(l[1]) > 0 and int(l[7]) > 0 for l in looks) and res[1] is True and res[2] is False and res[3] is False,
        res)
    pg.evaluate("()=>document.documentElement.classList.remove('lb-paint')")
    br.close()
sys.exit(0 if g["ok"] else 1)
