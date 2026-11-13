"""Build 384.94: the class button is option C, the medallion - exactly the one that was picked.
Madison, shown three looks behind ?classbtn=a|b|c (branch claude/b384-classbtn, 5f85d51): "Option c for the class thing."

  K1  the button on Home, both classes, on an iPhone 17 Pro Max (installed), an iPad Pro 11" and a laptop, is pixel for pixel the
      picked preview (5f85d51 loaded with ?classbtn=c): the same coin, bezel, glow and mark (mean channel difference under 1.0,
      no pixel more than 24 out - antialiasing only). Reduce motion on both, so nothing behind it moves.
  K2  the mark on the button is the coin's drawing (classBtnIcon "button": its own cbx ids, the light colours) and the button's
      background is the enamel coin (its bezel colour is in the computed background);
  K3  the class list (the button opened, with both classes enrolled) shows the other class in its full-colour mark;
  K4  nothing is left of the choice: ?classbtn=a in the address sets no data-classbtn and changes no pixel.
Run:  python3 tools/check-b384-classbtn.py [--against REV|DIR]   (--against origin/main must FAIL K1-K3)"""
import importlib.util, io, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("glitches", os.path.join(HERE, "check-b384-glitches.py"))
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)   # takes --against from sys.argv
from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat
chk = G.chk
PICK = subprocess.run(["git", "-C", G.REPO, "show", "5f85d51:index.html"], check=True, capture_output=True).stdout.decode("utf-8")
PICK_BODIES = {}
def pick_body(ins):
    if ins not in PICK_BODIES:
        v = {"top": "%dpx" % ins[0], "right": "%dpx" % ins[1], "bottom": "%dpx" % ins[2], "left": "%dpx" % ins[3]}
        PICK_BODIES[ins] = G.INSET_RE.sub(lambda m: v[m.group(1)], PICK)
    return PICK_BODIES[ins]
QUIET = "()=>{ theme.reduceMotion = true; try{ applyTheme(); }catch(e){} try{ homeUnlocksOwed=()=>false; }catch(e){} showHome(); }"
RECT = "()=>{ const b = document.querySelector('.class-bubble'); if(!b) return null; const r = b.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; }"
def shot(pg):
    r = pg.evaluate(RECT)
    if not r: return None, None
    m = 18   # the glow
    clip = {"x": max(0, r["x"] - m), "y": max(0, r["y"] - m), "width": r["w"] + 2 * m, "height": r["h"] + 2 * m}
    return Image.open(io.BytesIO(pg.screenshot(clip=clip))).convert("RGB"), r
def diff(a, b):
    if a is None or b is None or a.size != b.size: return {"mean": 999, "max": 999, "sizes": [a and a.size, b and b.size]}
    d = ImageChops.difference(a, b)
    return {"mean": round(sum(ImageStat.Stat(d).mean) / 3, 2), "max": max(e[1] for e in d.getextrema())}
def load(br, dev, cls, pick=False, query=""):
    pg = G.open_dev(br, dev, inits=[G.seed_init(cls)], dsf=2)
    if pick or query:
        w, h, sw, sh, ins, ua, touch, inst = G.DEV[dev]
        b = pick_body(ins) if pick else G.body(ins)
        pg.unroute("**/index.html")
        pg.route("**/index.html*", lambda r, q, b=b: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=b))
        pg.goto(G.URL + ("?classbtn=c" if pick else query)); pg.wait_for_timeout(3200)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    pg.evaluate(QUIET); pg.wait_for_timeout(1800); G.clear_popups(pg); pg.wait_for_timeout(400)
    return pg

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    out = os.environ.get("OUT")
    for cls in ["academy", "ifc"]:
        for dev in ["promax", "ipad", "laptop"]:
            tag = "%s %s" % (cls, dev)
            pg = load(br, dev, cls); a, ra = shot(pg)
            pp = load(br, dev, cls, pick=True); b, rb = shot(pp)
            if out and a is not None and b is not None:
                os.makedirs(out, exist_ok=True); a.save(os.path.join(out, "%s-%s-build.png" % (cls, dev))); b.save(os.path.join(out, "%s-%s-picked.png" % (cls, dev)))
            d = diff(a, b)
            chk("[%s] K1 the button is the picked option C, pixel for pixel (mean %.2f, max %s)" % (tag, d["mean"], d["max"]),
                d["mean"] < 1.0 and d["max"] <= 24 and ra == rb, {"diff": d, "build": ra, "picked": rb, "picked has data-classbtn": pp.evaluate("()=>document.documentElement.getAttribute('data-classbtn')")})
            if dev == "promax":
                k2 = pg.evaluate("""()=>{ const b = document.querySelector('.class-bubble'); const svg = b && b.querySelector(':scope > svg');
                  const ids = svg ? [...svg.querySelectorAll('[id]')].map(e => e.id) : [];
                  const bg = b ? getComputedStyle(b).backgroundImage : '';
                  const bez = b ? getComputedStyle(b).getPropertyValue('--bezel').trim() : '';
                  return { ids, coin: /radial-gradient/.test(bg) && !!bez, bez }; }""")
                chk("[%s] K2 the mark is the coin's drawing (its own cbx ids) on the enamel coin" % tag,
                    k2["ids"] and all(i.startswith("cbx") for i in k2["ids"]) and k2["coin"], k2)
                # K3 both classes enrolled: open the stack, read the other class's mark
                pg.evaluate("()=>{ try{ localStorage.setItem('class26e.enrolled', JSON.stringify(['ifc'])); }catch(e){} showHome(); }"); pg.wait_for_timeout(1400)
                pg.evaluate("()=>{ const b = document.querySelector('.class-bubble'); b && b.click(); }"); pg.wait_for_timeout(900)
                k3 = pg.evaluate("""()=>{ const it = [...document.querySelectorAll('.class-stack-item')].filter(x => !x.classList.contains('is-add'));
                  return it.map(x => { const svg = x.querySelector('svg'); const ids = svg ? [...svg.querySelectorAll('[id]')].map(e => e.id) : [];
                    const fills = svg ? [...svg.querySelectorAll('stop')].map(s => s.getAttribute('stop-color')) : []; return { cls: x.className, ids, fills }; }); }""")
                full = {"ifc": "#FF6B35", "academy": "#5470F2"}
                chk("[%s] K3 the class list shows the other class in its full-colour mark" % tag,
                    len(k3) >= 1 and all(x["ids"] and all(i.startswith("cbx") for i in x["ids"]) and any(f in x["fills"] for f in full.values()) for x in k3), k3)
                # K4 the address switch is gone
                pq = load(br, dev, cls, query="?classbtn=a"); c, rc = shot(pq)
                d4 = diff(a, c)
                chk("[%s] K4 ?classbtn=a changes nothing (no data-classbtn, mean %.2f)" % (tag, d4["mean"]),
                    pq.evaluate("()=>document.documentElement.getAttribute('data-classbtn')") is None and d4["mean"] < 1.0, {"attr": pq.evaluate("()=>document.documentElement.getAttribute('data-classbtn')"), "diff": d4})
                chk("[%s] no page errors" % tag, not (pg.errs or pq.errs), (pg.errs + pq.errs)[:3])
                pq.ctx.close()
            pg.ctx.close(); pp.ctx.close()
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
