"""Build 382: the Leaderboard opens clean, and its new look.
With an iPhone user agent, touch, 440x956 at 3x and the CPU slowed 4x:
(1) art that comes in after the board is up comes in together: on a first visit (nothing recorded, every row's character and flare
    filled from the queue) the rows on screen go from no art to their art in at most two steps - never a row a frame - and all of them
    end with their art;
(2) the same board is not built twice: the listener's answer a moment after the board opens (the same rows it opened with) leaves the
    rows' nodes as they were (none removed), and the main-thread time spent drawing the board over the open is one build's (<= 1.3x the
    first build), not two;
(3) no layout shift while the board opens (CLS over the 2.5s after the tap under 0.01);
(4) placeholders to rows: the board opened with nothing in memory shows its column header and placeholder rows where the real ones will
    be - when the rows arrive (1.5s late) the header and the first five rows are within 1.5px of where the header and placeholders stood;
(5) a still board (the watchdog's layers) starts moving as one: every row takes its moving loop in the same frame;
(6) the look, read off the page at the Pro Max and an iPad 11: the medals are circles, the place's "#" is quieter than its number, gold,
    silver and bronze rows each carry their metal ring and their own light, your row wears the accent's ring and a wash of it, every
    real row is one height (>= 44px) with no backdrop blur, the column labels are spaced capitals.
Run:  python3 tools/check-b382-board.py   (--against: copy the old index.html over first)"""
import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(HERE + "/check-b330.py").read().split("want = sys.argv")[0]
g = {"__file__": HERE + "/check-b330.py", "__name__": "b330"}; exec(src, g)
from playwright.sync_api import sync_playwright
chk = g["chk"]
CLEAR = "()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }"
IPH = """(()=>{ const ua='Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148';
  Object.defineProperty(Navigator.prototype,'userAgent',{get:()=>ua,configurable:true}); try{ delete Navigator.prototype.vibrate; }catch(e){}
  window.__cls=[]; try{ new PerformanceObserver(l=>l.getEntries().forEach(e=>{ if(!e.hadRecentInput) __cls.push([e.startTime, e.value]); })).observe({type:'layout-shift', buffered:true}); }catch(e){}
  window.__lt=[]; try{ new PerformanceObserver(l=>l.getEntries().forEach(e=>__lt.push([e.startTime, e.duration]))).observe({type:'longtask'}); }catch(e){} })()"""
# per frame: the rows on screen, how many show their art (a character - drawing or loop - and not held back by the reveal)
FRAMES = """async(ms)=>{ const L=[]; const T0=performance.now();
  await new Promise(res=>{ const tick=()=>{ const scr=document.querySelector('.screen-rankings');
    if(scr){ const vh=innerHeight; const rs=[...scr.querySelectorAll('.rank-rows > .rank-row[data-pub]')].filter(r=>{ const b=r.getBoundingClientRect(); return b.bottom>0 && b.top<vh-100; });
      const art=rs.filter(r=>!r.classList.contains('lb-art-new') && !r.dataset.lazyArt && r.querySelector('.rank-avatar > svg, .rank-avatar > .char-flip-play')).length;
      L.push([Math.round(performance.now()-T0), rs.length, art]); }
    if(performance.now()-T0<ms) requestAnimationFrame(tick); else res(); }; requestAnimationFrame(tick); });
  return L; }"""
FILLFN = """()=>{ window.__fill=()=>{ const ids=['ninja','wizard','ghost','grizzly']; const rows=[]; for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%4]}, boardNumbersOf(store), {weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:40-(i>>1), badges:20-(i>>2), xp:90000-i*2000})); } return rows; }; }"""
TAP = """()=>{ const el=document.getElementById('bottomtab-rewards'); const b=el.getBoundingClientRect(), x=b.left+b.width/2, y=b.top+b.height/2;
  const mk=t=>new PointerEvent(t,{bubbles:true,cancelable:true,pointerType:'touch',pointerId:77,isPrimary:true,clientX:x,clientY:y});
  window.__tapAt=performance.now(); el.dispatchEvent(mk('pointerdown')); el.dispatchEvent(mk('pointerup')); el.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:x,clientY:y})); }"""
