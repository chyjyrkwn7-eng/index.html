#!/usr/bin/env python3
"""Build 384.119 (lagaudio): four things Madison reported from his installed iPhone (17 Pro Max, iOS 26, mostly Fire Code).

 1. UNITS: "I feel like going into the unit selection screen is a smidge delayed idk." His recording: 133ms from the finger lifting
    off Drill to the first frame that changed, and that frame was the units, all at once. On an installed iPhone 17 Pro Max at its
    real 3x, at 4x CPU, both classes, from Home by real taps (Start Studying, then Drill):
    (1a) THE FIRST FRAME AFTER THE TAP MOVES: in it the mode screen is under a running opacity animation, and the units have not
         been built in the tap's own task (they come in a later one);
    (1b) THE UNITS SETTLE: they are up within 2.5s, their opacity never falls and ends at 1, and they start no dimmer than the mode
         screen ended (no flash);
    (1c) NOTHING COMES IN LATE: in the units' first frame every badge picture in view is decoded;
    (1d) Reduce motion keeps the old behaviour (built in the tap, no animation).
 2. DROP-DOWNS (Fire Code, the county booklet drawn with pdf.js: set PDFJS_DIR to an unpacked pdfjs-dist 5.4.149, or 2 is SKIPPED):
    "Couple laggy issues involving the drop downs and the next question button." The Hint's picture and the answer's code box:
    (2a) opening, the box's layout height is its final one from the first frame after the tap and stays so: the page is laid out
         once, not every frame; what is shown of it (its height less its clip) grows over several frames, never shrinks, and ends
         whole; what is under it never moves up and ends where it is laid out, with no last-frame jump;
    (2b) shutting, the same the other way: the layout untouched until the end, the shown height falling over several frames to
         nothing, what is under it never moving down, and no last-frame jump (the end is the same picture as the frame before);
    (2c) Next question, through the code box opening and shutting (at the top of the page and at its very end): its place on the
         screen moves one way only (never drops and floats back) and ends where it is placed;
    (2d) the page is laid out in at most 3 of the ten 33ms slices from 60 to 400ms after the tap (a height eased frame by frame: nearly all).
 3. SOUND: "If I have my volume on, and I leave the app, the sound screeches badly like it lags." Every Web Audio call logged from
    before the app's script runs; a test under way (its leave handlers save the run) and a 12s sound playing, then the page is hidden:
    (3a) the sound is told to go before any other leave work (its master ramp before the first localStorage write after the event);
    (3b) the master goes to silence by a RAMP of 8-40ms, never a step to 0;
    (3c) the context is suspended within 60ms of the event, and only once the ramp has played (suspend() at or after its end);
    (3d) every source sounding or scheduled at the leave is stopped by the ramp's end;
    (3e) nothing that makes a sound starts while hidden (a play() and the ambience are tried while hidden);
    (3f) back: the master the page comes back to is not the one it left (whose echo and room still held the cut sound), it starts
         at silence and rises, and the context runs again;
    (3g) a freeze alone, and a pagehide alone, suspend it too (within 60ms);
    (3h) "safariSound": false (class26e.safarisound "0" in an iPhone Safari tab) still means no audio context at all.
 4. TOP ROW: "After hitting the back button while on the mode selection screen, the Haptic Touch is missing." On every screen with
    a top row - by real taps (Home -> Choose your mode -> units -> back -> back) and mounted (Settings and its pages, Profile's,
    the Virtual Room's, the calendar, a question with Pause): in the screen's FIRST frame every round back button, the chat button
    and Pause carry their native switch, and a finger at each one's middle lands on it; still so 1.5s later.
 5. no page errors.
  python3 tools/check-b384-lagaudio.py [--against FILE] [--sections 1,2,3,4] [--classes ifc,academy]   (origin/main 384.95 must FAIL)
"""
import json, os, re, sys, time, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import b384_lagaudio_lib as L
from playwright.sync_api import sync_playwright
def arg(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
RAWPATH = arg("--against")
RAW = L.raw_of(RAWPATH)
SECTIONS = (arg("--sections") or "1,2,3,4").split(",")
CLASSES = (arg("--classes") or "ifc,academy").split(",")
ok = True; errs_all = []
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:900], flush=True)
    return bool(cond)

# ---------------------------------------------------------------------------------------------------------------- 1. units
FRAMES = """()=>{ window.__fr = []; window.__clk = null;
  addEventListener('click', () => { if(window.__clk === null) window.__clk = performance.now(); }, true);
  const f = () => { const m = document.querySelector('#stage > .modeselect'), s = document.querySelector('#stage > .screen-setup');
    let vis = 0, nd = 0;
    /* a badge drawn as a picture must be decoded to be drawn; one drawn in place (a live SVG: a token still a draft) is drawn as it is */
    if(s) s.querySelectorAll('img.pick-badge-img').forEach(i => { const r = i.getBoundingClientRect(); if(r.bottom > 0 && r.top < innerHeight && r.width){ vis++; if(!i.complete || !i.naturalWidth) nd++; } });
    const an = m ? m.getAnimations().find(a => a.playState === 'running' && a.effect && a.effect.getKeyframes().some(k => k.opacity !== undefined)) : null;
    if(an && !window.__dimA){ window.__dimA = an; window.__dimT0 = performance.now(); }
    /* where the dim is on the compositor now (it goes on through a long task; the page's own clock does not): its start (as reported,
       or the frame it was first seen in) and the real time */
    let dimNow = null; const A = window.__dimA;
    if(A){ const st0 = A.startTime != null ? A.startTime : window.__dimT0;
      const tm = A.effect.getTiming(), kf = A.effect.getKeyframes(), p = Math.max(0, Math.min(1, (performance.now() - st0) / tm.duration));
      dimNow = tm.easing === 'linear' ? +kf[0].opacity + (+kf[kf.length - 1].opacity - +kf[0].opacity) * p : (p >= 1 ? +kf[kf.length - 1].opacity : null); }
    window.__fr.push({ t: performance.now(), m: m ? +getComputedStyle(m).opacity : null, anim: !!an, s: s ? +getComputedStyle(s).opacity : null, vis, nd, dimNow });
    if(window.__fr.length < 400) requestAnimationFrame(f); };
  requestAnimationFrame(f); }"""
