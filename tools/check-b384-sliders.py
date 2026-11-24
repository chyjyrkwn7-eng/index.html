#!/usr/bin/env python3
"""384.134 (sliders): every slider in the app is the iOS 26 slider from Madison's screen recording, in the theme's colour.
Madison: "Our sliders need to be this way, they need to also match the theme of what you have selected. But ours need to look
just like, anywhere we have one, update it, ensure it's extremely smooth and nice."
For EVERY range input the app shows (Settings > Sound: Volume; the start sheet: How many, Minutes; the Virtual Room: How many),
on an installed iPhone 17 Pro Max (440x956, 2x, touch through CDP), read off the page and its pixels:
 A  at rest: the thumb is a capsule wider than tall (w/h 1.35-1.75, 20-30px tall) inside a >=44px tall control, the track thin
    (<= 8px); the filled part is the theme's own colour (a probe painted with the theme's --switch-on, read as pixels), and it
    follows a change of theme: Default, Amethyst (purple), Silver, Sapphire, and the light mode;
 B  a press: the thumb grows (>= 1.3x wide and tall) and its body turns clear - above the track the thumb's pixels are the card's
    (within 45 of it, where at rest they are the solid knob) and the track's own fill shows through it;
 C  the value follows the finger: at 20/50/80% of the track the input's value is that fraction (+-0.07) and the thumb's middle
    is under the finger (+-4px);
 D  past either end the thumb goes past the track's end (stretch >= 3px) and, let go, comes back inside and to its rest size;
 E  only transform and opacity move: every running animation in the slider during a press and a release animates nothing else,
    and no element in it has a transition on any other property; at least one transform runs (it is not instant);
 F  the touch band: a press 20px above the track's middle takes the slider (the value moves);
 G  Reduce motion: a press does not grow the thumb and no transform animation runs;
 H  a drag across the slider at 4x CPU has no long task over 50ms (on a quiet page; best of up to three drags, each printed -
    the machine is shared);
 I  a touch that moves upright first changes nothing (the value stays, the thumb is not left pressed).
Run:  TMPDIR=/dev/shm python3 tools/check-b384-sliders.py [--only volume,howmany,minutes,vroom] [--against OLD/index.html]
Must FAIL on 384.133 (a native range input: a round white knob, a blue fill, no glass)."""
import io, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "shoot-flow.py")).read().rsplit("\nmain()", 1)[0]
g = {"__file__": os.path.join(HERE, "shoot-flow.py"), "__name__": "sf"}; exec(src, g)
from playwright.sync_api import sync_playwright
from PIL import Image
argv = sys.argv[1:]
ONLY = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
AGAINST = argv[argv.index("--against") + 1] if "--against" in argv else None
INS = (62, 0, 34, 0)
ok = True; fails = 0
def chk(name, cond, info=""):
    global ok, fails
    ok = ok and bool(cond); fails += 0 if cond else 1
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else "  -> " + str(info)[:400]), flush=True)

def body():
    s = open(AGAINST, encoding="utf-8").read() if AGAINST else open(os.path.join(g["ROOT"], "index.html"), encoding="utf-8").read()
    v = {"top": "%dpx" % INS[0], "right": "%dpx" % INS[1], "bottom": "%dpx" % INS[2], "left": "%dpx" % INS[3]}
    return g["INSET_RE"].sub(lambda m: v[m.group(1)], s)

SEEDJS = ("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.drill.v1', %s);"
          "localStorage.setItem('class26e.synccode','MADI-0001');localStorage.setItem('class26e.frame.ok','go-live-1');"
          "localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');"
          "localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');"
          "localStorage.setItem('class26e.penal256578.seen','1');localStorage.setItem('class26e.daily.seen','x');"
          "localStorage.setItem('class26e.savecode.card','1');}catch(e){}") % ("'" + g["SEED"].replace("__WEEK__", g["week_key_now"]()) + "'")

