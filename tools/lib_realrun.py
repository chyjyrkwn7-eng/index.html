"""Shared driver for the grade-card tools: a REAL results screen (a drill run through summarize(), as check-results / record-hundo
do it) in the Fire Code class or the academy, on the recorder's own clock (every animation seeked, so a still is a chosen moment).
  open_run(br, cls, W, H, fx, missN=0, mode='drill')  -> (ctx, pg, errs)  the run is under way, the clock installed
  advance(pg, seconds)                                  step the page's clock
  wait_fx(pg)                                           step until the effect has started
"""
import importlib.util, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); WT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location("cb", HERE + "/check-behaviour.py")
cb = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(cb)
_r = open(HERE + "/check-results.py").read()
_i = _r.index('SETUP = """') + len('SETUP = """'); SETUP = _r[_i:_r.index('"""', _i)]
_rec = open(HERE + "/record-hundo.py").read()
_j = _rec.index('CLOCK = r"""') + len('CLOCK = r"""'); CLOCK = _rec[_j:_rec.index('"""', _j)]

def open_run(br, cls, W, H, fx, missN=0, mode="drill", retake=False, unit=None, dpr=2, run=True):
    ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=dpr)
    acct = cb.USED_ACCOUNT
    if cls == "ifc":
        a = json.loads(acct); a["publicId"] = "xph5b57jbp5a"; a["novaMet"] = 99; acct = json.dumps(a)
        ctx.add_init_script("try{localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');"
                            "localStorage.setItem('class26e.weekrecap.v1','9999-12-31');localStorage.setItem('class26e.savecode.card','1');"
                            "['intro.seen','unithold.tip','daily.seen','weekrecap.v1','savecode.card'].forEach(k=>localStorage.setItem('class26e.ifc.'+k, k==='weekrecap.v1'?'9999-12-31':'9'));"
                            "if(!localStorage.getItem('class26e.ifc.drill.v1')) localStorage.setItem('class26e.ifc.drill.v1', %s);}catch(e){}" % json.dumps(acct))
    ctx.add_init_script("try{localStorage.setItem('class26e.freshstart','1');localStorage.setItem('class26e.frame.ok','go-live-1');localStorage.setItem('class26e.intro.seen','9');localStorage.setItem('class26e.unithold.tip','1');localStorage.setItem('class26e.penal55124.seen','1');localStorage.setItem('class26e.penal124256.seen','1');localStorage.setItem('class26e.penal256578.seen','1');"
                        "localStorage.setItem('class26e.drill.v1', %s);}catch(e){}" % json.dumps(acct))
    pg = cb.open_page(ctx); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.goto(cb.URL); pg.wait_for_timeout(2600)
    pg.evaluate("()=>{document.getElementById('splashscreen')?.remove(); __stub();}")
    pg.evaluate(SETUP)
    pg.evaluate("""(fx) => { store.lifetime.perfectTests = 600; store.hundoFx = fx;
      const u = pendingHomeUnlocks ? pendingHomeUnlocks() : null; if(u) markUnlocksShown(u.chars, u.banners, u.fx); saveStore();
      try{ hfxWarm(fx); }catch(e){}
      window.__fxAt = 0; const real = playHundoFx; window.playHundoFx = function(a, b){ window.__fxAt = performance.now(); return real(a, b); };
      const rc = celebrate; window.celebrate = function(a, b){ window.__fxAt = performance.now(); return rc(a, b); }; }""", fx)
    pg.wait_for_timeout(1800)
    pg.evaluate("() => { document.getElementById('splashscreen')?.remove(); }")
    pg.evaluate(CLOCK)
    if run:
        u = unit or pg.evaluate("() => topicsIn(QUESTIONS)[0]") if cls == "ifc" else (unit or "Identity Crimes")
        pg.evaluate("([u, m, mode, rt]) => __run(u, m, mode, rt)", [u, missN, mode, retake])
    return ctx, pg, errs

STEP = 1 / 10   # the page's clock moves in tenths of a second: every animation is seeked, so a still is the same; 30 steps a second is three times the wait
def advance(pg, seconds):
    n = max(1, int(round(seconds / STEP)))
    for _ in range(n):
        pg.evaluate("async (d) => { await __clk.advance(d); }", 1000 * seconds / n)

def wait_fx(pg, limit=60):
    k = 0
    while k < limit / STEP and not pg.evaluate("() => window.__fxAt > 0"):
        pg.evaluate("async (d) => { await __clk.advance(d); }", 1000 * STEP); k += 1
    return k * STEP

# every part of the grade card and the XP card beside it, as computed on the page (shape, not label strings)
READ_GRADE = r"""() => {
  const g = document.querySelector('.rs-grade'); if(!g) return null;
  const P = (e, props) => { if(!e) return null; const cs = getComputedStyle(e), r = e.getBoundingClientRect(); const o = { w: Math.round(r.width*10)/10, h: Math.round(r.height*10)/10 };
    props.forEach(p => o[p] = cs[p]); return o; };
  const T = ['backgroundColor','backgroundImage','borderTopWidth','borderTopColor','boxShadow','borderRadius','filter','opacity'];
  const F = ['fontFamily','fontSize','fontWeight','letterSpacing','color','webkitTextFillColor','backgroundImage','filter','textShadow','lineHeight'];
  const vars = {}; ['--hfx-b','--hfx-g1','--hfx-g2','--hfx-g3'].forEach(k => vars[k] = g.style.getPropertyValue(k).trim());
  return { cls: g.className, vars, card: P(g, T.concat(['paddingTop','paddingLeft'])), xp: P(document.querySelector('.rs-xp'), T.concat(['paddingTop','paddingLeft'])),
    kicker: P(g.querySelector('.rs-kicker'), F), pct: P(g.querySelector('.rs-pct'), F), sign: P(g.querySelector('.rs-pct-sign'), F),
    frac: P(g.querySelector('.rs-grade-frac'), F), sub: P(g.querySelector('.rs-grade-sub'), F), stamps: P(g.querySelector('.rs-stamps'), F), line: P(g.querySelector('.rs-retake-line'), F),
    uname: P(g.querySelector('.unit-breakdown-name'), F), track: P(g.querySelector('.unit-breakdown-track'), T), fill: P(g.querySelector('.unit-breakdown-fill'), T.concat(['background','backgroundColor'])),
    tint: P(g.querySelector('.hfx-tint'), T) };
}"""