def section1():
    print("\n== 1. into the units, at 4x CPU (installed iPhone 17 Pro Max, 440x956 at 3x)")
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        for cls in CLASSES:
            for reduce in (False, True):
                ctx, pg, errs = L.open_page(br, RAW, "promax", cls)
                s = L.cdp(pg)
                pg.evaluate("(r)=>{ store.seenModeSelectTour = true; store.seenUnitSelectTour = true; theme.reduceMotion = r; showHome(); }", reduce)
                pg.wait_for_timeout(2000)
                c = L.center(pg, ".playbtn"); L.tap(s, c[0], c[1], 60, pg)
                pg.wait_for_selector("#stage > .modeselect", timeout=60000)
                # the mode screen as a person meets it: a few seconds on it (idle time; on a build that warms the badges, until done)
                pg.wait_for_timeout(3000)
                for _ in range(120):
                    if pg.evaluate("()=>typeof cardBadgeWarmBusy === 'undefined' || (!cardBadgeWarmBusy && !cardBadgeWarmLater)"): break
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(1500)
                L.throttle(s, 4); pg.wait_for_timeout(800)
                pg.evaluate(FRAMES)
                c = L.center(pg, '.modecard[data-mode="drill"]'); L.tap(s, c[0], c[1], 70, pg)
                pg.wait_for_timeout(3500)
                L.throttle(s, 1)
                fr = pg.evaluate("()=>window.__fr"); ck = pg.evaluate("()=>window.__clk")
                errs_all.extend(errs)
                tag = "%s%s" % (cls, ", Reduce motion" if reduce else "")
                after = [f for f in fr if ck is not None and f["t"] > ck]
                if not after:
                    chk("(1) %s: frames after the tap" % tag, False, fr[-3:]); ctx.close(); continue
                f1 = after[0]
                up = [f for f in after if f["s"] is not None]
                first_up = up[0] if up else None
                last_m = [f for f in after if f["m"] is not None]
                print("   %s: tap -> first frame %.0fms (mode %s, animating %s, units %s); units first drawn %s; settled %s" % (tag, f1["t"] - ck, f1["m"], f1["anim"], f1["s"],
                      "%.0fms" % (first_up["t"] - ck) if first_up else "-", "%.0fms" % (next((f["t"] for f in up if f["s"] >= .999), 0) - ck) if up else "-"))
                if reduce:
                    chk("(1d) %s: built in the tap as before - the units are in the first frame after it, at full opacity, no animation (%s)" % (tag, {k: f1[k] for k in ("m", "anim", "s")}),
                        f1["s"] == 1 and not f1["anim"], f1)
                    ctx.close(); continue
                chk("(1a) %s: the first frame after the tap moves (the mode screen under a running opacity animation) and the units were not built in the tap's task (%s)" % (tag, {k: f1[k] for k in ("m", "anim", "s")}),
                    f1["anim"] and f1["s"] is None and f1["m"] is not None, f1)
                ops = [round(f["s"], 3) for f in up]
                # the mode screen as last shown: its dim where the compositor has it as the units arrive (no dim: as it stood)
                cont = first_up["dimNow"] if (first_up and first_up.get("dimNow") is not None) else (last_m[-1]["m"] if last_m else 1)
                # the units' own fade has run a frame or more (steep at its start, and slow frames at 4x) before the frame that reads it: a rise
                # of up to .30 over the dim is that; the flash this guards against is the units popping in at ~1 (+.65) or under the dim
                chk("(1b) %s: the units are up within 2.5s, their opacity never falls and ends at 1, starting where the mode screen's dim is - no flash (%s .. %s, the dim at %.2f)" % (tag, ops[:1], ops[-1:], cont),
                    first_up is not None and first_up["t"] - ck < 2500 and all(b >= a - .005 for a, b in zip(ops, ops[1:])) and ops[-1] >= .999
                    and -.12 <= ops[0] - cont <= .30, ops[:12])
                chk("(1c) %s: in the units' first frame every badge picture in view is decoded (%s in view, %s not)" % (tag, first_up and first_up["vis"], first_up and first_up["nd"]),
                    first_up is not None and first_up["vis"] > 0 and first_up["nd"] == 0, first_up)
                ctx.close()
        br.close()

