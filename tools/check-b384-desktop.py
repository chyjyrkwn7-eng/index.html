"""Build 384, computers and big monitors, and the Leaderboard loading everywhere. Madison: "Please do another check on computers,
larger monitors and things like that to ensure this app runs really well on them without any lag as well." / "Please ensure
leaderboard functions really well, and it loads properly."
Read off the page in Chromium, academy, 44 classmates from a fake cloud (every rank, a podium, 28 characters), shapes and counts
(no frame times - the sandbox is shared). A phone is 440x956 at 3x (touch, Safari's user agent, installed); a window is a desktop
browser tab at the size named (a mouse, Windows' user agent).
(1) A COLD BOARD ON A SLOW NETWORK (nothing in memory - the launch's board fetch never answers - and the board's own listener
    answering 3.5s after it subscribes; phone and a 1920x1080 window): from the tap until the class is up, no frame shows the
    board as you alone (1st of 1) - the placeholders hold until the class arrives - and then every row is there, in order.
(2) OFFLINE, THEN THE CLASS (the browser says offline: the board shows your row after 2.5s, as designed, and the class turns up
    5s later; phone): from the first frame with the class every row on the screen shows its character, and the board's kept
    screenful (lbgeom .vis) is the screen's, not the one-row board's.
(3) A FIRST BOARD ON A TALL WINDOW (3840x2160 and 2560x1440, nothing measured on that window yet, cold - the class arrives by the
    listener): from the first frame with rows, every row on the screen shows its character (a still, a loop or the drawing) and,
    where it has a rank, its flare.
(4) THE LEADERBOARD LOADS PROPERLY (phone, 1366x768, 3840x2160 - B384_DESKTOP_DEVS=phone,ipad,1920x1080x2,... for others; the class in memory as after a
    launch): opened by a real tap, the rows come up whole (no blank frame, no frame as you alone, no row without its art); all
    45 rows in the board's order, places 1..45, the podium the top three, every rank the app's own (rankOfEntry); Find me puts
    your row on the screen and flashes it; each board's tab (This Week, Overall, Hundos) brings that board in its order with
    every row on screen whole; scrolled to the bottom no row comes on screen without its art; and Home <-> Leaderboard four times,
    each time whole and in order, with the page's element count not growing.
(5) THE FRIENDS TAB CATCHES UP (a 1920x1080 window and a phone; three friends; the chat dock's Friends tab opened before the class's
    rows have arrived, so each friend is drawn without a name): when the rows land (the board fetch answers), the open list
    shows each friend's name and character - without leaving the tab.
(6) no page errors.
Run:  python3 tools/check-b384-desktop.py [--against REV] [--only 1,2,...]   (--against f9694e7 must FAIL (1)(2)(3)(5))"""
import functools, http.server, json, os, re, socket, subprocess, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
if not os.path.exists(CHROME):
    import glob as _g; CHROME = (sorted(_g.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")) or [CHROME])[-1]
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else None
def want(n): return ONLY is None or str(n) in ONLY
if "--against" in sys.argv:
    SRC = subprocess.check_output(["git", "-C", ROOT, "show", sys.argv[sys.argv.index("--against") + 1] + ":index.html"]).decode("utf-8")
else:
    SRC = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
BUILD = (re.search(r'const APP_BUILD = "([^"]+)"', SRC) or [None, ""])[1]
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:700], flush=True)
def info(s): print("INFO " + s, flush=True)
INSET_RE = re.compile(r"env\(safe-area-inset-(top|bottom|left|right)(?:\s*,[^()]*)?\)")
def body_for(ins):
    t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
    return INSET_RE.sub(lambda m: v[m.group(1)], SRC)
def serve():
    so = socket.socket(); so.bind(("127.0.0.1", 0)); port = so.getsockname()[1]; so.close()
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/index.html" % port
URL = serve()
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 26_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.0 Mobile/15E148 Safari/604.1"
WIN_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0"
STANDALONE = """Object.defineProperty(navigator,'standalone',{get:()=>true,configurable:true});
(function(){ const mm = window.matchMedia.bind(window); window.matchMedia = q => /display-mode:\\s*standalone/.test(q)
  ? {matches:true, media:q, addListener(){}, removeListener(){}, addEventListener(){}, removeEventListener(){}, onchange:null, dispatchEvent(){return false;}} : mm(q); })();"""
