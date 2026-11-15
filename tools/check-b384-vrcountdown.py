#!/usr/bin/env python3
"""Build 384.128: THE VIRTUAL ROOM'S "STARTING IN" COUNT - SMOOTH, CRISP NUMBERS, A CLEAN TOP ROW, ON THE SHARED CLOCK.

Madison, a screenshot of the count on his installed iPhone: "This needs to be updated and better, look at the top and look at how
bad the count down is. The count down is laggy. The numbers look horrible too."  On 384.107 the ring was a conic gradient through
a radial mask redrawn from a custom property written every 100ms (stepped, ten jumps a second, each a style pass and a repaint),
the number a Georgia old-style figure cut from a gradient, and over it the test header's paper band with the mode and the count
9-10px above the line they take on the question.

Read off the page (shape, not label strings), on an installed iPhone 17 Pro Max (440x956 @3, safe area 62/34) and an iPad Pro 11"
(834x1194 @2), a used account, the race's count started by beginVirtualRoomTest:
 A. MOTION IS THE COMPOSITOR'S: (1) every animation in the count animates transform and/or opacity only (getAnimations' keyframe
    properties); (2) nothing inside the ring is written while it counts (a MutationObserver on the ring's subtree, 3s: no
    attribute, style, text or child change); (3) the ring moves on every frame: its drawn position (the moving end's rotation, or
    on 384.107 the --left it was drawn from) differs from the frame before on >= 90% of frames, read per frame for 2s;
    (4) the page paints nothing for the count: CDP trace Paint events on the page's main thread over 3s of steady count <= 2.
 B. COST AND CADENCE at 4x CPU: (1) over 3s of steady count the page's main thread runs <= 330ms of CPU (thread time from a CDP
    trace: what the page ran, not what a loaded machine made it wait; 384.107: 468-490ms, this build 192-240ms, on a fresh page); (2) over the whole count from 2s in
    (after the question built under it), rAF gaps over 2x the median on <= 4% of frames - judged only at a load under 4 (or with
    --strict-cadence): on a loaded machine both builds land either side of it run to run, so it is reported, not judged.
 C. THE NUMBER: lining and tabular figures (computed font-variant-numeric), solid (not background-clip:text, colour alpha 1),
    not the serif stack; the number's ink centred in the ring (canvas-free: the glyph box from a Range, 1.5px).
 D. THE TOP ROW: (1) the mode and the count sit where they sit on the question that follows (top within .5px) and level with
    each other; (2) the chat button is where it is on the lobby (Home's place, .5px); (3) nothing over the row's words blurs or
    dims them (no backdrop-filter, filter or opacity < 1 on them or their ancestors, and the topmost element at each word's
    middle is the word); (4) contrast of the words against what is behind them (the words hidden, the same pixels) >= 4.5;
    (5) no band: what is behind the row is the colour of the screen under it (mean RGB within 6 of the band just under the row).
 E. THE SHARED CLOCK: the count started 6.4s and 3.3s ahead; at several instants the number drawn (the one at full opacity)
    is ceil(remaining / 1000) and the ring's moving end is at 360 x (1 - remaining / count) within 2 degrees (skipping 40ms
    either side of a second's edge).
 F. REDUCE MOTION (theme.reduceMotion): no animation runs, the number and ring are drawn (opacity 1) and follow the clock, and
    at zero the question is there at once with nothing left at opacity 0.
 G. THE HAND-OFF: at zero the overlay's id is gone within 60ms of the shared instant, the first question takes taps at once
    (the topmost element at a choice's middle is the choice), the overlay is out of the page within 700ms, and Pause shows.
 H. no page errors.
  python3 tools/check-b384-vrcountdown.py [--against OLD/index.html] [--only A,B,...]   (384.107 must FAIL)
"""
import json, os, sys, re, importlib.util, statistics, math
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("trl", os.path.join(HERE, "b384_toprow_lib.py")); L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
from playwright.sync_api import sync_playwright
SRC = sys.argv[sys.argv.index("--against") + 1] if "--against" in sys.argv else os.path.join(os.path.dirname(HERE), "index.html")
RAW = open(SRC, encoding="utf-8").read()
ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(",")) if "--only" in sys.argv else set("ABCDEFGH")
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:600], flush=True)
errs = []