# ---------------------------------------------------------------------------------------------------------- 2. drop-downs
def section2():
    print("\n== 2. the drop-downs (Fire Code, a county number question, iPhone 17 Pro Max)")
    pdf = os.environ.get("PDFJS_DIR", "")
    if not os.path.exists(os.path.join(pdf, "build/pdf.min.mjs")):
        print("SKIP 2: set PDFJS_DIR to an unpacked pdfjs-dist 5.4.149 (the county booklet is drawn with it)"); return
    src = open(os.path.join(HERE, "check-b382-test.py")).read().split("\nwith sync_playwright() as pw:")[0]
    src = src.replace("pg.goto(url)", "pg.set_default_timeout(180000); pg.goto(url, timeout=240000)")
    G = {"__file__": os.path.join(HERE, "check-b382-test.py"), "__name__": "b384lg"}
    exec(src, G)
    IR = G["g"]["INSET_RE"]
    def _pat(ins):
        t, r, b, l = ins; v = {"top": "%dpx" % t, "right": "%dpx" % r, "bottom": "%dpx" % b, "left": "%dpx" % l}
        return IR.sub(lambda m: v[m.group(1)], RAW)
    G["g"]["patched"] = _pat
    # version.json at the build under test (an --against build would otherwise be told of an update and reload under the gate)
    _rp = G["route_pdf"]; _bld = (re.search(r'const APP_BUILD = "([^"]+)"', RAW) or [None, ""])[1]
    def _route(ctx):
        _rp(ctx)
        ctx.route("**/version.json*", lambda r, q: r.fulfill(status=200, headers={"content-type": "application/json"},
                  body=json.dumps({"build": _bld, "note": "", "frameId": "", "force": True, "safariSound": True})))
    G["route_pdf"] = _route
    PROBE = """([sel, ms])=>{ window.__f = []; const t0 = performance.now();
      const clipB = el => { const m = /inset\\(([^)]*?)(?:\\sround\\b|\\))/.exec(getComputedStyle(el).clipPath || ''); if(!m) return 0; const v = m[1].trim().split(/\\s+/).map(parseFloat); return (v.length >= 3 ? v[2] : v[0]) || 0; };
      /* read once each frame has been drawn (a task after the frame): what every rAF callback of that frame, the app's included, put
         on the screen - a read inside the frame's first rAF callback would come before the app's own */
      const s = () => { const box = document.querySelector(sel), nx = document.getElementById('nextbtn'), ch = [...document.querySelectorAll('.qpanel .choice')].pop();
        const r = box ? box.getBoundingClientRect() : null, disp = box ? getComputedStyle(box).display : 'none';
        window.__f.push({ t: performance.now() - t0, lay: r && disp !== 'none' ? r.height : 0, shown: r && disp !== 'none' ? Math.max(0, r.height - clipB(box)) : 0,
          next: nx && !nx.hidden && nx.getClientRects().length ? nx.getBoundingClientRect().top : null, under: ch ? ch.getBoundingClientRect().top : null, sy: scrollY }); };
      const f = () => { setTimeout(s, 0); if(performance.now() - t0 < ms) requestAnimationFrame(f); };
      requestAnimationFrame(f); }"""
    def layouts(cdp, act, pg=None):
        ev = []; done = {"v": False}
        h1 = lambda p: ev.extend(p["value"]); h2 = lambda p: done.__setitem__("v", True)
        cdp.on("Tracing.dataCollected", h1); cdp.on("Tracing.tracingComplete", h2)
        cdp.send("Tracing.start", {"categories": "devtools.timeline", "transferMode": "ReportEvents"})
        act()
        cdp.send("Tracing.end")
        for _ in range(150):
            if done["v"]: break
            (pg.wait_for_timeout(100) if pg else time.sleep(.1))
        cdp.remove_listener("Tracing.dataCollected", h1); cdp.remove_listener("Tracing.tracingComplete", h2)
        # the frames IN the move that laid the page out: 33ms bins from 60 to 400ms after the finger lands (the tap's own work and the
        # end's are outside it; a height eased frame by frame lays it out in nearly every bin, the clock's tick in at most one)
        d0 = [e["ts"] for e in ev if e.get("ph") == "X" and e.get("name") == "EventDispatch"]
        if not d0: return 99
        t0 = min(d0)
        return len({int((e["ts"] - t0) / 1000 / 33) for e in ev if e.get("ph") == "X" and e.get("name") == "Layout" and 60 <= (e["ts"] - t0) / 1000 <= 400})
    def tapsel(pg, cdp, sel):
        c = pg.evaluate("(s)=>{ const b=document.querySelector(s); if(!b) return null; const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2]; }", sel)
        if c: G["tap"](cdp, *c)
        return bool(c)
    def moves(name, fr, opening, under_key="under"):
        """fr: frames from just before the tap. The move's frames: from the first change of 'shown' to the end."""
        sh = [f["shown"] for f in fr]; lay = [f["lay"] for f in fr]
        ch = [i for i in range(1, len(sh)) if abs(sh[i] - sh[i - 1]) > .3]
        if not ch:
            chk("(2) %s: the box moves at all" % name, False, sh[:20]); return
        i0, i1 = ch[0], ch[-1]
        seg = sh[i0 - 1:i1 + 1]; lseg = lay[i0:i1 + 1]
        steps = [b - a for a, b in zip(seg, seg[1:])]
        total = abs(seg[-1] - seg[0]) or 1
        mono = all(s >= -.3 for s in steps) if opening else all(s <= .3 for s in steps)
        lay_const = (max(lseg[:-1] or [0]) - min(lseg[:-1] or [0])) < .6 if not opening else (max(lseg) - min(lseg)) < .6
        end_ok = abs(steps[-1]) < .4 * total if len(steps) > 1 else False
        u = [f[under_key] for f in fr[i0 - 1:] if f[under_key] is not None]
        us = [b - a for a, b in zip(u, u[1:])]
        # one way (down when what is under it is pushed, up when it is let back - or, at the end of the page, down with the scroll it
        # gives back), and the last step it takes is no jump
        u_mono = not (any(x > .6 for x in us) and any(x < -.6 for x in us))
        utot = abs(u[-1] - u[0]) if u else 0
        nz = [x for x in us if abs(x) > .3]
        u_end = (not nz) or utot < 2 or abs(nz[-1]) < .45 * utot
        print("   %s: shown %s ... %s over %d frames, layout %s..%s, under moves %.0fpx" % (name, [round(x) for x in seg[:6]], [round(x) for x in seg[-3:]], len(seg) - 1,
              round(min(lseg)), round(max(lseg)), utot))
        chk("(2%s) %s: the layout changes once (%s while it moves); what is shown %s over %d frames (>= 4), one way only, with no last-frame jump" % ("a" if opening else "b", name,
            "height %.0f..%.0f" % (min(lseg), max(lseg)), "grows" if opening else "shrinks", len(seg) - 1), lay_const and mono and len(seg) - 1 >= 4 and end_ok,
            {"shown": [round(x, 1) for x in seg], "layout": [round(x, 1) for x in lseg]})
        chk("(2%s) %s: what is under it moves one way only and does not jump at the end (%s)" % ("a" if opening else "b", name, [round(x, 1) for x in us[-4:]]), u_mono and u_end, [round(x, 1) for x in us])
    def next_ok(name, fr):
        n = [f["next"] for f in fr if f["next"] is not None]
        if len(n) < 3: print("   %s: Next not up" % name); return
        st = [b - a for a, b in zip(n, n[1:])]
        up = [x for x in st if x < -.6]; dn = [x for x in st if x > .6]
        chk("(2c) %s: Next question moves one way only - never drops and floats back (%d frames up, %d down; steps %s)" % (name, len(up), len(dn), [round(x, 1) for x in st if abs(x) > .6][:12]),
            not (up and dn), [round(x, 1) for x in st])
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=G["g"]["CHROME"])
        label, w, h, ins, ua = G["SIZES"][0]
        ctx, pg, cdp = G["page"](br, w, h, ins, ua)
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.evaluate("()=>{ try{ localStorage.removeItem('class26e.codeopen'); localStorage.removeItem('class26e.ifc.codeopen'); }catch(e){} }")
        # his question (the county wood-chips permit: a number answer, so it carries the Hint); four county number ones if it is gone
        pg.evaluate("""()=>{ let ids = %s; ids = ids.filter(i => /\\d/.test(QUESTIONS[i].choices.join(' ')));
          const his = ids.find(i => /wood chips or hogged/i.test(String(QUESTIONS[i].q || QUESTIONS[i].question || '')));
          ids = his != null ? [his] : ids.slice(0, 4);   /* (one question: a drill shuffles, and his must be the one up) */
          cfg.source='all'; cfg.mode='drill'; cfg.units=[QUESTIONS[ids[0]].topic]; beginRun(ids); }""" % G["AMEND"])
        pg.wait_for_selector(".qpanel .choice", timeout=60000)
        for _ in range(120):
            if pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-hint-btn')"): break
            pg.wait_for_timeout(250)
        if not pg.evaluate("()=>!!document.querySelector('.qpanel .ifc-hint-btn')"):
            chk("(2) the Hint is there on a county number question", False)
        else:
            HP = ".qpanel .ifc-hintpic"
            # the first open paints the picture; then shut, open again (drawn before), shut
            pg.evaluate(PROBE, [HP, 2600]); tapsel(pg, cdp, ".qpanel .ifc-hint-btn"); pg.wait_for_timeout(2900)
            fr = pg.evaluate("()=>window.__f"); sh = [f["shown"] for f in fr]
            st = [b - a for a, b in zip(sh, sh[1:])]
            tot = max(sh) - min(sh) if sh else 0
            chk("(2a) the Hint's first open (its picture painted after the tap): what is shown never shrinks, ends whole, and no one frame carries more than 60%% of it (%s)" % [round(x) for x in st if abs(x) > .3][:12],
                tot > 20 and all(x >= -.3 for x in st) and max(st) < .6 * tot and abs(sh[-1] - fr[-1]["lay"]) < .6, [round(x, 1) for x in sh])
            for k in range(2):
                pg.wait_for_timeout(600)
                pg.evaluate(PROBE, [HP, 1100])
                n = layouts(cdp, lambda: (tapsel(pg, cdp, ".qpanel .ifc-hint-btn"), pg.wait_for_timeout(1300)), pg)
                fr = pg.evaluate("()=>window.__f"); moves("the Hint shutting (%d)" % (k + 1), fr, False)
                chk("(2d) the Hint shutting (%d): the page laid out in %d of the move's ten 33ms slices (<= 3, not every frame)" % (k + 1, n), n <= 3, n)
                pg.wait_for_timeout(600)
                pg.evaluate(PROBE, [HP, 1100])
                n = layouts(cdp, lambda: (tapsel(pg, cdp, ".qpanel .ifc-hint-btn"), pg.wait_for_timeout(1300)), pg)
                fr = pg.evaluate("()=>window.__f"); moves("the Hint opening again, drawn before (%d)" % (k + 1), fr, True)
                chk("(2d) the Hint opening (%d): the page laid out in %d of the move's ten 33ms slices (<= 3)" % (k + 1, n), n <= 3, n)
        G["answer_right"](pg, cdp); pg.wait_for_timeout(1200)
        CB = ".qpanel .ifc-ref"
        for where in ("top", "end"):
            pg.evaluate("(w)=>scrollTo({ top: w === 'end' ? 99999 : 0, behavior: 'instant' })", where); pg.wait_for_timeout(500)
            pg.evaluate(PROBE, [CB, 1500])
            n = layouts(cdp, lambda: (tapsel(pg, cdp, ".qpanel .ifc-code-sum"), pg.wait_for_timeout(1700)), pg)
            fr = pg.evaluate("()=>window.__f")
            for _ in range(60):
                if pg.evaluate("()=>!!document.querySelector('.ifc-code[open] .ifc-clips canvas')"): break
                pg.wait_for_timeout(150)
            moves("the code box opening (page at its %s)" % where, fr, True)
            next_ok("the code box opening (page at its %s)" % where, fr)
            chk("(2d) the code box opening (page at its %s): the page laid out in %d of the move's ten 33ms slices (<= 3)" % (where, n), n <= 3, n)
            pg.wait_for_timeout(700)
            pg.evaluate("()=>scrollTo({ top: 99999, behavior: 'instant' })"); pg.wait_for_timeout(500)
            pg.evaluate(PROBE, [CB, 1500])
            n = layouts(cdp, lambda: (tapsel(pg, cdp, ".qpanel .ifc-code-sum"), pg.wait_for_timeout(1700)), pg)
            fr = pg.evaluate("()=>window.__f")
            moves("the code box shutting (page at its end)", fr, False)
            next_ok("the code box shutting (page at its end)", fr)
            chk("(2d) the code box shutting: the page laid out in %d of the move's ten 33ms slices (<= 3)" % n, n <= 3, n)
            shut = pg.evaluate("()=>{ const d = document.querySelector('.qpanel details.ifc-code'); return d ? d.open : null; }")
            chk("(2b) the code box ends shut (%s)" % shut, shut is False)
        errs_all.extend(errs)
        br.close()
    G["srv"].shutdown()

