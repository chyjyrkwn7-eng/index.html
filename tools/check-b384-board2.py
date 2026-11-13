"""Build 384: the Leaderboard fills in right, coming back to the app, switching class, last week's top 3, the new dot.
Madison (iPhone 17 Pro Max, the installed app):
  "When switching between classes, the screen completely blank and then loading bar comes up. Remove the completely blank part.."
  "When leaving the app and coming back, the lag is a lot better but it still kinda does a weird thing"
  "... the leaderboard doesn't perfectly populate when you open it. Even when it does load, the ranks aren't showing right. The
   characters don't load in by the way that's what I was referring to mostly."
  "The top three on the leaderboard (last weeks top 3) ensure that's updated to the new iOS theme."
  "The yellow dot you get next to your profile when something is unlocked and next to stuff, ensure that thing looks better too"
Installed, an iPhone's user agent, 440x956 at 3x, real touches (CDP), the CPU slowed 4x where it says so; shape read off the page:
(1) CLASS SWITCH: every composited frame from the tap on Fire Code in the class list until the new page's splash is up (CDP
    screencast, across the reload) shows the screen or the loader - none is blank (a blank frame: no edges anywhere, as the bare
    page background is); the old page put the loader up; the new page arrives in Fire Code with its splash showing at once.
(2) COMING BACK (Home with its moving flares on, and the Leaderboard): hidden -> frozen 3s -> shown (pageshow persisted, focus),
    4x CPU: the first frame back has every element where it was (within 2px; flip-book sheets excepted - they step by design);
    in the 2s after, nothing re-animates (no CSS animation starts, no element.animate(), no moving sheet put back) and no long
    task over 120ms (best of up to three returns: the sandbox is shared).
(3) THE LEADERBOARD BY A REAL TAP (4x CPU), its rows arrive in one piece: in every frame that shows rows, every row on the screen
    shows its character (an svg or a loaded loop, not hidden) and its flare - from the first; at the end every row on screen has
    its character drawn; every row's rank (its flare's tier and the rank word, and its colour) is the app's own rankOfEntry for
    that row's numbers (levels over the badge wall, rank floors and secret flares among them).
(4) LAST WEEK'S TOP 3 (This Week): no backdrop-filter anywhere in it; its card is the list's surface (the same computed background
    as a list row); the caption is grey sentence case (no capitals, no letter-spacing); the three places carry the board's medals
    (round, the board's size); and (384 round 2, the podium back - this replaced the list's "a 1px line between rows" check) it
    is a podium: 2nd, 1st, 3rd left to right on steps that rise from the card's floor, 1st's the tallest, the outer steps clear
    of the card's rounded corners. (tools/check-b384-podium-hint.py checks the podium at four sizes.)
(5) THE NEW DOT (seen-unlocks cleared, a rank not yet shown): on the Profile tab, Profile (Customize, the badge case, the rank) and
    Customize's character / banner / theme / hundo pages, every dot is one style - a solid fill (no gradient; since 384 r8 one small glow, a 10-20px
    blur, round every one), round, 8-10px, the same fill and size everywhere - and sits on its icon's corner on the 45-degree line (as far in
    from the right edge as down from the top, within 1.5px, and not past a third of the icon in).
(6) no page errors.
Run:  python3 tools/check-b384-board2.py [--against REV] [--only 1,2,...]"""
import base64, io, json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
import numpy as np
from PIL import Image
srv, url = g["serve"]()
ONLY = None
if "--only" in sys.argv: ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))
AGAINST = None
if "--against" in sys.argv:
    AGAINST = subprocess.check_output(["git", "-C", ROOT, "show", sys.argv[sys.argv.index("--against") + 1] + ":index.html"]).decode("utf-8")
def body_for(ins):
    if AGAINST is None: return g["patched"](ins)
    t, r, b, l = ins; v = {"top": f"{t}px", "right": f"{r}px", "bottom": f"{b}px", "left": f"{l}px"}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], AGAINST)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
def want(n): return ONLY is None or str(n) in ONLY
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
OWNER = "xph5b57jbp5a"
INIT = """(()=>{ if(localStorage.getItem('class26e.drill.v1')) return;
 localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3842');
 ['class26e.freshstart','class26e.intro.seen','class26e.unithold.tip','class26e.daily.seen','class26e.savecode.asked','class26e.savecode.card','class26e.getstarted'].forEach(k=>localStorage.setItem(k,'1'));
 localStorage.setItem('class26e.frame.ok','go-live-1'); localStorage.setItem('class26e.penal256578.seen','1'); })()"""