NO_RIC = "try{ delete window.requestIdleCallback; delete window.cancelIdleCallback; window.requestIdleCallback = undefined; window.cancelIdleCallback = undefined; }catch(e){}"
# the browser's online flag, settable (window.__offline)
ONLINE = "try{ Object.defineProperty(Navigator.prototype, 'onLine', { get(){ return !window.__offline; }, configurable: true }); }catch(e){}"
# 44 classmates. The leaderboard collection answers a listener after window.__LBD ms and a one-off read (the launch's board fetch)
# after window.__LBGET ms (default: the same).
FAKE = """(function(){
  function wk(){ const d=new Date(); d.setHours(0,0,0,0); d.setDate(d.getDate()-((d.getDay()+6)%7)); return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0'); }
  function rows(){ const ids=['ninja','ghost','wizard','grizzly','alien','detective','masked','zeus','poseidon','clown','valkyrie','marksman','astronaut','hacker','timekeeper','ronin','hive','lunar','solar','tempest','frost','oracle','inferno','astral','celestial','zenith','umbra','voidwalker'];
    const names=['Avery','Blake','Cameron','Dakota','Emerson','Finley','Gray','Harper','Indy','Jordan','Kai','Logan','Morgan','Noel','Oakley','Parker','Quinn','Reese','Sage','Taylor','Uri','Vale','Wren','Xen','Yael','Zion','Ash','Bay','Cole','Drew','Ellis','Flynn','Gale','Hollis','Ira','Jules','Kit','Lane','Marlo','Nico','Onyx','Pax','Rory','Shay'];
    const out=[]; for(let i=0;i<44;i++) out.push({ id:'p'+(1000+i).toString(36)+'x'+i, d:{ firstName:names[i], avatarChar:ids[(i*11)%ids.length], accent:'ink', correct:6000-i*120, level:Math.max(1,82-i*2),
      badges:Math.max(0,22-(i>>1)), mystery:i<2?3:0, hundos:300-i*6, rankFloor:(i===11?5:0), xp:120000-i*2500, tests:200-i*3, week:wk(), weekPoints:(i%9===3)?0:4000-i*80, banner:'', prevWeek:'', lastModified:1700000000000+i } });
    return out; }
  function snap(name){ const docs=(name==='leaderboard'?rows():[]).map(r=>({ id:r.id, exists:true, data:()=>Object.assign({}, r.d), metadata:{fromCache:false} }));
    return { empty:!docs.length, size:docs.length, docs, docChanges:()=>[], metadata:{fromCache:false, hasPendingWrites:false}, forEach:cb=>docs.forEach(cb) }; }
  const delay=(k)=>{ const v=window[k]; return v!=null ? v : (window.__LBD!=null ? window.__LBD : 60); };
  function doc(){ return { get:()=>Promise.resolve({ exists:false, data:()=>null, metadata:{fromCache:false} }), set:()=>Promise.resolve(), update:()=>Promise.resolve(), delete:()=>Promise.resolve(),
    onSnapshot:function(){ const n=[].slice.call(arguments).filter(x=>typeof x==='function')[0]; setTimeout(()=>n({ exists:false, id:'x', data:()=>null, metadata:{fromCache:false, hasPendingWrites:false} }), 40); return ()=>{}; },
    collection:()=>coll('sub') }; }
  function coll(name){ const c={ doc, where:()=>c, orderBy:()=>c, limit:()=>c,
    get:()=>new Promise(res=>setTimeout(()=>res(snap(name)), name==='leaderboard'?delay('__LBGET'):60)),
    onSnapshot:function(){ const n=[].slice.call(arguments).filter(x=>typeof x==='function')[0]; if(name==='leaderboard') window.__lbSubAt=performance.now();
      const t=setTimeout(()=>n(snap(name)), name==='leaderboard'?delay('__LBD'):60); return ()=>clearTimeout(t); } }; return c; }
  const db={ collection:coll, batch:()=>({ set(){}, update(){}, delete(){}, commit:()=>Promise.resolve() }), runTransaction:()=>Promise.reject(new Error('offline')) };
  const fs=function(){ return db; }; fs.FieldValue={ delete:()=>null, serverTimestamp:()=>Date.now(), arrayUnion:function(){ return [].slice.call(arguments); }, arrayRemove:()=>[], increment:n=>n };
  window.firebase={ apps:[], initializeApp(){ this.apps.push({}); return {}; }, firestore:fs, app:()=>({}) }; })();"""
