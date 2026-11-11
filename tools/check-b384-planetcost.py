#!/usr/bin/env python3
"""384.31: WHAT THE PLANET SYSTEM COSTS, AND WHERE IT STANDS WHEN THE APP COMES BACK.

Madison sent a screen recording of his iPhone 17 Pro Max (the build before 384.29): "the planet system lag hasn't been fixed". Read frame by
frame (1320x2868 at 59fps, no gap over 42ms in the capture itself):
  - STEADY STATE IS FINE: the six orbit dots move on every frame (0.19-0.37 px per frame at 1/2 scale, the inner ring ~7 deg/s, the outer ~3),
    the seven flare emblems step every second frame (the sheets are 30 a second, a 60Hz capture sees 0,N,0,N), nothing stops.
  - THE RETURN: after the app switcher's zoom there are exactly five identical frames (83ms, the whole screen, both returns), then the loops
    come back layer by layer over ~6 frames (emblems, then dots and the sphere's glow, then smoke, then the seven bubbles) and THE DOTS LURCH
    AHEAD: +11.4 degrees on the inner ring and +4.6 on the outer, both ~1.6 SECONDS of travel, between the card's frame and the live page.
That lurch is a pose that was not held. pause() is a request: the animation stays pending until the page draws its next frame, and its hold time
is the timeline's time THEN. A Home Screen app iOS suspends before that frame (the usual way out) has all its pauses still pending, and the first
frame after the return completes them at the moment of the return - the loops stand where they would be had nothing paused them. loopsPauseAll
now writes the pose it just read (setting currentTime completes a pending pause at that time, in the same task).

What is measured here is by SHAPE, on the page, nothing typed as a label:
 (1) THE PAUSE HOLDS IN THE TASK THAT ASKS FOR IT: hidden (visibilitychange + pagehide), and in the same task every loop that was running is paused
     and NOT pending, at the pose it had (origin/main: every one still pending).
 (2) ...and 3s later no loop has moved from that pose (origin/main: it moves by the frames it takes the pause to be completed; the number is
     printed; a pose that moved is what the dots' lurch is made of when the page is suspended instead of drawing).
 (3) THE PHONE SAYS HOW IT WENT: the return's line in the resume log carries "slip<ms>" - how far the reference loop's pose moved between the hide
     and the moment the loops were let go (0 when the pause held) - and it is within 150ms (origin/main: no such field).
 (4) EVERY LOOP THAT RAN IS RUNNING AGAIN after the return, and the loops' poses against the reference loop are what they were (384.29's guard).
 (5) THE PLANET SYSTEM'S COST, counted off the page and held to a ceiling so it only goes down (guards: these pass on 384.29 too, the numbers are
     printed): animations running on Home's hero, distinct elements animated, those that animate anything but transform/opacity (the flip-books'
     left/top, one per bubble and nothing else), and elements under an animation with a filter or backdrop-filter.
 (6) REDUCE MOTION: no loops, none started, nothing thrown.   (7) no page error.

  python3 tools/check-b384-planetcost.py [--against REV|DIR|index.html] [--cpu 1]

Phone = iPhone 17 Pro Max installed 440x956 at 3x. Chromium cannot say what iOS does with a suspended page: (1)-(3) are what the page asks of the
animations, which is the part the app owns; whether the lurch is gone is for the phone (the resume log's "slip" and the recording)."""
import json, os, re, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0]] + sys.argv[1:]
head = open(os.path.join(HERE, "check-b384-resume.py")).read().split("def scenario(")[0]
G = {"__file__": os.path.join(HERE, "check-b384-resume.py"), "__name__": "rh"}
exec(compile(head, "resume-head", "exec"), G)
g, sync_playwright, UA, init_for, body_for, url, VIS, INSTR, chk = (G[k] for k in ("g", "sync_playwright", "UA", "init_for", "body_for", "url", "VIS", "INSTR", "chk"))
CPU = G["CPU"]