# --------------------------------------------------------------------------------------------------------------- 3. sound
def section3():
    print("\n== 3. leaving with sound on (a test under way, a 12s sound playing)")
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME, args=["--autoplay-policy=no-user-gesture-required"])
        def page(extra=None, devkey="promax"):
            ctx, pg, errs = L.open_page(br, RAW, devkey, "academy", extra_init=L.AUDIO + (";" + extra if extra else ""))
            s = L.cdp(pg)
            pg.evaluate("()=>{ store.seenModeSelectTour = true; theme.soundOn = true; showHome(); }")
            pg.wait_for_timeout(1500)
            L.tap(s, 220, 300, 60, pg); pg.wait_for_timeout(1500)
            return ctx, pg, s, errs
        def watch(pg, tagname):
            m = pg.evaluate(L.MASTER)
            pg.evaluate("([id, t])=>{ const n = window.__au.nodes.get(id); n.gain.__watch = t; n.gain.__ctx = n.context; window.__au.master = id; }", [m, tagname])
            return m
        RUN = """()=>{ theme.autoAdvance=false; cfg.mode='drill'; cfg.source='all'; cfg.size=0; cfg.timer='off';
          const c = {}; QUESTIONS.forEach(q => { const t = (q.topic||'').trim(); c[t] = (c[t]||0)+1; }); const u = Object.keys(c).sort((a,b)=>c[a]-c[b])[0];
          cfg.units=[u]; beginRun(QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u)); }"""
        ctx, pg, s, errs = page()
        chk("(3) the sound is on and running", (pg.evaluate("()=>NovaSound.state()") or {}).get("ctxState") == "running", pg.evaluate("()=>NovaSound.state()"))
        pg.evaluate(RUN); pg.wait_for_timeout(2500)
        m0 = watch(pg, "m0")
        pg.evaluate("()=>{ playSound('rank.whirl'); playSound('test.correct'); }"); pg.wait_for_timeout(700)
        # as iOS does it (384 r375's note): the window loses focus first (the home swipe beginning; the test pauses itself there), then
        # the page is hidden
        pg.evaluate("()=>{ const W = window.__au; W.mark = performance.now(); W.ct0 = W.nodes.get(W.master).context.currentTime; window.dispatchEvent(new Event('blur')); }")
        pg.wait_for_timeout(300)
        pg.evaluate("()=>{ window.__au.mark2 = performance.now(); }")
        pg.evaluate("(h)=>{ (" + L.PROBE + ")(); (" + L.HIDE + ")(h); }", True)
        pg.wait_for_timeout(250)
        pg.evaluate("()=>{ playSound('test.wrong'); try{ showHome(); startAmbience('amb.home', { owner: document.querySelector('#stage > *') }); }catch(e){} }")
        pg.wait_for_timeout(500)
        W = pg.evaluate("()=>{ const W = window.__au; return { log: W.log, params: W.params, srcs: W.srcs, mark: W.mark, mark2: W.mark2, ct0: W.ct0, probe: W.probe, probeAt: W.probeAt }; }")
        mk, ct0 = W["mark"], W["ct0"]
        ev = next((x for x in W["log"] if x[0] == "event" and x[1] == "visibilitychange" and x[2] >= W["mark2"] - 1), None)
        T = ev[2] if ev else W["mark2"]
        allp = [p for p in W["params"] if p["at"] >= mk - .5 and p["w"] == "m0"]
        ps = [p for p in allp if p["at"] >= T - .5]
        first_p = ps[0]["at"] if ps else None
        first_set = next((x[2] for x in W["log"] if x[0] == "setItem" and x[2] >= T - .5), None)
        chk("(3a) at the hide the sound is told to go before any other leave work (master at +%s ms, first save at +%s ms)" % (first_p and round(first_p - T, 1), first_set and round(first_set - T, 1)),
            first_p is not None and (first_set is None or first_p <= first_set), {"params": ps[:4], "first save": first_set})
        # a step: the master set to 0 at once from a level that was sounding
        steps = [p for p in allp if (p.get("v") or 0) > .001 and ((p["m"] == "value=" and p["a"][0] == 0) or (p["m"] == "setValueAtTime" and p["a"][0] == 0 and abs(p["a"][1] - p["ct"]) < .004))]
        ramps = [p for p in allp if (p.get("v") or 0) > .001 and ((p["m"] == "linearRampToValueAtTime" and p["a"][0] == 0) or (p["m"] == "setTargetAtTime" and p["a"][0] == 0))]
        rend = None
        if ramps:
            r = ramps[0]; rend = r["a"][1] if r["m"] == "linearRampToValueAtTime" else r["a"][1] + 3 * r["a"][2]
        rlen = (rend - ramps[0]["ct"]) * 1000 if ramps else None
        chk("(3b) the master goes to silence (on the blur and at the hide) by a ramp of 8-40ms, never a step to 0 from a sounding level (ramp %s ms, steps %d)" % (rlen and round(rlen, 1), len(steps)),
            ramps and not steps and 8 <= rlen <= 40, allp[:6])
        # the hide's own silence: the last ramp to 0 asked for at the hide (whatever the level then), or none
        hr = [p for p in ps if p["m"] == "linearRampToValueAtTime" and p["a"][0] == 0]
        rendH = hr[0]["a"][1] if hr else None
        ctH = ps[0]["ct"] if ps else None
        sus = next((x for x in W["log"] if x[0] == "suspend" and x[1] >= T - .5), None)
        susd = next((x for x in W["log"] if x[0] == "suspended" and x[1] >= T - .5), None)
        silentBy = max([x for x in (rend, rendH) if x is not None] or [None]) if (rend or rendH) else None
        # how soon could the page run anything after the hide's ramp (this machine's load and the page's own leave work hold every
        # timer back alike): the suspend must be asked for within 25ms of that; with the page free, the context is suspended in 60ms
        rampMs = (rendH - ctH) * 1000 if (rendH is not None and ctH is not None) else 15
        off = (W["probeAt"] or T) - T
        free = L.free_after([x + off for x in (W["probe"] or [])], rampMs)
        callMs = sus[1] - T if sus else None
        doneMs = susd[1] - T if susd else None
        timely = callMs is not None and free is not None and callMs <= free + 25 and (doneMs is not None and (doneMs <= 60 or free > rampMs + 10))
        chk("(3c) suspended %s ms after the hide (asked for at +%s ms; the page could first run anything after the ramp at +%s ms), and only once the master has ramped to silence "
            "(suspend at ctx %s, silent from %s)" % (doneMs and round(doneMs, 1), callMs and round(callMs, 1), free and round(free, 1), sus and round(sus[2], 4), silentBy and round(silentBy, 4)),
            sus and susd and timely and silentBy is not None and sus[2] >= silentBy - .0015, {"suspend": sus, "suspended": susd, "free": free})
        ref = ctH if ctH is not None else ct0
        # sounding or scheduled at the hide: started before it, and every stop asked for before it (its natural end) still ahead
        def ends_before(x): return [t for t, at in (x.get("st") or []) if at < T]
        before = [x for x in W["srcs"] if x["at"] < T and all(t > ref + .001 for t in ends_before(x))]
        late = [x for x in before if x["stop"] is None or x["stop"] > ref + .03]
        chk("(3d) every source sounding or scheduled at the hide (%d) is stopped within 30ms of it (%d not)" % (len(before), len(late)), before and not late,
            [(x["kind"], x["stop"] and round((x["stop"] - ref) * 1000)) for x in late[:8]])
        hid = [x for x in W["srcs"] if x["hidden"] and not (x["stop"] is not None and x["stop"] - x["start"] <= .05)]
        chk("(3e) nothing that makes a sound starts while hidden (a play() and the ambience were tried): %d" % len(hid), not hid, hid[:4])
        pg.evaluate(L.HIDE, False); pg.wait_for_timeout(700)
        m1 = pg.evaluate(L.MASTER)
        if m1: pg.evaluate("([id])=>{ const n = window.__au.nodes.get(id); window.__au.v1 = n.gain.value; }", [m1])
        st = pg.evaluate("()=>NovaSound.state()")
        old_gone = pg.evaluate("(id)=>window.__au.log.some(x => x[0] === 'disc' && x[1] === id)", m0)
        chk("(3f) back: the page comes back to a fresh master, not the one it left (whose echo and room held the cut sound: old master %s, now %s, left disconnected %s), running" % (m0, m1, old_gone),
            m1 and m1 != m0 and old_gone and st.get("ctxState") == "running", st)
        errs_all.extend(errs); ctx.close()
        # a freeze alone, a pagehide alone
        for kind in ("freeze", "pagehide"):
            ctx, pg, s, errs = page()
            watch(pg, "k")
            # off Home (its planet system draws every frame; a page really hidden draws nothing, so its frames would only stand in
            # for this machine's load)
            pg.evaluate("()=>{ store.seenSettingsTour = true; showAppearance(); }"); pg.wait_for_timeout(1200)
            pg.evaluate("()=>{ playSound('rank.whirl'); }"); pg.wait_for_timeout(500)
            # the page's own leave work for this event ends when the last listener (added here, after the app's) has run
            pg.evaluate("""(k)=>{ const W = window.__au; const end = () => { W.dispEnd = performance.now(); };
              if(k === 'freeze') document.addEventListener('freeze', end); else window.addEventListener('pagehide', end);
              }""", kind)
            pg.evaluate("(k)=>{ const W = window.__au; W.mark = performance.now(); W.ctL = W.nodes.get(W.master).context.currentTime; (" + L.PROBE + ")(); if(k === 'freeze'){ Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('freeze')); }"
                        " else window.dispatchEvent(new PageTransitionEvent('pagehide', { persisted: true })); }", kind)
            pg.wait_for_timeout(400)
            d = pg.evaluate("""()=>{ const W = window.__au; const s = W.log.find(x => x[0] === 'suspended' && x[1] >= W.mark), c = W.log.find(x => x[0] === 'suspend' && x[1] >= W.mark);
              const r = W.params.find(p => p.at >= W.mark - .5 && p.m === 'linearRampToValueAtTime' && p.a[0] === 0);
              return { ms: s ? s[1] - W.mark : null, call: c ? c[1] - W.mark : null, at: c ? c[2] : null, rampEnd: r ? r.a[1] : null, ctL: W.ctL,
                       disp: W.dispEnd ? W.dispEnd - W.mark : null, probe: W.probe, off: W.probeAt - W.mark }; }""")
            rampMs = ((d["rampEnd"] - d["ctL"]) * 1000) if d["rampEnd"] is not None else 15
            free = L.free_after([x + (d["off"] or 0) for x in (d["probe"] or [])], rampMs)
            timely = d["call"] is not None and free is not None and d["call"] <= free + 25 and d["ms"] is not None and (d["ms"] <= 60 or free > rampMs + 10)
            chk("(3g) a %s alone: silence by a ramp first (suspend at ctx %s, ramp ends %s); suspend() asked for at +%s ms (the page could first run anything after the "
                "ramp at +%s ms; its own %s handlers ran to +%s ms); suspended at +%s ms" % (kind, d["at"] and round(d["at"], 4), d["rampEnd"] and round(d["rampEnd"], 4),
                d["call"] and round(d["call"], 1), free and round(free, 1), kind, d["disp"] and round(d["disp"], 1), d["ms"] and round(d["ms"], 1)),
                d["rampEnd"] is not None and d["at"] is not None and d["at"] >= d["rampEnd"] - .0015 and timely, {k: d[k] for k in ("ms", "call", "at", "rampEnd", "disp")})
            errs_all.extend(errs); ctx.close()
        # "safariSound": false in an iPhone Safari tab (version.json says so; the update check writes class26e.safarisound)
        ctx, pg, errs = L.open_page(br, RAW, "safari", "academy", extra_init=L.AUDIO, safari_sound=False)
        s = L.cdp(pg)
        pg.evaluate("()=>{ theme.soundOn = true; showHome(); }"); pg.wait_for_timeout(1200)
        for _ in range(80):
            if pg.evaluate("()=>{ try{ return localStorage.getItem('class26e.safarisound') === '0'; }catch(e){ return false; } }"): break
            pg.wait_for_timeout(250)
        L.tap(s, 220, 300, 60, pg); pg.wait_for_timeout(1200)
        made = pg.evaluate("()=>({ made: window.__made, tabOff: NovaSound.tabOff(), st: NovaSound.state() })")
        chk("(3h) safariSound off in an iPhone Safari tab: no audio context at all (%s)" % made, made["made"] == 0 and made["tabOff"] is True, made)
        errs_all.extend(errs); ctx.close()
        br.close()

