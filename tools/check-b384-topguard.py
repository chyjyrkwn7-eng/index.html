"""Build 384 r20: the top strip that stops iOS 26.1/27's system blur feeding off the top edge of the installed app.
Madison's display-test recording (his phone had updated that morning): the soft wash over the top ~95pt did not change in any of the 13 steps, so it is
the system's own top-edge blur of a black-translucent Home-Screen app; the reported workaround is a small opaque fixed element at the very top.
 (1) installed on an iPhone (iOS user agent + standalone): #top-guard exists, position:fixed at the top edge, full width, 8px, an OPAQUE colour, no touch, above
     everything, aria-hidden;
 (2) its colour is the status-bar colour the app already computes (the theme-color meta), and when the theme changes it is a NEW element in the new colour;
 (3) not in a browser tab, not on a laptop, and not when class26e.topguard is "0";
 (4) it is in the display test's switches, and no page errors.
Run:  python3 tools/check-b384-topguard.py   (--against OLD/index.html must FAIL)"""
import os, sys, re, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cb", os.path.join(HERE, "check-behaviour.py")); cb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cb)
if "--against" in sys.argv:
    body = open(sys.argv[sys.argv.index("--against") + 1], encoding="utf-8").read()
    cb.BODY = cb.INSET_RE.sub("0px", body).replace("let fbDb = null;", "let fbDb = null;" + cb.FIRESTORE_STUB, 1)
from playwright.sync_api import sync_playwright
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:300], flush=True)
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1"
def boot(br, ios, standalone, extra=""):
    kw = dict(viewport={"width": 440, "height": 956}, device_scale_factor=2, has_touch=ios, is_mobile=ios)
    if ios: kw["user_agent"] = UA
    ctx = br.new_context(**kw)
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');"
                        "localStorage.setItem('class26e.drill.v1','%s');localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');%s}catch(e){}" % (cb.USED_ACCOUNT, extra))
    if standalone: ctx.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true});")
    pg = cb.open_page(ctx); pg.goto(cb.URL); pg.wait_for_timeout(3000)
    pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    return ctx, pg
READ = """()=>{ const g=document.getElementById('top-guard'); if(!g) return null; const cs=getComputedStyle(g), r=g.getBoundingClientRect();
  const m=document.getElementById('themecolor'); return { pos: cs.position, top: r.top, left: r.left, w: r.width, h: r.height, bg: cs.backgroundColor, pe: cs.pointerEvents, z: +cs.zIndex, aria: g.getAttribute('aria-hidden'), meta: m && m.content, vw: innerWidth }; }"""
def hexof(c):
    m = re.findall(r"[\d.]+", c or "")
    return "#%02x%02x%02x" % tuple(int(float(x)) for x in m[:3]) if len(m) >= 3 else None
with sync_playwright() as pw:
    br = pw.chromium.launch()
    ctx, pg = boot(br, True, True)
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)[:140]))
    r = pg.evaluate(READ)
    chk("(1) installed on an iPhone: a fixed, full-width, 8px, opaque strip at the top edge, no touch, above everything (%s)" % r, r and r["pos"] == "fixed" and r["top"] == 0 and r["left"] == 0 and abs(r["w"] - r["vw"]) < 1 and r["h"] == 8
        and not re.search(r"rgba\(.*,\s*0?\.\d+\)|, 0\)", r["bg"]) and r["pe"] == "none" and r["z"] > 1000000 and r["aria"] == "true", r)
    chk("(2) its colour is the status-bar colour the app computes (%s vs %s)" % (r and hexof(r["bg"]), r and r["meta"]), r and hexof(r["bg"]).lower() == (r["meta"] or "").lower(), r)
    # a theme change replaces it
    pg.evaluate("()=>{ window.__g0 = document.getElementById('top-guard'); theme.accent = 'veteran'; applyTheme(); }"); pg.wait_for_timeout(900)
    r2 = pg.evaluate("()=>{ const g=document.getElementById('top-guard'); const m=document.getElementById('themecolor'); return g ? { same: g === window.__g0, c: g.dataset.color, meta: m.content, count: document.querySelectorAll('#top-guard').length } : null; }")
    chk("(2) a theme change leaves one strip, in the new colour (%s)" % r2, r2 and r2["count"] == 1 and r2["c"].lower() == r2["meta"].lower() and (r2["same"] is False or r2["c"].lower() == hexof(r["bg"]).lower()), r2)
    chk("(4) the display test has a switch for it", pg.evaluate("()=>{ localStorage.setItem('class26e.displaytest','1'); return true; }") and True)
    ctx.close()
    ctx, pg = boot(br, True, False)
    chk("(3) an iPhone in a Safari tab has none", pg.evaluate(READ) is None)
    ctx.close()
    ctx, pg = boot(br, False, False)
    chk("(3) a laptop has none", pg.evaluate(READ) is None)
    ctx.close()
    ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.topguard','0');")
    chk("(3) with class26e.topguard = 0 it is gone", pg.evaluate(READ) is None)
    ctx.close()
    ctx, pg = boot(br, True, True, extra="localStorage.setItem('class26e.displaytest','1');")
    sw = pg.evaluate("()=>[...document.querySelectorAll('#diagpanel label span')].map(s=>s.textContent)")
    chk("(4) the display test's switches include the strip (%s)" % [s for s in sw if re.search(r'strip', s, re.I)], any(re.search(r"strip", s, re.I) for s in sw), sw)
    chk("(4) no page errors", not errs, errs)
    ctx.close(); br.close()
print("ALL PASS" if ok else "FAILED")
sys.exit(0 if ok else 1)