INVENTORY = r"""()=>{
  const hero = document.querySelector('#stage .cosmic-hero-wrap');
  const loops = document.getAnimations().filter(a => { try{ const t = a.effect.getTiming(); return t.iterations === Infinity && Number(t.duration) > 0; }catch(e){ return false; } });
  const inHero = loops.filter(a => { try{ return hero && hero.contains(a.effect.target); }catch(e){ return false; } });
  const els = new Set(), nonCompositor = [], under = [];
  inHero.forEach(a => {
    const t = a.effect.target; els.add(t);
    const props = new Set(); a.effect.getKeyframes().forEach(k => Object.keys(k).forEach(p => { if(!['offset','easing','composite','computedOffset'].includes(p)) props.add(p); }));
    const bad = [...props].filter(p => p !== 'transform' && p !== 'opacity');
    if(bad.length) nonCompositor.push({ props: bad.join(','), where: (t.tagName + '.' + (t.parentElement && t.parentElement.className || '')).slice(0, 60), flip: !!(t.closest && t.closest('.rk-frame')) });
    let n = t, f = 0;
    while(n && n !== hero.parentElement){ const cs = getComputedStyle(n); if((cs.filter && cs.filter !== 'none') || (cs.backdropFilter && cs.backdropFilter !== 'none') || (cs.webkitBackdropFilter && cs.webkitBackdropFilter !== 'none')) f++; n = n.parentElement; }
    if(f) under.push(t.tagName);
  });
  return { hero: inHero.length, all: loops.length, elements: els.size, nonCompositor, nonFlip: nonCompositor.filter(x => !x.flip).length, flip: nonCompositor.filter(x => x.flip).length,
           bubbles: document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank').length, withFilterAbove: under.length };
}"""
# hidden in ONE task: poses read, the page hidden, every loop that was running read again before anything can draw
HIDE_NOW = """()=>{ const ls = __M.loops().filter(a => a.playState === 'running'); window.__ls = ls; const before = ls.map(a => a.currentTime);
  __setHidden(true); window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true}));
  const after = ls.map(a => [a.playState, a.pending, a.currentTime]); window.__pose0 = after.map(x => x[2]); window.__t0 = performance.now();
  return { n: ls.length, paused: after.filter(x => x[0] === 'paused').length, pending: after.filter(x => x[1]).length,
           moved: Math.max(0, ...after.map((x, i) => Math.abs((x[2] || 0) - (before[i] || 0)))) }; }"""
POSE_DRIFT = "()=>{ const p = window.__ls.map(a => a.currentTime); return { drift: Math.max(0, ...p.map((v, i) => Math.abs(v - window.__pose0[i]))), state: window.__ls.filter(a => a.playState === 'paused').length, n: p.length }; }"

