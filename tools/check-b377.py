"""Build 377: (1) when the page is hidden it notes what it held (elements, images, canvases, sheets) with the hide, and the next launch puts it
in the ended log; (2) the board's characters that have never been recorded on this device are recorded in the quiet after launch, without
anybody looking at the board; (3) a ready sheet keeps its decoded picture while the app is up and lets it go when the app is hidden;
(4) a slide across the bar takes the tabs' native switches away while it lasts (no ticks on the way) and puts them back; (5) a board left in
the background keeps its art; (6) a board switch brings the screenful back as loops only (no drawing under them, nothing queued) and its
flares as loops only; (7) the bar is see-through glass (a blur of at most 10px over a body at most 30% dark).
Run:  python3 tools/check-b377.py   (--against: copy the old index.html and version.json over first)"""
import os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
def fill(ids):
    return """()=>{ const ids=%s; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%%ids.length]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2)})); } leaderboardRows = rows; }""" % ids
HIDE = """()=>{ Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'}); Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); document.dispatchEvent(new Event('visibilitychange')); }"""
SHOW = """()=>{ Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'visible'}); Object.defineProperty(document,'hidden',{configurable:true,get:()=>false}); document.dispatchEvent(new Event('visibilitychange')); }"""
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    ctx, pg = g["page_for"](br, "promax")
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(fill("['ninja','wizard','ghost']")); pg.wait_for_timeout(300)
    pg.evaluate("()=>showRankings()")
    PROBE = "()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;}); return [vis.length, vis.filter(r=>r.querySelector('.char-flip-play')).length]; }"
    t0 = time.time()
    while time.time() - t0 < 90:
        pg.wait_for_timeout(1000)
        n, k = pg.evaluate(PROBE)
        if k >= n - 1: break
    # (6) a board switch: the screenful comes back as loops, with no drawing under them and nothing queued
    sw = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const btn=k=>[...document.querySelectorAll('.screen-rankings .navsegment button')].find(x=>new RegExp(k,'i').test(x.textContent));
      btn('hundo').click(); await wait(900); btn('overall').click(); await wait(60);
      const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row:not(.rank-row-head)')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;});
      const looping=vis.filter(r=>r.querySelector('.rank-avatar .char-flip-play'));
      return { vis: vis.length, looping: looping.length, withDrawing: looping.filter(r=>r.querySelector('.rank-avatar svg.avatarchar-svg')).length, queued: looping.filter(r=>r.dataset.lazyArt).length,
        flaresLoop: vis.filter(r=>r.querySelector('.rank-mark[data-loop-only] > .cosmic-rank-anim')).length, flaresDrawn: vis.filter(r=>r.querySelector('.rank-mark svg.cosmic-rank-emblem')).length }; }""")
    chk("a board switch brings the screenful back as loops only (%s)" % (sw,), sw["looping"] >= sw["vis"] - 1 and sw["withDrawing"] == 0 and sw["queued"] == 0 and sw["flaresLoop"] >= sw["vis"] - 1 and sw["flaresDrawn"] <= 1, sw)
    # (5) a board left in the background keeps its art
    pg.evaluate(HIDE); pg.wait_for_timeout(300)
    kept_bg = pg.evaluate("()=>{ const vis=[...document.querySelectorAll('.screen-rankings .rank-rows > .rank-row:not(.rank-row-head)')].filter(r=>{const b=r.getBoundingClientRect(); return b.top<innerHeight-90 && b.bottom>60;}); return [vis.length, vis.filter(r=>r.querySelector('.rank-avatar .char-flip-play') && !r.dataset.lazyArt).length]; }")
    pg.evaluate(SHOW); pg.wait_for_timeout(2600)
    chk("a board left in the background keeps its art (%s of %s rows)" % (kept_bg[1], kept_bg[0]), kept_bg[1] >= kept_bg[0] - 1, kept_bg)
    # (3) decoded pictures kept while up, let go when hidden
    kept = pg.evaluate("()=>[...charAnimReady.values()].filter(sp=>sp && sp.pre && sp.pre.complete).length")
    pg.evaluate(HIDE); pg.wait_for_timeout(200)
    let_go = pg.evaluate("()=>[...charAnimReady.values()].filter(sp=>sp && sp.pre).length")
    sess = pg.evaluate("()=>JSON.parse(localStorage.getItem('class26e.session')||'null')")
    pg.evaluate(SHOW); pg.wait_for_timeout(500)
    chk("a ready sheet keeps its decoded picture while the app is up (%s, again after a return) and lets it go when hidden (%s left)" % (kept, let_go), kept >= 2 and let_go == 0, [kept, let_go])
    fp = (sess or {}).get("fp") or ""
    chk("the hide notes what the page held (%s)" % fp, sess and sess.get("state") == "hidden" and fp.startswith("el") and " sh" in fp and "mp" in fp, sess)
    # (1) the next launch carries it in the ended log
    # as if iOS ended it while hidden: the hide's note is what the next launch finds (the reload's own "closed" is put back over)
    pg.evaluate("(s)=>{ window.addEventListener('pagehide', ()=>{ localStorage.setItem('class26e.session', JSON.stringify(s)); }); }", sess)
    pg.reload(); pg.wait_for_timeout(2500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    log = pg.evaluate("()=>JSON.parse(localStorage.getItem('class26e.crashlog')||'[]')")
    chk("the next launch's ended log carries it (%s)" % (log[-1:] if log else log,), bool(log) and "ENDED-hidden" in log[-1] and " el" in log[-1] and "mp" in log[-1], log)
    # (2) a character never recorded here is recorded in the quiet after launch, nobody on the board
    pg.evaluate(fill("['ninja','wizard','ghost','alien']"))
    before = pg.evaluate("()=>charAnimReady.size")
    pg.evaluate("()=>{ showProfile(); if(typeof lbArtPreloadSoon==='function') lbArtPreloadSoon(); }")
    t0 = time.time(); now = before
    while time.time() - t0 < 120:
        pg.wait_for_timeout(2000)
        now = pg.evaluate("()=>{ const G=lbGeomGet(); if(!G||!G.flip) return -1; const d=charAnimDrawings.get('alien'); return d && charAnimReady.has(d.id+'|'+G.flip.px) ? 100 : charAnimReady.size; }")
        if now == 100: break
    chk("a board character never recorded on this device is recorded after launch with nobody on the board (%s)" % ("yes" if now == 100 else "no: %s ready" % now), now == 100, [before, now])
    # (4) a slide takes the tabs' native switches away while it lasts (iPhone-only in the app; put in by hand here) and puts them back
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(2500)
    hs = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); const tabs=[...document.querySelectorAll('.bottomtabs-navrow .bottomtab')].filter(t=>t.offsetWidth);
      tabs.forEach(t=>{ if(!t.querySelector(':scope > .nova-hsw')){ const i=document.createElement('input'); i.type='checkbox'; i.className='nova-hsw'; t.appendChild(i); } });
      const n=()=>document.querySelectorAll('.bottomtabs-navrow .bottomtab > .nova-hsw').length;
      const nav=document.querySelector('.bottomtabs-navrow'), a=document.getElementById('bottomtab-home'), c=document.getElementById('bottomtab-calendar');
      const ra=a.getBoundingClientRect(), rc=c.getBoundingClientRect(), y=ra.top+ra.height/2, x0=ra.left+ra.width/2, x1=rc.left+rc.width/2;
      const mk=(t,xx)=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:95,isPrimary:true,clientX:xx,clientY:y});
      const before=n(); a.dispatchEvent(mk('pointerdown',x0)); await wait(60); for(let i=1;i<=10;i++){ nav.dispatchEvent(mk('pointermove',x0+(x1-x0)*i/20)); await wait(16); }
      const during=n(); for(let i=9;i>=0;i--){ nav.dispatchEvent(mk('pointermove',x0+(x1-x0)*i/20)); await wait(16); } nav.dispatchEvent(mk('pointerup',x0)); await wait(600);
      return { before, during, after: n() }; }""")
    chk("a slide takes the tabs' switches away while it lasts and puts them back (%s)" % (hs,), hs["before"] >= 4 and hs["during"] == 0 and hs["after"] == hs["before"], hs)
    # (7) see-through glass
    gl = pg.evaluate("""()=>{ const c=getComputedStyle(document.querySelector('.bottomtabs')); const bf=c.backdropFilter||c.webkitBackdropFilter||''; const m=/blur\(([\d.]+)px\)/.exec(bf);
      const bg=c.backgroundColor; const a=/rgba?\([^,]+,[^,]+,[^,]+(?:,\s*([\d.]+))?\)/.exec(bg); return { blur: m?parseFloat(m[1]):-1, bodyAlpha: a&&a[1]!==undefined?parseFloat(a[1]):1, bf, bg }; }""")
    chk("the bar is see-through glass (blur %spx, body %s)" % (gl["blur"], gl["bodyAlpha"]), 0 < gl["blur"] <= 10 and gl["bodyAlpha"] <= .3, gl)
    br.close()
sys.exit(0 if g["ok"] else 1)