def week_key_now():
    import datetime
    d = datetime.date.today(); d -= datetime.timedelta(days=d.weekday()); return d.isoformat()
SEED = {"firstName": "Casey", "avatarChar": "ninja", "onboardingComplete": True, "weekKey": week_key_now(), "weekPoints": 640, "leaderboardOptIn": True,
        "lastModified": 1700000000000, "publicId": "xph5b57jbp5a", "novaMet": 99, "tourRev": 99, "rankMapFx244": True, "seenProfileTour": True,
        "seenModeSelectTour": True, "seenUnitSelectTour": True, "seenMainMenuTour": True, "seenClassTip": True, "seenRankingsTour": True, "seenRewardsTour": True,
        "seenAppearanceTour": True, "novaHeard": {"@recap": 99991231, "hello": 1}, "unitPerfects": {"Penal Code": 35, "TCOLE Rules": 35, "Racial Profiling": 22},
        "lifetime": {"points": 12400, "answered": 5400, "correct": 4980, "drillPlays": 64, "examPlays": 22, "perfectTests": 141, "currentStreak": 23, "longestStreak": 57}}
SEEN = ["freshstart", "intro.seen", "unithold.tip", "daily.seen", "savecode.asked", "savecode.card", "getstarted", "penal55124.seen", "penal124256.seen", "penal256578.seen", "a2hs"]
def init_js():
    s = "(()=>{ try{ if(sessionStorage.getItem('__seeded')) return; sessionStorage.setItem('__seeded','1'); localStorage.setItem('class26e.frame.ok','go-live-1');"
    for k in SEEN: s += "localStorage.setItem('class26e.%s','1');" % k
    s += "localStorage.setItem('class26e.intro.seen','99');"
    s += "localStorage.setItem('class26e.drill.v1', %s); localStorage.setItem('class26e.synccode','TEST-3846');" % json.dumps(json.dumps(SEED))
    s += "localStorage.setItem('class26e.classseen', JSON.stringify(['academy','ifc'])); localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc']));"
    return s + " }catch(e){} })()"