PERF = """(()=>{ window.__lt=[]; try{ new PerformanceObserver(l=>l.getEntries().forEach(e=>__lt.push([e.startTime, e.duration]))).observe({type:'longtask'}); }catch(e){} })()"""
VIS = """(()=>{ let hid=false; try{ Object.defineProperty(Document.prototype,'hidden',{get(){return hid;},configurable:true});
  Object.defineProperty(Document.prototype,'visibilityState',{get(){return hid?'hidden':'visible';},configurable:true}); }catch(e){}
  window.__setHidden=v=>{ hid=v; document.dispatchEvent(new Event('visibilitychange')); }; })()"""
def seed(pid):
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["publicId"] = pid; d["firstName"] = "Casey"; d["novaMet"] = 99
    return d
# thirty classmates: eight characters, every rank from none to Titan, a level over its badge wall, rank floors, secret flares
FILLFN = """()=>{ window.__fill=()=>{ const ids=['ninja','wizard','ghost','grizzly','alien','detective','zeus','clown']; const rows=[];
  for(let i=0;i<30;i++){ rows.push(Object.assign({pub:'zz'+i, firstName:'Cadet'+i, avatarChar:ids[i%ids.length]}, boardNumbersOf(store),
    {week: weekKeyNow(), weekPoints:1000-i*17, hundos:60-i, correct:5000-i*70, level:Math.max(1,84-i*3), badges:Math.max(0,24-i), mystery:i<3?3:(i%5===0?1:0),
     rankFloor:(i===9||i===17)?5:0, xp:90000-i*2000})); }
  return rows; }; }"""
def page(br, pid="pubtest0384b2", w=440, h=956, ins=(62, 0, 34, 0), extra=None):
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=3, has_touch=True, is_mobile=True, user_agent=UA)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    ctx.add_init_script(PERF)
    if extra: ctx.add_init_script(extra)
    pg = ctx.new_page(); body = body_for(ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(INIT % json.dumps(json.dumps(seed(pid))))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    return ctx, pg, errs
def boot(pg):
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(300)
    pg.evaluate(FILLFN)
    # Nova's weekly recap (it would cover the board a few seconds in) is not what is measured here
    pg.evaluate("()=>{ try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} }")
def tap(cdp, x, y, hold=0.06):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]}); time.sleep(hold)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
CENTRE = "(sel)=>{ const b=document.querySelector(sel); if(!b) return null; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }"
class Cast:
    def __init__(self, ctx, pg):
        self.cdp = ctx.new_cdp_session(pg); self.frames = []; self.on = False
        self.cdp.on("Page.screencastFrame", self._f)
    def _f(self, p):
        try: self.cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception: pass
        if self.on: self.frames.append((time.time(), p["data"]))
    def start(self):
        self.frames = []; self.on = True
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 70, "maxWidth": 440, "maxHeight": 956, "everyNthFrame": 1})
    def stop(self):
        self.on = False
        try: self.cdp.send("Page.stopScreencast")
        except Exception: pass
        return self.frames
def edges(b64):
    a = np.asarray(Image.open(io.BytesIO(base64.b64decode(b64))).convert("L")).astype(np.int16)
    gx = np.abs(a[:, 2:] - a[:, :-2]); gy = np.abs(a[2:, :] - a[:-2, :])
    return int((gx > 28).sum() + (gy > 28).sum())
MEDIA = os.environ.get("B384_MEDIA")
def save_video(frames, out, fps=30):
    if not frames or not out: return
    import tempfile, shutil
    d = tempfile.mkdtemp(); t0 = frames[0][0]; end = frames[-1][0]; k = 0; idx = 0; t = t0
    while t <= end + 1e-6:
        while idx + 1 < len(frames) and frames[idx + 1][0] <= t: idx += 1
        open(os.path.join(d, "f%05d.jpg" % k), "wb").write(base64.b64decode(frames[idx][1])); k += 1; t += 1.0 / fps
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(d, "f%05d.jpg"),
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-pix_fmt", "yuv420p", out], check=False)
    shutil.rmtree(d, ignore_errors=True)
