"""Build 379: (1) the board counts the rows it shows at its top on this device, and the next visit brings only those (and one more) up
with their loops in the mounting task - not 16; (2) the rows past them get their loops from the queue just after (loops alone, no drawing
under them), with none of the first 16 left bare; (3) html.lb-paint.lb-win: painted loops, each window a small layer - the board looks the
same frame for frame and the loops move; (4) the Leaderboard speed test's looks are base, nostill, paintwin, noloops, norows;
(5) a board opened from the tab comes up with every loop still (painted, paused - none moving on a layer) while the glass is up, and once it
has landed the rows take their moving loops back a row a frame (never more than one row's two loops a frame) until every loop moves and the
board is no longer still;
(6) Arrest, Search, and Seizure #31 and #55 (the same question twice in the 8-28-26 guide, with different answers) each count the guide's
own answer - #31 "Revoked by the person granting consent", #55 "Is a mere acquiescence to authority claimed by the officer" - and no
question carries a "being verified" note.
Run:  python3 tools/check-b379.py   (--against: copy the old index.html and version.json over first)"""
import os, sys, time, io, re
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
    pg.evaluate(FILL); pg.evaluate("()=>showRankings()")
    t0 = time.time()
    while time.time() - t0 < 120:
        pg.wait_for_timeout(1500)
        k = pg.evaluate("()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;}); return [vis.length, vis.filter(r=>r.querySelector('.char-flip-play')).length]; }")
        if k[1] >= k[0] - 1: break
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
    r = pg.evaluate("""async()=>{ showRankings(); const rows=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row[data-pub]')];
       const at0=rows.map(r=>r.querySelector('.char-flip-play')?1:0);
       const shown=rows.filter(r=>r.getBoundingClientRect().top<innerHeight).length;
       await new Promise(r=>setTimeout(r,2600));
       const all=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row[data-pub]')], rows2=all.slice(0,16);
       const withArt=all.filter(r=>r.querySelector('.char-flip-play') || r.querySelector('.rank-avatar svg.avatarchar-svg'));
       return { at0, shown, looping16: rows2.filter(r=>r.querySelector('.char-flip-play')).length, art: withArt.length, drawn: withArt.filter(r=>r.querySelector('.rank-avatar svg.avatarchar-svg')).length,
         bare16: rows2.filter(r=>!r.querySelector('.char-flip-play') && !r.querySelector('.rank-avatar svg')).length }; }""")
    first = sum(r["at0"]); lead = r["at0"][:first]
    chk("the next visit brings up only the rows it shows (%s) and one more with their loops in the mounting task (%s)" % (r["shown"], first),
        r["shown"] >= 6 and first == r["shown"] + 1 and all(lead), r)
    chk("the rows past them get their loops just after, alone (first 16: %s looping, %s bare; of the %s rows with art by then, %s carry a drawing)" % (r["looping16"], r["bare16"], r["art"], r["drawn"]),
        r["looping16"] >= 16 and r["bare16"] == 0 and r["art"] >= 17 and r["drawn"] == 0, r)
    # (3) painted, each window a layer
    pg.wait_for_timeout(1500)
    def shot(t):
        pg.evaluate("(t)=>{ document.getAnimations().forEach(a=>{ try{ const el=a.effect&&a.effect.target; if(el&&el.closest&&el.closest('.rank-rows')){ a.pause(); a.currentTime=t; } }catch(e){} }); }", t)
        pg.wait_for_timeout(300)
        return Image.open(io.BytesIO(pg.screenshot(clip={"x": 0, "y": 150, "width": 440, "height": 650}))).convert("RGB")
    def play(): pg.evaluate("()=>document.getAnimations().forEach(a=>{ try{ a.play(); }catch(e){} })")
    def differs(a, b):
        h = ImageChops.difference(a, b).convert("L").histogram(); return sum(h[25:])
    A = [shot(t) for t in (1010, 2345)]; play()
    pg.evaluate("()=>{ const c=document.documentElement.classList; c.add('lb-paint'); c.add('lb-win'); if(typeof lbPaintAll==='function') lbPaintAll(document.querySelector('.screen-rankings .rank-rows')); }")
    pg.wait_for_timeout(500)
    W = [shot(t) for t in (1010, 2345)]; play()
    wc = pg.evaluate("()=>[...new Set([...document.querySelectorAll('.screen-rankings .rank-rows .char-flip-play, .screen-rankings .rank-rows .rk-frame')].map(e=>getComputedStyle(e).willChange))]")
    d = [differs(a, b) for a, b in zip(A, W)]
    chk("painted loops on their own small layers: the board looks the same (%s px off), the loops move (%s), every window is a layer (%s)" % (d, differs(W[0], W[1]) > 50, wc),
        max(d) < 400 and differs(W[0], W[1]) > 50 and wc == ["transform"], [d, wc])
    pg.evaluate("()=>{ const c=document.documentElement.classList; c.remove('lb-paint'); c.remove('lb-win'); }")
    # (4)
    looks = pg.evaluate("()=>typeof BOARD_TEST_LOOKS!=='undefined' ? BOARD_TEST_LOOKS.map(l=>l[0]+':'+l[2]) : null")
    chk("the speed test's looks are base, nostill, paintwin, noloops, norows (%s)" % (looks,),
        looks == ["base:", "nostill:lb-nostill", "paintwin:lb-paint lb-win", "noloops:", "norows:"], looks)
    # (5) still first, then a row a frame
    pg.evaluate("()=>showProfile()"); pg.wait_for_timeout(1500)
    L = pg.evaluate("""async()=>{ const el=document.getElementById('bottomtab-rewards'); const b=el.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
      const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:41,isPrimary:true,clientX:x,clientY:y});
      const L=[]; const T0=performance.now(); let done=false;
      const tick=()=>{ const rows=document.querySelector('.screen-rankings .rank-rows'); if(rows){ const imgs=[...rows.querySelectorAll('.char-flip-play img, .rk-frame img')];
          L.push({ t: Math.round(performance.now()-T0), still: rows.classList.contains('lb-still'), moving: imgs.filter(i=>getComputedStyle(i).animationName.startsWith('rk-sheet')).length, movingVis: imgs.filter(i=>!i.closest('.is-offscreen') && getComputedStyle(i).animationName.startsWith('rk-sheet')).length,
            layered: imgs.filter(i=>getComputedStyle(i).willChange==='transform').length, n: imgs.length, up: !!document.querySelector('#bottomtabs-lens.is-up') }); }
        if(performance.now()-T0<3200) requestAnimationFrame(tick); else done=true; };
      el.dispatchEvent(mk('pointerdown')); await new Promise(r=>setTimeout(r,60)); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y}));
      requestAnimationFrame(tick); while(!done) await new Promise(r=>setTimeout(r,100)); return L; }""")
    upf = [f for f in L if f["up"]]
    still_up = bool(upf) and all(f["still"] and f["moving"] == 0 and f["layered"] == 0 and f["n"] >= 10 for f in upf)
    steps = [L[i]["movingVis"] - L[i - 1]["movingVis"] for i in range(1, len(L))]   # rows skipped by the browser (off screen) cost nothing
    end = L[-1] if L else {}
    first_move = next((f["t"] for f in L if f["moving"] > 0), None)
    landed = next((f["t"] for f in L if not f["up"]), None)
    chk("a board opened from the tab is still while the glass is up (%s frames up, all still: %s), moves a row a frame once it has landed (landed %sms, first loop moving %sms, most loops on screen started in one frame %s) until all %s move (%s, board still: %s)"
        % (len(upf), still_up, landed, first_move, max(steps) if steps else None, end.get("n"), end.get("moving"), end.get("still")),
        still_up and first_move is not None and landed is not None and first_move >= landed and max(steps) <= 2 and end.get("moving") == end.get("n") and end.get("still") is False,
        [L[:3], L[-3:]])
    # (6) the twins keep the guide's answers
    tw = pg.evaluate("""()=>{ const f=s=>QUESTIONS.find(q=>q.topic==='Arrest, Search, and Seizure' && q.src===s); return { a31: f(31).choices[f(31).answer], a55: f(55).choices[f(55).answer], notes: QUESTIONS.filter(q=>q.verifyNote).length }; }""")
    chk("#31 counts '%s', #55 '%s', %s questions with a being-verified note" % (tw["a31"], tw["a55"], tw["notes"]),
        tw["a31"] == "Revoked by the person granting consent" and tw["a55"] == "Is a mere acquiescence to authority claimed by the officer" and tw["notes"] == 0, tw)
    br.close()
sys.exit(0 if g["ok"] else 1)