DEVS = {"phone": (440, 956, 3, True), "ipad": (834, 1194, 2, True)}
def open_page(br, dev, extra=()):
    if dev in DEVS:
        w, h, d, touch = DEVS[dev]
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=d, has_touch=True, is_mobile=True, user_agent=IPHONE_UA)
        ctx.add_init_script(NO_RIC); ctx.add_init_script(STANDALONE); ins = (62, 0, 34, 0) if w < 600 else (24, 0, 20, 0)
    else:
        a = dev.split("x"); w, h, d = int(a[0]), int(a[1]), float(a[2]) if len(a) > 2 else 1
        ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=d, has_touch=False, is_mobile=False, user_agent=WIN_UA); ins = (0, 0, 0, 0)
    ctx.add_init_script(ONLINE)
    for e in extra: ctx.add_init_script(e)
    ctx.add_init_script(FAKE); ctx.add_init_script(init_js())
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    body = body_for(ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.route("**/version.json*", lambda route, request: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": BUILD, "note": "", "frameId": "", "force": True, "safariSound": True})))
    cdp = ctx.new_cdp_session(pg)
    pg.goto(URL)
    for _ in range(400):
        if pg.evaluate("()=>!!document.querySelector('#stage .screen-home-actual') && !document.getElementById('splashscreen')"): break
        pg.wait_for_timeout(250)
    # an account with nothing owed: the cards Home would play (hundo effects unlocked by the seed) are let go by a tap, as a person would
    pg.evaluate("""()=>{ try{ store.rankUpShown = TIER_ORDER_FULL.length; store.seenUnlockedTiers = TIER_ORDER_FULL.slice(); saveStore(); }catch(e){}
      try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} }""")
    quiet = 0
    for _ in range(80):
        busy = pg.evaluate("()=>{ const s=document.querySelector('.rs-spot'); if(s && s.classList.contains('is-up') && !s.classList.contains('is-leaving')) s.click(); return !!(s || document.body.classList.contains('cutscene-focus')); }")
        quiet = 0 if busy else quiet + 1
        if quiet >= 4: break
        pg.wait_for_timeout(600)
    pg.evaluate("()=>{ for(let i=0;i<3;i++) [...document.querySelectorAll('button')].filter(b=>/^(Got it|Not now|Later|I.ll add it later)$/i.test(b.textContent.trim()) && b.offsetParent).forEach(b=>b.click()); }")
    return ctx, pg, cdp, errs, dev in DEVS
def tap(pg, cdp, touch, sel):
    c = pg.evaluate("(s)=>{ const e=document.querySelector(s); if(!e) return null; const r=e.getBoundingClientRect(); if(!r.width) return null; return [r.left+r.width/2, r.top+r.height/2]; }", sel)
    if not c: return False
    if touch:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": c[0], "y": c[1]}]}); time.sleep(0.06)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    else:
        pg.mouse.move(c[0], c[1], steps=3); pg.mouse.down(); pg.mouse.up()
    return True
def wait_for(pg, js, ms=30000, arg=None):
    t0 = time.time()
    while time.time() - t0 < ms / 1000:
        if pg.evaluate(js, arg): return round((time.time() - t0) * 1000)
        pg.wait_for_timeout(100)
    return None
# per frame, the board's rows on screen: [t, rows, placeholders, without character, without flare, you alone, empty note, rows in the list]
SAMPLE = r"""()=>{ window.__S=[]; window.__stopS=0; const T0=performance.now(); const me=store.publicId;
  const vis=e=>{ if(!e) return false; for(let n=e; n && n.nodeType===1 && !n.classList.contains('rank-row'); n=n.parentElement){ const cs=getComputedStyle(n); if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity<.05) return false; } return true; };
  const f=()=>{ const t=Math.round(performance.now()-T0); const scr=document.querySelector('#stage .screen-rankings');
    if(scr){ const vh=innerHeight; const on=r=>{ const b=r.getBoundingClientRect(); return b.height>0 && b.bottom>0 && b.top<vh-60; };
      const skel=[...scr.querySelectorAll('.rank-row-skel')].filter(on).length;
      const rs=[...scr.querySelectorAll('.rank-rows > .rank-row[data-pub]')].filter(on);
      let noch=0, nofl=0;
      rs.forEach(r=>{ const av=r.querySelector('.rank-avatar'); const play=av&&av.querySelector(':scope > .char-flip-play'); const img=play&&play.querySelector('img, canvas'); const svg=av&&av.querySelector(':scope > svg');
        const ch=(img && (img.tagName==='CANVAS' ? img.__f>=0 : (img.complete && img.naturalWidth>0)) && vis(play)) || (svg && vis(svg) && !svg.classList.contains('char-under-flip'));
        const fl=r.querySelector('.rank-col-flare'); const fi=fl&&fl.querySelector('.rk-frame img, .rk-frame canvas'); const fs=fl&&fl.querySelector('svg');
        const fo=!fl || (!fl.classList.contains('is-lazy') && ((fi && (fi.tagName==='CANVAS' ? fi.__f>=0 : (fi.complete && fi.naturalWidth>0)) && vis(fi)) || (fs && vis(fs) && !fs.classList.contains('rk-under-anim'))));
        if(!ch) noch++; if(!fo) nofl++; });
      __S.push([t, rs.length, skel, noch, nofl, (rs.length===1 && rs[0].dataset.pub===me)?1:0, scr.querySelector('.lb-board-empty, .rank-rows > .info-note')?1:0, scr.querySelectorAll('.rank-rows > .rank-row[data-pub]').length]); }
    if(!window.__stopS && performance.now()-T0<120000) requestAnimationFrame(f); }; requestAnimationFrame(f); }"""
def frames(pg):
    pg.evaluate("()=>{ window.__stopS=1; }")
    return pg.evaluate("()=>__S")
ORDER = r"""()=>{ const key=rankingsBoardKey; const board=RANKING_BOARDS.find(b=>b.key===key); const val=e=>Number(e&&e[board.field])||0;
  const mine=Object.assign({ pub: store.publicId, firstName: store.firstName, avatarChar: store.avatarChar }, boardNumbersOf(store));
  const all=(leaderboardRows||[]).filter(e=>e.pub!==store.publicId).concat([mine]);
  const srt=board.sort||((a,b)=>(val(b)-val(a))||String(a.firstName||'').localeCompare(String(b.firstName||'')));
  const want=all.slice().sort(srt).map(e=>e.pub);
  const rowsEl=[...document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]')];
  const got=rowsEl.map(r=>r.dataset.pub);
  const places=rowsEl.map(r=>(r.querySelector('.rank-place')||{}).textContent||'').map(t=>t.replace(/\D/g,''));
  const pod=[1,2,3].map(n=>{ const r=document.querySelector('#stage .screen-rankings .rank-rows > .rank-row.rank-podium-'+n); return r?r.dataset.pub:null; });
  let rkBad=0; const by={}; all.forEach(e=>by[e.pub]=e);
  if(key==='overall') rowsEl.forEach(r=>{ const e=by[r.dataset.pub]; if(!e) return; const w=rankOfEntry(e); const nm=r.querySelector('.rank-col-rankname'); const fl=r.querySelector('.rank-col-flare');
    const tier=fl?(fl.dataset.rankTier||fl.dataset.lazyMark||null):null; if(w ? (!nm || nm.textContent!==RANK_DISPLAY_NAME[w] || tier!==w) : (nm||fl)) rkBad++; });
  let firstBad=-1; for(let i=0;i<Math.max(want.length,got.length);i++){ if(want[i]!==got[i]){ firstBad=i; break; } }
  const placesOk = places.every((p,i)=>p==='' || +p===i+1);
  return { key, n: got.length, want: want.length, firstBad, podOk: JSON.stringify(pod)===JSON.stringify(want.slice(0,3)), rkBad, placesOk }; }"""
def order_ok(o): return o["n"] == o["want"] == 45 and o["firstBad"] == -1 and o["podOk"] and o["rkBad"] == 0 and o["placesOk"]
ALLERR = []
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=CHROME)
    # ---------------------------------------------------------------- (1) cold board, slow network
    if want(1):
        for dev in ("phone", "1920x1080x1"):
            ctx, pg, cdp, errs, touch = open_page(br, dev, extra=["window.__LBGET = 1e9; window.__LBD = 3500;"])
            pg.wait_for_timeout(2000)
            have = pg.evaluate("()=>(leaderboardRows||[]).length")
            pg.evaluate(SAMPLE)
            tap(pg, cdp, touch, "#bottomtab-rewards")
            t_rows = wait_for(pg, "()=>document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length >= 40", 40000)
            pg.wait_for_timeout(3000)
            S = frames(pg)
            alone = [s for s in S if s[5]]
            skel_then = [s for s in S if s[2] > 0]
            o = pg.evaluate(ORDER)
            chk("(1) %s, cold (%d rows in memory), the class 3.5s away: no frame shows the board as you alone (%d of %d frames did, from %sms); the placeholders held (%d frames) until the class (%sms)"
                % (dev, have, len(alone), len(S), alone[0][0] if alone else None, len(skel_then), t_rows), have == 0 and t_rows is not None and not alone and skel_then, [alone[:3], S[:4]])
            chk("(1) %s ...then all 45 rows in the board's order, places 1-45, the podium the top three, every rank right (%s)" % (dev, o), order_ok(o), o)
            ALLERR += errs; ctx.close()
    # ---------------------------------------------------------------- (2) offline, then the class
    if want(2):
        ctx, pg, cdp, errs, touch = open_page(br, "phone", extra=["window.__offline = true; window.__LBGET = 1e9; window.__LBD = 6000;"])
        pg.wait_for_timeout(2000)
        pg.evaluate(SAMPLE)
        tap(pg, cdp, touch, "#bottomtab-rewards")
        t_me = wait_for(pg, "()=>document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length === 1", 20000)
        pg.wait_for_timeout(800)
        vis1 = pg.evaluate("()=>{ try{ const G=lbGeomGet(); return G ? (G.vis == null ? null : G.vis) : null; }catch(e){ return 'err'; } }")
        t_cls = wait_for(pg, "()=>document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length >= 40", 40000)
        pg.wait_for_timeout(1500)
        S = frames(pg)
        cls = [s for s in S if s[7] >= 40]
        short = [s for s in cls if s[3] or s[4]]
        vis = pg.evaluate("()=>{ try{ const G=lbGeomGet(); return G ? G.vis : null; }catch(e){ return 'err'; } }")
        chk("(2) offline: your row alone after the beat (%sms, as designed), then the class (%sms)" % (t_me, t_cls), t_me is not None and t_cls is not None, [t_me, t_cls])
        chk("(2) ...from the first frame with the class every row on screen shows its character and flare (%d of %d frames short: %s)" % (len(short), len(cls), short[:3]), cls and not short, short[:5])
        chk("(2) ...and the one-row board did not set the kept screenful (vis %s while it was up; %s after the class)" % (vis1, vis), vis1 is None and isinstance(vis, int) and vis >= 8, [vis1, vis])
        ALLERR += errs; ctx.close()
    # ---------------------------------------------------------------- (3) a first board on a tall window
    if want(3):
        for dev in ("3840x2160x1", "2560x1440x1"):
            ctx, pg, cdp, errs, touch = open_page(br, dev, extra=["window.__LBGET = 1e9; window.__LBD = 1500;"])
            pg.wait_for_timeout(1500)
            g0 = pg.evaluate("()=>{ try{ return lbGeomGet(); }catch(e){ return 'err'; } }")
            pg.evaluate(SAMPLE)
            tap(pg, cdp, touch, "#bottomtab-rewards")
            wait_for(pg, "()=>document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length >= 40", 40000)
            pg.wait_for_timeout(2500)
            S = frames(pg)
            rowsf = [s for s in S if s[1] > 0]
            short = [s for s in rowsf if s[3] or s[4]]
            most = max([s[1] for s in rowsf] or [0])
            chk("(3) %s, a first board (nothing measured: %s), cold: from the first frame with rows every row on screen shows its character and flare (%d of %d frames short, worst %s rows of %d: %s)"
                % (dev, g0, len(short), len(rowsf), max([s[3] + s[4] for s in short] or [0]), most, short[:3]), rowsf and most >= 18 and not short and not (g0 or {}).get("vis"), short[:5])
            ALLERR += errs; ctx.close()
    # ---------------------------------------------------------------- (4) the Leaderboard everywhere
    if want(4):
        for dev in (os.environ.get("B384_DESKTOP_DEVS") or "phone,1366x768x1,3840x2160x1").split(","):
            ctx, pg, cdp, errs, touch = open_page(br, dev)
            pg.wait_for_timeout(5000)
            have = pg.evaluate("()=>(leaderboardRows||[]).length")
            pg.evaluate(SAMPLE)
            tap(pg, cdp, touch, "#bottomtab-rewards")
            t = wait_for(pg, "()=>document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length >= 40", 30000)
            pg.wait_for_timeout(3000)
            S = frames(pg); rowsf = [s for s in S if s[1] > 0]
            bad = [s for s in S if (s[1] == 0 and s[2] == 0 and not s[6]) or s[5] or (s[1] and (s[3] or s[4]))]
            o = pg.evaluate(ORDER)
            chk("(4) %s: the board by a tap (%d in memory) comes up whole - no blank frame, none as you alone, no row without its art (%d of %d frames not: %s)"
                % (dev, have, len(bad), len(S), bad[:3]), t is not None and rowsf and not bad, bad[:5])
            chk("(4) %s ...45 rows in order, places, podium, ranks (%s)" % (dev, o), order_ok(o), o)
            tap(pg, cdp, touch, ".rank-me-btn"); pg.wait_for_timeout(1200)
            fm = pg.evaluate("()=>{ const r=document.querySelector('#stage .rank-row[data-me=\"1\"]'); if(!r) return null; const b=r.getBoundingClientRect(); return { inView: b.top>=0 && b.bottom<=innerHeight, flash: r.classList.contains('rank-flash') }; }")
            chk("(4) %s ...Find me: your row on the screen, flashing (%s)" % (dev, fm), fm and fm["inView"] and fm["flash"], fm)
            pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})"); pg.wait_for_timeout(400)
            tabs_bad = []
            for key in ("week", "hundos", "overall"):
                idx = pg.evaluate("(k)=>RANKING_BOARDS.findIndex(b=>b.key===k)", key)
                pg.evaluate(SAMPLE)
                tap(pg, cdp, touch, ".screen-rankings .navsegment .iconbtn:nth-child(%d)" % (idx + 1))
                wait_for(pg, "(k)=>rankingsBoardKey===k && document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length >= 40", 20000, key)
                pg.wait_for_timeout(1500)
                S = frames(pg); o = pg.evaluate(ORDER)
                b = [s for s in S if (s[1] == 0 and s[2] == 0) or (s[1] and (s[3] or s[4]))]
                if b or not order_ok(o) or o["key"] != key: tabs_bad.append((key, o, b[:2]))
            chk("(4) %s ...This Week, Hundos, Overall by their tabs: each in its order, every row on screen whole in every frame (%s)" % (dev, tabs_bad[:2]), not tabs_bad, tabs_bad)
            pg.evaluate(SAMPLE)
            for _ in range(80):
                at = pg.evaluate("()=>[scrollY, document.documentElement.scrollHeight-innerHeight]")
                if at[0] >= at[1] - 2: break
                if touch:
                    W_ = pg.evaluate("()=>innerWidth"); H_ = pg.evaluate("()=>innerHeight")
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": W_ / 2, "y": H_ * .7}]})
                    for k in range(1, 6):
                        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": W_ / 2, "y": H_ * .7 - k * 60}]}); time.sleep(0.016)
                    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []}); pg.wait_for_timeout(120)
                else:
                    pg.mouse.wheel(0, 400); pg.wait_for_timeout(60)
            pg.wait_for_timeout(1500)
            S = frames(pg); b = [s for s in S if s[1] and (s[3] or s[4])]
            # a row scrolled to may take its art a moment (the queue): a row is short for at most a few frames, never left so
            chk("(4) %s ...scrolled to the bottom: no row on screen left without its art (%d frames short, at the end %s)" % (dev, len(b), S[-1] if S else None),
                S and not (S[-1][3] or S[-1][4]) and len(b) <= max(6, len(S) // 10), b[:4])
            pg.evaluate("()=>window.scrollTo({top:0, behavior:'instant'})")
            ret_bad = []; nodes = []
            for k in range(4):
                tap(pg, cdp, touch, "#bottomtab-home"); wait_for(pg, "()=>!!document.querySelector('#stage .screen-home-actual')", 20000); pg.wait_for_timeout(1500)
                pg.evaluate(SAMPLE)
                tap(pg, cdp, touch, "#bottomtab-rewards")
                t = wait_for(pg, "()=>document.querySelectorAll('#stage .screen-rankings .rank-rows > .rank-row[data-pub]').length >= 40", 20000)
                pg.wait_for_timeout(2500)
                S = frames(pg); o = pg.evaluate(ORDER)
                b = [s for s in S if (s[1] == 0 and s[2] == 0 and not s[6]) or s[5] or (s[1] and (s[3] or s[4]))]
                if t is None or b or not order_ok(o): ret_bad.append((k, t, b[:2], o))
                nodes.append(pg.evaluate("()=>document.getElementsByTagName('*').length"))
            chk("(4) %s ...Home <-> Leaderboard four times: each whole and in order (%s); elements %s, not growing" % (dev, ret_bad[:2], nodes),
                not ret_bad and nodes[-1] <= nodes[0] * 1.15 + 200, [ret_bad, nodes])
            ALLERR += errs; ctx.close()
    # ---------------------------------------------------------------- (5) the friends tab catches up
    if want(5):
        FR = "(()=>{ const ids=[0,5,20]; return ids.map(i=>'p'+(1000+i).toString(36)+'x'+i); })()"
        LIST = """()=>[...document.querySelectorAll('.chatdock-chatlist.is-friends .chatdock-chatrow.is-friend')].filter(r=>r.dataset.code!==NOVA_CODE).map(r=>{ const a=r.querySelector('.chatdock-chatrow-avatar'); const g=a&&a.querySelector('svg, img');
          return [r.querySelector('.chatdock-chatrow-name').textContent, !!g && (g.getBoundingClientRect().width>0)]; })"""
        for dev in ("1920x1080x1", "phone"):
            ctx, pg, cdp, errs, touch = open_page(br, dev, extra=["window.__LBGET = 1e9;"])
            pg.evaluate("()=>{ store.friendsIn = %s; saveStore(); }" % FR)
            pg.wait_for_timeout(1500)
            pg.evaluate("()=>{ chatDockTab = 'friends'; openChatDock(); }"); pg.wait_for_timeout(1500)
            before = pg.evaluate(LIST)
            pg.evaluate("()=>{ window.__LBGET = 1200; boardFetchInFlight = false; boardFetchedAt = 0; fetchBoardForInvites(true); }")
            wait_for(pg, "()=>(leaderboardRows||[]).length >= 40", 20000); pg.wait_for_timeout(1500)
            after = pg.evaluate(LIST)
            names = sorted(n for n, _ in after)
            chk("(5) %s: the Friends tab opened before the class's rows (%s) shows each friend's name and character once they land (%s), without leaving the tab"
                % (dev, before, after), len(before) == 3 and all(n == "Friend" for n, _ in before) and names == ["Avery", "Finley", "Uri"] and all(g for _, g in after), [before, after])
            ALLERR += errs; ctx.close()
    br.close()
chk("(6) no page errors (%s)" % (ALLERR[:3],), not ALLERR, ALLERR[:5])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