def open_page(br):
    ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=2, has_touch=True)
    ctx.add_init_script(g["STANDALONE"])
    ctx.add_init_script(g["FAKE_FIREBASE"].replace("__ROWS__", g["rows_json"]()))
    ctx.add_init_script(SEEDJS)
    ctx.add_init_script("""(()=>{ window.__lt = []; try{ new PerformanceObserver(l => l.getEntries().forEach(e => window.__lt.push(e.duration))).observe({ type: 'longtask', buffered: false }); }catch(e){} })()""")
    pg = ctx.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    b = body()
    pg.route("**/index.html", lambda route, request: route.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
    pg.goto(URL); pg.wait_for_timeout(3500)
    pg.evaluate("document.getElementById('splashscreen')?.remove()")
    cdp = ctx.new_cdp_session(pg)
    return ctx, pg, cdp, errs

COMMON = """(()=>{ if(!document.getElementById('sl-quiet')){ const st = document.createElement('style'); st.id = 'sl-quiet';
    st.textContent = '.rs-spot, .unlock-card, .rs-fly{ display:none !important; pointer-events:none !important; }'; document.body.appendChild(st); } })();
  window.__sl = { wait: ms => new Promise(r => setTimeout(r, ms)),
  calm(){ try{ homeUnlocksOwed = () => false; }catch(e){} document.querySelectorAll('.unlock-card,.rs-spot,.rs-fly').forEach(n => n.remove()); document.body.classList.remove('cutscene-focus'); } };"""
# each opener leaves the slider it is about on screen and returns the input's index among the page's visible range inputs
OPENERS = {
  "volume": """async()=>{ ${COMMON} __sl.calm(); store.seenSettingsTour = true; theme.soundOn = true; theme.soundVolume = .35; showAppearance({ page: 'sound' }); await __sl.wait(900);
     const s = document.querySelector('.settings-volume input[type=range]'); return s ? 'ok' : 'none'; }""",
  "howmany": """async()=>{ ${COMMON} __sl.calm(); document.getElementById('unitoptions-modal')?.remove();
     cfg.mode='drill'; cfg.source='all'; cfg.timer='off'; showSetup(); await __sl.wait(900);
     const picks = [...document.querySelectorAll('.pick input')]; if(!picks.length) return 'nounit'; picks.slice(0, 2).forEach(c => { c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); }); await __sl.wait(300);
     document.getElementById('nextbtn').click(); await __sl.wait(1400);
     const sh = document.querySelector('.unitoptions-modal-sheet.is-setup'); if(!sh) return 'nosheet';
     const s = sh.querySelector('.howmany-sect input[type=range]'); if(!s) return 'none'; s.closest('.sect').scrollIntoView({ block: 'center' }); await __sl.wait(300); return 'ok'; }""",
  "minutes": """async()=>{ ${COMMON} __sl.calm(); document.getElementById('unitoptions-modal')?.remove();
     cfg.mode='drill'; cfg.source='all'; cfg.timer='off'; cfg.timerMinutes = 30; showSetup(); await __sl.wait(900);
     const picks = [...document.querySelectorAll('.pick input')]; if(!picks.length) return 'nounit'; picks.slice(0, 2).forEach(c => { c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); }); await __sl.wait(300);
     document.getElementById('nextbtn').click(); await __sl.wait(1400);
     const sh = document.querySelector('.unitoptions-modal-sheet.is-setup'); if(!sh) return 'nosheet';
     const row = [...sh.querySelectorAll('.opt')].find(r => /time limit/i.test(r.textContent)); const cb = row && row.querySelector(':scope > input[type=checkbox]');
     if(!cb) return 'norow'; if(!cb.checked) cb.click(); await __sl.wait(900);
     const s = sh.querySelector('.minutes-sect input[type=range]'); if(!s) return 'none'; s.closest('.sect').scrollIntoView({ block: 'center' }); await __sl.wait(500); return 'ok'; }""",
  "vroom": """async()=>{ ${COMMON} __sl.calm(); document.getElementById('unitoptions-modal')?.remove(); try{ showVirtualRoomSetup(); }catch(e){ return 'err ' + e.message; } await __sl.wait(1200);
     const picks = [...document.querySelectorAll('#stage .pick input')]; if(!picks.length) return 'nounit';
     picks.slice(0, 2).forEach(c => { if(!c.checked){ c.checked = true; c.dispatchEvent(new Event('change', { bubbles: true })); } }); await __sl.wait(400);
     document.getElementById('nextbtn').click(); await __sl.wait(1400);
     const s = document.querySelector('.vroom-howmany input[type=range]'); if(!s) return 'none';
     s.closest('.vroom-howmany').scrollIntoView({ block: 'center' }); await __sl.wait(400); return s.disabled ? 'disabled' : s.getClientRects().length ? 'ok' : 'hidden'; }""",
}
SEL = {"volume": ".settings-volume input[type=range]", "howmany": ".unitoptions-modal-sheet .howmany-sect input[type=range]",
       "minutes": ".minutes-sect input[type=range]", "vroom": ".vroom-howmany input[type=range]"}
INFO = """(sel)=>{ const s = document.querySelector(sel); if(!s) return null;
  const R = e => { if(!e) return null; const q = e.getBoundingClientRect(); return { l: q.left, t: q.top, r: q.right, b: q.bottom, w: q.width, h: q.height, cx: q.left + q.width / 2, cy: q.top + q.height / 2 }; };
  const host = s.closest('.nsl'), knob = host && host.querySelector('.nsl-knob'), track = host && host.querySelector('.nsl-track');
  const mn = +s.min, mx = +s.max, v = +s.value;
  const probe = document.createElement('div'); probe.style.cssText = 'position:fixed;left:-50px;top:0;width:10px;height:10px;background:var(--switch-on)'; document.body.appendChild(probe);
  const acc = getComputedStyle(probe).backgroundColor; probe.remove();
  return { host: R(host || s), input: R(s), knob: R(knob), track: R(track), f: mx > mn ? (v - mn) / (mx - mn) : 1, v, mn, mx, step: s.step, disabled: s.disabled, accent: acc,
           pressed: !!(host && host.classList.contains('is-pressed')) }; }"""
ANIMS = """(sel)=>{ const s = document.querySelector(sel); const host = s.closest('.nsl') || s.parentElement;
  const an = host.getAnimations({ subtree: true }).map(a => a.transitionProperty || (a.effect && a.effect.getKeyframes ? Object.keys(Object.assign({}, ...a.effect.getKeyframes())).filter(k => !['offset', 'easing', 'composite', 'computedOffset'].includes(k)).join('+') : '?'));
  const bad = [];
  [host, ...host.querySelectorAll('*')].forEach(el => { const cs = getComputedStyle(el); const ps = cs.transitionProperty.split(','), ds = cs.transitionDuration.split(',');
    ps.forEach((p, i) => { p = p.trim(); const d = parseFloat(ds[i % ds.length]) || 0; if(d > 0 && !['transform', 'opacity'].includes(p)) bad.push((el.className || el.tagName) + ':' + p); }); });
  return { an, bad }; }"""

def touch(cdp, kind, x, y):
    cdp.send("Input.dispatchTouchEvent", {"type": kind, "touchPoints": [] if kind == "touchEnd" else [{"x": x, "y": y, "id": 1, "radiusX": 4, "radiusY": 4, "force": 1}]})

def shot(pg):
    return Image.open(io.BytesIO(pg.screenshot())).convert("RGB")
def px(img, x, y, r=1):
    D = 2; pts = [img.getpixel((int(round(x * D)) + dx, int(round(y * D)) + dy)) for dx in range(-r, r + 1) for dy in range(-r, r + 1)]
    return tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
def dist(a, b): return sum((a[i] - b[i]) ** 2 for i in range(3)) ** .5
def rgb(s):
    import re
    m = re.findall(r"[\d.]+", s or ""); return tuple(float(v) for v in m[:3]) if len(m) >= 3 else (0, 0, 0)

def drag_to(cdp, pg, x0, y, x1, n=10, dt=16):
    for i in range(1, n + 1):
        touch(cdp, "touchMove", x0 + (x1 - x0) * i / n, y); pg.wait_for_timeout(dt)

ACCENTS = [("Default", "ink", "dark"), ("Amethyst", "elite", "dark"), ("Silver", "ranger", "dark"), ("Sapphire", "adept", "dark"), ("Default light", "ink", "light")]

def run(br, key):
    ctx, pg, cdp, errs = open_page(br)
    r = pg.evaluate(OPENERS[key].replace("${COMMON}", COMMON))
    sel = SEL[key]
    i0 = pg.evaluate(INFO, sel)
    print("\n  %s: %s" % (key, r))
    if r != "ok" or not i0:
        chk(key + " opens", False, r); ctx.close(); return
    # A: rest shape
    k, t, h = i0["knob"], i0["track"], i0["host"]
    chk(key + " A1 a capsule thumb (w/h 1.35-1.75, 20-30px tall)", k and 1.35 <= k["w"] / k["h"] <= 1.75 and 20 <= k["h"] <= 30, k)
    chk(key + " A2 a thin track (<= 8px) in a >= 44px control", t and t["h"] <= 8 and h["h"] >= 44, {"track": t, "host": h})
    if not (k and t):
        ctx.close(); return
    y = t["cy"]
    # C: value follows the finger (and leaves it at ~50% for the colour checks)
    span = t["w"] - k["w"]; res = []
    touch(cdp, "touchStart", k["cx"], y); pg.wait_for_timeout(60)
    for frac in (.2, .8, .5):
        fx = t["l"] + k["w"] / 2 + frac * span
        drag_to(cdp, pg, pg.evaluate(INFO, sel)["knob"]["cx"], y, fx, n=8); pg.wait_for_timeout(120)
        q = pg.evaluate(INFO, sel); res.append((frac, round(q["f"], 3), round(q["knob"]["cx"] - fx, 1)))
    ok_c = all(abs(a - b) <= .07 and abs(d) <= 4 for a, b, d in res)
    chk(key + " C value and thumb follow the finger (20/80/50%)", ok_c, res)
    touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(700)
    # A3: fill in the theme's colour, following the theme
    for label, acc, mode in ACCENTS:
        pg.evaluate("([a, m])=>{ theme.accent = a; theme.mode = m; applyTheme(); }", [acc, mode]); pg.wait_for_timeout(450)
        q = pg.evaluate(INFO, sel); img = shot(pg)
        fx = (q["track"]["l"] + q["knob"]["l"]) / 2
        got = px(img, fx, q["track"]["cy"], 0); want = rgb(q["accent"])
        chk("%s A3 the fill is the theme's colour: %s" % (key, label), q["knob"]["l"] - q["track"]["l"] > 8 and dist(got, want) <= 60, {"fill": got, "theme": want, "at": fx})
    pg.evaluate("()=>{ theme.accent = 'elite'; theme.mode = 'dark'; applyTheme(); }"); pg.wait_for_timeout(400)
    # B: press -> glass
    q0 = pg.evaluate(INFO, sel); k0 = q0["knob"]; img0 = shot(pg)
    above = k0["cy"] - k0["h"] * .32
    bgx = q0["track"]["r"] - 6 if k0["cx"] < q0["track"]["cx"] else q0["track"]["l"] + 6
    bg = px(img0, bgx, above); solid = px(img0, k0["cx"] + 4, above)
    touch(cdp, "touchStart", k0["cx"], y)
    # read a few times in the swell (a busy machine may draw its first frame late)
    an_press = {"an": [], "bad": []}
    for _ in range(4):
        pg.wait_for_timeout(30); r_ = pg.evaluate(ANIMS, sel)
        an_press["an"] += r_["an"]; an_press["bad"] += r_["bad"]
        if "transform" in r_["an"]: break
    pg.wait_for_timeout(240)
    q1 = pg.evaluate(INFO, sel); k1 = q1["knob"]; img1 = shot(pg)
    chk(key + " B1 a press grows the thumb (>= 1.3x wide and tall)", k1["w"] >= 1.3 * k0["w"] and k1["h"] >= 1.3 * k0["h"], {"rest": [k0["w"], k0["h"]], "pressed": [k1["w"], k1["h"]]})
    glass = px(img1, k0["cx"] + 4, above)
    chk(key + " B2 the pressed thumb is clear: the card shows through it", dist(solid, bg) > 60 and dist(glass, bg) <= 45, {"rest knob": solid, "card": bg, "pressed": glass})
    inside = px(img1, k1["cx"] - 6, q1["track"]["cy"], 0)
    chk(key + " B3 the fill shows through the glass", dist(inside, rgb(q1["accent"])) <= 90, {"through": inside, "theme": q1["accent"]})
    chk(key + " E1 a press animates transform/opacity only, and does animate", an_press["an"] and all(a in ("transform", "opacity") for a in an_press["an"]) and "transform" in an_press["an"] and not an_press["bad"], an_press)
    # D: overshoot both ends
    drag_to(cdp, pg, k1["cx"], y, q1["track"]["r"] + 70, n=12); pg.wait_for_timeout(150)
    qr = pg.evaluate(INFO, sel)
    drag_to(cdp, pg, q1["track"]["r"] + 70, y, q1["track"]["l"] - 70, n=20); pg.wait_for_timeout(150)
    ql = pg.evaluate(INFO, sel)
    touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(40)
    an_rel = pg.evaluate(ANIMS, sel)
    pg.wait_for_timeout(900)
    qe = pg.evaluate(INFO, sel)
    chk(key + " D1 past the right end the thumb goes past the track's end", qr["knob"]["r"] >= t["r"] + 3, {"knob r": qr["knob"]["r"], "track r": t["r"]})
    chk(key + " D2 past the left end too", ql["knob"]["l"] <= t["l"] - 3, {"knob l": ql["knob"]["l"], "track l": t["l"]})
    chk(key + " D3 let go, it is back inside the track at its rest size", qe["knob"]["l"] >= t["l"] - .5 and abs(qe["knob"]["w"] - k0["w"]) <= 1 and abs(qe["knob"]["h"] - k0["h"]) <= 1 and not qe["pressed"], qe["knob"])
    chk(key + " E2 the release animates transform/opacity only", an_rel["an"] and all(a in ("transform", "opacity") for a in an_rel["an"]) and not an_rel["bad"], an_rel)
    # F: the touch band
    q = pg.evaluate(INFO, sel); before = q["v"]
    target = q["track"]["l"] + q["knob"]["w"] / 2 + .7 * (q["track"]["w"] - q["knob"]["w"])
    touch(cdp, "touchStart", target, q["track"]["cy"] - 20); pg.wait_for_timeout(40)
    touch(cdp, "touchMove", target + 6, q["track"]["cy"] - 20); pg.wait_for_timeout(60)
    touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(600)
    q2 = pg.evaluate(INFO, sel)
    chk(key + " F a touch 20px above the track's middle takes the slider", abs(q2["f"] - .7) <= .1 and q2["v"] != before, {"before": before, "after": q2["v"], "f": q2["f"]})
    # G: Reduce motion
    pg.evaluate("()=>{ theme.reduceMotion = true; applyTheme(); }"); pg.wait_for_timeout(300)
    q = pg.evaluate(INFO, sel); kk = q["knob"]
    touch(cdp, "touchStart", kk["cx"], q["track"]["cy"]); pg.wait_for_timeout(30)
    an_rm = pg.evaluate(ANIMS, sel); pg.wait_for_timeout(250)
    qq = pg.evaluate(INFO, sel)
    touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(300)
    chk(key + " G Reduce motion: no grow, no transform animation", abs(qq["knob"]["w"] - kk["w"]) <= .5 and "transform" not in an_rm["an"] and qq["pressed"], {"rest": kk["w"], "pressed": qq["knob"]["w"], "anims": an_rm["an"], "pressedClass": qq["pressed"]})
    pg.evaluate("()=>{ theme.reduceMotion = false; applyTheme(); }"); pg.wait_for_timeout(300)
    # I: an upright touch changes nothing
    q = pg.evaluate(INFO, sel); v0 = q["v"]
    sx = q["track"]["l"] + .25 * q["track"]["w"]
    touch(cdp, "touchStart", sx, q["track"]["cy"]); pg.wait_for_timeout(30)
    for i in range(1, 9): touch(cdp, "touchMove", sx + i * .5, q["track"]["cy"] - i * 14); pg.wait_for_timeout(16)
    touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(500)
    q3 = pg.evaluate(INFO, sel)
    chk(key + " I an upright drag leaves the value and lets go of the thumb", q3["v"] == v0 and not q3["pressed"], {"before": v0, "after": q3["v"], "pressed": q3["pressed"]})
    # H: long tasks at 4x CPU during a drag
    q = pg.evaluate("(sel)=>{ const s = document.querySelector(sel); (s.closest('.sect') || s.parentElement).scrollIntoView({ block: 'center' }); return 1; }", sel); pg.wait_for_timeout(300)
    q = pg.evaluate(INFO, sel)
    # the page's own launch warm-ups (badge strikes, flip-books: idle callbacks) are not the slider's: wait for a quiet page first
    # (2s with no long task, 30s at most), so what is counted is the drag
    for _ in range(15):
        pg.evaluate("()=>{ window.__lt = []; }"); pg.wait_for_timeout(2000)
        if not pg.evaluate("()=>window.__lt.length"): break
    # three drags (this machine is shared and timing-sensitive): the best one is the slider's, every one is printed
    runs = []
    for _ in range(3):
        q = pg.evaluate(INFO, sel)
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        pg.evaluate("()=>{ window.__lt = []; }")
        kx = q["knob"]["cx"]; L, Rr = q["track"]["l"] + 20, q["track"]["r"] - 20
        touch(cdp, "touchStart", kx, q["track"]["cy"]); pg.wait_for_timeout(30)
        drag_to(cdp, pg, kx, q["track"]["cy"], Rr, n=12); drag_to(cdp, pg, Rr, q["track"]["cy"], L, n=24); drag_to(cdp, pg, L, q["track"]["cy"], (L + Rr) / 2, n=12)
        touch(cdp, "touchEnd", 0, 0); pg.wait_for_timeout(600)
        runs.append([round(d) for d in pg.evaluate("()=>window.__lt.slice()")])
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 1})
        if all(d <= 50 for d in runs[-1]): break
        pg.wait_for_timeout(1500)
    lt = min(runs, key=lambda r: max(r or [0]))
    print("    H long tasks per drag:", runs)
    chk(key + " H no long task over 50ms in a drag at 4x CPU", all(d <= 50 for d in lt), {"longtasks": [round(d) for d in lt]})
    chk(key + " no page errors", not errs, errs)
    ctx.close()

with sync_playwright() as pw:
    srv, URL = g["serve"]()
    br = pw.chromium.launch(executable_path=g["CHROME"])
    for key in OPENERS:
        if ONLY and key not in ONLY: continue
        run(br, key)
    br.close()
print("\nALL PASS" if ok else "\n%d FAILED" % fails)
sys.exit(0 if ok else 1)
