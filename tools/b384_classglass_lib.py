"""Shared by check-b384-classmarks.py and check-b384-classcards.py (classglass): is a class circle Home's class button's
liquid glass (option B), read against a probe of the button on the same page?

ONE_JS is a JS function source `el => {...}` that reads one circle; PROBE_JS(key) builds and reads a probe of Home's button
(54px, inside a .class-bubble-wrap without has-new, so its light is on as on Home); glass(e, ref) judges."""
import re

ONE_JS = r"""(el => { if(!el) return null; const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
    const svg = el.matches('svg') ? el : el.querySelector(':scope > svg');
    const be = getComputedStyle(el, '::before');
    return { w: Math.round(r.width * 10) / 10, R: el.clientWidth / 2, ring: cs.getPropertyValue('--cb-ring').trim(), bg: cs.backgroundImage,
      clip: cs.backgroundClip, border: cs.borderTopColor, bw: parseFloat(cs.borderTopWidth) || 0, shadow: cs.boxShadow, svg: svg ? svg.outerHTML.replace(/cbx\d+-/g, 'cbx-') : '',
      light: { content: be.content, bg: be.backgroundImage, inset: (parseFloat(be.top) || 0) / (r.height || 1), z: be.zIndex, svgZ: svg ? getComputedStyle(svg).zIndex : '' },
      vis: r.width > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' }; })"""
PROBE_JS = r"""(key => { const pw = document.createElement('span'); pw.className = 'class-bubble-wrap'; pw.style.cssText = 'position:fixed;left:-300px;top:0';
    const probe = document.createElement('span'); probe.className = 'class-bubble is-' + key;
    probe.style.cssText = 'position:relative;display:block;width:54px;height:54px;box-sizing:border-box';
    pw.appendChild(probe); document.body.appendChild(pw); const ref = (""" + ONE_JS + r""")(probe); pw.remove(); return ref; })"""

def colours(s): return re.findall(r"(?:rgba?|color|oklab|color-mix)\([^()]*(?:\([^()]*\)[^()]*)*\)", s)
def layers(bg): return [x.strip() for x in re.split(r",(?![^(]*(?:\([^()]*\)[^()]*)*\))", bg)]
def geom(layer):
    """a gradient layer with its colours taken out: its shape and stop positions"""
    g = layer
    for c in colours(layer): g = g.replace(c, "C")
    return re.sub(r"\s+", " ", g)
def tint(shadow):
    """(y, blur, spread, colour) of the shadow in the class's colour (not the plain black drop)"""
    for p in re.split(r",(?![^(]*\))", shadow):
        cols = colours(p); rest = p
        for c in cols: rest = rest.replace(c, "")
        nums = [float(x[:-2]) for x in re.findall(r"-?[\d.]+px", rest)]
        if cols and "inset" not in p and len(nums) >= 3 and not re.match(r"rgba?\(0, 0, 0", cols[0]) and nums[2] > 0:
            return (nums[1], nums[2], nums[3] if len(nums) > 3 else 0, cols[0])
    return None

def glass(e, ref):
    """(ok, summary, info): e is the button's liquid glass at e's size.
    - five layers: arc, foot, sheen, body (padding-box) and the rim (border-box), the same shapes and stops; the same colours
      (the body may be its own: the class list's is more opaque); a transparent border, its width the button's 1.5px as the same
      share of the size (never under 1px; Chromium reads widths floored to whole px, so within 1px);
    - the light behind the mark: ::before, the same radial in the same colours, inset the same share, under the mark;
    - the class-coloured shadow: the same colour, its blur the same share of the size (within 25%);
    - no lit ring (--cb-ring) on either."""
    le, lr = layers(e["bg"]), layers(ref["bg"])
    ok_glass = len(lr) == 5 and ref["clip"].replace(" ", "").split(",")[-1] == "border-box" and len(le) == len(lr) \
        and [colours(x) for i, x in enumerate(le) if i != 3] == [colours(x) for i, x in enumerate(lr) if i != 3] \
        and [geom(x) for x in le] == [geom(x) for x in lr] and e["clip"] == ref["clip"] \
        and e["border"] in ("rgba(0, 0, 0, 0)", "transparent") and e["border"] == ref["border"]
    want_bw = max(1.0, ref["bw"] * e["w"] / max(ref["w"], 1))
    # (Chromium floors a border's computed width to whole CSS px: the button's 1.5px reads 1 here; WebKit draws 1.5 at 3x)
    ok_bw = ref["bw"] >= .99 and e["bw"] >= .99 and abs(e["bw"] - want_bw) <= 1
    el_, rl = e["light"], ref["light"]
    zi = lambda v: int(v) if str(v).lstrip("-").isdigit() else 0
    ok_light = rl["content"] not in ("none", "normal") and el_["content"] == rl["content"] and "radial-gradient" in rl["bg"] \
        and el_["bg"] == rl["bg"] and abs(el_["inset"] - rl["inset"]) <= .02 and zi(el_["svgZ"]) > zi(el_["z"])
    te, tr = tint(e["shadow"]), tint(ref["shadow"])
    sh = lambda v, w: v / max(w, 1)
    ok_tint = bool(te and tr) and te[3] == tr[3] and abs(sh(te[1], e["w"]) - sh(tr[1], ref["w"])) <= .25 * sh(tr[1], ref["w"])
    ok = ok_glass and ok_bw and ok_light and ok_tint and not e["ring"] and not ref["ring"]
    summary = "rim %.2fpx, the button's %.2f; light inset %.3f vs %.3f; class shadow %s vs %s" % (
        e["bw"], ref["bw"], el_["inset"], rl["inset"], te and te[1], tr and tr[1])
    info = {"glass": ok_glass, "bw": ok_bw, "light": ok_light, "tint": ok_tint, "ring": [e["ring"], ref["ring"]],
            "layers": [le[:5], lr[:5]], "clip": [e["clip"], ref["clip"]], "border": [e["border"], ref["border"]], "lights": [el_, rl], "shadows": [te, tr]}
    return ok, summary, info