# -------------------------------------------------------------------------------------------------------------- 4. top row
TOPS = """()=>{ const sel = '.settings-nav > button, #chatdock-btn, #pausebtn, .roomchat-fab';
  const out = [];
  document.querySelectorAll(sel).forEach(e => { const r = e.getBoundingClientRect(); const st = getComputedStyle(e);
    if(!r.width || !r.height || r.bottom <= 0 || r.top > innerHeight * .25 || st.visibility === 'hidden' || st.display === 'none' || e.closest('[hidden]') || parseFloat(st.opacity) < .05) return;
    if(r.right <= 0 || r.left >= innerWidth) return;
    const sw = e.querySelector(':scope > .nova-hsw') || e.querySelector(':scope > .nova-hlb');
    const x = r.left + r.width / 2, y = r.top + r.height / 2, hit = document.elementFromPoint(x, y);
    out.push({ el: (e.id ? '#' + e.id : '.' + String(e.className).split(' ')[0]), sw: !!sw, lands: !!(sw && hit && (hit === sw || sw.contains(hit))) }); });
  return out; }"""
FIRST = """(js)=>new Promise(res => { let done = false;
  const look = () => { if(done) return; done = true; res(window.__tops()); };
  const mo = new MutationObserver(() => { mo.disconnect(); requestAnimationFrame(look); });
  mo.observe(document.getElementById('stage'), { childList: true });
  if(js) (0, eval)(js);
  setTimeout(() => { if(!done){ done = true; mo.disconnect(); res(null); } }, 20000); })"""
