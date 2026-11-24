"""The class button is option B, the liquid glass - exactly the one Madison circled (classglass, on 384.133).
History: shown three looks behind ?classbtn=a|b|c (branch claude/b384-classbtn, 5f85d51) he picked C, the medallion ("Option c for
the class thing.", 384.94), then A with C live ("Try option a, the lit ring.", 384.98), and then, with the option sheet in front of
him, circled B: "The class buttons, why do I kinda prefer the ones I circled? Ensure that's updated app wide, anywhere it's supposed
to be, update it." (REVISED for classglass: K1/K1b compared with ?classbtn=a and K2 asked for the lit ring's --cb-ring; both were
the A decision, now superseded.)

  K1  the button on Home, both classes, on an iPhone 17 Pro Max (installed), an iPad Pro 11" and a laptop, is pixel for pixel the
      preview he saw (5f85d51 loaded with ?classbtn=b): the same rim, arc, foot, light and mark (mean channel difference under
      1.0, no pixel more than 24 out - antialiasing only). Reduce motion on both, so the light stands still at the same opacity.
      The new dot (384.98, a .new-dot child of the button) is hidden by rule on both sides, as is the old one (the button's
      ::after), so this compares the button and not the dot.
  K1b the same with the button's "something new" state on, on both sides (the 329 ring round it, still under Reduce motion), the
      dot hidden by rule. The preview's Reduce-motion rule for B's light also caught that ring and held it at .8 instead of its own
      .5; the build keeps 329's .5 (the light rule is :not(.has-new)), so the preview side is given 329's .5 back by rule.
  K1c ...and with the dot shown (this build), the dot is there on B's button: drawn, on the button's corner on the 45-degree line.
  K2  the mark on the button is the class's full-colour drawing (classBtnIcon: its own cbx ids, the class list's colours) and the
      button is the liquid glass: a transparent border (1.5px; Chromium reports it floored to 1px) over a border-box gradient rim that ends in the class's colour, the light
      behind the mark (::before, a radial in the class's colour, breathing with motion on, still at .8 under Reduce motion), no
      lit ring (--cb-ring) and no medallion (--bezel);
  K3  the class list (the button opened, with both classes enrolled) shows the other class in its full-colour mark;
  K4  nothing is left of the choice: ?classbtn=c (and ?classbtn=a) in the address set no data-classbtn and change no pixel.
Run:  python3 tools/check-b384-classbtn.py [--against REV|DIR]   (--against 384.133 final, the lit ring, must FAIL K1, K1b, K2)"""
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
        pg.goto(G.URL + ("?classbtn=b" if pick else query)); pg.wait_for_timeout(3200)
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
def has_new(pg, pick=False):
    pg.evaluate("()=>{ try{ newClassPulseOn = true; }catch(e){} showHome(); }"); pg.wait_for_timeout(1800); G.clear_popups(pg)
    pg.evaluate("()=>{ const w = document.querySelector('.class-bubble-wrap'); if(w) w.classList.add('has-new'); }"); pg.wait_for_timeout(400)
    if pick:   # the preview's B light rule held 329's ring at .8 under Reduce motion; 329's own still ring is .5 (see K1b)
        pg.evaluate("()=>{ const s = document.createElement('style'); s.textContent = 'html[data-reduce-motion=\"true\"][data-classbtn] body .class-bubble-wrap.has-new .class-bubble::before{ opacity:.5 !important; }'; document.body.appendChild(s); }")
        pg.wait_for_timeout(200)

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
            chk("[%s] K1 the button is option B as he saw it, pixel for pixel, the dot hidden on both (mean %.2f, max %s)" % (tag, d["mean"], d["max"]),
                d["mean"] < 1.0 and d["max"] <= 24 and ra == rb, {"diff": d, "build": ra, "picked": rb, "picked has data-classbtn": pp.evaluate("()=>document.documentElement.getAttribute('data-classbtn')")})
            if dev in ("promax", "ipad"):
                # K1b: the button's "something new" state on both sides, the dot still hidden by rule
                has_new(pg); has_new(pp, pick=True)
                a2, ra2 = shot(pg); b2, rb2 = shot(pp); d2 = diff(a2, b2)
                chk("[%s] K1b with something new on both (the 329 ring), the dot hidden: still B, pixel for pixel (mean %.2f, max %s)" % (tag, d2["mean"], d2["max"]),
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
                chk("[%s] K1c the new dot is on B's button: drawn (%.0fpx), on its corner on the 45-degree line (%s, %s)" % (tag, k1c["w"], k1c["dx"], k1c["dy"]),
                    k1c["vis"] and 8 <= k1c["w"] <= 10.5 and abs(k1c["dx"] - k1c["dy"]) <= 1.5 and 0 <= k1c["dx"] <= k1c["hw"] / 3, k1c)
            if dev == "promax":
                pg.evaluate("()=>{ document.getElementById('__nodot')?.remove(); try{ newClassPulseOn = false; }catch(e){} showHome(); }"); pg.wait_for_timeout(1500)
                k2 = pg.evaluate(r"""()=>{ const b = document.querySelector('.class-bubble'); const svg = b && b.querySelector(':scope > svg');
                  const ids = svg ? [...svg.querySelectorAll('[id]')].map(e => e.id) : [];
                  const fills = svg ? [...svg.querySelectorAll('stop')].map(s => s.getAttribute('stop-color')) : [];
                  const cs = b ? getComputedStyle(b) : null, be = b ? getComputedStyle(b, '::before') : null;
                  const cbc = cs ? cs.getPropertyValue('--cbc').trim() : '';
                  const t = document.createElement('i'); t.style.color = cbc; document.body.appendChild(t); const cbcRgb = getComputedStyle(t).color; t.remove();
                  const bg = cs ? cs.backgroundImage : '', clip = cs ? cs.backgroundClip : '';
                  const layers = bg.split(/,(?![^(]*\))/).length;
                  const lastGrad = bg.slice(bg.lastIndexOf('linear-gradient('));
                  return { ids, fills, ring: cs ? cs.getPropertyValue('--cb-ring').trim() : '', coin: cs ? cs.getPropertyValue('--bezel').trim() : '',
                    border: cs ? [cs.borderTopWidth, cs.borderTopColor] : null, clip, rim: lastGrad.slice(0, 220), cbc, cbcRgb,
                    light: be ? { content: be.content, bg: be.backgroundImage.slice(0, 120), anim: be.animationName, op: be.opacity, pos: be.position } : null,
                    w: b ? b.getBoundingClientRect().width : 0 }; }""")
                rgbnum = lambda c: [int(round(float(x))) for x in __import__("re").findall(r"[\d.]+", c)[:3]]
                clsrgb = rgbnum(k2["cbcRgb"]) if k2["cbcRgb"] else []
                rim_ok = bool(k2["border"]) and float(k2["border"][0][:-2]) >= .99 and k2["border"][1] in ("rgba(0, 0, 0, 0)", "transparent") \
                    and k2["clip"].rstrip().endswith("border-box") and "linear-gradient" in k2["rim"]
                lit = k2["light"] or {}
                light_ok = lit.get("content") not in (None, "none", "normal") and "radial-gradient" in lit.get("bg", "") and lit.get("anim") == "none" and abs(float(lit.get("op") or 0) - .8) < .02
                full = {"ifc": "#FF6B35", "academy": "#5470F2"}
                chk("[%s] K2 the mark is the class's full-colour drawing (its own cbx ids) on the liquid glass (a %s transparent rim over a border-box gradient, the light behind the mark still at %s under Reduce motion), no lit ring, no coin" % (tag, k2["border"] and k2["border"][0], lit.get("op")),
                    k2["ids"] and all(i.startswith("cbx") for i in k2["ids"]) and full[cls] in k2["fills"] and rim_ok and light_ok and not k2["ring"] and not k2["coin"], k2)
                # with motion on, the light breathes (opacity + transform only)
                mv = pg.evaluate("""()=>{ theme.reduceMotion = false; try{ applyTheme(); }catch(e){} const b = document.querySelector('.class-bubble'); const be = b && getComputedStyle(b, '::before');
                  const an = be ? be.animationName : ''; let props = [];
                  for(const sh of document.styleSheets){ let rs; try{ rs = sh.cssRules; }catch(e){ continue; } for(const r of rs){ if(r.type === 7 && r.name === an){ for(const k of r.cssRules) for(let i = 0; i < k.style.length; i++) props.push(k.style[i]); } } }
                  const out = { anim: an, dur: be ? be.animationDuration : '', props: [...new Set(props)] }; theme.reduceMotion = true; try{ applyTheme(); }catch(e){} return out; }""")
                chk("[%s] K2b with motion on, the light behind the mark breathes (%s, %s), opacity and transform only (%s)" % (tag, mv["anim"], mv["dur"], mv["props"]),
                    mv["anim"] not in ("", "none") and mv["props"] and set(mv["props"]) <= {"opacity", "transform"}, mv)
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
                errs = list(pg.errs)
                for q in ("?classbtn=c", "?classbtn=a"):
                    pq = load(br, dev, cls, query=q); nodot(pq); c, rc = shot(pq)
                    d4 = diff(a, c)
                    chk("[%s] K4 %s changes nothing (no data-classbtn, mean %.2f)" % (tag, q, d4["mean"]),
                        pq.evaluate("()=>document.documentElement.getAttribute('data-classbtn')") is None and d4["mean"] < 1.0, {"attr": pq.evaluate("()=>document.documentElement.getAttribute('data-classbtn')"), "diff": d4})
                    errs += pq.errs; pq.ctx.close()
                chk("[%s] no page errors" % tag, not errs, errs[:3])
            pg.ctx.close(); pp.ctx.close()
    br.close()
print("\n%s - %d failed" % ("ALL PASS" if not G.fails else "FAIL", len(G.fails)))
sys.exit(1 if G.fails else 0)