def scenario(br, rm=False):
    w, h, dpr = 440, 956, 3
    ctx = br.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=UA, reduced_motion="reduce" if rm else "no-preference")
    ctx.add_init_script(g["STANDALONE"]); ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    ctx.add_init_script(VIS); ctx.add_init_script(INSTR)
    pg = ctx.new_page(); body = body_for((62, 0, 34, 0))
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"}, body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.add_init_script(init_for(False))
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(url); pg.wait_for_timeout(4000)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    pg.evaluate("()=>{ homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
    for _ in range(3):
        pg.evaluate("()=>{ [...document.querySelectorAll('button')].filter(b=>/^Got it$/.test(b.textContent.trim())).forEach(b=>b.click()); document.querySelectorAll('.rs-spot,.unlock-card').forEach(n=>n.remove()); }")
        pg.wait_for_timeout(300)
    pg.evaluate("()=>{ try{ scheduleWeekRecap=()=>{}; maybeShowWeekRecap=()=>{}; }catch(e){} }")
    if rm:
        pg.evaluate("()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} homeUnlocksOwed=()=>false; showHome(); }"); pg.wait_for_timeout(1500)
        own = pg.evaluate("()=>__M.loops().map(a => { try{ return a.animationName || '?'; }catch(e){ return '?'; } }).filter(n => n !== 'daily-ready')")
        pg.evaluate("()=>{ window.__M.RT = performance.now(); __setHidden(true); window.dispatchEvent(new PageTransitionEvent('pagehide',{persisted:true})); }"); pg.wait_for_timeout(500)
        pg.evaluate("()=>{ window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})); __setHidden(false); window.dispatchEvent(new Event('focus')); }"); pg.wait_for_timeout(3000)
        started = pg.evaluate("()=>__M.ev.filter(e => e.d !== 'daily-ready' && (e.k === 'resume' || e.k === 'write-running')).length")
        ctx.close(); return dict(rm=True, own=own, started=started, errs=errs)
    t0 = time.time(); n = [0, 0]
    while time.time() - t0 < 240:
        pg.wait_for_timeout(3000)
        n = pg.evaluate("()=>[document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank').length, document.querySelectorAll('#stage .cosmic-hero-wrap .cosmic-badge-rank > .cosmic-rank-anim').length]")
        if n[0] and n[1] >= n[0]: break
    pg.wait_for_timeout(3000)
    cdp = ctx.new_cdp_session(pg)
    inv = pg.evaluate(INVENTORY)
    before = pg.evaluate("()=>__M.poses().filter(p => p[1] === 'running').length")
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": CPU})
    held = pg.evaluate(HIDE_NOW)
    pg.wait_for_timeout(3000)
    drift = pg.evaluate(POSE_DRIFT)
    P = pg.evaluate("()=>__M.poses()")
    pg.evaluate("()=>{ window.__M.RT = performance.now(); window.dispatchEvent(new PageTransitionEvent('pageshow',{persisted:true})); __setHidden(false); window.dispatchEvent(new Event('focus')); }")
    t1 = time.time(); Q = None
    while time.time() - t1 < 9:
        pg.wait_for_timeout(300)
        Q = pg.evaluate("()=>__M.poses()")
        if len([q for q in Q if q[1] == 'running']) >= before and not [q for q in Q if q[3]]: break
    pg.wait_for_timeout(1500)
    log = pg.evaluate("()=>JSON.parse(localStorage.getItem('class26e.resumelog') || '[]')")
    running = pg.evaluate("()=>__M.poses().filter(p => p[1] === 'running').length")
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
    ctx.close()
    return dict(rm=False, sheets=n, inv=inv, before=before, held=held, drift=drift, P=P, Q=Q, log=log, running=running, errs=errs)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=g["CHROME"])
    s = scenario(br)
    inv, held, drift = s["inv"], s["held"], s["drift"]
    print("   hero inventory: %s" % json.dumps({k: v for k, v in inv.items() if k != "nonCompositor"}))
    print("   hide in one task: %s   3s later: %s" % (held, drift))
    chk("(1) the pause holds in the task that asks for it: all %d running loops paused and none pending (pending: %d)" % (held["n"], held["pending"]),
        held["n"] >= 30 and held["paused"] == held["n"] and held["pending"] == 0, held)
    chk("(2) 3s hidden later no loop has moved from its pose (most: %.1fms)" % drift["drift"], drift["n"] >= 30 and drift["drift"] <= 2, drift)
    line = next((x for x in reversed(s["log"]) if x.startswith("told")), "")
    mm = re.search(r" slip(-?\d+)", line)
    chk("(3) the return's line in the resume log says how far the reference loop's pose moved while paused (%r)" % (mm.group(0).strip() if mm else line[:90]),
        bool(mm) and abs(int(mm.group(1))) <= 150, s["log"])
    P, Q = s["P"], s["Q"]
    bad = []
    tol = 45 + 40
    if len(P) == len(Q) and P:
        ref = next((i for i, p in enumerate(P) if p[0] == "cosmic-orbit-spin"), 0)
        for i, (p, q) in enumerate(zip(P, Q)):
            if p[1] != "paused" or q[1] != "running": continue
            if abs((p[2] - P[ref][2]) - (q[2] - Q[ref][2])) > tol: bad.append((p[0], round((q[2] - Q[ref][2]) - (p[2] - P[ref][2]))))
    chk("(4) every loop that ran runs again (%d of %d) and keeps its pose against the reference loop" % (s["running"], s["before"]), P and len(P) == len(Q) and not bad and s["running"] >= s["before"], [bad[:6], s["running"], s["before"]])
    chk("(5a) the hero animates nothing but transform and opacity except the flip-books' left/top (%d outside that; %d flip-books for %d bubbles)" % (inv["nonFlip"], inv["flip"], inv["bubbles"]),
        inv["nonFlip"] == 0 and inv["flip"] <= max(inv["bubbles"], 1), inv["nonCompositor"][:6])
    chk("(5b) the hero's animations stay within the count measured on 384.29 (running %d of 41; elements %d of 41; under a filter %d of 14)" % (inv["hero"], inv["elements"], inv["withFilterAbove"]),
        inv["hero"] <= 41 and inv["elements"] <= 41 and inv["withFilterAbove"] <= 14, inv)
    r = scenario(br, rm=True)
    chk("(6) reduce motion: no loops (%d), none started on a return (%d)" % (len(r["own"]), r["started"]), not r["own"] and not r["started"], r)
    chk("(7) no page error", not s["errs"] and not r["errs"], s["errs"][:3] + r["errs"][:3])
    br.close()
print("ALL PASS" if G["ok"] else "SOME FAILED")
sys.exit(0 if G["ok"] else 1)
