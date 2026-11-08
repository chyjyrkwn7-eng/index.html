"""Stills of the hundo grade box and everything that wears it, for a before / after: per class (Fire Code and the academy) and
per effect, at 2x -
  box-<cls>-<fx>.png      a results screen's grade box and the XP card under it (the real classes and markup, the box tinted
                          by hfxTintGrade as the landing does it), settled
  tile-<cls>.png          Customize's Hundo effect page (every tile)
  spot-<cls>-<fx>.png     the unlock pop-up (playUnlockSpotlight), the effect's small box playing in it, a moment in
  card-<cls>-<fx>.png     the effect's detail card (showUnlockDetail), its miniature results screen playing
  python3 tools/shoot-hundobox.py OUTDIR [--against FILE] [--only box,tile,spot,card] [W H]
spot and card are a moment in (about 2.6s), not paused."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
AG = []
ONLY = ["box", "tile", "spot", "card"]
if "--against" in args:
    i = args.index("--against"); AG = ["--against", args[i + 1]]; del args[i:i + 2]
if "--only" in args:
    i = args.index("--only"); ONLY = args[i + 1].split(","); del args[i:i + 2]
OUT = os.path.abspath(args[0]); W = int(args[1]) if len(args) > 1 else 440; H = int(args[2]) if len(args) > 2 else 956
sys.argv = [sys.argv[0]] + AG
src = open(os.path.join(HERE, "check-b384-extspr.py")).read().split("\nsrv, port = serve()")[0]
G = {"__file__": os.path.join(HERE, "check-b384-extspr.py"), "__name__": "shootbox"}
exec(src, G)
os.makedirs(OUT, exist_ok=True)
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
BOX = r"""(id) => {
  const stage = document.getElementById('stage');
  document.body.classList.remove('sky-home');
  const el = (tag, cls, txt, parent) => { const e = document.createElement(tag); if(cls) e.className = cls; if(txt != null) e.textContent = txt; if(parent) parent.appendChild(e); return e; };
  const sc = el('div', 'rs-screen'); sc.id = 'shootbox'; sc.style.cssText = 'padding:14px 18px;width:100%;box-sizing:border-box';
  const gr = el('div', 'rs-card rs-grade is-perfect rs-graded', null, sc);
  el('p', 'rs-kicker', 'Grade', gr);
  const row = el('div', 'rs-grade-row', null, gr);
  const pct = el('span', 'rs-pct pct perfect', null, row); gradePctMarkup(pct, 100);
  const side = el('div', 'rs-grade-side', null, row);
  rsPair(el('p', 'rs-grade-frac', null, side), 88, 88);
  el('p', 'rs-grade-sub slabel', 'right on the first try', side);
  const bu = el('div', 'unit-breakdown rs-byunit is-single', null, gr);
  const r = el('div', 'unit-breakdown-row', null, bu); const top = el('div', 'unit-breakdown-top', null, r);
  el('span', 'unit-breakdown-name', 'Chapter 1: Scope and Administration', top);
  const tr = el('div', 'unit-breakdown-track', null, r);
  const fill = el('div', 'unit-breakdown-fill full is-gold', null, tr); fill.style.width = '100%';
  const xp = el('div', 'rs-card rs-xp', null, sc);
  el('p', 'rs-kicker', 'XP earned', xp);
  [['Correct answers', '+880'], ['Hundo', '+100']].forEach(([a, b]) => { const l = el('div', 'rs-line', null, xp); l.style.cssText = 'display:flex;justify-content:space-between;padding:.2rem 0'; el('span', '', a, l); el('b', '', b, l); });
  stage.replaceChildren(sc);
  if(id !== 'confetti') hfxTintGrade(gr, id);
  return true;
}"""
srv, port = G["serve"]()
with G["sync_playwright"]() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    for cls in ("ifc", "academy"):
        init = G["INIT"] if cls == "ifc" else G["INIT"].replace("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');", "")
        ctx = br.new_context(viewport={"width": W, "height": H}, device_scale_factor=2)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
        pg.add_init_script(init)
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=G["BODY"]))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2800)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
        print(cls, pg.evaluate("() => window.NOVA_CLASS"), flush=True)
        if "box" in ONLY:
            for fx in IDS:
                pg.evaluate(BOX, fx); pg.wait_for_timeout(400)
                pg.locator("#shootbox").screenshot(path=os.path.join(OUT, "box-%s-%s.png" % (cls, fx)))
        if "tile" in ONLY:
            pg.evaluate("() => { document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); showCustomize('fx'); }"); pg.wait_for_timeout(900)
            pg.screenshot(path=os.path.join(OUT, "tile-%s.png" % cls))
        if "spot" in ONLY:
            for fx in IDS[1:]:
                pg.evaluate("(fx) => { document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); playUnlockSpotlight(hundoFxUnlockItem(fx), 1, 1, () => {}); }", fx)
                pg.wait_for_timeout(3600)
                pg.screenshot(path=os.path.join(OUT, "spot-%s-%s.png" % (cls, fx)))
        if "card" in ONLY:
            for fx in IDS[1:]:
                pg.evaluate("(fx) => { document.querySelectorAll('.invite-overlay,.rs-spot').forEach(e => e.remove()); showUnlockDetail(hundoFxDetail(fx)); }", fx)
                pg.wait_for_timeout(2600)
                pg.screenshot(path=os.path.join(OUT, "card-%s-%s.png" % (cls, fx)))
        if errs: print("ERRORS", errs[:3])
        ctx.close()
    br.close()
print("done")
