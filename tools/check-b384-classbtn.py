"""Build 384.98 (was 384.94): the class button is option A, the lit ring - exactly the one Madison saw.
Madison, shown three looks behind ?classbtn=a|b|c (branch claude/b384-classbtn, 5f85d51): "Option c for the class thing." (384.94,
the medallion), and then, with C live: "I don't like the class button after all. Try option a, the lit ring." (384.98)

  K1  the button on Home, both classes, on an iPhone 17 Pro Max (installed), an iPad Pro 11" and a laptop, is pixel for pixel the
      preview he saw (5f85d51 loaded with ?classbtn=a): the same ring, glow, rim and mark (mean channel difference under 1.0, no
      pixel more than 24 out - antialiasing only). Reduce motion on both, so nothing behind it moves. The new dot (384.98, a
      .new-dot child of the button while the class list has something new) is hidden by rule on both sides, as is the old one
      (the button's ::after), so this compares the button and not the dot.
  K1b the same with the button's "something new" state on, on both sides (the 329 ring round it, still under Reduce motion), the
      dot hidden by rule: the lit ring is unchanged under the dot's state too.
  K1c ...and with the dot shown (this build), the dot is there on A's button: drawn, on the button's corner on the 45-degree line.
  K2  the mark on the button is the class's full-colour drawing (classBtnIcon: its own cbx ids, the class list's colours) and the
      button's background is the lit ring (--cb-ring, the class's colour lifted towards white, set and in the computed background);
  K3  the class list (the button opened, with both classes enrolled) shows the other class in its full-colour mark;
  K4  nothing is left of the choice: ?classbtn=c in the address sets no data-classbtn and changes no pixel.
Run:  python3 tools/check-b384-classbtn.py [--against REV|DIR]   (--against 384.94 / 384.95, the medallion, must FAIL K1, K1b, K2)"""
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
        pg.goto(G.URL + ("?classbtn=a" if pick else query)); pg.wait_for_timeout(3200)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
    pg.evaluate(QUIET); pg.wait_for_timeout(1800); G.clear_popups(pg)
    # the picked build (5f85d51, from 384.88) still opens its intro pop-up (#intro-pop, a full-screen dim) over Home for this fixture;
    # it is not the button and comes off on both sides, so only the button is compared
    # (a rule, not a removal: it can open after any one moment the harness picks, as it did on the laptop)
    pg.add_style_tag(content="#intro-pop, .intro-pop{ display:none !important; }"); pg.wait_for_timeout(400)
    return pg
# the new dot (384.98) and the old one (the button's ::after) off, by rule, on both sides: the button is compared, not the dot
# (specific enough to beat both builds' own "has-new" rules for the dot, which are !important too)
NODOT = ("html body .class-bubble-wrap.class-bubble-wrap .class-bubble.class-bubble > .new-dot, "
         "html body .class-bubble-wrap.class-bubble-wrap .class-bubble.class-bubble::after{ display:none !important; }")
def nodot(pg):
    pg.evaluate("(c)=>{ const s = document.createElement('style'); s.id = '__nodot'; s.textContent = c; document.body.appendChild(s); }", NODOT)
    pg.wait_for_timeout(250)
def has_new(pg):
    pg.evaluate("()=>{ try{ newClassPulseOn = true; }catch(e){} showHome(); }"); pg.wait_for_timeout(1800); G.clear_popups(pg)
    pg.evaluate("()=>{ const w = document.querySelector('.class-bubble-wrap'); if(w) w.classList.add('has-new'); }"); pg.wait_for_timeout(400)

