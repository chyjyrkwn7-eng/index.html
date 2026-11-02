"""Build 382: the units screen ("Choose your units") - its lag and its look.
Madison (iPhone 17 Pro Max): "I think the unit selection screen has some lag." / "the unit selection screens interface.. I'm not a fan.
I like the layout but I think the interface/look isn't it ... that entire page needs a nicer look ... ensure it's cohesive with the app".

Speed, on an iPhone's page (iPhone user agent, touch, 440x956 at 3x), as the work a phone 4x slower than this machine would do: the main
thread's CPU time (a trace's thread clock - what the page itself spent, not the wall clock, which other browsers on this machine
inflate) times 4. (Chromium's own CPU throttle is not used for these: its pauses land in the thread clock too.)
 (1) opening the screen (a second visit, after the launch's badge warm-up): the main thread's work from showSetup() to the first frame
     drawn (budget 340ms at 4x; 381 measured ~420, 24 live badge SVGs - 848 of its ~1,200 elements - in every style pass and layout),
     and the first 1.5s after it (budget 650ms at 4x; 381 ~800: the haptic switches measured and written card by card, the Back pill
     measured afresh on every screen);
 (2) ticking a card restyles only what changed: elements restyled per tick (budget 250; 381 restyled ~680 - every card's name, count,
     circle and badge - because three unit-card rules put .pname/.pcount/.box and a bare svg in the one :has() invalidation set
     Chromium re-applies under <body> on each :has() re-check), and the tick's longest main-thread task (budget 110ms at 4x);
 (3) scrolling the grid by touch: no element restyled for the scroll (budget 40 for two flicks; the old cards each took a class as
     they came into view) and no main-thread task over 60ms at 4x.
Look and shape:
 (4) no card has a backdrop-filter, and no card's badge has a filter (the old badge carried two drop-shadows inside a card that scales);
 (5) a picked card reads as picked: its fill is lighter than an unpicked card's (luminance step >= 6 of 255 at the same spot), its
     border is the accent, and its tick circle shows;
 (6) every control on the screen is at least 44px tall: the level tabs, Select all, Review's Starred (Select all and Starred were 40);
 (7) the level control is the Leaderboard's at its own width, centred (not stretched edge to edge), and Select all centred under it;
 (8) nothing overflows, nothing scrolls sideways and no card's count runs under its badge at 440x956, 518x1125, 375x667, 320x568,
     834x1194 and 1440x900, academy and Fire Code.
Run:  python3 tools/check-b382-units.py   (--against: copy the old index.html over first; (1), (2) restyle, (3) restyle, (4) filter, (6) and (7) fail there)"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
srv, url = g["serve"]()
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
OWNER = "xph5b57jbp5a"
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else info)

def page(br, w, h, ifc=False, phone=None):
    phone = (w < 600) if phone is None else phone
    installed = w < 1200
    ins = (62, 0, 34, 0) if phone else ((24, 0, 20, 0) if installed else (0, 0, 0, 0))
    kw = dict(viewport={"width": w, "height": h}, device_scale_factor=3 if phone else 2)
    if phone: kw.update(user_agent=UA, has_touch=True, is_mobile=True)
    ctx = br.new_context(**kw)
    if installed: ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    d = json.loads(g["SEED"].replace("__WEEK__", g["week_key_now"]())); d["novaMet"] = 99
    if ifc: d["publicId"] = OWNER
    pre = "class26e.ifc." if ifc else "class26e."
    ctx.add_init_script("""(()=>{ if(localStorage.getItem('%sdrill.v1')) return; const d=%s;
      localStorage.setItem('class26e.drill.v1', JSON.stringify(d)); %s
      ['freshstart','intro.seen','unithold.tip','daily.seen','savecode.asked','getstarted','penal256578.seen','penal55124.seen','penal124256.seen'].forEach(k=>localStorage.setItem('%s'+k,'1'));
      localStorage.setItem('%ssynccode','TEST-0382'); localStorage.setItem('%sframe.ok','go-live-1'); })()""" % (
        pre, json.dumps(d), ("localStorage.setItem('class26e.ifc.drill.v1', JSON.stringify(d)); localStorage.setItem('class26e.activeclass','ifc');" if ifc else ""), pre, pre, pre))
    ctx.add_init_script("addEventListener('DOMContentLoaded',()=>{const s=document.createElement('style');s.textContent='.daily-alert{display:none!important}';document.head.appendChild(s);});")
    pg = ctx.new_page()
    body = g["patched"](ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(url); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ try{ homeUnlocksOwed=()=>false; }catch(e){} store.seenUnitSelectTour=true; store.seenUnitOptionsTour=true; showHome(); }")
    pg.wait_for_timeout(1500)
    return ctx, pg

SETUP = "(m)=>{ const u=unitsInTeachingOrder(); cfg.mode=m||'drill'; cfg.units=[u[1],u[4]]; showSetup(); }"
CATS = "devtools.timeline,disabled-by-default-devtools.timeline"

def traced(pg, cdp, fn):
    """Run fn under a trace; return main-thread events (name, ts, dur, tdur, args) and fn's value."""
    cdp.send("Tracing.start", {"categories": CATS, "transferMode": "ReturnAsStream"})
    w0 = time.time(); fn(); v = (time.time() - w0) * 1000      # the window's wall length, ms
    done = {}
    cdp.on("Tracing.tracingComplete", lambda e: done.setdefault("s", e["stream"]))
    cdp.send("Tracing.end")
    t0 = time.time()
    while "s" not in done and time.time() - t0 < 60: pg.wait_for_timeout(100)
    data = ""
    while True:
        r = cdp.send("IO.read", {"handle": done["s"], "size": 1 << 20}); data += r["data"]
        if r.get("eof"): break
    cdp.send("IO.close", {"handle": done["s"]})
    ev = json.loads(data); ev = ev["traceEvents"] if isinstance(ev, dict) else ev
    main = None
    for e in ev:
        if e.get("name") == "thread_name" and e.get("args", {}).get("name") == "CrRendererMain": main = (e["pid"], e["tid"])
    return [e for e in ev if (e.get("pid"), e.get("tid")) == main], v