LOOK = """()=>{ const scr=document.querySelector('.screen-rankings'); const rows=[...scr.querySelectorAll('.rank-rows > .rank-row[data-pub]')];
  const cs=e=>getComputedStyle(e); const px=v=>parseFloat(v)||0;
  const med=[...scr.querySelectorAll('.rank-place.lb-rank-medal')].map(m=>{ const b=m.getBoundingClientRect(); return [Math.round(b.width*10)/10, Math.round(b.height*10)/10]; });
  const r4=rows.find(r=>!r.querySelector('.lb-rank-medal')); const hash=r4 && r4.querySelector('.rank-place .rank-hash');
  const pod=[1,2,3].map(n=>{ const r=scr.querySelector('.rank-row.rank-podium-'+n+':not(.lb-row-me)'); if(!r) return null; const be=getComputedStyle(r,'::before');
    return { ring: be.content!=='none' && be.backgroundImage.includes('gradient'), light: cs(r).backgroundImage.includes('radial-gradient') }; });
  const me=scr.querySelector('.rank-row.lb-row-me'); const acc=me ? (()=>{ const t=document.createElement('span'); t.style.color='var(--accent)'; me.appendChild(t); const c=cs(t).color; t.remove(); return c; })() : null;
  const hs=rows.map(r=>Math.round(r.getBoundingClientRect().height*10)/10);
  const head=[...scr.querySelectorAll('.rank-row-head .rank-col-head')].map(h=>px(cs(h).letterSpacing)/px(cs(h).fontSize));
  return { med, hash: hash ? +cs(hash).opacity : null, hashText: r4 ? r4.querySelector('.rank-place').textContent : null, pod,
    me: me ? { border: cs(me).borderTopColor, acc, wash: cs(me).backgroundImage.includes('gradient') } : null,
    hmin: Math.min(...hs), hmax: Math.max(...hs), blur: rows.filter(r=>{ const f=cs(r).backdropFilter||cs(r).webkitBackdropFilter||'none'; return f!=='none'; }).length,
    head }; }"""

def load(pw, dev):
    br = pw.chromium.launch(executable_path=g["g"]["CHROME"])
    w, h, ins, inst = g["DEV"][dev]; g["g"]["new_page"].w, g["g"]["new_page"].h = w, h
    ctx, pg = g["g"]["new_page"](br, ins, inst, False)
    ctx.add_init_script(IPH)
    pg.add_init_script(g["INIT"] % json.dumps(g["seed"]()))
    pg.goto(g["url"]); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3): pg.evaluate(CLEAR); pg.wait_for_timeout(300)
    pg.evaluate(FILLFN)
    # the watchdog may put the loops on layers mid-measure in a slow sandbox: held off
    pg.evaluate("()=>{ try{ loopsWatch.busy=true; }catch(e){} }")
    return br, ctx, pg