with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path=G.CHROME)
    out = os.environ.get("OUT")
    for cls in ["academy", "ifc"]:
        for dev in ["promax", "ipad", "laptop"]:
            tag = "%s %s" % (cls, dev)
            pg = load(br, dev, cls); nodot(pg); a, ra = shot(pg)
            pp = load(br, dev, cls, pick=True); nodot(pp); b, rb = shot(pp)
            if out and a is not None and b is not None:
                os.makedirs(out, exist_ok=True); a.save(os.path.join(out, "%s-%s-build.png" % (cls, dev))); b.save(os.path.join(out, "%s-%s-picked.png" % (cls, dev)))
            d = diff(a, b)
            chk("[%s] K1 the button is option A as he saw it, pixel for pixel, the dot hidden on both (mean %.2f, max %s)" % (tag, d["mean"], d["max"]),
                d["mean"] < 1.0 and d["max"] <= 24 and ra == rb, {"diff": d, "build": ra, "picked": rb, "picked has data-classbtn": pp.evaluate("()=>document.documentElement.getAttribute('data-classbtn')")})
            if dev in ("promax", "ipad"):
                # K1b: the button's "something new" state on both sides, the dot still hidden by rule
                has_new(pg); has_new(pp)
                a2, ra2 = shot(pg); b2, rb2 = shot(pp); d2 = diff(a2, b2)
                chk("[%s] K1b with something new on both (the 329 ring), the dot hidden: still A, pixel for pixel (mean %.2f, max %s)" % (tag, d2["mean"], d2["max"]),
                    d2["mean"] < 1.0 and d2["max"] <= 24 and ra2 == rb2, {"diff": d2, "build": ra2, "picked": rb2})
                # K1c: the dot shown on this build - on A's button, drawn, on its corner
                pg.evaluate("()=>document.getElementById('__nodot')?.remove()"); pg.wait_for_timeout(300)
                k1c = pg.evaluate("""()=>{ const b = document.querySelector('.class-bubble'); const d = b && b.querySelector(':scope > .new-dot');
                  let w = 0, cx = 0, cy = 0, vis = false;
                  if(d && getComputedStyle(d).display !== 'none'){ const r = d.getBoundingClientRect(); w = r.width; cx = r.left + r.width / 2; cy = r.top + r.height / 2;
                    const a = getComputedStyle(d, '::after'); vis = a.content !== 'none' && /radial-gradient/.test(a.backgroundImage); }
                  else if(b){ const a = getComputedStyle(b, '::after'); if(a.content !== 'none' && a.display !== 'none'){ const hb = b.getBoundingClientRect(); w = parseFloat(a.width);
                    cx = hb.left + b.clientLeft + parseFloat(a.left) + w / 2; cy = hb.top + b.clientTop + parseFloat(a.top) + w / 2; vis = true; } }
                  const hb = b ? b.getBoundingClientRect() : { right: 0, top: 0, width: 0 };
                  return { w, vis, dx: Math.round((hb.right - cx) * 10) / 10, dy: Math.round((cy - hb.top) * 10) / 10, hw: Math.round(hb.width) }; }""")
                chk("[%s] K1c the new dot is on A's button: drawn (%.0fpx), on its corner on the 45-degree line (%s, %s)" % (tag, k1c["w"], k1c["dx"], k1c["dy"]),
                    k1c["vis"] and 8 <= k1c["w"] <= 10.5 and abs(k1c["dx"] - k1c["dy"]) <= 1.5 and 0 <= k1c["dx"] <= k1c["hw"] / 3, k1c)
            if dev == "promax":
                pg.evaluate("()=>{ document.getElementById('__nodot')?.remove(); try{ newClassPulseOn = false; }catch(e){} showHome(); }"); pg.wait_for_timeout(1500)
                k2 = pg.evaluate("""()=>{ const b = document.querySelector('.class-bubble'); const svg = b && b.querySelector(':scope > svg');
                  const ids = svg ? [...svg.querySelectorAll('[id]')].map(e => e.id) : [];
                  const fills = svg ? [...svg.querySelectorAll('stop')].map(s => s.getAttribute('stop-color')) : [];
                  const cs = b ? getComputedStyle(b) : null;
                  const ring = cs ? cs.getPropertyValue('--cb-ring').trim() : '';
                  return { ids, fills, ring, lit: !!ring && /radial-gradient/.test(cs.backgroundImage), coin: cs ? cs.getPropertyValue('--bezel').trim() : '' }; }""")
                full = {"ifc": "#FF6B35", "academy": "#5470F2"}
                chk("[%s] K2 the mark is the class's full-colour drawing (its own cbx ids) on the lit ring (--cb-ring %s)" % (tag, k2["ring"][:40]),
                    k2["ids"] and all(i.startswith("cbx") for i in k2["ids"]) and full[cls] in k2["fills"] and k2["lit"] and not k2["coin"], k2)
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
                pq = load(br, dev, cls, query="?classbtn=c"); nodot(pq); c, rc = shot(pq)
                d4 = diff(a, c)
                chk("[%s] K4 ?classbtn=c changes nothing (no data-classbtn, mean %.2f)" % (tag, d4["mean"]),
                    pq.evaluate("()=>document.documentElement.getAttribute('data-classbtn')") is None and d4["mean"] < 1.0, {"attr": pq.evaluate("()=>document.documentElement.getAttribute('data-classbtn')"), "diff": d4})
                chk("[%s] no page errors" % tag, not (pg.errs or pq.errs), (pg.errs + pq.errs)[:3])
                pq.ctx.close()
            pg.ctx.close(); pp.ctx.close()
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
