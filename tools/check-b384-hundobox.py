"""Build 384, round 6: the hundo's grade box is the app's card, with the effect's colour as a glow on it - in every class.
Madison: "The Hundo effects are cool, but the grade box has the old look and not the new one.. here's the thing though, it
doesn't need to be the exact new one because we still need hundo grade boxes to be cool. Just still make it cohesive app wide
all classes."
Until now a 100% in any effect but Confetti turned its box back into the old card (translucent glass, a gradient wash, a
coloured rim, the grade's red / green frame) beside XP and Level cards that were solid. For each rung's effect, in the Fire
Code class and in the Police Academy, a results screen's grade box in that effect's colours (hfxTintGrade, as the landing does it)
is read off the page next to the XP card:
 (B1) it is the SAME card: its colour is the XP card's, fully opaque, no gradient on the card itself, no backdrop blur, NO BORDER
      (round 2: it is the XP card's border, none - the one hairline in the effect's colour is gone), and the grade's coloured frame
      (.rs-grade-tone) is not drawn - on every effect;
 (B2) it is still special: its light layer (.hfx-tint) is on (shown), sits behind the words, carries a wash down from the top and a
      pool behind the number in the effect's colour - and no box-shadow, so no rim and no glow off the edge (round 2);
 (B3) and the light is the EFFECT'S colour, proved from the layer's own gradients (the border no longer carries it), differing between at least
      three of the four effects;
 (B4) Confetti's box (untinted) is that card as well (no glow layer: the plain card with its gold number, as it was).
Run:  python3 tools/check-b384-hundobox.py   (--against OLD/index.html must FAIL)"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "check-b384-extspr.py")).read().split("\nsrv, port = serve()")[0]
G = {"__file__": os.path.join(HERE, "check-b384-extspr.py"), "__name__": "b384hundobox"}
exec(src, G)
ok = True
def chk(name, cond, info=""):
    global ok; ok = ok and bool(cond); print(("PASS " if cond else "FAIL ") + name, "" if cond else "  -> " + str(info)[:500], flush=True)

PROBE = r"""(ids) => {
  const stage = document.getElementById('stage');
  document.body.classList.remove('sky-home');   /* Home's sky is not on a results screen */
  const out = { _html: [document.documentElement.dataset.theme, document.documentElement.dataset.layout] };
  const mk = () => {
    const sc = document.createElement('div'); sc.className = 'rs-screen';
    const xp = document.createElement('div'); xp.className = 'rs-card rs-xp'; xp.textContent = 'XP';
    const gr = document.createElement('div'); gr.className = 'rs-card rs-grade is-perfect';
    const tone = document.createElement('div'); tone.className = 'rs-grade-tone';
    ['is-red', 'is-green'].forEach(c => { const i = document.createElement('i'); i.className = c; tone.appendChild(i); });
    gr.appendChild(tone);
    const pct = document.createElement('span'); pct.className = 'rs-pct pct perfect'; gradePctMarkup(pct, 100); gr.appendChild(pct);
    sc.appendChild(gr); sc.appendChild(xp); stage.replaceChildren(sc);
    return { sc, xp, gr, tone, pct };
  };
  const a = (c) => (c.match(/[\d.]+/g) || []).map(Number);
  const read = (e) => { const cs = getComputedStyle(e); return { bg: cs.backgroundColor, img: cs.backgroundImage, blur: cs.backdropFilter || cs.webkitBackdropFilter || 'none', rim: cs.borderTopColor, shadow: cs.boxShadow }; };
  ids.forEach(id => {
    const m = mk();
    if(id !== 'confetti') hfxTintGrade(m.gr, id);
    const g = read(m.gr), x = read(m.xp), t = m.gr.querySelector(':scope > .hfx-tint');
    const r = { bw: getComputedStyle(m.gr).borderTopWidth, g, x, tone: getComputedStyle(m.tone).display, tinted: m.gr.classList.contains('hfx-tinted') };
    if(t){ const ts = getComputedStyle(t); r.t = { op: +ts.opacity, z: ts.zIndex, img: ts.backgroundImage, shadow: ts.boxShadow, pos: ts.position }; }
    r.num = getComputedStyle(m.pct).backgroundImage;
    r.vars = ['--hfx-b', '--hfx-glow', '--hfx-rimglow'].map(k => m.gr.style.getPropertyValue(k));
    out[id] = r;
  });
  return out;
}"""

def shadows(s):
    """[(blur, spread, inset, alpha)] from a computed box-shadow"""
    out = []
    items = re.split(r",\s*(?![^()]*\))", s or "")
    for it in items:
        it = it.strip()
        if not it or it == "none": continue
        inset = "inset" in it
        col = re.search(r"(rgba?\([^)]*\)|color\([^)]*\))", it)
        nums = [float(n) for n in re.findall(r"(?<![\d.#a-z])(-?[\d.]+)px", re.sub(r"(rgba?\([^)]*\)|color\([^)]*\))", "", it))]
        alpha = 1.0
        if col:
            c = col.group(1)
            if c.startswith("rgba"): alpha = float(re.findall(r"[\d.]+", c)[3]) if len(re.findall(r"[\d.]+", c)) > 3 else 1
            elif c.startswith("color"): m = re.search(r"/\s*([\d.]+)", c); alpha = float(m.group(1)) if m else 1
        blur = nums[2] if len(nums) > 2 else 0; spread = nums[3] if len(nums) > 3 else 0
        out.append((blur, spread, inset, alpha))
    return out

srv, port = G["serve"]()
IDS = ["confetti", "fireworks", "underwater", "bubbles", "ufo"]
res = {}
with G["sync_playwright"]() as pw:
    br = pw.chromium.launch(executable_path=G["CHROME"])
    for cls in ("ifc", "academy"):
        init = G["INIT"] if cls == "ifc" else G["INIT"].replace("localStorage.setItem('class26e.activeclass','ifc');localStorage.setItem('class26e.enrolled',JSON.stringify(['ifc']));localStorage.setItem('class26e.greet.ifc','done');", "")
        ctx = br.new_context(viewport={"width": 440, "height": 956}, device_scale_factor=1)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:300]))
        pg.add_init_script(init)
        pg.route("**/index.html", lambda r: r.fulfill(status=200, headers={"content-type": "text/html; charset=utf-8"}, body=G["BODY"]))
        pg.goto("http://127.0.0.1:%d/index.html" % port); pg.wait_for_timeout(2800)
        pg.evaluate("()=>{ document.getElementById('splashscreen')?.remove(); }")
        res[cls] = (pg.evaluate("() => window.NOVA_CLASS"), pg.evaluate(PROBE, IDS), errs)
        ctx.close()
    br.close()

for cls in ("ifc", "academy"):
    nc, R, errs = res[cls]
    chk("%s: the page is in the %s class (%s)" % (cls, cls, nc), (nc == "ifc") == (cls == "ifc"), nc)
    hues = set()
    print(cls, 'html', R.get('_html'))
    for id in IDS:
        r = R[id]; g, x = r["g"], r["x"]
        same = g["bg"] == x["bg"] and "/" not in g["bg"] and not re.search(r"rgba\(.*,\s*0?\.\d+\)$|,\s*0\)$", g["bg"])
        edge = lambda c: re.search(r"(,\s*0\)|/\s*0\))$", c or "") is not None or c in ("transparent", "rgba(0, 0, 0, 0)")
        chk("(B1) %s %s: the box is the XP card - same colour (%s / %s), opaque, no gradient, no blur, no shadow on the card itself, no tone frame (%s), and NO BORDER of its own (the XP card's is %s, its is %s, %s)" % (cls, id, g["bg"], x["bg"], r["tone"], x["rim"], g["rim"], r["bw"]),
            same and g["img"] == "none" and g["blur"] in ("none", "") and r["tone"] == "none" and g["shadow"] == "none" and edge(g["rim"]) and g["rim"] == x["rim"], r)
        if id == "confetti":
            chk("(B4) %s confetti: untinted, no glow layer, the plain card" % cls, not r["tinted"] and "t" not in r, r)
            continue
        t = r.get("t")
        sh = shadows(t["shadow"]) if t else []
        rgbs = [tuple(float(n) for n in m[:3]) for m in (re.findall(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)(?:,\s*([\d.]+))?\)", (t or {}).get("img", "")))] if t else []
        cs = [tuple(float(n) * 255 for n in m) for m in re.findall(r"color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)", (t or {}).get("img", ""))]
        lay = rgbs + cs
        chk("(B2) %s %s: the light layer is on, behind the words (z %s): a wash down from the top and a pool behind the number (two gradients), and NO box-shadow at all (no rim, no glow off the edge)" % (cls, id, t and t["z"]),
            t and t["op"] == 1 and t["z"] == "-1" and (t["img"] or "").count("gradient(") >= 2 and not sh, [t, sh])
        hues.add(r["vars"][0])
        hx = r["vars"][0].strip().lstrip("#")
        want = tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4)) if len(hx) == 6 else None
        near = lambda a, b: max(abs(a[i] - b[i]) for i in range(3)) <= 14
        chk("(B3) %s %s: the light is the effect's colour (%s) - proved from the layer's own gradients (%s), and the number's ramp is in it" % (cls, id, r["vars"][0], lay[:2]),
            want and lay and any(near(c, want) for c in lay) and "gradient" in r["num"], [r["vars"], lay, t and t["img"]])
    chk("(B3) %s: the four effects glow in different colours (%s)" % (cls, sorted(hues)), len(hues) >= 3, hues)
    chk("no page errors (%s)" % cls, not errs, errs[:2])
print("ALL PASS" if ok else "SOME FAILED")
sys.exit(0 if ok else 1)