with sync_playwright() as pw:
    br, ctx, pg = load(pw, "promax")
    cdp = ctx.new_cdp_session(pg)
    # (1) first visit: nothing recorded, the rows' art from the queue
    pg.evaluate("()=>{ leaderboardRows=__fill(); }")
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    pg.evaluate(TAP)
    L = pg.evaluate(FRAMES, 9000)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    seen = [f for f in L if f[1] >= 5]
    ups = [b[2] - a[2] for a, b in zip(seen, seen[1:]) if b[2] > a[2]]
    last = seen[-1] if seen else [0, 0, 0]
    chk("first visit: the rows on screen get their art in %d step(s) (%s), never a row a frame; at the end %d of %d show it"
        % (len(ups), ups[:12], last[2], last[1]), seen and len(ups) <= 2 and last[2] >= last[1] - 1, [seen[:3], seen[-3:]])
    # (2)/(3) the next visit: rows in memory, the listener answers with the same rows
    pg.evaluate("()=>{ showHome(); leaderboardRows=__fill(); }"); pg.wait_for_timeout(2500)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    r = pg.evaluate("""async()=>{ const real=window.renderRankingRows; const T=[]; window.renderRankingRows=function(){ const t=performance.now(); const o=real.apply(this, arguments); T.push(performance.now()-t); return o; };
      const wait=ms=>new Promise(r=>setTimeout(r,ms)); __cls.length=0;
      (%s)(); let first=null; const t0=performance.now();
      while(!(first=document.querySelector('.screen-rankings .rank-rows > .rank-row[data-pub]')) && performance.now()-t0<8000) await wait(10);
      const rowsEl=document.querySelector('.screen-rankings .rank-rows'); const nodes=[...rowsEl.querySelectorAll(':scope > .rank-row[data-pub]')];
      let removed=0; const mo=new MutationObserver(ms=>ms.forEach(m=>m.removedNodes.forEach(n=>{ if(n.nodeType===1 && n.matches && n.matches('.rank-row[data-pub]')) removed++; }))); mo.observe(rowsEl,{childList:true});
      await wait(2500); mo.disconnect(); window.renderRankingRows=real;
      const still=nodes.filter(n=>n.isConnected).length;
      const cls=__cls.filter(x=>x[0]>=__tapAt).reduce((a,x)=>a+x[1],0);
      const lt=__lt.filter(x=>x[0]>=__tapAt && x[0]<__tapAt+1500).map(x=>Math.round(x[1]));
      return { builds: T.map(x=>Math.round(x)), removed, still, n: nodes.length, cls: Math.round(cls*10000)/10000, lt }; }""" % TAP)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    total = sum(r["builds"]); one = r["builds"][0] if r["builds"] else 0
    chk("the next visit is built once: the listener's same answer removes %d row(s), %d of %d first rows still up; drawing time %sms (first build %sms)"
        % (r["removed"], r["still"], r["n"], r["builds"], one), r["n"] >= 5 and r["removed"] == 0 and r["still"] == r["n"] and total <= one * 1.3 + 5, r)
    chk("no layout shift while the board opens (CLS %s; long tasks in the first 1.5s at 4x, for the record: %s)" % (r["cls"], r["lt"]), r["cls"] < 0.01, r)
    # (4) placeholders to rows
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    s = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); leaderboardRows=[];
      const real=window.onSnapshotResilient; const F=__fill(); const fake={ forEach:f=>F.forEach(e=>f({ id:e.pub, data:()=>Object.assign({}, e) })), metadata:{ fromCache:false }, size:F.length, docs:[] };
      window.onSnapshotResilient=(ref, cb, o)=>real(ref, snap=>setTimeout(()=>cb(fake), 1500), o);
      showRankings(); await wait(400);
      const tops=sel=>[...document.querySelectorAll('.screen-rankings .rank-rows > '+sel)].map(e=>Math.round(e.getBoundingClientRect().top*10)/10);
      const before={ head: tops('.rank-row-head'), rows: tops('.rank-row-skel') };
      await wait(2600); window.onSnapshotResilient=real;
      return { before, after: { head: tops('.rank-row-head'), rows: tops('.rank-row[data-pub]') } }; }""")
    b, a = s["before"], s["after"]
    ok4 = bool(b["head"]) and bool(a["head"]) and abs(b["head"][0] - a["head"][0]) <= 1.5 and len(b["rows"]) >= 5 and len(a["rows"]) >= 5 \
        and all(abs(x - y) <= 1.5 for x, y in zip(b["rows"][:5], a["rows"][:5]))
    chk("placeholders to rows: header %s -> %s, first rows %s -> %s" % (b["head"], a["head"], b["rows"][:5], a["rows"][:5]), ok4, s)
    # (5) a still board starts moving as one
    st = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms)); while(Date.now()<(window.settleUntil||0) || document.querySelector('#bottomtabs-lens.is-up')) await wait(50);
      const rows=document.createElement('div'); rows.className='rank-rows lb-still'; rows.style.cssText='position:fixed;left:0;top:0;width:200px;opacity:0;pointer-events:none';
      for(let i=0;i<8;i++){ const r=document.createElement('div'); r.className='rank-row'; r.innerHTML='<span class="char-flip-play"><img alt=""></span>'; rows.appendChild(r); }
      document.body.appendChild(rows); rows._lbFill=1; lbStillGo(rows, 1); const seen=[]; const t0=performance.now();
      await new Promise(res=>{ const f=()=>{ seen.push(rows.querySelectorAll('.lb-go').length); if(seen[seen.length-1]>=8 || performance.now()-t0>4000) res(); else requestAnimationFrame(f); }; requestAnimationFrame(f); });
      rows.remove(); return seen.filter((v,i)=>i===0 || v!==seen[i-1]); }""")
    chk("a still board starts moving as one: rows moving per frame %s" % (st,), st and st[-1] == 8 and len([v for v in st if 0 < v < 8]) == 0, st)
    # (6) the look
    pg.evaluate("()=>{ showHome(); leaderboardRows=__fill(); rankingsBoardKey='overall'; showRankings('overall'); }"); pg.wait_for_timeout(2500)
    def look_ok(lk):
        circ = len(lk["med"]) >= 3 and all(abs(w - h) <= 1 and w >= 20 for w, h in lk["med"])
        pod = all(p and p["ring"] and p["light"] for p in lk["pod"])
        me = lk["me"] and lk["me"]["border"] == lk["me"]["acc"] and lk["me"]["wash"]
        return circ and lk["hash"] is not None and lk["hash"] < 0.9 and (lk["hashText"] or "").startswith("#") and pod and me \
            and lk["hmax"] - lk["hmin"] <= 1 and lk["hmin"] >= 44 and lk["blur"] == 0 and lk["head"] and min(lk["head"]) >= 0.05
    lk = pg.evaluate(LOOK)
    chk("the look on a Pro Max: %s" % (lk,), look_ok(lk), lk)
    br.close()
    br, ctx, pg = load(pw, "ipad11")
    pg.evaluate("()=>{ leaderboardRows=__fill(); rankingsBoardKey='overall'; showRankings('overall'); }"); pg.wait_for_timeout(2500)
    lk = pg.evaluate(LOOK)
    chk("the look on an iPad 11: %s" % (lk,), look_ok(lk), lk)
    br.close()
print("ALL PASS" if g["ok"] else "SOME FAILED")
sys.exit(0 if g["ok"] else 1)