SCREENS = [("Settings", "showAppearance()"), ("Settings: sound", "showAppearance({page:'sound'})"), ("Settings: study", "showAppearance({page:'study'})"),
           ("Settings: motion", "showAppearance({page:'motion'})"), ("Settings: sync", "showAppearance({page:'sync'})"), ("Advanced", "showAdvancedSettings()"),
           ("Contributors", "showCredits()"), ("Legal", "showSettingsText('legal')"), ("Release history", "showReleaseHistory()"),
           ("Class catalog", "showClassCatalog()"), ("Virtual Room", "showVirtualRoomChoice()"), ("Virtual Room host", "showVirtualRoomSetup()"),
           ("Virtual Room join", "showRoomBrowser()"), ("Rank ladder", "showRanksScreen()"), ("badge case", "showRanksScreen('badges')"),
           ("Customize", "showCustomize()"), ("Customize: theme", "showCustomize('theme')"), ("Calendar", "showCalendar()"), ("Friends", "showFriends()"),
           ("Test history", "showTestReviewList()"), ("units: review", "cfg.mode='review'; showSetup()"), ("Choose your mode", "showModeSelect()")]
def section4():
    print("\n== 4. the top row's switches, in each screen's first frame (iPhone 17 Pro Max, installed)")
    with sync_playwright() as pw:
        br = pw.chromium.launch(executable_path=L.CHROME)
        for cls in CLASSES:
            ctx, pg, errs = L.open_page(br, RAW, "promax", cls)
            s = L.cdp(pg)
            pg.evaluate("()=>{ store.seenModeSelectTour = true; store.seenUnitSelectTour = true; window.__tops = " + TOPS + "; showHome(); }")
            pg.wait_for_timeout(2500)
            bad = []; seen = 0
            def by_tap(name, sel):
                c = L.center(pg, sel)
                if not c: bad.append((name, "no " + sel)); return
                p = pg.evaluate_handle("()=>{ const w = { r: null }; const mo = new MutationObserver(() => { mo.disconnect(); requestAnimationFrame(() => { w.r = window.__tops(); }); }); mo.observe(document.getElementById('stage'), { childList: true }); window.__w = w; return 1; }")
                L.tap(s, c[0], c[1], 60, pg)
                pg.wait_for_timeout(1800)
                r = pg.evaluate("()=>window.__w.r")
                note(name + " (tapped)", r)
                note(name + " (1.5s on)", pg.evaluate("()=>window.__tops()"))
            def note(name, r):
                nonlocal seen
                if r is None: bad.append((name, "never mounted")); return
                for x in r:
                    seen += 1
                    if not (x["sw"] and x["lands"]): bad.append((name, x))
            by_tap("Choose your mode, from Home", ".playbtn")
            by_tap("the units, from Drill", '.modecard[data-mode="drill"]')
            by_tap("Choose your mode, back from the units", ".setup-nav-back")
            by_tap("Home, back", ".modeselect .ios-nav-back")
            for name, js in SCREENS:
                pg.evaluate("()=>showHome()"); pg.wait_for_timeout(250)
                r = pg.evaluate(FIRST, js)
                note(name, r)
            # a question: Pause and the chat button beside it
            pg.evaluate("()=>showHome()"); pg.wait_for_timeout(250)
            r = pg.evaluate(FIRST, """theme.autoAdvance=false; cfg.mode='drill'; cfg.source='all'; cfg.size=0; cfg.timer='off';
              (() => { const c = {}; QUESTIONS.forEach(q => { const t = (q.topic||'').trim(); c[t] = (c[t]||0)+1; }); const u = Object.keys(c).sort((a,b)=>c[a]-c[b])[0];
              cfg.units=[u]; beginRun(QUESTIONS.map((q,i)=>i).filter(i=>(QUESTIONS[i].topic||'').trim()===u)); })()""")
            pg.wait_for_selector(".qpanel .choice", timeout=60000); pg.wait_for_timeout(300)
            note("a question (Pause, chat)", pg.evaluate("()=>window.__tops()"))
            chk("(4) %s: in each screen's first frame, every round back button, the chat button and Pause carry their switch and a finger at the middle lands on it (%d controls checked, %d not)" % (cls, seen, len(bad)),
                seen > 30 and not bad, bad[:10])
            errs_all.extend(errs); ctx.close()
        br.close()

if "1" in SECTIONS: section1()
if "2" in SECTIONS: section2()
if "3" in SECTIONS: section3()
if "4" in SECTIONS: section4()
chk("(5) no page errors", not errs_all, errs_all[:4])
print("\nALL PASS" if ok else "\nFAILURES")
sys.exit(0 if ok else 1)