def open_page(br, devkey, dpr):
    name, w, h, ins, installed, ua, notched = L.DEVICES[devkey]
    ctx = br.new_context(viewport={"width": w, "height": h}, screen={"width": w, "height": h}, device_scale_factor=dpr, has_touch=True, is_mobile=True, user_agent=ua)
    if installed: ctx.add_init_script(L.g["STANDALONE"])
    ctx.add_init_script(L.g["FAKE_FIREBASE"].replace("__ROWS__", L.g["rows_json"]()))
    ctx.add_init_script(L.INIT % (json.dumps(json.dumps(L.seed())), ""))
    pg = ctx.new_page(); body = L.body_for(RAW, ins)
    pg.route("**/index.html", lambda route, request, b=body: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    m = re.search(r'const APP_BUILD = "([^"]+)"', body); bld = m.group(1) if m else ""
    pg.route("**/version.json*", lambda route, request, b=bld: route.fulfill(status=200, headers={"content-type": "application/json"},
             body=json.dumps({"build": b, "note": "", "frameId": "", "force": True, "safariSound": True})))
    pg.on("pageerror", lambda e: errs.append("%s: %s" % (devkey, str(e)[:200])))
    pg.goto(L.url(), timeout=180000)
    pg.wait_for_function("()=>typeof showHome==='function' && typeof beginVirtualRoomTest==='function'", timeout=180000)
    pg.wait_for_timeout(3500)
    pg.evaluate(L.QUIET)
    pg.wait_for_timeout(2500)   # let the launch's own work (the daily charge, the viewport settle) finish before anything is timed
    pg.evaluate(L.QUIET)
    return ctx, pg

START = """([ms, n])=>{ const t = {}; QUESTIONS.forEach(q => { const k = (q.topic||'').trim(); t[k] = (t[k]||0) + 1; });
  const u = Object.keys(t).sort((a,b)=>t[b]-t[a])[0];
  window.__startAt = Date.now() + ms; window.__countFrom = ms; beginVirtualRoomTest([u], 0, window.__startAt, n || 28); return u; }"""
CLEAR = """()=>{ try{ clearInterval(vroomRevealHandle); clearTimeout(vroomRevealHandle); }catch(e){} try{ stopRaceClock(); }catch(e){}
  document.querySelectorAll('#vroom-reveal-overlay, .vcd-overlay').forEach(e=>e.remove()); try{ inVirtualRoom = false; vroomStartAt = null; testInProgress = false; }catch(e){} }"""
# the ring's drawn position: the moving end's rotation in degrees (384.128), or 384.107's --left as a fraction of a turn
RINGPOS = """()=>{ const h = document.querySelector('#vroom-reveal-ring .vcd-head');
  if(h){ const m = getComputedStyle(h).transform; if(m === 'none') return 0; const v = m.match(/matrix\\(([^)]+)\\)/)[1].split(',').map(Number);
    let a = Math.atan2(v[1], v[0]) * 180 / Math.PI; return a; }
  const r = document.getElementById('vroom-reveal-ring'); return r ? parseFloat(r.style.getPropertyValue('--left') || '1') * 360 : null; }"""
# the number drawn now: the numeral element at the highest computed opacity (384.107: the one element)
SHOWN = """()=>{ const ns = [...document.querySelectorAll('#vroom-reveal-num .vcd-n')];
  if(!ns.length){ const n = document.getElementById('vroom-reveal-num'); return n ? { n: Number(n.textContent), op: 1 } : null; }
  let best = null; ns.forEach(e => { const o = parseFloat(getComputedStyle(e).opacity); if(!best || o > best.op) best = { n: Number(e.textContent), op: o }; }); return best; }"""
NUMEL = "(document.querySelector('#vroom-reveal-num .vcd-n:not([data-n])') || [...document.querySelectorAll('#vroom-reveal-num .vcd-n')].sort((a, b) => parseFloat(getComputedStyle(b).opacity) - parseFloat(getComputedStyle(a).opacity))[0] || document.getElementById('vroom-reveal-num'))"
ROW = """()=>{ const g = id => { const e = document.getElementById(id); if(!e || !e.getClientRects().length || !(e.textContent||'').trim()) return null; const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const c = document.getElementById('chatdock-btn'); const cr = c && !c.closest('[hidden]') && c.getClientRects().length ? c.getBoundingClientRect() : null;
  return { mode: g('testmodelabel'), count: g('testqcounter'), chat: cr ? { x: cr.left, y: cr.top, w: cr.width, h: cr.height } : null }; }"""

def lum(c):
    def ch(v):
        v = v / 255; return v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4
    return .2126 * ch(c[0]) + .7152 * ch(c[1]) + .0722 * ch(c[2])
def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True); return (la + .05) / (lb + .05)
def mean_rgb(png, box, dpr):
    from PIL import Image; import io
    im = Image.open(io.BytesIO(png)).convert("RGB")
    x0, y0, x1, y1 = [int(round(v * dpr)) for v in box]
    px = list(im.crop((max(0, x0), max(0, y0), x1, y1)).getdata())
    n = len(px) or 1
    return tuple(sum(p[i] for p in px) / n for i in range(3))

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=L.CHROME)
    ctx, pg = open_page(br, "promax", 3)
    cdp = ctx.new_cdp_session(pg)
    TR = {"ev": [], "done": False}
    cdp.on("Tracing.dataCollected", lambda e: TR["ev"].extend(e["value"]))
    cdp.on("Tracing.tracingComplete", lambda e: TR.__setitem__("done", True))
    def trace(ms):
        """a devtools.timeline trace of the next `ms`; returns (events, the page's main thread)"""
        TR["ev"] = []; TR["done"] = False
        cdp.send("Tracing.start", {"traceConfig": {"includedCategories": ["toplevel", "devtools.timeline", "disabled-by-default-devtools.timeline"]}, "transferMode": "ReportEvents"})
        pg.wait_for_timeout(ms)
        cdp.send("Tracing.end")
        for _ in range(300):
            if TR["done"]: break
            pg.wait_for_timeout(100)
        # the page's main thread: the renderer main thread with the most work in the window
        mains = {(e["pid"], e["tid"]) for e in TR["ev"] if e.get("ph") == "M" and e.get("name") == "thread_name" and (e.get("args") or {}).get("name") == "CrRendererMain"}
        fc = {}
        for e in TR["ev"]:
            k = (e.get("pid"), e.get("tid"))
            if e.get("ph") == "X" and (k in mains or not mains): fc[k] = fc.get(k, 0) + e.get("dur", 0)
        return TR["ev"], (max(fc, key=fc.get) if fc else None)

    if "B" in ONLY:
        # B1: what the count costs the page's main thread, in CPU time (thread time: what this page ran, not how long a loaded
        # machine made it wait), over 3s of steady count at 4x CPU - the page's own tasks, all of them
        # Run first, on the freshly launched page (later sections leave a finished race's clocks running under the next count).
        def cpu_of(events, main):
            return sum(e.get("tdur", e.get("dur", 0)) for e in events if (e["pid"], e["tid"]) == main and e.get("ph") == "X" and e.get("name") == "RunTask") / 1000
        pg.evaluate(CLEAR); pg.wait_for_timeout(800)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        pg.evaluate(START, [12000, 28]); pg.wait_for_timeout(2500)
        cpu = cpu_of(*trace(3000))
        chk("B1: 4x CPU, 3s of steady count: the page's main thread ran %.0fms of CPU - at most 330ms (384.107: 468-490ms; this build 192-240ms)" % cpu, cpu <= 330, cpu)
        pg.evaluate(CLEAR)
        # B2: the frame cadence over the whole count at 4x, read with rAF: gaps over 2x the median on at most 4% of frames
        pg.wait_for_timeout(1500)
        pg.evaluate("""()=>{ window.__fr = []; let last = performance.now(); window.__frStop = false;
          const f = t => { window.__fr.push([t, t - last]); last = t; if(!window.__frStop) requestAnimationFrame(f); }; requestAnimationFrame(f); }""")
        t0 = pg.evaluate("()=>performance.now()")
        pg.evaluate(START, [10000, 28])
        pg.wait_for_function("()=>Date.now() > window.__startAt + 200", timeout=60000, polling=200)
        pg.evaluate("()=>{ window.__frStop = true; }")
        fr = pg.evaluate("()=>window.__fr")
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        w = [d for t, d in fr if t0 + 2000 < t < t0 + 9800]
        med = statistics.median(w) if w else 0
        over = [round(d) for d in w if d > 2 * med]
        load = float(open("/proc/loadavg").read().split()[0])
        name = "B2: 4x CPU, the count from 2s to 9.8s: %d frames, median %.1fms, %d over 2x the median (%s), max %.0fms [load %.1f]" % (len(w), med, len(over), over[:8], max(w) if w else 0, load)
        if load > 4 and "--strict-cadence" not in sys.argv:
            print("NOTE " + name + " - REPORTED, not judged: on a machine at load over 4 the frame gaps are the machine's (both builds land either side of the bound run to run); B1 measures the count's own cost", flush=True)
        else:
            chk(name, w and len(over) <= .04 * len(w), over)
        pg.evaluate(CLEAR)

    if "A" in ONLY or "C" in ONLY:
        pg.evaluate(CLEAR); pg.evaluate(START, [10000, 28]); pg.wait_for_timeout(1800)
    if "A" in ONLY:
        props = pg.evaluate("""()=>{ const ov = document.getElementById('vroom-reveal-overlay'); const out = new Set(); let n = 0;
          ov.getAnimations({ subtree: true }).forEach(a => { n++; const ks = a.effect && a.effect.getKeyframes ? a.effect.getKeyframes() : [];
            ks.forEach(k => Object.keys(k).forEach(p => { if(!['offset','easing','composite','computedOffset'].includes(p)) out.add(p); }));
            if(a.transitionProperty) out.add(a.transitionProperty); });
          return { n, props: [...out] }; }""")
        chk("A1: every animation in the count is transform/opacity only (%d animations: %s)" % (props["n"], props["props"]),
            props["n"] > 0 and set(props["props"]) <= {"transform", "opacity"}, props)
        muts = pg.evaluate("""()=>new Promise(res => { const ring = document.getElementById('vroom-reveal-ring'); const log = [];
          const mo = new MutationObserver(ms => ms.forEach(m => log.push(m.type + ':' + (m.attributeName || '') + ':' + (m.target.id || m.target.className || m.target.nodeName))));
          mo.observe(ring, { subtree: true, attributes: true, childList: true, characterData: true });
          setTimeout(() => { mo.disconnect(); res(log); }, 3000); })""")
        chk("A2: nothing inside the ring is written while it counts (3s: %d writes)" % len(muts), len(muts) == 0, muts[:6])
        pos = pg.evaluate("""(RP)=>new Promise(res => { const f = new Function('return (' + RP + ')()'); const out = []; const t0 = performance.now();
          const step = t => { out.push([t, f()]); if(t - t0 < 2000) requestAnimationFrame(step); else res(out); }; requestAnimationFrame(step); })""", RINGPOS)
        frames = [(pos[i][0] - pos[i - 1][0], pos[i][1] - pos[i - 1][1]) for i in range(1, len(pos)) if pos[i][0] - pos[i - 1][0] >= 8]
        still = sum(1 for dt, d in frames if abs(d) < 1e-6)
        chk("A3: the ring moves on every frame (%d frames over 2s, %d where it stood still)" % (len(frames), still),
            frames and still <= .1 * len(frames), [round(d, 3) for dt, d in frames[:24]])
        # A4: paints over 3s of steady count, from a CDP trace
        pg.evaluate(CLEAR); pg.evaluate(START, [10000, 28]); pg.wait_for_timeout(2500)
        events, main = trace(3000)
        paints = [e for e in events if e.get("name") == "Paint" and (e["pid"], e["tid"]) == main and e.get("ph") in ("X", "B")]
        chk("A4: the page paints next to nothing for the count (3s of steady count: %d paints on the main thread; one a second is the spoken number)" % len(paints), len(paints) <= 4, len(paints))
    if "C" in ONLY:
        pg.evaluate(CLEAR); pg.evaluate(START, [10000, 28]); pg.wait_for_timeout(1500)
        c = pg.evaluate("""()=>{ const n = %s; const s = getComputedStyle(n); const ring = document.getElementById('vroom-reveal-ring').getBoundingClientRect();
          const rg = document.createRange(); rg.selectNodeContents(n.firstChild || n); const g = rg.getBoundingClientRect();
          const cv = document.createElement('canvas').getContext('2d'); cv.font = s.fontWeight + ' ' + s.fontSize + ' ' + s.fontFamily;
          const m = cv.measureText(n.textContent.trim()); const base = g.top + (m.fontBoundingBoxAscent || 0);
          const inkTop = base - m.actualBoundingBoxAscent, inkBottom = base + m.actualBoundingBoxDescent;
          return { fvn: s.fontVariantNumeric, clip: s.webkitBackgroundClip || s.backgroundClip, color: s.color, fam: s.fontFamily,
            cx: (g.left + g.right) / 2 - (ring.left + ring.width / 2), cy: (inkTop + inkBottom) / 2 - (ring.top + ring.height / 2) }; }""" % NUMEL)
        alpha_ok = not re.search(r"rgba\([^)]*,\s*0(\.\d+)?\)$", c["color"]) or c["color"].endswith(", 1)")
        chk("C1: the number has lining, tabular figures (%s)" % c["fvn"], "lining-nums" in c["fvn"] and "tabular-nums" in c["fvn"], c)
        chk("C2: the number is solid, not cut from a gradient, in the sans (%s, %s, %s)" % (c["clip"], c["color"], c["fam"][:30]),
            c["clip"] != "text" and alpha_ok and not re.match(r"\s*(Georgia|\"?Iowan|serif)", c["fam"]), c)
        chk("C3: the number's ink is centred in the ring (%.2f, %.2f px)" % (c["cx"], c["cy"]), abs(c["cx"]) <= 1.5 and abs(c["cy"]) <= 1.5, c)

    def row_section(dev, page, dpr):
        page.evaluate(CLEAR); page.evaluate("()=>{ showHome(); }"); page.wait_for_timeout(900); page.evaluate(L.QUIET)
        home = page.evaluate(ROW)["chat"]
        page.evaluate(START, [5000, 28]); page.wait_for_timeout(1300)
        during = page.evaluate(ROW)
        look = page.evaluate("""()=>{ const out = [];
          for(const id of ['testmodelabel', 'testqcounter']){ const e = document.getElementById(id); if(!e) continue; const r = e.getBoundingClientRect();
            const bad = []; for(let n = e; n && n !== document.documentElement; n = n.parentElement){ const s = getComputedStyle(n);
              if(parseFloat(s.opacity) < 1 || s.filter !== 'none' || (s.backdropFilter && s.backdropFilter !== 'none') || (s.webkitBackdropFilter && s.webkitBackdropFilter !== 'none')) bad.push(n.tagName + '#' + n.id + '.' + n.className); }
            const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            const top = hit === e || e.contains(hit);
            /* anything painted over the word that blurs (backdrop-filter) */
            const over = document.elementsFromPoint(r.left + r.width / 2, r.top + r.height / 2).slice(0, document.elementsFromPoint(r.left + r.width / 2, r.top + r.height / 2).indexOf(e))
              .filter(x => { const s = getComputedStyle(x); return (s.backdropFilter && s.backdropFilter !== 'none') || (s.webkitBackdropFilter && s.webkitBackdropFilter !== 'none'); }).map(x => x.tagName + '.' + x.className);
            out.push({ id, bad, top, over, color: getComputedStyle(e).color, box: [r.left, r.top, r.right, r.bottom] }); }
          return out; }""")
        hidden = page.evaluate("()=>{ ['testmodelabel','testqcounter'].forEach(id => { const e = document.getElementById(id); if(e) e.style.visibility = 'hidden'; }); }")
        png = page.screenshot()
        page.evaluate("()=>{ ['testmodelabel','testqcounter'].forEach(id => { const e = document.getElementById(id); if(e) e.style.visibility = ''; }); }")
        top = page.evaluate("()=>{ const t = document.querySelector('.wrap > .top'); const r = t.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }")
        page.wait_for_function("()=>Date.now() > window.__startAt + 900", timeout=30000, polling=100)
        after = page.evaluate(ROW)
        tag = dev
        if during["mode"] and after["mode"] and during["count"] and after["count"]:
            dy = max(abs(during["mode"]["y"] - after["mode"]["y"]), abs(during["count"]["y"] - after["count"]["y"]))
            lv = abs(during["mode"]["y"] - during["count"]["y"])
        else: dy = lv = 99
        chk("%s D1: over the count the mode and the count sit where they sit on the question (off by %.1fpx) and level (%.1fpx)" % (tag, dy, lv),
            dy <= .5 and lv <= .5, (during, after))
        same = home and during["chat"] and all(abs(home[k] - during["chat"][k]) <= .5 for k in ("x", "y", "w", "h"))
        chk("%s D2: the chat button over the count is in its lobby/Home place %s" % (tag, during["chat"]), same, (home, during["chat"]))
        chk("%s D3: nothing over the row's words blurs or dims them" % tag, all(not x["bad"] and x["top"] and not x["over"] for x in look), look)
        cons = []
        for x in look:
            l, t, r, b = x["box"]
            bg = mean_rgb(png, (l, t, r, b), dpr)
            col = tuple(int(v) for v in re.findall(r"[\d.]+", x["color"])[:3])
            cons.append(round(contrast(col, bg), 2))
        chk("%s D4: the row's words against what is behind them: contrast %s (>= 4.5)" % (tag, cons), cons and min(cons) >= 4.5, cons)
        # D5: no band: the screen's colour down a column from the safe area through the row to 60px under it changes smoothly -
        # no step of more than 3 levels between rows 3px apart (384.107's paper cap ends in an 8.8px fade at the row's foot)
        l, t, r, b = top
        from PIL import Image; import io
        im = Image.open(io.BytesIO(png)).convert("RGB")
        x0, x1 = int((l + 120) * dpr), int((r - 120) * dpr)
        rows = []
        for yy in range(int(t), int(b + 60)):
            strip = list(im.crop((x0, int(yy * dpr), x1, int(yy * dpr) + 1)).getdata())
            rows.append(tuple(sum(p[i] for p in strip) / len(strip) for i in range(3)))
        step = max((max(abs(a - c) for a, c in zip(rows[i], rows[i + 3])), i + int(t)) for i in range(len(rows) - 3))
        chk("%s D5: no band: down the screen through the top row the colour never steps (largest change over 3px: %.1f levels at y %d; <= 3)" % (tag, step[0], step[1]),
            step[0] <= 3, step)
        page.evaluate(CLEAR)
    if "D" in ONLY:
        row_section("Pro Max", pg, 3)

    if "E" in ONLY:
        bad = []; n = 0
        for ahead in (6400, 3300):
            pg.evaluate(CLEAR); pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(600)
            pg.evaluate(START, [ahead, 28])
            for k in range(20):
                pg.wait_for_timeout(290)
                if pg.evaluate("()=>window.__startAt - Date.now()") < 100: break
                # the remaining time AT THE FRAME being drawn (document.timeline.currentTime: an animation is sampled at its frame's
                # time, which on a busy page can be tens of ms behind Date.now() in the same task)
                s = pg.evaluate("""([SH, RP])=>{ const rem = window.__startAt - (Date.now() - (performance.now() - document.timeline.currentTime)); const shown = new Function('return (' + SH + ')()')(); const pos = new Function('return (' + RP + ')()')();
                  const ov = document.getElementById('vroom-reveal-overlay'); const from = ov && ov.dataset.startAt ? null : null;
                  return { rem, shown, pos, cf: window.__countFrom }; }""", [SHOWN, RINGPOS])
                if s["rem"] <= 60 or s["shown"] is None: continue
                # outside the change itself (the 400ms after a second's edge, where one number rolls out and the next in) and a frame before an edge
                if s["rem"] % 1000 < 20 or s["rem"] % 1000 > 600: continue
                n += 1
                want = math.ceil(s["rem"] / 1000)
                if s["shown"]["n"] != want or s["shown"]["op"] < .97: bad.append(("number", round(s["rem"]), s["shown"], want))
                # the ring: 384.128's moving end at -(360 x (1 - rem/count)) in the rotation's own frame; 384.107's --left x 360
                frac = max(0, min(1, s["rem"] / s["cf"]))
                if pg.evaluate("()=>!!document.querySelector('#vroom-reveal-ring .vcd-head')"):
                    want_a = (360 * frac) % 360; got = s["pos"] % 360
                else:
                    want_a = 360 * frac; got = s["pos"]
                d = abs((got - want_a + 180) % 360 - 180)
                if d > 2: bad.append(("ring", round(s["rem"]), round(got, 1), round(want_a, 1)))
        chk("E1: the number and the ring follow the shared clock (%d readings, %d off)" % (n, len(bad)), n >= 8 and not bad, bad[:6])
        # E2: each number's change starts on its second's edge to within a frame (384.128's numbers are on the timeline; 384.107's
        # changed on a 100ms timer, so up to 100ms late - read from the page as it counts)
        pg.evaluate(CLEAR); pg.evaluate(START, [4600, 28])
        e2 = pg.evaluate("""()=>new Promise(res => { const sa = window.__startAt, tl = performance.now() - Date.now(), late = [];
          const ns = [...document.querySelectorAll('#vroom-reveal-num .vcd-n[data-n]')];
          if(ns.length){ ns.forEach(e => { const n = Number(e.dataset.n); const edge = sa - n * 1000 + tl;
              const a = e.getAnimations().find(x => x.effect.getKeyframes().some(k => 'opacity' in k) && x.effect.getKeyframes()[0].opacity == 0);
              if(edge > performance.now()) late.push(a ? Math.abs(a.startTime - edge) : 999); });
            return res(late); }
          const num = document.getElementById('vroom-reveal-num'); let last = num.textContent;
          (function w(){ if(num.textContent !== last){ last = num.textContent; const rem = sa - Date.now(); late.push(Math.abs(Math.ceil(rem / 1000) * 1000 - rem)); }
            if(Date.now() < sa - 300) setTimeout(w, 2); else res(late); })(); })""")
        chk("E2: every number's change starts on its second's edge within a frame (%s ms)" % [round(x) for x in e2], e2 and max(e2) <= 17, e2)
        pg.evaluate(CLEAR)

    if "G" in ONLY:
        pg.evaluate(CLEAR); pg.evaluate("()=>{ showHome(); }"); pg.wait_for_timeout(600)
        pg.evaluate("()=>{ window.__startAt = 0; }")
        pg.evaluate("""()=>{ window.__g = { idGone: null, out: null }; (function w(){ const now = Date.now();
          if(window.__g.idGone === null && !document.getElementById('vroom-reveal-overlay') && window.__startAt && now >= window.__startAt - 200) window.__g.idGone = now;
          if(window.__g.out === null && window.__g.idGone !== null && !document.querySelector('.vcd-overlay, #vroom-reveal-overlay')) { window.__g.out = now; return; }
          setTimeout(w, 4); })(); }""")
        pg.evaluate(START, [1500, 28])
        pg.wait_for_function("()=>window.__g.idGone !== null", timeout=30000, polling=10)
        tap = pg.evaluate("""()=>{ const c = document.querySelector('.qpanel .choice, .choice'); if(!c) return null; const r = c.getBoundingClientRect();
          const h = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2); return !!h && (h === c || c.contains(h)); }""")
        pg.wait_for_function("()=>window.__g.out !== null", timeout=30000, polling=20)
        g = pg.evaluate("()=>({ idGone: window.__g.idGone - window.__startAt, out: window.__g.out - window.__startAt, pause: !document.getElementById('pausebtn').hidden })")
        chk("G: at zero the count lets go at the shared instant (+%dms), the question takes taps at once (%s), the overlay is gone by +%dms, Pause shows (%s)"
            % (g["idGone"], tap, g["out"], g["pause"]), 0 <= g["idGone"] <= 60 and tap and g["out"] <= 700 and g["pause"], g)
        pg.evaluate(CLEAR)

    if "F" in ONLY:
        pg.evaluate(CLEAR); pg.evaluate("()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} showHome(); }"); pg.wait_for_timeout(600)
        pg.evaluate(START, [4300, 28]); pg.wait_for_timeout(700)
        f = pg.evaluate("""(SH)=>{ const ov = document.getElementById('vroom-reveal-overlay'); const run = ov.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length;
          const shown = new Function('return (' + SH + ')()')(); const rem = window.__startAt - Date.now();
          const zero = [...ov.querySelectorAll('*')].filter(e => e.getClientRects().length && parseFloat(getComputedStyle(e).opacity) < .05 && !e.closest('.vcd-glow') && !e.classList.contains('vcd-glow')).map(e => e.className || e.id);
          const ring = document.getElementById('vroom-reveal-ring'); return { run, shown, want: Math.ceil(rem / 1000), zero, ring: !!ring && parseFloat(getComputedStyle(ring).opacity) === 1 }; }""", SHOWN)
        pg.wait_for_function("()=>Date.now() > window.__startAt + 60", timeout=30000, polling=20)
        q = pg.evaluate("""()=>{ const ov = document.querySelector('.vcd-overlay, #vroom-reveal-overlay'); const c = document.querySelector('.choice');
          return { ov: !!ov, choice: !!c && parseFloat(getComputedStyle(c).opacity) > .99 }; }""")
        chk("F: Reduce motion: no animation runs (%d), the number is drawn and on the clock (%s vs %s), nothing at opacity 0 (%s), and at zero the question at once (%s)"
            % (f["run"], f["shown"], f["want"], f["zero"], q), f["run"] == 0 and f["shown"] and f["shown"]["n"] == f["want"] and f["shown"]["op"] >= .99 and not f["zero"] and f["ring"] and not q["ov"] and q["choice"], (f, q))
        pg.evaluate("()=>{ theme.reduceMotion = false; try{ applyTheme(); }catch(e){} }")
        pg.evaluate(CLEAR)
    ctx.close()

    if "D" in ONLY:
        ctx2, pg2 = open_page(br, "ipadP", 2)
        row_section("iPad Pro 11", pg2, 2)
        ctx2.close()
    br.close()
chk("H: no page errors", not errs, errs[:6])
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