def top_tasks(evs, t_from=None, t_to=None):
    """Top-level main-thread tasks (thread time, ms), optionally within [t_from, t_to] (trace µs)."""
    out = []
    for e in evs:
        if e.get("ph") == "X" and e.get("name") in ("ThreadControllerImpl::RunTask", "RunTask") and "tdur" in e:
            if t_from is not None and e["ts"] + e.get("dur", 0) < t_from: continue
            if t_to is not None and e["ts"] > t_to: continue
            out.append(e)
    # RunTask can nest inside ThreadControllerImpl::RunTask: keep outermost
    out.sort(key=lambda e: e["ts"]); keep = []; end = -1
    for e in out:
        if e["ts"] >= end: keep.append(e); end = e["ts"] + e.get("dur", 0)
    return keep
def restyled(evs):
    return sum((e.get("args", {}).get("elementCount") or 0) for e in evs if e.get("name") == "UpdateLayoutTree" and e.get("ph") == "X")
def marker(evs, label):
    for e in evs:
        if e.get("name") == "TimeStamp" and (e.get("args", {}).get("data", {}).get("message") == label): return e["ts"]
    return None
def first_frame_after(evs, ts):
    best = None
    for e in evs:
        if e.get("name") in ("Paint", "PaintImage", "Commit", "Layerize") and e["ts"] >= ts:
            if best is None or e["ts"] < best: best = e["ts"]
    return best