ALLERRS = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # ---------------------------------------------------------------- (1) the class switch
    if want(1):
        ctx, pg, errs = page(br, pid=OWNER)
        boot(pg)
        pg.evaluate("()=>{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.setItem('class26e.classseen', JSON.stringify(NOVA_CLASSES.map(c=>c.key))); showHome(); }")
        pg.wait_for_timeout(3000)
        cdp = ctx.new_cdp_session(pg)
        c = pg.evaluate(CENTRE, ".class-bubble")
        tap(cdp, *c); pg.wait_for_timeout(1200)
        ci = pg.evaluate(CENTRE, ".class-stack-item.is-ifc .csi-bubble")
        cast = Cast(ctx, pg); cast.start(); pg.wait_for_timeout(500)
        t_tap = time.time(); tap(cdp, *ci)
        loader = False
        try: loader = pg.evaluate("()=>!!document.getElementById('class-switch-loader')")
        except Exception: loader = None
        # until the new page's splash is up
        arrived = None; t_end = time.time() + 12
        while time.time() < t_end:
            pg.wait_for_timeout(150)
            try:
                arrived = pg.evaluate("()=>window.NOVA_CLASS==='ifc' && document.getElementById('splash-group') ? { cls: window.NOVA_CLASS, op: +getComputedStyle(document.getElementById('splash-group')).opacity, arrive: document.documentElement.classList.contains('class-arrive') } : null")
            except Exception: arrived = None
            if arrived and arrived["op"] > .99: break
        pg.wait_for_timeout(700)
        frames = cast.stop()
        save_video(frames, MEDIA and os.path.join(MEDIA, "class-switch-%s.mp4" % ("before" if AGAINST else "after")))
        after = [(round((t - t_tap) * 1000), edges(b)) for t, b in frames if t >= t_tap]
        blank = [x for x in after if x[1] < 150]
        chk("(1) class switch: none of the %d frames from the tap to the new splash is blank (fewest edges %s; blank frames %s)"
            % (len(after), min([x[1] for x in after]) if after else None, blank[:8]), after and not blank and len(after) >= 5, after[:40])
        chk("(1) ...the loader went up over the screen at the tap (%s), and the page arrived in Fire Code with its splash showing (%s)" % (loader, arrived),
            loader is True and arrived and arrived["cls"] == "ifc" and arrived["op"] > .99, [loader, arrived])
        ALLERRS += errs; ctx.close()
    # ---------------------------------------------------------------- (2) coming back
    SNAP = """()=>{ const out={}; const vh=innerHeight, vw=innerWidth;
      for(const e of document.querySelectorAll('body *')){ if(e.closest('.char-flip-play, .rk-frame, svg *, #__statusbar')) continue; const r=e.getBoundingClientRect();
        if(!r.width||!r.height||r.bottom<0||r.top>vh||r.right<0||r.left>vw) continue;
        const id=e.__rid||(e.__rid='r'+(window.__ridn=(window.__ridn||0)+1)); out[id]=[r.left,r.top,r.width,r.height,(e.className&&e.className.baseVal!==undefined?e.className.baseVal:e.className||e.tagName).toString().slice(0,40)]; }
      return out; }"""
    LOG = """()=>{ window.__EV=[]; window.__RT=0; if(window.__logOn) return; window.__logOn=1; const nm=e=>{ const c=e&&e.className; return ((c&&c.baseVal!==undefined?c.baseVal:c)||(e&&e.tagName)||'').toString().slice(0,50); };
      document.addEventListener('animationstart', e=>{ if(window.__RT) __EV.push([Math.round(performance.now()-__RT),'css',e.animationName,nm(e.target)]); }, true);
      const oa=Element.prototype.animate; Element.prototype.animate=function(k,o){ if(window.__RT) __EV.push([Math.round(performance.now()-__RT),'animate',JSON.stringify(k).slice(0,50),nm(this)]); return oa.apply(this,arguments); };
      new MutationObserver(ms=>{ if(!window.__RT) return; ms.forEach(m=>m.addedNodes.forEach(n=>{ if(n.nodeType===1 && (n.matches('.cosmic-rank-anim, .char-flip-play') || n.querySelector && n.querySelector('.cosmic-rank-anim, .char-flip-play'))) __EV.push([Math.round(performance.now()-__RT),'sheet',nm(n),nm(m.target)]); })); }).observe(document.body,{childList:true,subtree:true}); }"""
    def come_back(ctx, pg, cdp, rec=None):
        pg.evaluate(LOG)
        cast = None
        if rec: cast = Cast(ctx, pg); cast.start(); pg.wait_for_timeout(700)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        before = pg.evaluate("(S)=>{ const b=(eval(S))(); __setHidden(true); window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true})); return b; }", SNAP)
        cdp.send("Page.setWebLifecycleState", {"state": "frozen"}); time.sleep(3)
        cdp.send("Page.setWebLifecycleState", {"state": "active"})
        first = pg.evaluate("""(S)=>new Promise(res=>{ window.__RT=performance.now(); window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})); __setHidden(false); window.dispatchEvent(new Event('focus'));
          requestAnimationFrame(()=>res((eval(S))())); })""", SNAP)
        pg.wait_for_timeout(2300)
        if cast: save_video(cast.stop(), rec)
        r = pg.evaluate("()=>({ ev: __EV.filter(e=>e[0]<=2000), lt: __lt.filter(x=>x[0]>=__RT-20 && x[0]<=__RT+2000).map(x=>[Math.round(x[0]-__RT),Math.round(x[1])]) })")
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        moved = []
        for k, v in first.items():
            if k in before:
                o = before[k]; d = max(abs(v[i] - o[i]) for i in range(4))
                if d > 2: moved.append((v[4], round(d, 1)))
        return moved, r["ev"], r["lt"]
    if want(2):
        for scr in ("home", "board"):
            ctx, pg, errs = page(br, extra=VIS)
            boot(pg)
            cdp = ctx.new_cdp_session(pg)
            if scr == "home":
                # its moving flares on (recorded at 1x; a minute at most here)
                # (all of them, as on a phone that has had the app a while: a sheet still being recorded goes on whenever it is done)
                t0 = time.time(); n = [0, 0]
                while time.time() - t0 < 300:
                    pg.wait_for_timeout(3000)
                    n = pg.evaluate("()=>[document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank').length, document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank > .cosmic-rank-anim').length]")
                    if n[0] and n[1] >= n[0]: break
                pg.wait_for_timeout(2000)
                chk("(2) home: its flares are moving on their sheets before it is put away (%d of %d)" % (n[1], n[0]), n[1] >= 2, n)
            else:
                pg.evaluate("()=>{ leaderboardRows=__fill(); showRankings(); }"); pg.wait_for_timeout(12000)
            best = None
            for attempt in range(3):
                moved, ev, lt = come_back(ctx, pg, cdp, rec=(MEDIA and attempt == 0) and os.path.join(MEDIA, "coming-back-%s-%s.mp4" % (scr, "before" if AGAINST else "after")))
                worst = max([x[1] for x in lt] or [0])
                res = (moved, ev, lt, worst)
                if best is None or (len(res[0]) + len(res[1]), res[3]) < (len(best[0]) + len(best[1]), best[3]): best = res
                if not moved and not ev and worst <= 120: break
                pg.wait_for_timeout(4000)
            moved, ev, lt, worst = best
            chk("(2) %s: the first frame back has everything where it left it (moved: %s)" % (scr, moved[:8]), not moved, moved[:12])
            chk("(2) %s: nothing re-animates in the 2s after coming back (%d: %s)" % (scr, len(ev), ev[:6]), not ev, ev[:20])
            chk("(2) %s: no long task over 120ms in those 2s at 4x (worst %dms: %s)" % (scr, worst, lt), worst <= 120, lt)
            ALLERRS += errs; ctx.close()
    # ---------------------------------------------------------------- (3) the Leaderboard by a real tap, (4) last week's top 3
    if want(3) or want(4):
        ctx, pg, errs = page(br)
        boot(pg)
        cdp = ctx.new_cdp_session(pg)
        # the class arrives in memory as on a phone (the invite fetch), which readies the board's art in the quiet
        pg.evaluate("()=>{ leaderboardRows=__fill(); try{ lbArtPreloadSoon(); }catch(e){} }"); pg.wait_for_timeout(8000)
        ROWS = """()=>{ const scr=document.querySelector('.screen-rankings'); if(!scr) return null; const vh=innerHeight;
          const vis=e=>{ if(!e) return false; for(let n=e; n && n.nodeType===1 && !n.classList.contains('rank-row'); n=n.parentElement){ const cs=getComputedStyle(n); if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity<.05) return false; } return true; };
          const rs=[...scr.querySelectorAll('.rank-rows > .rank-row[data-pub]')].filter(r=>{ const b=r.getBoundingClientRect(); return b.bottom>0 && b.top<vh-110; });
          return rs.map(r=>{ const av=r.querySelector('.rank-avatar'); const play=av&&av.querySelector(':scope > .char-flip-play'); const img=play&&play.querySelector('img, canvas'); const svg=av&&av.querySelector(':scope > svg');
            const ch = (img && (img.tagName==='CANVAS' ? img.__f>=0 : (img.complete && img.naturalWidth>0)) && vis(play)) || (svg && vis(svg) && !svg.classList.contains('char-under-flip'));
            const fl=r.querySelector('.rank-col-flare'); const fi=fl&&fl.querySelector('.rk-frame img'); const fs=fl&&fl.querySelector('svg.cosmic-rank-emblem');
            const fo = !fl || (!fl.classList.contains('is-lazy') && ((fi && fi.complete && fi.naturalWidth>0 && vis(fi)) || (fs && vis(fs) && !fs.classList.contains('rk-under-anim'))));
            return [r.dataset.pub, ch?1:0, fo?1:0]; }); }"""
        if want(3):
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
            c = pg.evaluate(CENTRE, "#bottomtab-rewards")
            cast = Cast(ctx, pg); cast.start(); pg.wait_for_timeout(300)
            pg.evaluate("(S)=>{ window.__T0=performance.now(); window.__F=[]; const f=()=>{ const s=(eval(S))(); if(s && s.length) __F.push([Math.round(performance.now()-__T0), s]); if(performance.now()-__T0<6500) requestAnimationFrame(f); }; requestAnimationFrame(f); }", ROWS)
            tap(cdp, *c)
            pg.wait_for_timeout(7000)
            frames = cast.stop()
            cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
            save_video(frames, MEDIA and os.path.join(MEDIA, "leaderboard-open-%s.mp4" % ("before" if AGAINST else "after")))
            F = pg.evaluate("()=>__F")
            bare = [(t, sum(1 for x in rs if not x[1]), sum(1 for x in rs if not x[2]), len(rs)) for t, rs in F if any(not x[1] or not x[2] for x in rs)]
            firstf = F[0] if F else None
            chk("(3) the board's rows arrive whole: from the first frame with rows (%sms, %d rows) every row on screen shows its character and flare (frames short of it: %d, first %s)"
                % (firstf[0] if firstf else None, len(firstf[1]) if firstf else 0, len(bare), bare[:5]), F and len(F[0][1]) >= 5 and not bare, bare[:10])
            last = F[-1][1] if F else []
            chk("(3) ...and at the end every row on screen has its character drawn (%d of %d)" % (sum(x[1] for x in last), len(last)), last and all(x[1] for x in last), last)
            rk = pg.evaluate("""()=>{ const by={}; (leaderboardRows||[]).forEach(e=>by[e.pub]=e); const bad=[]; let n=0;
              document.querySelectorAll('.screen-rankings .rank-rows > .rank-row[data-pub]').forEach(r=>{ const e=by[r.dataset.pub]; if(!e) return; n++;
                const want=rankOfEntry(e); const nm=r.querySelector('.rank-col-rankname'); const fl=r.querySelector('.rank-col-flare');
                const tier = fl ? (fl.dataset.rankTier || fl.dataset.lazyMark || null) : null;
                const got = nm ? nm.textContent : null; const col = nm ? getComputedStyle(nm).color : null;
                const probe=document.createElement('span'); probe.style.color = want ? RANK_COLOR[want] : 'inherit'; document.body.appendChild(probe); const wc=getComputedStyle(probe).color; probe.remove();
                if(want ? (got !== RANK_DISPLAY_NAME[want] || tier !== want || col !== wc) : (nm || fl)) bad.push([r.dataset.pub, e.level, e.badges, e.mystery, e.rankFloor, want, got, tier]); });
              return { n, bad, tiers: [...new Set((leaderboardRows||[]).map(e=>rankOfEntry(e)))] }; }""")
            chk("(3) every row's rank is rankOfEntry's for its numbers - flare tier, word and colour (%d rows, ranks on the board %s; wrong %s)" % (rk["n"], rk["tiers"], rk["bad"][:4]),
                rk["n"] >= 25 and not rk["bad"] and len(rk["tiers"]) >= 5, rk)
            # a flare whose sheet is already in memory, put on while its row's art is still held (382's .lb-art-new): its loop must
            # be laid on at the flare's own opacity, and that is what the board keeps for next time - not the hold's 0 (an empty bubble)
            hd = pg.evaluate("""async()=>{ const wait=ms=>new Promise(r=>setTimeout(r,ms));
              const rows=document.querySelector('.screen-rankings .rank-rows'); const row=[...rows.querySelectorAll(':scope > .rank-row[data-pub]')][2];
              const tier='elite'; const old=row.querySelector('.rank-col-flare'); const fl=buildRankMark(tier,'rank-col-flare'); fl.dataset.mark='zz2|'+tier; old.replaceWith(fl);
              const w=fl.getBoundingClientRect().width; const px=Math.round(w*Math.min(devicePixelRatio||1,2)); const P=px-px%2;
              const cv=document.createElement('canvas'); cv.width=cv.height=P; const x=cv.getContext('2d'); x.fillStyle='#fff'; x.beginPath(); x.arc(P/2,P/2,P/3,0,7); x.fill();
              const sp={ url: cv.toDataURL('image/png'), px: P, n: 1, cols: 1, rows: 1 }; const key=orbitAnimDrawing(tier).id+'|'+P;
              orbitAnimReady.set(key, sp); orbitAnimSheets.set(key, Promise.resolve(sp));
              row.classList.add('lb-art-new'); while(Date.now()<(window.settleUntil||0)) await wait(50);
              startOrbitEmblemAnims(row); for(let t=0;t<80 && !fl.querySelector(':scope > .cosmic-rank-anim');t++) await wait(50);
              row.classList.remove('lb-art-new'); await wait(700);
              const a=fl.querySelector(':scope > .cosmic-rank-anim'); let G=null; try{ G=JSON.parse(localStorage.getItem('class26e.lbgeom')||'null'); }catch(e){}
              const gm=G ? Object.values(G).map(v=>v && v.marks && v.marks[tier]).filter(Boolean)[0] : null;
              return { loop: a ? +getComputedStyle(a).opacity : null, kept: gm ? gm.opacity : null }; }""")
            chk("(3) a rank's flare put on while its row is held comes up at its own opacity (%s), and that is what is kept (%s)" % (hd["loop"], hd["kept"]),
                hd["loop"] is not None and hd["loop"] > .5 and hd["kept"] is not None and float(hd["kept"]) > .5, hd)
        if want(4):
            pg.evaluate("""()=>{ const c={}; c[lastWeekKey()] = [{pub:'zz4', name:'Cadet4', avatar:'alien', pts:4210}, {pub:'zz1', name:'Cadet1', avatar:'wizard', pts:3980}, {pub:'zz7', name:'Cadet7', avatar:'clown', pts:2105}];
              localStorage.setItem(WEEK_TOP_KEY, JSON.stringify(c)); leaderboardRows=__fill(); showRankings('week'); window.scrollTo(0,0); }""")
            pg.wait_for_timeout(3000)
            lw = pg.evaluate("""()=>{ const pod=document.querySelector('.screen-rankings .lw-podium'); if(!pod) return null; const cs=e=>getComputedStyle(e); const px=v=>parseFloat(v)||0;
              const blur=[pod, ...pod.querySelectorAll('*')].filter(e=>{ const f=cs(e).backdropFilter||cs(e).webkitBackdropFilter||'none'; return f!=='none'; }).length;
              const card=pod.querySelector(':scope > :not(.lw-podium-head)'); const head=pod.querySelector('.lw-podium-head');
              const listRow=document.querySelector('.screen-rankings .rank-rows > .rank-row[data-pub]:not(.rank-podium-1):not(.rank-podium-2):not(.rank-podium-3):not(.lb-row-me)');
              const bgOf=e=>e?cs(e).backgroundImage+'|'+cs(e).backgroundColor:null;
              const soft=(()=>{ const t=document.createElement('span'); t.style.color='var(--soft)'; pod.appendChild(t); const c=cs(t).color; t.remove(); return c; })();
              const cb=card?card.getBoundingClientRect():null;
              /* (384 round 2) the podium: each place's step, where it stands (left to right) and how tall */
              const steps=[...pod.querySelectorAll('.lw-podium-spot')].map(s=>{ const m=/lw-place-(\\d)/.exec(s.className); const st=s.querySelector('.lw-podium-block'); const b=st?st.getBoundingClientRect():null;
                return { place: m?+m[1]:0, l: b?b.left:null, r: b?b.right:null, b: b?b.bottom:null, h: b?b.height:0 }; });
              const meds=[...pod.querySelectorAll('.lb-rank-medal')].map(m=>{ const b=m.getBoundingClientRect(); return [Math.round(b.width*10)/10, Math.round(b.height*10)/10]; });
              const bm=document.querySelector('.screen-rankings .rank-rows > .rank-row .lb-rank-medal'); const bmb=bm?bm.getBoundingClientRect():null;
              return { blur, cardBg: bgOf(card), rowBg: bgOf(listRow), head: head?{ tt:cs(head).textTransform, ls:cs(head).letterSpacing, col:cs(head).color, text:head.textContent }:null, soft,
                steps, card: cb?{ l:cb.left, r:cb.right, b:cb.bottom, rad:px(cs(card).borderBottomLeftRadius) }:null, meds, boardMed: bmb?[Math.round(bmb.width*10)/10, Math.round(bmb.height*10)/10]:null }; }""")
            if MEDIA: pg.screenshot(path=os.path.join(MEDIA, "last-week-top3-%s.png" % ("before" if AGAINST else "after")))
            chk("(4) last week's top 3 is up on This Week (%s)" % (bool(lw),), bool(lw), lw)
            if lw:
                chk("(4) ...no backdrop-filter in it (%d), its card the list's own surface (%s)" % (lw["blur"], lw["cardBg"] == lw["rowBg"]), lw["blur"] == 0 and lw["cardBg"] and lw["cardBg"] == lw["rowBg"], [lw["cardBg"], lw["rowBg"]])
                hd = lw["head"] or {}
                chk("(4) ...the caption grey sentence case (%s)" % (hd,), hd and hd["tt"] == "none" and hd["ls"] in ("normal", "0px") and hd["col"] == lw["soft"] and not hd["text"].isupper(), [hd, lw["soft"]])
                chk("(4) ...the board's medals, round, the board's size (%s vs %s)" % (lw["meds"], lw["boardMed"]),
                    len(lw["meds"]) == 3 and lw["boardMed"] and all(abs(w - h) <= .5 and abs(w - lw["boardMed"][0]) <= .5 for w, h in lw["meds"]), lw["meds"])
                # (384 round 2: the podium is back - Madison: "Last weeks top 3 should not look like the list, I liked the podium style".
                # This replaced the list's "a line between its rows" check.)
                S = {s["place"]: s for s in lw["steps"] if s["l"] is not None}; C = lw["card"]
                pod_ok = set(S) == {1, 2, 3} and C is not None
                if pod_ok:
                    mid = lambda s: (s["l"] + s["r"]) / 2
                    floors = [S[k]["b"] for k in (1, 2, 3)]
                    # an outer step meeting the floor stays clear of the card's rounded corner (cut by under 1px)
                    def corner_cut(clear, r): return 0 if clear >= r else r - (r * r - (r - clear) ** 2) ** .5
                    cuts = [round(corner_cut(S[2]["l"] - C["l"], C["rad"]), 2), round(corner_cut(C["r"] - S[3]["r"], C["rad"]), 2)]
                    pod_ok = (mid(S[2]) < mid(S[1]) < mid(S[3]) and S[1]["h"] > S[2]["h"] > S[3]["h"] > 0
                              and max(floors) - min(floors) <= 1 and abs(max(floors) - C["b"]) <= 2.5 and max(cuts) < 1)
                chk("(4) ...a podium: 2nd, 1st, 3rd on steps that rise from the card's floor, 1st's the tallest, the outer steps clear of its rounded corners (%s)"
                    % ([(s["place"], round(s["h"], 1)) for s in lw["steps"]],), pod_ok, [lw["steps"], C])
        ALLERRS += errs; ctx.close()
    # ---------------------------------------------------------------- (5) the new dot
    if want(5):
        ctx, pg, errs = page(br, pid=OWNER)
        boot(pg)
        DOTS = """()=>{ const out=[]; const px=v=>parseFloat(v)||0;
          const take=(host, dot, pe)=>{ const cs=getComputedStyle(dot, pe||null); if(pe && (cs.content==='none'||cs.content==='normal')) return; if(cs.display==='none' || cs.visibility==='hidden') return;
            const hb=host.getBoundingClientRect(); if(!hb.width || hb.bottom<0 || hb.top>innerHeight) return;
            let w, h, cx, cy;
            if(pe){ w=px(cs.width); h=px(cs.height); const l=cs.left!=='auto'?px(cs.left):hb.width-px(cs.right)-w; const t=cs.top!=='auto'?px(cs.top):hb.height-px(cs.bottom)-h; cx=hb.left+l+w/2; cy=hb.top+t+h/2; }
            else { const b=dot.getBoundingClientRect(); w=b.width; h=b.height; cx=b.left+w/2; cy=b.top+h/2; }
            const shadows=(cs.boxShadow==='none'?[]:cs.boxShadow.split(/,(?![^(]*\\))/)).map(s=>{ const n=s.replace(/rgba?\\([^)]*\\)/,'').trim().split(/\\s+/).map(px); return n[2]||0; });
            out.push({ where:(host.className&&host.className.baseVal!==undefined?host.className.baseVal:host.className).toString().slice(0,40)+(pe||''),
              w:Math.round(w*10)/10, h:Math.round(h*10)/10, fill:cs.backgroundColor, img:cs.backgroundImage, rad:cs.borderRadius, blur:Math.max(0,...shadows), filter:cs.filter,
              dx:Math.round((hb.right-cx)*10)/10, dy:Math.round((cy-hb.top)*10)/10, hw:Math.round(hb.width), hh:Math.round(hb.height) }); };
          document.querySelectorAll('.new-dot').forEach(d=>{ let host=d.parentElement; if(host.classList.contains('new-dot-anchor') && host.firstElementChild!==d) host=host.firstElementChild; take(host, d); });
          document.querySelectorAll('#bottomtab-profile.has-new .bottomtab-icon').forEach(i=>take(i, i, '::after'));
          document.querySelectorAll('.class-bubble-wrap.has-new .class-bubble').forEach(i=>take(i, i, '::after'));
          return out; }"""
        pg.evaluate("()=>{ store.seenUnlocks={chars:[],banners:[],themes:[],badges:[],fx:[],v:2}; store.rankMapSeen=-1; store.rankMapFx244=true; localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); localStorage.removeItem('class26e.classseen'); showHome(); }")
        pg.wait_for_timeout(2500); pg.evaluate("()=>syncProfileTabDot()"); pg.wait_for_timeout(600)
        D = {"home": pg.evaluate(DOTS)}
        if MEDIA: pg.screenshot(path=os.path.join(MEDIA, "dots-home-%s.png" % ("before" if AGAINST else "after")))
        pg.evaluate("()=>{ showProfile(); window.scrollTo(0,0); }"); pg.wait_for_timeout(2500)
        D["profile"] = pg.evaluate(DOTS)
        if MEDIA: pg.screenshot(path=os.path.join(MEDIA, "dots-profile-%s.png" % ("before" if AGAINST else "after")))
        for p in ("character", "banner", "theme", "fx"):
            pg.evaluate("(p)=>{ showCustomize(p); window.scrollTo(0,0); }", p); pg.wait_for_timeout(2200)
            D[p] = pg.evaluate(DOTS)
        if MEDIA: pg.screenshot(path=os.path.join(MEDIA, "dots-customize-%s.png" % ("before" if AGAINST else "after")))
        alld = [dict(d, screen=k) for k, v in D.items() for d in v]
        where = sorted(set(d["screen"] + ":" + d["where"].split(" ")[0] for d in alld))
        chk("(5) dots found on the tab, Profile and Customize's pages (%d: %s)" % (len(alld), where), len(alld) >= 8 and D["home"] and len(D["profile"]) >= 3 and D["character"] and D["theme"], where)
        # REVISED IN 384 r8: "The yellow notification looks a little weak ... Maybe a small glow?" - the dot is still a solid
        # circle (no gradient, no filter), and now every one carries the same small glow outside its ring (a blur of 10-20px).
        bad = [d for d in alld if d["img"] != "none" or not (10 <= d["blur"] <= 20) or d["filter"] != "none" or not re.match(r"rgb\(\d+, \d+, \d+\)$", d["fill"])]
        chk("(5) ...each a solid fill, no gradient, with the same small glow round it (%d not: %s)" % (len(bad), [(d["screen"], d["where"], d["img"][:30], d["blur"]) for d in bad[:3]]), not bad, bad[:4])
        bad = [d for d in alld if d["rad"] != "50%" or abs(d["w"] - d["h"]) > .5 or not (8 <= d["w"] <= 10.5)]
        chk("(5) ...round, 8-10px (%d not: %s)" % (len(bad), [(d["screen"], d["where"], d["w"], d["h"], d["rad"]) for d in bad[:4]]), not bad, bad[:4])
        fills = sorted(set(d["fill"] for d in alld)); sizes = sorted(set(round(d["w"]) for d in alld if d["screen"] != "character"))
        chk("(5) ...one look everywhere: one fill %s, one size %s" % (fills, sizes), len(fills) == 1 and len(sizes) == 1, [fills, sizes])
        bad = [d for d in alld if abs(d["dx"] - d["dy"]) > 1.5 or d["dx"] < -1 or d["dx"] > min(d["hw"], d["hh"]) / 3]
        chk("(5) ...each on its icon's corner, on the 45-degree line (%d not: %s)" % (len(bad), [(d["screen"], d["where"], d["dx"], d["dy"], d["hw"], d["hh"]) for d in bad[:5]]), not bad, bad[:6])
        ALLERRS += errs; ctx.close()
    br.close()
chk("(6) no page errors (%s)" % (ALLERRS[:3],), not ALLERRS, ALLERRS[:5])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