X4 = lambda ms: round(ms * 4)
TICKB = 110; SCROLLB = 60

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    # ---------------- (1)-(3) speed ----------------
    ctx, pg = page(br, 440, 956)
    cdp = ctx.new_cdp_session(pg)
    pg.evaluate(SETUP); pg.wait_for_timeout(2500)          # the first visit warms the caches, as a session's first look does
    pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
    opens = []; settles = []; ticks = []; tick_ms = []; scroll_el = []; scroll_ms = []; scroll_max = []
    cpu = lambda evs: sum(e["tdur"] for e in top_tasks(evs)) / 1000
    # what the page does on its own while the screen sits there (the tab bar's loops, idle-time renders): taken off a tick's and a
    # scroll's window, so they measure the tick and the scroll
    # The launch's own warm-up (every badge struck in idle slices from 5s after launch - warmBadgeStrikes) is waited out first: it is
    # the app's, not this screen's, and it would be counted against whichever window it lands in.
    pg.evaluate("()=>{ cfg.mode='drill'; cfg.units=[]; showSetup(); }"); pg.wait_for_timeout(3000)
    rates = []; t_wait = time.time()
    while time.time() - t_wait < 60:
        evs, wall = traced(pg, cdp, lambda: pg.wait_for_timeout(700))
        rates.append(cpu(evs) / max(1, wall))
        if len(rates) >= 3 and max(rates[-3:]) < .2: break
    idle_rate = sorted(rates[-3:])[1]
    for rep in range(3):
        pg.evaluate("()=>showHome()"); pg.wait_for_timeout(1500)
        evs, _ = traced(pg, cdp, lambda: pg.evaluate("async()=>{ console.timeStamp('open-382'); cfg.mode='drill'; cfg.units=[]; showSetup(); await new Promise(r=>setTimeout(r,1500)); console.timeStamp('settled-382'); }"))
        t0 = marker(evs, "open-382"); t1 = marker(evs, "settled-382")
        ff = first_frame_after(evs, t0)
        first = sum(e["tdur"] for e in top_tasks(evs, t0, ff)) / 1000 if ff else 1e9
        allw = sum(e["tdur"] for e in top_tasks(evs, t0, t1)) / 1000
        opens.append(X4(first)); settles.append(X4(allw))
        pg.wait_for_timeout(400)
        # (2) ticks: two cards on, two off
        for i in (0, 2, 0, 2):
            b = pg.evaluate("(i)=>{ const r=[...document.querySelectorAll('#stage label.pick')].filter(x=>x.offsetParent)[i]; r.scrollIntoView({block:'center'}); const b=r.querySelector('.pname').getBoundingClientRect(); return [b.left+b.width/2,b.top+b.height/2]; }", i)
            pg.wait_for_timeout(500)
            evs, wall = traced(pg, cdp, lambda: (pg.touchscreen.tap(b[0], b[1]), pg.wait_for_timeout(700)))
            # the tick's longest piece of main-thread work (what holds the next frame back), not the frames of its pop that follow
            ticks.append(restyled(evs)); tick_ms.append(X4(max([e["tdur"] for e in top_tasks(evs)] or [0]) / 1000))
        pg.evaluate("()=>window.scrollTo(0,0)"); pg.wait_for_timeout(600)
        # (3) a fresh screen, scrolled by touch
        pg.evaluate("()=>{ cfg.mode='drill'; cfg.units=[]; showSetup(); }"); pg.wait_for_timeout(2000)
        def flick():
            # the middle of the left column: a finger on a card's corner circle is drag-select's handle, not a scroll
            cdp.send("Input.synthesizeScrollGesture", {"x": 110, "y": 760, "yDistance": -900, "speed": 1400, "gestureSourceType": "touch"})
            cdp.send("Input.synthesizeScrollGesture", {"x": 110, "y": 300, "yDistance": 900, "speed": 1400, "gestureSourceType": "touch"})
        evs, wall = traced(pg, cdp, flick)
        tt = top_tasks(evs)
        scroll_el.append(restyled(evs)); scroll_ms.append(X4(max(0, cpu(evs) - idle_rate * wall))); scroll_max.append(X4(max([e["tdur"] for e in tt] or [0]) / 1000))
    med = lambda a: sorted(a)[len(a) // 2]
    chk("(1) opening: main thread to the first frame %dms at 4x (budget 340; runs %s)" % (med(opens), opens), med(opens) <= 340, opens)
    chk("(1) opening: main thread in its first 1.5s %dms at 4x (budget 650; runs %s)" % (med(settles), settles), med(settles) <= 650, settles)
    chk("(2) a tick restyles %d elements (median; budget 250; ticks %s)" % (med(ticks), ticks), med(ticks) <= 250, ticks)
    chk("(2) a tick's longest main-thread task %dms at 4x (median; budget %d; ticks %s)" % (med(tick_ms), TICKB, tick_ms), med(tick_ms) <= TICKB, tick_ms)
    chk("(3) scrolling restyles nothing (elements restyled per two flicks: %s; budget 40)" % (scroll_el,), med(scroll_el) <= 40, scroll_el)
    chk("(3) scrolling: no main-thread task over %dms at 4x (longest per two flicks %s; the work in all %s)" % (SCROLLB, scroll_max, scroll_ms),
        max(scroll_max) <= SCROLLB, [scroll_ms, scroll_max])
    # ---------------- (4)-(7) look and shape (Pro Max) ----------------
    pg.evaluate(SETUP); pg.wait_for_timeout(2000)
    shape = pg.evaluate("""()=>{ const cards=[...document.querySelectorAll('#stage label.pick')];
      const bd=cards.filter(c=>getComputedStyle(c).backdropFilter!=='none').length;
      const flt=cards.filter(c=>[...c.querySelectorAll('.pick-badge, .pick-badge *')].some(e=>getComputedStyle(e).filter!=='none')).length;
      const on=cards.find(c=>c.querySelector('input').checked), off=cards.find(c=>!c.querySelector('input').checked);
      const box=on.querySelector('.box'); const bs=getComputedStyle(box);
      const acc=getComputedStyle(document.documentElement).getPropertyValue('--accent').trim();
      const probe=document.createElement('span'); probe.style.color=acc; document.body.appendChild(probe); const accRGB=getComputedStyle(probe).color; probe.remove();
      const bc=getComputedStyle(on).borderTopColor;
      const r=e=>{ const b=e.getBoundingClientRect(); return {x:b.left,y:b.top,w:b.width,h:b.height}; };
      const lv=document.querySelector('.setup-levels'), sa=document.querySelector('.selall-btn'), panel=document.querySelector('.screen-setup');
      const tabs=[...lv.querySelectorAll('.iconbtn')].map(b=>Math.round(b.getBoundingClientRect().height));
      return { bd, flt, n:cards.length, on:r(on), off:r(off), tickShown: bs.opacity==='1' && bs.display!=='none', accRGB, bc, tabs,
               lv:r(lv), sa:r(sa), panel:r(panel), vw:innerWidth }; }""")
    chk("(4) no card has a backdrop-filter (%d of %d)" % (shape["bd"], shape["n"]), shape["bd"] == 0, shape)
    chk("(4) no card's badge carries a filter (%d cards do)" % shape["flt"], shape["flt"] == 0, shape["flt"])
    # luminance at the same spot inside a picked and an unpicked card (the middle, below the name)
    import io
    try:
        from PIL import Image
        dpr = 3
        im = Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
        def lum(rc):
            xs = [rc["x"] + rc["w"] * f for f in (.3, .5, .7)]; ys = [rc["y"] + rc["h"] * f for f in (.55, .62)]
            v = [im.getpixel((int(x * dpr), int(y * dpr))) for x in xs for y in ys]
            return sum(.2126 * p[0] + .7152 * p[1] + .0722 * p[2] for p in v) / len(v)
        lon, loff = lum(shape["on"]), lum(shape["off"])
    except Exception as e:
        lon, loff = 0, 0
    def rgb(s):
        import re; m = [float(x) for x in re.findall(r"[\d.]+", s)[:3]] or [0, 0, 0]
        return [x * 255 for x in m] if s.startswith("color(") else m
    acc, bc = rgb(shape["accRGB"]), rgb(shape["bc"])
    border_is_accent = sum(abs(a - b) for a, b in zip(acc, bc)) < 90
    chk("(5) a picked card reads as picked: fill %.1f vs %.1f (step >= 6), accent border (%s vs %s), its tick shows (%s)" % (lon, loff, shape["bc"], shape["accRGB"], shape["tickShown"]),
        lon - loff >= 6 and border_is_accent and shape["tickShown"], [lon, loff])
    # Review: Select all and Starred
    pg.evaluate("()=>{ cfg.mode='review'; cfg.units=[]; showSetup(); }"); pg.wait_for_timeout(1500)
    rv = pg.evaluate("()=>({ sa: Math.round(document.querySelector('.selall-btn').getBoundingClientRect().height), st: Math.round((document.querySelector('.starred-pill')||{getBoundingClientRect:()=>({height:0})}).getBoundingClientRect().height) })")
    chk("(6) controls are 44px+: level tabs %s, Select all %dpx, Review's Select all %d and Starred %dpx" % (shape["tabs"], shape["sa"]["h"], rv["sa"], rv["st"]),
        min(shape["tabs"]) >= 44 and shape["sa"]["h"] >= 44 and rv["sa"] >= 44 and rv["st"] >= 44, [shape, rv])
    lvc = shape["lv"]["x"] + shape["lv"]["w"] / 2; pc = shape["panel"]["x"] + shape["panel"]["w"] / 2; sac = shape["sa"]["x"] + shape["sa"]["w"] / 2
    chk("(7) the levels are their own width (%dpx of %dpx), centred (%.1f vs %.1f), Select all centred under them (%.1f)" % (shape["lv"]["w"], shape["panel"]["w"], lvc, pc, sac),
        shape["lv"]["w"] < shape["panel"]["w"] - 40 and abs(lvc - pc) <= 2 and abs(sac - pc) <= 2, shape)
    ctx.close()
    # ---------------- (8) every size ----------------
    bad = []
    for (w, h, ifc) in ((440, 956, False), (518, 1125, False), (375, 667, False), (320, 568, False), (834, 1194, False), (1440, 900, False), (440, 956, True), (320, 568, True)):
        ctx, pg = page(br, w, h, ifc=ifc)
        pg.evaluate(SETUP); pg.wait_for_timeout(1800)
        r = pg.evaluate("""()=>{ const de=document.documentElement; const cards=[...document.querySelectorAll('#stage label.pick')].filter(c=>c.offsetParent);
          const over=cards.filter(c=>{ const r=c.getBoundingClientRect(); return [...c.querySelectorAll('.pname,.pcount,.pick-badge,.pick-barrow')].some(e=>{ const q=e.getBoundingClientRect(); return q.width && (q.right>r.right+1||q.left<r.left-1||q.bottom>r.bottom+1); }); }).length;
          const under=cards.filter(c=>{ const a=c.querySelector('.pcount').getBoundingClientRect(), b=c.querySelector('.pick-badge').getBoundingClientRect(); return a.right>b.left+1 && a.bottom>b.top+1 && a.top<b.bottom-1; }).length;
          const ctl=[...document.querySelectorAll('.screen-setup .setup-levels:not([hidden]), .screen-setup .selall-btn')].filter(e=>{ const q=e.getBoundingClientRect(); return q.left<-1 || q.right>innerWidth+1; }).length;
          return { hs: de.scrollWidth>de.clientWidth, n:cards.length, over, under, ctl }; }""")
        good = r["n"] > 0 and not r["hs"] and r["over"] == 0 and r["under"] == 0 and r["ctl"] == 0
        if not good: bad.append([w, h, ifc, r])
        ctx.close()
    chk("(8) nothing overflows or runs under the badge at 440, 518, 375, 320, 834, 1440 (academy) and 440, 320 (Fire Code)", not bad, bad)
    br.close()
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
